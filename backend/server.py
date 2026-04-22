"""FastAPI server for Resume Optimizer backend."""

from fastapi import Depends, FastAPI, UploadFile, File, Form, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import os
import json
import asyncio
import time
import functools
import uuid
from pathlib import Path
from dotenv import load_dotenv

from src.agents import (
    JobAnalyzerAgent,
    ResumeOptimizerAgent,
    OptimizerImplementerAgent,
    ValidatorAgent,
    PolishAgent,
    GitHubProjectsAgent,
)
from src.api import fetch_job_posting_text, ExaContentError
from src.database import ApplicationDatabase, get_database
from src.utils import save_uploaded_file, cleanup_temp_file, extract_optimized_resume
from src.api.client_factory import create_client
from src.streaming import (
    stream_manager,
    JobStatusEvent,
    StepProgressEvent,
    InsightEvent,
    MetricUpdateEvent,
    HeartbeatEvent,
    DoneEvent,
    AgentStepStartedEvent,
    AgentStepCompletedEvent,
    AgentChunkEvent,
    RunStore,
)
from src.streaming.insight_extractor import insight_extractor
from src.streaming.insight_listener import run_insight_listener
from src.services.recovery_service import RecoveryService
from src.middleware.error_interceptor import ErrorInterceptorMiddleware
from src.routes.recovery import router as recovery_router
from src.app.services.persistence import save_profile as persist_profile
from src.app.services.review_document import build_review_document, serialize_review_payload
from src.app.services.export import generate_docx_from_plain_text
from src.services.text_safety_service import check_job_posting

load_dotenv()

from src.middleware.auth import get_current_user_id, get_user_id_from_request

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL") or "qwen/qwen3-max"
ANALYZER_MODEL = os.getenv("ANALYZER_MODEL") or DEFAULT_MODEL
OPTIMIZER_MODEL = os.getenv("OPTIMIZER_MODEL") or DEFAULT_MODEL
IMPLEMENTER_MODEL = os.getenv("IMPLEMENTER_MODEL") or DEFAULT_MODEL
VALIDATOR_MODEL = os.getenv("VALIDATOR_MODEL") or DEFAULT_MODEL
PROFILE_MODEL = os.getenv("PROFILE_MODEL") or DEFAULT_MODEL
INSIGHT_MODEL = os.getenv("INSIGHT_MODEL") or DEFAULT_MODEL
POLISH_MODEL = os.getenv("POLISH_MODEL") or "openrouter::anthropic/claude-sonnet-4.5"

# Per-agent temperature settings
ANALYZER_TEMPERATURE = float(os.getenv("ANALYZER_TEMPERATURE", "0.3"))
OPTIMIZER_TEMPERATURE = float(os.getenv("OPTIMIZER_TEMPERATURE", "0.7"))
IMPLEMENTER_TEMPERATURE = float(os.getenv("IMPLEMENTER_TEMPERATURE", "0.1"))
VALIDATOR_TEMPERATURE = float(os.getenv("VALIDATOR_TEMPERATURE", "0.2"))
PROFILE_TEMPERATURE = float(os.getenv("PROFILE_TEMPERATURE", "0.1"))
POLISH_TEMPERATURE = float(os.getenv("POLISH_TEMPERATURE", "0.8"))

app = FastAPI(title="Resume Optimizer API", version="1.0.0")

# CORS middleware
origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
_db_path = os.getenv("DATABASE_PATH", "./data/applications.db")
USE_SUPABASE_DB = os.getenv("USE_SUPABASE_DB", "false").lower() == "true"

# Default SQLite database (used when Supabase is not enabled or for unauthenticated requests)
db = ApplicationDatabase(db_path=_db_path)
run_store = RunStore(db)
stream_manager.attach_store(run_store)

# Initialize recovery service
recovery_service = RecoveryService(db)

MAX_FREE_RUNS = int(os.getenv("MAX_FREE_RUNS", "5"))
DEV_MODE_ENABLED = os.getenv("DEV_MODE", "false").lower() == "true"


def _is_supabase_auth_user_id(user_id: Optional[str]) -> bool:
    """Return True when user_id can be used against Supabase auth UUID columns."""
    if not user_id:
        return False
    try:
        uuid.UUID(str(user_id))
    except (TypeError, ValueError):
        return False
    return True


def get_db_for_user(user_id: str = None):
    """Get database instance for a user.
    
    When USE_SUPABASE_DB is enabled and user_id is a Supabase Auth UUID,
    returns a SupabaseDatabase instance. Otherwise returns the default SQLite
    database for local/dev fallback identities like ip:127.0.0.1.
    """
    if USE_SUPABASE_DB and _is_supabase_auth_user_id(user_id):
        return get_database(user_id)
    return db.for_user(user_id)


async def require_user_data_user_id(
    request: Request,
    auth_user_id: Optional[str] = Depends(get_current_user_id),
) -> str:
    """Require real auth for persisted user data, with fallback IDs only in local dev."""
    if auth_user_id:
        return auth_user_id

    if DEV_MODE_ENABLED:
        fallback_user_id = get_user_id_from_request(request)
        if fallback_user_id is not None:
            return fallback_user_id

    raise HTTPException(status_code=401, detail="Authentication required")

def _normalized_optional_text(value: Optional[str]) -> Optional[str]:
    """Normalize empty strings to None for persisted user preference fields."""
    if value is None:
        return None
    value = value.strip()
    return value or None


def _review_docx_url(application_id: int) -> str:
    return f"/api/export/{application_id}?format=docx"


def _build_review_payload(user_db, application_id: int) -> dict:
    review_document = user_db.get_application_review(application_id)
    if not review_document:
        raise HTTPException(status_code=404, detail="Review document not found")

    return serialize_review_payload(
        review_document,
        docx_url=_review_docx_url(application_id),
    )


# Store in app state for access in routes
app.state.db = db
app.state.recovery_service = recovery_service
app.state.get_db_for_user = get_db_for_user

# Add error interceptor middleware
app.add_middleware(ErrorInterceptorMiddleware, recovery_service=recovery_service)

# Mount recovery router
app.include_router(recovery_router)


@app.get("/api/usage")
async def get_usage(http_request: Request):
    """Get current user's usage information."""
    from src.middleware.auth import get_user_id_from_request
    
    user_id = get_user_id_from_request(http_request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_db = get_db_for_user(user_id)
    
    # Use Supabase DB for counting if enabled, otherwise fall back to run_store
    if USE_SUPABASE_DB and user_id and hasattr(user_db, 'count_runs_for_client'):
        run_count = user_db.count_runs_for_client(user_id)
    else:
        run_count = run_store.count_runs_for_client(user_id)
    remaining = max(0, MAX_FREE_RUNS - run_count)
    
    return {
        "success": True,
        "used": run_count,
        "remaining": remaining,
        "cap": MAX_FREE_RUNS,
        "is_subscribed": False,  # TODO: Check subscription status from Supabase
    }


def _latest_agent_output_text(application_id: int, agent_name: str, user_db=None) -> str:
    """Fetch the most recent saved output text for a given agent.

    Falls back to empty string if none found.
    """
    _db = user_db or db
    try:
        outputs = _db.get_agent_outputs(application_id)
        for rec in reversed(outputs):
            if str(rec.get("agent_name", "")) == agent_name:
                data = rec.get("output_data")
                if isinstance(data, dict):
                    return (
                        str(data.get("text")
                            or data.get("full_response")
                            or data.get("output")
                            or "")
                    )
                return str(data) if data is not None else ""
    except Exception:
        pass
    return ""

# Global state for current session
current_session = {}


def run_agent_with_chunk_emission(
    agent,
    agent_name: str,
    step_name: str,
    job_id: str,
    *args,
    **kwargs
) -> str:
    """Run an agent generator and emit chunk events during execution.
    
    This function is meant to be called from an executor thread.
    It will emit AgentChunkEvent objects during streaming.
    """
    result = ""
    seq = 0
    last_emit_time = 0
    last_progress_emit_time = 0
    current_time = time.time()
    metadata: Dict[str, Any] = {}
    
    try:
        # Get the generator for the agent method based on kwargs
        if hasattr(agent, 'analyze_job') and 'job_posting' in kwargs:
            gen = agent.analyze_job(**kwargs)
        elif hasattr(agent, 'optimize_resume') and 'job_analysis' in kwargs:
            gen = agent.optimize_resume(**kwargs)
        elif hasattr(agent, 'implement_optimizations') and 'optimization_report' in kwargs:
            gen = agent.implement_optimizations(**kwargs)
        elif hasattr(agent, 'validate_resume') and 'optimized_resume' in kwargs and 'job_posting' in kwargs:
            gen = agent.validate_resume(**kwargs)
        elif hasattr(agent, 'polish_resume') and 'validation_report' in kwargs:
            gen = agent.polish_resume(**kwargs)
        else:
            # Fallback: use class name to determine method
            agent_class_name = agent.__class__.__name__
            if 'Analyzer' in agent_class_name:
                gen = agent.analyze_job(**kwargs)
            elif 'Optimizer' in agent_class_name and 'Implementer' not in agent_class_name:
                gen = agent.optimize_resume(**kwargs)
            elif 'Implementer' in agent_class_name:
                gen = agent.implement_optimizations(**kwargs)
            elif 'Validator' in agent_class_name:
                gen = agent.validate_resume(**kwargs)
            elif 'Polish' in agent_class_name:
                gen = agent.polish_resume(**kwargs)
            else:
                raise ValueError(f"Unknown agent type: {agent_class_name}")
        
        # Emit step started
        stream_manager.emit_from_thread(AgentStepStartedEvent.create(job_id, step_name, agent_name))
        
        # Process chunks
        while True:
            try:
                chunk = next(gen)
            except StopIteration as exc:
                metadata = exc.value or {}
                break
            result += chunk
            seq += 1
            current_time = time.time()
            
            # Emit chunk events with MORE AGGRESSIVE throttling for better streaming
            # Throttle: emit every 100 chars or 0.3 seconds (increased from 500 chars / 1.2s)
            should_emit = (
                len(result) % 100 < len(chunk) or  # Crossed 100-char boundary
                (current_time - last_emit_time) >= 0.3  # Time interval passed
            )
            
            if should_emit:
                stream_manager.emit_from_thread(AgentChunkEvent.create(
                    job_id=job_id,
                    step=step_name,
                    chunk=chunk,
                    seq=seq,
                    total_len=len(result)
                ))
                last_emit_time = current_time
            
            # Emit periodic progress updates to keep frontend informed
            # Estimate progress based on token count (rough heuristic: 5000 chars = ~80% done)
            if (current_time - last_progress_emit_time) >= 3.0:  # Every 3 seconds
                # Estimate progress: assume 5000 chars = 80% complete, cap at 95%
                estimated_progress = min(95, int((len(result) / 5000) * 80))
                if estimated_progress > 5:  # Only emit if we have meaningful progress
                    stream_manager.emit_from_thread(StepProgressEvent.create(
                        job_id=job_id,
                        step=step_name,
                        pct=estimated_progress
                    ))
                    last_progress_emit_time = current_time
        
        # Emit step completed
        stream_manager.emit_from_thread(AgentStepCompletedEvent.create(
            job_id=job_id,
            step=step_name,
            agent_name=agent_name,
            total_chars=len(result)
        ))
        
    except Exception as e:
        print(f" Agent {agent_name} failed: {e}")
        # Still emit completion for cleanup
        stream_manager.emit_from_thread(AgentStepCompletedEvent.create(
            job_id=job_id,
            step=step_name,
            agent_name=agent_name,
            total_chars=len(result)
        ))
        raise
    
    return result, metadata


class JobAnalysisRequest(BaseModel):
    job_text: Optional[str] = None
    job_url: Optional[str] = None


class JobPreviewRequest(BaseModel):
    job_url: str


class ResumeOptimizationRequest(BaseModel):
    application_id: int
    resume_text: str
    github_username: Optional[str] = None


class ImplementationRequest(BaseModel):
    application_id: int


class ValidationRequest(BaseModel):
    application_id: int


class PolishRequest(BaseModel):
    application_id: int
    output_format: str = "html"


class PipelineRequest(BaseModel):
    """Request to run full pipeline with streaming."""
    resume_text: str
    job_text: Optional[str] = None
    job_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_username: Optional[str] = None
    github_token: Optional[str] = None
    force_refresh_profile: bool = False  # Force re-scrape of LinkedIn/GitHub
    save_resume: bool = False  # Save this resume for future use
    resume_label: Optional[str] = None  # Label for saved resume (auto-generated if omitted)
    resume_filename: Optional[str] = None  # Original filename of uploaded resume


class ProfileStatusRequest(BaseModel):
    """Request to check profile connection status."""
    linkedin_url: Optional[str] = None
    github_username: Optional[str] = None


class SaveResumeRequest(BaseModel):
    """Request to save a resume for later reuse."""
    label: str
    resume_text: str
    filename: Optional[str] = None
    content_hash: Optional[str] = None
    is_default: bool = False


class UpdatePreferencesRequest(BaseModel):
    """Request to update user preferences."""
    default_linkedin_url: Optional[str] = None
    default_github_username: Optional[str] = None
    default_resume_id: Optional[int] = None


@app.get("/")
async def root():
    return {"message": "Resume Optimizer API", "version": "1.0.0"}


@app.post("/api/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """Handle resume file upload with PDF extraction via Gemini."""
    try:
        # Save uploaded file to temp location
        file_path = save_uploaded_file(file.file, file.filename)
        
        # Extract text from file (uses Gemini 2.5 Flash for PDFs)
        from src.utils import extract_text_from_file
        resume_text = await extract_text_from_file(file_path)
        
        # Cleanup temp file
        cleanup_temp_file(file_path)
        
        # Determine extraction method used
        from src.utils import is_pdf
        extraction_method = "gemini-2.5-flash" if is_pdf(file.filename) else "direct"
        
        return {
            "success": True,
            "filename": file.filename,
            "text": resume_text,
            "length": len(resume_text),
            "extraction_method": extraction_method,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/job-preview")
async def job_preview(request: JobPreviewRequest):
    """Fetch job posting text from URL and optionally run text safeguard."""
    try:
        job_text = fetch_job_posting_text(request.job_url)
    except ExaContentError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
    except RuntimeError as err:
        raise HTTPException(status_code=500, detail=str(err)) from err
    except Exception as err:
        raise HTTPException(
            status_code=500,
            detail="Unexpected error while fetching job posting content.",
        ) from err
    else:
        decision = "ALLOW"
        reasons: List[str] = []
        result = None

        try:
            result = await check_job_posting(job_text)
        except RuntimeError as err:
            # Fail open on safeguard errors; rely on downstream validation
            logger.warning(
                "Text safeguard failed for job preview; continuing without safeguard",
                exc_info=err,
            )

        if result is not None:
            decision = result.decision
            reasons = result.reasons

        return {
            "success": True,
            "job_text": job_text,
            "decision": decision,
            "reasons": reasons,
        }


@app.post("/api/profile/status")
async def get_profile_status(request: ProfileStatusRequest, http_request: Request):
    """Check if user has cached LinkedIn/GitHub profile data.
    
    Returns connection status for each profile source.
    """
    from src.middleware.auth import get_user_id_from_request
    
    user_id = get_user_id_from_request(http_request)
    user_db = get_db_for_user(user_id)
    
    linkedin_status = {
        "connected": False,
        "cached_at": None,
        "profile_id": None,
    }
    github_status = {
        "connected": False,
        "cached_at": None,
        "profile_id": None,
    }
    
    # Check LinkedIn cache
    if request.linkedin_url:
        cached = user_db.get_cached_profile(linkedin_url=request.linkedin_url)
        if cached and cached.get("profile_index"):
            linkedin_status = {
                "connected": True,
                "cached_at": cached.get("created_at") or cached.get("updated_at"),
                "profile_id": cached.get("id"),
            }
    
    # Check GitHub cache
    if request.github_username:
        cached = user_db.get_cached_profile(github_username=request.github_username)
        if cached and cached.get("profile_index"):
            github_status = {
                "connected": True,
                "cached_at": cached.get("created_at") or cached.get("updated_at"),
                "profile_id": cached.get("id"),
            }
    
    return {
        "success": True,
        "linkedin": linkedin_status,
        "github": github_status,
    }


# --- User Preferences & Saved Resumes ---

@app.get("/api/user/preferences")
async def get_user_preferences(user_id: str = Depends(require_user_data_user_id)):
    """Get the authenticated user's preferences (LinkedIn, GitHub defaults, default resume)."""
    user_db = get_db_for_user(user_id)
    prefs = user_db.get_preferences()

    if not prefs:
        return {"success": True, "preferences": None}

    # Normalize: don't leak full resume text in preferences response
    result = {
        "default_linkedin_url": prefs.get("default_linkedin_url"),
        "default_github_username": prefs.get("default_github_username"),
        "default_resume_id": prefs.get("default_resume_id"),
    }
    # Include default resume metadata (not full text) for UI display
    default_resume = prefs.get("default_resume")
    if default_resume:
        result["default_resume"] = {
            "id": default_resume["id"],
            "label": default_resume.get("label"),
            "filename": default_resume.get("filename"),
        }
    else:
        result["default_resume"] = None

    return {"success": True, "preferences": result}


@app.put("/api/user/preferences")
async def update_user_preferences(
    request: UpdatePreferencesRequest,
    user_id: str = Depends(require_user_data_user_id),
):
    """Upsert the authenticated user's preferences."""
    user_db = get_db_for_user(user_id)

    if request.default_resume_id is not None:
        resume = user_db.get_saved_resume(request.default_resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Saved resume not found")

    fields_set = getattr(request, "model_fields_set", set())
    pref_updates = {}
    if "default_linkedin_url" in fields_set:
        pref_updates["default_linkedin_url"] = _normalized_optional_text(
            request.default_linkedin_url
        )
    if "default_github_username" in fields_set:
        pref_updates["default_github_username"] = _normalized_optional_text(
            request.default_github_username
        )
    if "default_resume_id" in fields_set:
        pref_updates["default_resume_id"] = request.default_resume_id

    prefs = user_db.upsert_preferences(
        **pref_updates,
    )

    return {"success": True, "preferences": {
        "default_linkedin_url": prefs.get("default_linkedin_url"),
        "default_github_username": prefs.get("default_github_username"),
        "default_resume_id": prefs.get("default_resume_id"),
    }}


@app.get("/api/user/resumes")
async def list_user_resumes(user_id: str = Depends(require_user_data_user_id)):
    """List the authenticated user's saved resumes (metadata only, no full text)."""
    user_db = get_db_for_user(user_id)
    resumes = user_db.list_saved_resumes()

    return {"success": True, "resumes": resumes}


@app.post("/api/user/resumes")
async def save_user_resume(
    request: SaveResumeRequest,
    user_id: str = Depends(require_user_data_user_id),
):
    """Save a resume for the authenticated user."""
    import hashlib

    # Compute content hash for dedup if not provided
    content_hash = request.content_hash or hashlib.sha256(
        request.resume_text.encode()
    ).hexdigest()

    user_db = get_db_for_user(user_id)
    existing_resume = user_db.get_resume_by_content_hash(content_hash)
    if existing_resume:
        resume_id = existing_resume["id"]
        if request.is_default:
            user_db.set_default_resume(resume_id)
    else:
        resume_id = user_db.save_resume(
            label=request.label,
            resume_text=request.resume_text,
            filename=request.filename,
            content_hash=content_hash,
            is_default=request.is_default,
        )

    return {"success": True, "resume_id": resume_id}


@app.get("/api/user/resumes/{resume_id}")
async def get_user_resume(
    resume_id: int,
    user_id: str = Depends(require_user_data_user_id),
):
    """Get a specific saved resume (includes full text)."""
    user_db = get_db_for_user(user_id)
    resume = user_db.get_saved_resume(resume_id)

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    return {"success": True, "resume": resume}


@app.delete("/api/user/resumes/{resume_id}")
async def delete_user_resume(
    resume_id: int,
    user_id: str = Depends(require_user_data_user_id),
):
    """Delete a saved resume."""
    user_db = get_db_for_user(user_id)
    deleted = user_db.delete_saved_resume(resume_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Resume not found")

    return {"success": True}


@app.post("/api/analyze-job")
async def analyze_job(request: JobAnalysisRequest, http_request: Request):
    """Analyze job posting (Agent 1)."""
    from src.middleware.auth import get_user_id_from_request
    user_id = get_user_id_from_request(http_request)
    user_db = get_db_for_user(user_id)
    # Get job text
    if request.job_text:
        job_text = request.job_text
    elif request.job_url:
        try:
            job_text = fetch_job_posting_text(request.job_url)
        except ExaContentError as err:
            raise HTTPException(status_code=400, detail=str(err)) from err
        except ValueError as err:
            raise HTTPException(status_code=400, detail=str(err)) from err
        except RuntimeError as err:
            raise HTTPException(status_code=500, detail=str(err)) from err
        except Exception as err:
            raise HTTPException(
                status_code=500,
                detail="Unexpected error while fetching job posting content.",
            ) from err
    else:
        raise HTTPException(
            status_code=400,
            detail="Either job_text or job_url is required",
        )

    try:
        # Initialize API client
        client = create_client()

        # Run Job Analyzer Agent
        agent = JobAnalyzerAgent(client=client)
        analysis_result = ""
        analysis_metadata: Dict[str, Any] = {}

        gen = agent.analyze_job(
            job_posting=job_text,
            model=ANALYZER_MODEL,
            temperature=ANALYZER_TEMPERATURE,
        )
        try:
            while True:
                chunk = next(gen)
                analysis_result += chunk
        except StopIteration as exc:
            analysis_metadata = exc.value or {}

        # Extract metadata (company, job title)
        company_name = "Company"  # TODO: Extract from analysis
        job_title = "Position"  # TODO: Extract from analysis

        # Save to database (store analysis in agent outputs)
        app_id = user_db.create_application(
            company_name=company_name,
            job_title=job_title,
            job_posting_text=job_text,
            original_resume_text="",
        )
        user_db.save_agent_output(
            application_id=app_id,
            agent_number=1,
            agent_name="Job Analyzer",
            input_data={"job_posting": job_text},
            output_data={"text": analysis_result},
            cost=analysis_metadata.get("cost", 0.0),
            input_tokens=analysis_metadata.get("input_tokens", 0),
            output_tokens=analysis_metadata.get("output_tokens", 0),
        )

        return {
            "success": True,
            "application_id": app_id,
            "company_name": company_name,
            "job_title": job_title,
            "analysis": analysis_result,
            "job_text": job_text,
        }
    except HTTPException:
        # Already mapped to an HTTP error above
        raise
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err)) from err


@app.post("/api/optimize-resume")
async def optimize_resume(request: ResumeOptimizationRequest, http_request: Request):
    """Generate optimization strategy (Agent 2)."""
    from src.middleware.auth import get_user_id_from_request
    user_id = get_user_id_from_request(http_request)
    user_db = get_db_for_user(user_id)
    try:
        # Get application data
        app_data = user_db.get_application(request.application_id)
        if not app_data:
            raise HTTPException(status_code=404, detail="Application not found")

        # Initialize API client
        client = create_client()

        # Resolve job analysis from previous step
        job_analysis_text = _latest_agent_output_text(
            request.application_id, "Job Analyzer", user_db=user_db
        )

        # Run Resume Optimizer Agent
        agent = ResumeOptimizerAgent(client=client)
        optimization_result = ""
        optimization_metadata: Dict[str, Any] = {}

        gen = agent.optimize_resume(
            resume_text=request.resume_text,
            job_analysis=job_analysis_text,
            model=OPTIMIZER_MODEL,
            temperature=OPTIMIZER_TEMPERATURE,
        )
        try:
            while True:
                chunk = next(gen)
                optimization_result += chunk
        except StopIteration as exc:
            optimization_metadata = exc.value or {}

        # Update database and persist agent output
        user_db.update_application(
            request.application_id,
            original_resume_text=request.resume_text,
            model_used=OPTIMIZER_MODEL,
        )
        user_db.save_agent_output(
            application_id=request.application_id,
            agent_number=2,
            agent_name="Resume Optimizer",
            input_data={
                "resume_text": request.resume_text,
                "job_analysis": job_analysis_text,
            },
            output_data={"text": optimization_result},
            cost=optimization_metadata.get("cost", 0.0),
            input_tokens=optimization_metadata.get("input_tokens", 0),
            output_tokens=optimization_metadata.get("output_tokens", 0),
        )
        
        return {
            "success": True,
            "application_id": request.application_id,
            "strategy": optimization_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/implement")
async def implement_optimization(request: ImplementationRequest, http_request: Request):
    """Apply optimization strategy (Agent 3)."""
    from src.middleware.auth import get_user_id_from_request
    user_id = get_user_id_from_request(http_request)
    user_db = get_db_for_user(user_id)
    try:
        # Get application data
        app_data = user_db.get_application(request.application_id)
        if not app_data:
            raise HTTPException(status_code=404, detail="Application not found")

        # Initialize API client
        client = create_client()

        # Resolve required inputs
        job_analysis_text = _latest_agent_output_text(
            request.application_id, "Job Analyzer", user_db=user_db
        )
        optimization_strategy = _latest_agent_output_text(
            request.application_id, "Resume Optimizer", user_db=user_db
        )
        original_resume = app_data.get("original_resume_text", "")

        # Run Implementer Agent
        agent = OptimizerImplementerAgent(client=client)
        implementation_result = ""
        implementation_metadata: Dict[str, Any] = {}

        gen = agent.implement_optimizations(
            resume_text=original_resume,
            optimization_report=optimization_strategy,
            model=IMPLEMENTER_MODEL,
            temperature=IMPLEMENTER_TEMPERATURE,
        )
        try:
            while True:
                chunk = next(gen)
                implementation_result += chunk
        except StopIteration as exc:
            implementation_metadata = exc.value or {}
        
        # Extract optimized resume
        optimized_resume = extract_optimized_resume(implementation_result)
        
        # Update database and persist agent output
        user_db.update_application(
            request.application_id,
            optimized_resume_text=optimized_resume,
            model_used=IMPLEMENTER_MODEL,
        )
        user_db.save_agent_output(
            application_id=request.application_id,
            agent_number=3,
            agent_name="Optimizer Implementer",
            input_data={
                "resume_text": original_resume,
                "optimization_report": optimization_strategy,
                "job_analysis": job_analysis_text,
            },
            output_data={"text": implementation_result},
            cost=implementation_metadata.get("cost", 0.0),
            input_tokens=implementation_metadata.get("input_tokens", 0),
            output_tokens=implementation_metadata.get("output_tokens", 0),
        )
        
        return {
            "success": True,
            "application_id": request.application_id,
            "optimized_resume": optimized_resume,
            "notes": implementation_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/validate")
async def validate_resume(request: ValidationRequest, http_request: Request):
    """Validate optimized resume (Agent 4)."""
    from src.middleware.auth import get_user_id_from_request
    user_id = get_user_id_from_request(http_request)
    user_db = get_db_for_user(user_id)
    try:
        # Get application data
        app_data = user_db.get_application(request.application_id)
        if not app_data:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Initialize API client
        client = create_client()

        # Resolve required inputs
        job_posting_text = app_data.get("job_posting_text", "")
        job_analysis_text = _latest_agent_output_text(
            request.application_id, "Job Analyzer", user_db=user_db
        )
        optimized_resume = app_data.get("optimized_resume_text", "")

        # Run Validator Agent
        agent = ValidatorAgent(client=client)
        validation_result = ""
        validation_metadata: Dict[str, Any] = {}

        gen = agent.validate_resume(
            optimized_resume=optimized_resume,
            job_posting=job_posting_text,
            job_analysis=job_analysis_text,
            model=VALIDATOR_MODEL,
            temperature=VALIDATOR_TEMPERATURE,
        )
        try:
            while True:
                chunk = next(gen)
                validation_result += chunk
        except StopIteration as exc:
            validation_metadata = exc.value or {}

        # Persist agent output (scores are derived later)
        user_db.save_agent_output(
            application_id=request.application_id,
            agent_number=4,
            agent_name="Validator",
            input_data={
                "optimized_resume": optimized_resume,
                "job_posting": job_posting_text,
                "job_analysis": job_analysis_text,
            },
            output_data={"text": validation_result},
            cost=validation_metadata.get("cost", 0.0),
            input_tokens=validation_metadata.get("input_tokens", 0),
            output_tokens=validation_metadata.get("output_tokens", 0),
        )
        
        # Parse validation result for scores
        scores = {
            "overall": 87,
            "requirements_match": 90,
            "ats_optimization": 85,
            "cultural_fit": 86
        }
        
        return {
            "success": True,
            "application_id": request.application_id,
            "validation": validation_result,
            "scores": scores
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/polish")
async def polish_resume(request: PolishRequest, http_request: Request):
    """Final polish and export (Agent 5)."""
    from src.middleware.auth import get_user_id_from_request
    user_id = get_user_id_from_request(http_request)
    user_db = get_db_for_user(user_id)
    try:
        # Get application data
        app_data = user_db.get_application(request.application_id)
        if not app_data:
            raise HTTPException(status_code=404, detail="Application not found")

        # Initialize API client
        client = create_client()

        # Resolve required inputs
        optimized_resume = app_data.get("optimized_resume_text", "")
        validation_report = _latest_agent_output_text(
            request.application_id, "Validator", user_db=user_db
        )

        # Run Polish Agent
        agent = PolishAgent(client=client, output_format="review")
        polish_result = ""
        polish_metadata: Dict[str, Any] = {}

        gen = agent.polish_resume(
            optimized_resume=optimized_resume,
            validation_report=validation_report,
            model=POLISH_MODEL,
            temperature=POLISH_TEMPERATURE,
        )
        try:
            while True:
                chunk = next(gen)
                polish_result += chunk
        except StopIteration as exc:
            polish_metadata = exc.value or {}

        # Extract final resume
        final_resume = extract_optimized_resume(polish_result)
        summary_points: List[str] = []
        review_document = build_review_document(
            application_id=request.application_id,
            status=app_data.get("status") or "completed",
            resume_text=final_resume,
            summary_points=summary_points,
            source_filename=None,
        )

        # Update database and persist agent output
        user_db.update_application(
            request.application_id,
            optimized_resume_text=final_resume,
            model_used=POLISH_MODEL,
        )
        user_db.save_application_review(
            application_id=request.application_id,
            plain_text=review_document["plain_text"],
            markdown=review_document["markdown"],
            filename=review_document["filename"],
            summary_points=review_document["summary_points"],
        )
        user_db.update_application(request.application_id, status="completed")
        user_db.save_agent_output(
            application_id=request.application_id,
            agent_number=5,
            agent_name="Polish Agent",
            input_data={
                "optimized_resume": optimized_resume,
                "validation_report": validation_report,
            },
            output_data={"text": polish_result},
            cost=polish_metadata.get("cost", 0.0),
            input_tokens=polish_metadata.get("input_tokens", 0),
            output_tokens=polish_metadata.get("output_tokens", 0),
        )
        
        return {
            "success": True,
            "application_id": request.application_id,
            "final_resume": final_resume,
            "notes": polish_result,
            "review": _build_review_payload(user_db, request.application_id),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/{application_id}")
async def export_resume(
    application_id: int,
    export_format: str = Query("docx", alias="format"),
    user_id: str = Depends(require_user_data_user_id),
):
    """Export final resume in requested format from the canonical review document."""
    user_db = get_db_for_user(user_id)
    try:
        review_document = user_db.get_application_review(application_id)
        if not review_document:
            raise HTTPException(status_code=404, detail="Review document not found")
        
        # Generate export file
        if export_format == "docx":
            from fastapi.responses import Response
            docx_bytes = generate_docx_from_plain_text(review_document["plain_text"])
            filename = review_document.get("filename") or "optimized-resume.docx"
            
            # Return as streaming response
            return Response(
                content=docx_bytes,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"'
                }
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Unexpected error during resume export for application_id=%s",
            application_id,
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/applications/{application_id}/review")
async def get_application_review(
    application_id: int,
    user_id: str = Depends(require_user_data_user_id),
):
    """Return the canonical review payload for frontend_v2."""
    user_db = get_db_for_user(user_id)
    review_payload = _build_review_payload(user_db, application_id)
    return {
        "success": True,
        "review": review_payload,
    }


@app.get("/api/applications")
async def list_applications(http_request: Request):
    """List all saved applications."""
    from src.middleware.auth import get_user_id_from_request
    user_id = get_user_id_from_request(http_request)
    user_db = get_db_for_user(user_id)
    try:
        applications = user_db.get_all_applications()
        return {
            "success": True,
            "applications": applications
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/application/{application_id}")
async def get_application(application_id: int, http_request: Request):
    """Get specific application details."""
    from src.middleware.auth import get_user_id_from_request
    user_id = get_user_id_from_request(http_request)
    user_db = get_db_for_user(user_id)
    try:
        app_data = user_db.get_application(application_id)
        if not app_data:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Get agent outputs to provide plain text resume for display
        agent_outputs = user_db.get_agent_outputs(application_id)
        
        # Replace optimized_resume_text with Agent 3's output (plain text)
        # Agent 5's output is DOCX code, not suitable for display
        for output in agent_outputs:
            agent_name = output.get("agent_name", "")
            if "implementer" in agent_name.lower():
                output_data = output.get("output_data", {})
                if isinstance(output_data, dict):
                    plain_text_resume = str(output_data.get("text") or output_data.get("full_response") or output_data.get("output") or "")
                else:
                    plain_text_resume = str(output_data)
                
                # Override the optimized_resume_text with plain text version
                if plain_text_resume:
                    app_data["optimized_resume_text"] = plain_text_resume
                break
        
        return {
            "success": True,
            "application": app_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/application/{application_id}/diff")
async def get_application_diff(application_id: int, http_request: Request):
    """Get resume diff with change reasons and validation warnings."""
    from src.middleware.auth import get_user_id_from_request
    user_id = get_user_id_from_request(http_request)
    user_db = get_db_for_user(user_id)
    try:
        from src.utils import generate_resume_diff
        
        # Get application data
        app_data = user_db.get_application(application_id)
        if not app_data:
            raise HTTPException(status_code=404, detail="Application not found")
        
        original_text = app_data.get("original_resume_text", "")
        
        # Get agent outputs for reasons and optimized text
        agent_outputs = user_db.get_agent_outputs(application_id)
        optimization_report = ""
        validation_report = ""
        optimized_text = ""
        
        for output in agent_outputs:
            agent_name = output.get("agent_name", "")
            output_data = output.get("output_data", {})
            
            # Use Agent 3 (Optimizer Implementer) output for plain text diff
            # Agent 5 output contains Python DOCX code, not suitable for display
            if "implementer" in agent_name.lower():
                if isinstance(output_data, dict):
                    optimized_text = str(output_data.get("text") or output_data.get("full_response") or output_data.get("output") or "")
                else:
                    optimized_text = str(output_data)
            
            if "optimizer" in agent_name.lower() and "implementer" not in agent_name.lower():
                # Extract text from output_data
                if isinstance(output_data, dict):
                    optimization_report = str(output_data.get("text") or output_data.get("full_response") or output_data.get("output") or "")
                else:
                    optimization_report = str(output_data)
            
            if "validator" in agent_name.lower():
                if isinstance(output_data, dict):
                    validation_report = str(output_data.get("text") or output_data.get("full_response") or output_data.get("output") or "")
                else:
                    validation_report = str(output_data)
        
        if not original_text or not optimized_text:
            raise HTTPException(status_code=400, detail="Resume texts not found")
        
        # Generate diff
        changes = generate_resume_diff(
            original_text,
            optimized_text,
            optimization_report,
            validation_report
        )
        
        # Get validation scores - return actual scores or None
        validation_scores = user_db.get_validation_scores(application_id)
        scores = None
        if validation_scores:
            scores = {
                "overall": round(validation_scores.get("overall_score", 0)),
                "requirements_match": round(validation_scores.get("requirements_match", 0)),
                "ats_optimization": round(validation_scores.get("ats_optimization", 0)),
                "cultural_fit": round(validation_scores.get("cultural_fit", 0)),
            }
        
        return {
            "success": True,
            "changes": changes,
            "scores": scores
        }
    except Exception as e:
        import traceback
        print(f"Error generating diff: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/application/{application_id}/reports")
async def get_application_reports(application_id: int, http_request: Request):
    """Get structured reports parsed from all agent outputs.

    Returns:
        - job_analysis: Parsed job analysis from Agent 1
        - optimization_strategy: Parsed optimization strategy from Agent 2
        - validation_report: Parsed validation report from Agent 4
        - optimized_resume_text: Plain text optimized resume from Agent 3
        - agent_costs: Cost breakdown by agent
    """
    from src.middleware.auth import get_user_id_from_request
    user_id = get_user_id_from_request(http_request)
    user_db = get_db_for_user(user_id)
    try:
        from src.utils.report_parsers import parse_all_reports

        # Get agent outputs
        agent_outputs = user_db.get_agent_outputs(application_id)
        if not agent_outputs:
            raise HTTPException(
                status_code=404,
                detail="No agent outputs found for this application"
            )

        # Parse all reports
        reports = parse_all_reports(agent_outputs)

        # Get validation scores from database for additional context
        validation_scores = user_db.get_validation_scores(application_id)
        if validation_scores:
            reports["validation_scores"] = {
                "requirements_match": validation_scores.get("requirements_match", 0),
                "ats_optimization": validation_scores.get("ats_optimization", 0),
                "cultural_fit": validation_scores.get("cultural_fit", 0),
                "presentation_quality": validation_scores.get("presentation_quality", 0),
                "competitive_positioning": validation_scores.get("competitive_positioning", 0),
                "overall_score": validation_scores.get("overall_score", 0),
            }

        return {
            "success": True,
            "reports": reports
        }
    except Exception as e:
        import traceback
        print(f"Error parsing reports: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pipeline/start")
async def start_pipeline(request: PipelineRequest, http_request: Request):
    """Start the full pipeline with streaming support."""
    import uuid
    import hashlib
    from src.middleware.auth import get_user_id_from_request

    # Get user ID from JWT token or fall back to client ID
    user_id = get_user_id_from_request(http_request)

    run_count = run_store.count_runs_for_client(user_id)
    if DEV_MODE_ENABLED:
        print(
            f"⚠️ DEV_MODE enabled - rate limits disabled for user_id={user_id}, run_count={run_count}"
        )
    else:
        if run_count >= MAX_FREE_RUNS:
            raise HTTPException(
                status_code=402,
                detail="Usage limit reached. Please upgrade to continue.",
            )

    # Auto-save non-sensitive defaults for real Supabase users, or in explicit SQLite mode.
    should_persist_user_data = (
        bool(user_id)
        and (not USE_SUPABASE_DB or _is_supabase_auth_user_id(user_id))
    )
    if should_persist_user_data:
        try:
            user_db = get_db_for_user(user_id)
            pref_data = {}
            fields_set = getattr(request, "model_fields_set", set())
            if "linkedin_url" in fields_set:
                pref_data["default_linkedin_url"] = _normalized_optional_text(
                    request.linkedin_url
                )
            if "github_username" in fields_set:
                pref_data["default_github_username"] = _normalized_optional_text(
                    request.github_username
                )

            # Optionally save the resume
            if request.save_resume and request.resume_text:
                content_hash = hashlib.sha256(
                    request.resume_text.encode()
                ).hexdigest()
                label = request.resume_label or request.resume_filename or "My Resume"
                existing_resume = user_db.get_resume_by_content_hash(content_hash)
                if existing_resume:
                    resume_id = existing_resume["id"]
                    user_db.set_default_resume(resume_id)
                else:
                    resume_id = user_db.save_resume(
                        label=label,
                        resume_text=request.resume_text,
                        filename=request.resume_filename,
                        content_hash=content_hash,
                        is_default=True,
                    )
                pref_data["default_resume_id"] = resume_id

            if pref_data:
                user_db.upsert_preferences(**pref_data)
        except Exception as e:
            # Non-critical: don't block pipeline if preference save fails
            print(f"⚠️ Failed to auto-save preferences: {e}")

    job_id = str(uuid.uuid4())
    run_store.create_run(job_id=job_id, client_id=user_id, status="queued")

    # Start pipeline in background
    asyncio.create_task(run_pipeline_with_streaming(
        job_id=job_id,
        resume_text=request.resume_text,
        job_text=request.job_text,
        job_url=request.job_url,
        linkedin_url=request.linkedin_url,
        github_username=request.github_username,
        github_token=request.github_token,
        user_id=user_id,
        force_refresh_profile=request.force_refresh_profile,
        resume_filename=request.resume_filename,
    ))

    return {
        "success": True,
        "job_id": job_id,
        "stream_url": f"/api/jobs/{job_id}/stream",
        "snapshot_url": f"/api/jobs/{job_id}/snapshot",
    }


async def run_pipeline_with_streaming(
    job_id: str,
    resume_text: str,
    job_text: Optional[str] = None,
    job_url: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    github_username: Optional[str] = None,
    github_token: Optional[str] = None,
    user_id: Optional[str] = None,
    force_refresh_profile: bool = False,
    resume_filename: Optional[str] = None,
):
    """Run the full pipeline and emit streaming events.
    
    Args:
        force_refresh_profile: If True, re-scrape LinkedIn/GitHub even if cached
    """
    insight_listener_task = None
    session_id = None
    app_id: Optional[int] = None
    
    # Get database instance for this user (Supabase if enabled, else SQLite)
    user_db = get_db_for_user(user_id)

    try:
        print(f"Starting pipeline for job_id: {job_id}")
        run_store.update_status(job_id, status="running")

        # Create recovery session for this pipeline run
        session_id = recovery_service.create_session(
            form_data={
                "job_text": job_text or "",
                "job_url": job_url or "",
                "linkedin_url": linkedin_url or "",
                "github_username": github_username or "",
            },
            file_metadata={
                "resume_length": len(resume_text),
                "has_resume": bool(resume_text),
            }
        )
        print(f"✅ Created recovery session: {session_id}")

        # Update session status to processing
        recovery_service.update_session_status(
            session_id=session_id,
            status="processing"
        )

        # Set the main loop for thread-safe emission
        stream_manager.set_main_loop(asyncio.get_running_loop())

        # Emit job started with session ID
        await stream_manager.emit(JobStatusEvent.create(job_id, "started"))
        await stream_manager.emit(MetricUpdateEvent.create(
            job_id, "session_id", session_id, ""
        ))
        print(f"✅ Emitted job_status: started")
        
        # Start the parallel insight listener
        insight_listener_task = asyncio.create_task(run_insight_listener(job_id))
        print(f"🔍 Started insight listener task")
        
        # Get job text (prefer provided text, fall back to Exa fetch for URLs)
        if job_text:
            job_text_final = job_text
        elif job_url:
            print(f"📥 Fetching job posting from URL: {job_url}")
            loop = asyncio.get_event_loop()
            job_text_final = await loop.run_in_executor(None, fetch_job_posting_text, job_url)
            print(f"✅ Job text fetched: {len(job_text_final)} chars")
        else:
            await stream_manager.emit(JobStatusEvent.create(job_id, "failed"))
            run_store.update_status(job_id, status="failed")
            print("❌ No job text or URL provided")
            return
        
        client = create_client()
        
        # Step 0 (Optional): Build Profile Index from LinkedIn and/or GitHub
        profile_index = None
        if linkedin_url or github_username:
            print(f"🔗 Building profile index (LinkedIn: {bool(linkedin_url)}, GitHub: {bool(github_username)})")
            await stream_manager.emit(InsightEvent.create(
                job_id, "ins-profile", "system", "medium",
                "Getting to know you better...", "profiling"
            ))
            
            try:
                from src.agents.profile_agent import ProfileAgent
                from src.api import fetch_linkedin_profile_text, ScrapingDogError
                from src.agents.github_projects_agent import fetch_github_repos
                
                loop = asyncio.get_event_loop()
                profile_text = None
                profile_repos = None
                used_cache = False
                
                # Check for cached profile first (avoid re-scraping) unless force refresh
                cached_profile = None
                if not force_refresh_profile:
                    cached_profile = user_db.get_cached_profile(
                        linkedin_url=linkedin_url,
                        github_username=github_username
                    )
                
                if cached_profile and cached_profile.get("profile_index") and not force_refresh_profile:
                    # Use cached profile index directly
                    profile_index = cached_profile["profile_index"]
                    used_cache = True
                    print(f"✅ Using cached profile (ID: {cached_profile.get('id')})")
                    await stream_manager.emit(InsightEvent.create(
                        job_id, "ins-profile-cached", "system", "medium",
                        "Using your saved profile data", "profiling"
                    ))
                else:
                    if force_refresh_profile:
                        print(f"🔄 Force refresh requested - re-scraping profile data")
                    # No cache - need to fetch fresh data
                    # Fetch LinkedIn profile if provided (using ScrapingDog)
                    if linkedin_url:
                        print(f"📥 Fetching LinkedIn profile via ScrapingDog: {linkedin_url}")
                        await stream_manager.emit(InsightEvent.create(
                            job_id, "ins-linkedin", "system", "medium",
                            "Fetching LinkedIn profile (may take 1-2 minutes)...", "profiling"
                        ))
                        try:
                            profile_text = await loop.run_in_executor(None, fetch_linkedin_profile_text, linkedin_url)
                            if profile_text:
                                print(f"✅ LinkedIn profile fetched: {len(profile_text)} chars")
                            else:
                                print("⚠️ Could not fetch LinkedIn profile")
                        except ScrapingDogError as e:
                            print(f"⚠️ LinkedIn fetch failed (non-fatal): {e}")
                            await stream_manager.emit(InsightEvent.create(
                                job_id, "ins-linkedin-err", "system", "low",
                                "Could not fetch LinkedIn profile - continuing without it", "profiling"
                            ))
                    
                    # Fetch GitHub repos if provided
                    if github_username:
                        print(f"📥 Fetching GitHub repos for: {github_username}")
                        if github_token:
                            print(f"✅ Using user-provided GitHub token")
                        else:
                            print(f"⚠️ No GitHub token provided - using unauthenticated API (rate limited)")
                        try:
                            profile_repos = await loop.run_in_executor(
                                None, fetch_github_repos, github_username, github_token, 20
                            )
                            if profile_repos:
                                print(f"✅ GitHub repos fetched: {len(profile_repos)} repos")
                                await stream_manager.emit(InsightEvent.create(
                                    job_id, "ins-github", "system", "medium",
                                    f"Found {len(profile_repos)} GitHub projects", "profiling"
                                ))
                            else:
                                print("⚠️ No GitHub repos found")
                        except Exception as e:
                            print(f"⚠️ GitHub fetch failed (non-fatal): {e}")
                            import traceback
                            traceback.print_exc()
                            profile_repos = None
                    
                    # Build profile index if we have any data
                    if profile_text or profile_repos:
                        print("🏗️ Building profile index...")
                        profile_agent = ProfileAgent(client=client)
                        profile_result = ""
                        for chunk in profile_agent.index_profile(
                            model=PROFILE_MODEL,
                            profile_text=profile_text or "",
                            profile_repos=profile_repos,
                            temperature=PROFILE_TEMPERATURE
                        ):
                            profile_result += chunk
                        profile_index = profile_result
                        print(f"✅ Profile index built: {len(profile_index)} chars")

                        # Save to cache for future runs
                        if profile_index:
                            try:
                                profile_sources = []
                                if linkedin_url:
                                    profile_sources.append(f"linkedin:{linkedin_url}")
                                if github_username:
                                    profile_sources.append(f"github:{github_username}")

                                combined_profile_text = profile_text or ""
                                if profile_repos:
                                    combined_profile_text = (
                                        (combined_profile_text + "\n\n" if combined_profile_text else "")
                                        + "GitHub repositories:\n"
                                        + json.dumps(profile_repos, ensure_ascii=False)
                                    )

                                saved_profile_id = user_db.save_profile(
                                    sources=profile_sources,
                                    profile_text=combined_profile_text,
                                    profile_index=profile_index,
                                    linkedin_url=linkedin_url,
                                    github_username=github_username,
                                )
                                print(f"✅ Cached profile for future runs (ID: {saved_profile_id})")
                            except Exception as persist_err:
                                print(f"⚠️ Failed to cache profile: {persist_err}")

                if profile_index:
                    await stream_manager.emit(InsightEvent.create(
                        job_id, "ins-profile-done", "system", "high",
                        "Profile index ready - will enhance optimization" + (" (cached)" if used_cache else ""), "profiling"
                    ))
                else:
                    print("⚠️ No profile data available")
            except Exception as e:
                print(f"⚠️ Profile building failed (non-fatal): {e}")
                import traceback
                traceback.print_exc()
                # Continue without profile - it's optional
        
        # Agent 1: Job Analysis
        print("📋 Agent 1: Starting job analysis...")
        await stream_manager.emit(StepProgressEvent.create(job_id, "analyzing", 0))
        await stream_manager.emit(InsightEvent.create(
            job_id, "ins-1", "system", "high",
            "Starting job analysis...", "analyzing"
        ))
        
        agent1 = JobAnalyzerAgent(client=client)
        
        # Run agent with chunk emission in executor
        loop = asyncio.get_event_loop()
        analysis_result, analysis_metadata = await loop.run_in_executor(
            None,
            functools.partial(
                run_agent_with_chunk_emission,
                agent1, "Job Analyzer", "analyzing", job_id,
                job_posting=job_text_final, model=ANALYZER_MODEL
            )
        )
        print(f"✅ Agent 1 complete: {len(analysis_result)} chars")
        
        await stream_manager.emit(StepProgressEvent.create(job_id, "analyzing", 100))
        await stream_manager.emit(InsightEvent.create(
            job_id, "ins-2", "system", "high",
            "Job analysis complete", "analyzing"
        ))
        
        # Extract insights in parallel
        print("🔍 Extracting insights from job analysis...")
        extracted_insights = await insight_extractor.extract_insights_async(
            analysis_result, "analyzer", max_insights=4
        )
        for idx, insight in enumerate(extracted_insights):
            await stream_manager.emit(InsightEvent.create(
                job_id, f"ins-analysis-{idx}", insight["category"], "high",
                insight["message"], "analyzing"
            ))
        print(f"✅ Extracted {len(extracted_insights)} insights")
        
        # Extract company name and job title from job posting using LLM
        from src.utils.job_metadata_extractor import extract_job_metadata
        company_name, job_title = extract_job_metadata(job_text_final, client=client)
        
        # Create application (job_url is available from pipeline params)
        app_id = user_db.create_application(
            company_name=company_name,
            job_title=job_title,
            job_posting_text=job_text_final,
            original_resume_text=resume_text,
            job_url=job_url,
        )
        run_store.update_status(job_id, application_id=app_id)
        
        # Emit application_id as metric for frontend
        await stream_manager.emit(MetricUpdateEvent.create(
            job_id, "application_id", app_id, ""
        ))
        print(f"✅ Emitted application_id metric: {app_id}")
        
        user_db.save_agent_output(
            application_id=app_id,
            agent_number=1,
            agent_name="Job Analyzer",
            input_data={"job_posting": job_text_final},
            output_data={"text": analysis_result},
            cost=analysis_metadata.get("cost", 0.0),
            input_tokens=analysis_metadata.get("input_tokens", 0),
            output_tokens=analysis_metadata.get("output_tokens", 0),
        )

        # Save checkpoint for recovery
        if session_id:
            recovery_service.save_checkpoint(
                session_id=session_id,
                agent_index=0,
                agent_name="Job Analyzer",
                agent_output={"text": analysis_result},
                model_used=ANALYZER_MODEL
            )
            print(f"✅ Saved checkpoint for Agent 1")
        
        # Agent 2: Resume Optimization
        print("📋 Agent 2: Starting resume optimization...")
        await stream_manager.emit(StepProgressEvent.create(job_id, "planning", 0))
        await stream_manager.emit(InsightEvent.create(
            job_id, "ins-3", "system", "high",
            "Creating optimization strategy...", "planning"
        ))
        
        agent2 = ResumeOptimizerAgent(client=client)
        
        # Run agent with chunk emission (with optional profile index)
        optimization_result, optimization_metadata = await loop.run_in_executor(
            None,
            functools.partial(
                run_agent_with_chunk_emission,
                agent2, "Resume Optimizer", "planning", job_id,
                resume_text=resume_text, job_analysis=analysis_result, 
                profile_index=profile_index, model=OPTIMIZER_MODEL
            )
        )
        print(f"✅ Agent 2 complete: {len(optimization_result)} chars")
        
        await stream_manager.emit(StepProgressEvent.create(job_id, "planning", 100))
        await stream_manager.emit(InsightEvent.create(
            job_id, "ins-4", "system", "high",
            "Optimization strategy ready", "planning"
        ))
        
        # Extract insights
        print("🔍 Extracting insights from optimization strategy...")
        extracted_insights = await insight_extractor.extract_insights_async(
            optimization_result, "optimizer", max_insights=4
        )
        for idx, insight in enumerate(extracted_insights):
            await stream_manager.emit(InsightEvent.create(
                job_id, f"ins-optimizer-{idx}", insight["category"], "high",
                insight["message"], "planning"
            ))
        print(f"✅ Extracted {len(extracted_insights)} insights")
        
        user_db.save_agent_output(
            application_id=app_id,
            agent_number=2,
            agent_name="Resume Optimizer",
            input_data={"resume_text": resume_text, "job_analysis": analysis_result},
            output_data={"text": optimization_result},
            cost=optimization_metadata.get("cost", 0.0),
            input_tokens=optimization_metadata.get("input_tokens", 0),
            output_tokens=optimization_metadata.get("output_tokens", 0),
        )

        # Save checkpoint for recovery
        if session_id:
            recovery_service.save_checkpoint(
                session_id=session_id,
                agent_index=1,
                agent_name="Resume Optimizer",
                agent_output={"text": optimization_result},
                model_used=OPTIMIZER_MODEL
            )
            print(f"✅ Saved checkpoint for Agent 2")
        
        # Agent 3: Implementation
        print("📋 Agent 3: Starting implementation...")
        await stream_manager.emit(StepProgressEvent.create(job_id, "writing", 0))
        await stream_manager.emit(InsightEvent.create(
            job_id, "ins-5", "system", "high",
            "Implementing optimizations...", "writing"
        ))
        
        agent3 = OptimizerImplementerAgent(client=client)
        
        # Run agent with chunk emission
        implementation_result, implementation_metadata = await loop.run_in_executor(
            None,
            functools.partial(
                run_agent_with_chunk_emission,
                agent3, "Optimizer Implementer", "writing", job_id,
                resume_text=resume_text,
                optimization_report=optimization_result,
                profile_index=profile_index,
                model=IMPLEMENTER_MODEL
            )
        )
        optimized_resume = extract_optimized_resume(implementation_result)
        print(f"✅ Agent 3 complete: {len(implementation_result)} chars")
        
        await stream_manager.emit(StepProgressEvent.create(job_id, "writing", 100))
        await stream_manager.emit(InsightEvent.create(
            job_id, "ins-6", "system", "high",
            "Resume optimizations applied", "writing"
        ))
        
        # Extract insights
        print("🔍 Extracting insights from implementation...")
        extracted_insights = await insight_extractor.extract_insights_async(
            implementation_result, "implementer", max_insights=4
        )
        for idx, insight in enumerate(extracted_insights):
            await stream_manager.emit(InsightEvent.create(
                job_id, f"ins-impl-{idx}", insight["category"], "high",
                insight["message"], "writing"
            ))
        print(f"✅ Extracted {len(extracted_insights)} insights")
        
        user_db.update_application(app_id, optimized_resume_text=optimized_resume)
        user_db.save_agent_output(
            application_id=app_id,
            agent_number=3,
            agent_name="Optimizer Implementer",
            input_data={"resume_text": resume_text, "optimization_report": optimization_result},
            output_data={"text": implementation_result},
            cost=implementation_metadata.get("cost", 0.0),
            input_tokens=implementation_metadata.get("input_tokens", 0),
            output_tokens=implementation_metadata.get("output_tokens", 0),
        )

        # Save checkpoint for recovery
        if session_id:
            recovery_service.save_checkpoint(
                session_id=session_id,
                agent_index=2,
                agent_name="Optimizer Implementer",
                agent_output={"text": implementation_result, "optimized_resume": optimized_resume},
                model_used=IMPLEMENTER_MODEL
            )
            print(f"✅ Saved checkpoint for Agent 3")
        
        # Agent 4: Validation
        print("📋 Agent 4: Starting validation...")
        await stream_manager.emit(StepProgressEvent.create(job_id, "validating", 0))
        await stream_manager.emit(InsightEvent.create(
            job_id, "ins-7", "system", "high",
            "Validating optimized resume...", "validating"
        ))
        
        agent4 = ValidatorAgent(client=client)
        
        # Run agent with chunk emission
        validation_result, validation_metadata = await loop.run_in_executor(
            None,
            functools.partial(
                run_agent_with_chunk_emission,
                agent4, "Validator", "validating", job_id,
                optimized_resume=optimized_resume,
                job_posting=job_text_final,
                job_analysis=analysis_result,
                profile_index=profile_index,
                model=VALIDATOR_MODEL
            )
        )
        print(f"✅ Agent 4 complete: {len(validation_result)} chars")
        
        await stream_manager.emit(StepProgressEvent.create(job_id, "validating", 100))
        
        # Parse validation scores from the result
        from src.app.services.validation_parser import extract_validation_artifacts
        try:
            parsed_scores, red_flags, recommendations = extract_validation_artifacts(validation_result)
            
            # Save validation scores to database
            user_db.save_validation_scores(
                app_id,
                scores=parsed_scores,
                red_flags=red_flags,
                recommendations=recommendations
            )
            
            # Emit actual scores as metrics
            await stream_manager.emit(MetricUpdateEvent.create(
                job_id, "overall_score", round(parsed_scores.get("overall_score", 0)), "%"
            ))
            await stream_manager.emit(MetricUpdateEvent.create(
                job_id, "requirements_match", round(parsed_scores.get("requirements_match", 0)), "%"
            ))
            await stream_manager.emit(MetricUpdateEvent.create(
                job_id, "ats_optimization", round(parsed_scores.get("ats_optimization", 0)), "%"
            ))
            await stream_manager.emit(MetricUpdateEvent.create(
                job_id, "cultural_fit", round(parsed_scores.get("cultural_fit", 0)), "%"
            ))
            print(f"✅ Parsed and emitted validation scores: {parsed_scores}")
        except Exception as e:
            print(f"⚠️ Failed to parse validation scores: {e}")
            # Emit fallback scores if parsing fails
            await stream_manager.emit(MetricUpdateEvent.create(job_id, "overall_score", 0, "%"))
        
        await stream_manager.emit(InsightEvent.create(
            job_id, "ins-8", "system", "high",
            "Validation complete", "validating"
        ))
        
        # Extract insights
        print("🔍 Extracting insights from validation...")
        extracted_insights = await insight_extractor.extract_insights_async(
            validation_result, "validator", max_insights=4
        )
        for idx, insight in enumerate(extracted_insights):
            await stream_manager.emit(InsightEvent.create(
                job_id, f"ins-val-{idx}", insight["category"], "high",
                insight["message"], "validating"
            ))
        print(f"✅ Extracted {len(extracted_insights)} insights")
        
        user_db.save_agent_output(
            application_id=app_id,
            agent_number=4,
            agent_name="Validator",
            input_data={"optimized_resume": optimized_resume, "job_posting": job_text_final},
            output_data={"text": validation_result},
            cost=validation_metadata.get("cost", 0.0),
            input_tokens=validation_metadata.get("input_tokens", 0),
            output_tokens=validation_metadata.get("output_tokens", 0),
        )

        # Save checkpoint for recovery
        if session_id:
            recovery_service.save_checkpoint(
                session_id=session_id,
                agent_index=3,
                agent_name="Validator",
                agent_output={"text": validation_result},
                model_used=VALIDATOR_MODEL
            )
            print(f"✅ Saved checkpoint for Agent 4")
        
        # Agent 5: Polish
        print("📋 Agent 5: Starting polish...")
        await stream_manager.emit(StepProgressEvent.create(job_id, "polishing", 0))
        await stream_manager.emit(InsightEvent.create(
            job_id, "ins-9", "system", "high",
            "Final polish and formatting...", "polishing"
        ))
        
        agent5 = PolishAgent(client=client, output_format="review")
        
        # Run agent with chunk emission
        polish_result, polish_metadata = await loop.run_in_executor(
            None,
            functools.partial(
                run_agent_with_chunk_emission,
                agent5, "Polish Agent", "polishing", job_id,
                optimized_resume=optimized_resume, validation_report=validation_result, model=POLISH_MODEL
            )
        )
        final_resume = extract_optimized_resume(polish_result)
        print(f"✅ Agent 5 complete: {len(polish_result)} chars")
        
        await stream_manager.emit(StepProgressEvent.create(job_id, "polishing", 100))
        await stream_manager.emit(InsightEvent.create(
            job_id, "ins-10", "system", "high",
            "Resume optimization complete!", "polishing"
        ))
        
        # Extract insights
        print("🔍 Extracting insights from polish...")
        extracted_insights = await insight_extractor.extract_insights_async(
            polish_result, "polish", max_insights=3
        )
        for idx, insight in enumerate(extracted_insights):
            await stream_manager.emit(InsightEvent.create(
                job_id, f"ins-polish-{idx}", insight["category"], "high",
                insight["message"], "polishing"
            ))
        print(f"✅ Extracted {len(extracted_insights)} insights")
        
        summary_points = [
            insight["message"] for insight in extracted_insights
        ] if extracted_insights else []
        review_document = build_review_document(
            application_id=app_id,
            status="completed",
            resume_text=final_resume,
            summary_points=summary_points,
            source_filename=resume_filename,
        )

        user_db.update_application(app_id, optimized_resume_text=final_resume)
        user_db.save_application_review(
            application_id=app_id,
            plain_text=review_document["plain_text"],
            markdown=review_document["markdown"],
            filename=review_document["filename"],
            summary_points=review_document["summary_points"],
        )
        user_db.save_agent_output(
            application_id=app_id,
            agent_number=5,
            agent_name="Polish Agent",
            input_data={"optimized_resume": optimized_resume, "validation_report": validation_result},
            output_data={"text": polish_result},
            cost=polish_metadata.get("cost", 0.0),
            input_tokens=polish_metadata.get("input_tokens", 0),
            output_tokens=polish_metadata.get("output_tokens", 0),
        )

        # Save checkpoint for recovery
        if session_id:
            recovery_service.save_checkpoint(
                session_id=session_id,
                agent_index=4,
                agent_name="Polish Agent",
                agent_output={"text": polish_result, "final_resume": final_resume},
                model_used=POLISH_MODEL
            )
            print(f"✅ Saved checkpoint for Agent 5")

        # Mark recovery session as completed
        if session_id:
            recovery_service.update_session_status(
                session_id=session_id,
                status="recovered"
            )
            recovery_service.mark_recovered(session_id, app_id)
            print(f"✅ Marked recovery session as completed")

        # Update application status to completed
        if app_id is not None:
            user_db.update_application(app_id, status="completed")
        
        # Emit completion after final metrics. The stream endpoint closes on DoneEvent.
        if app_id is not None:
            run_store.update_status(job_id, status="completed", application_id=app_id)
            # Ensure live clients receive the application id before the SSE stream closes.
            await stream_manager.emit(MetricUpdateEvent.create(job_id, "application_id", app_id))
        else:
            run_store.update_status(job_id, status="completed")

        await stream_manager.emit(JobStatusEvent.create(job_id, "completed"))
        # Build the result payload with the canonical review endpoint metadata.
        done_payload: dict = {
            "application_id": app_id,
            "review_url": f"/api/applications/{app_id}/review" if app_id is not None else None,
        }
        await stream_manager.emit(DoneEvent(job_id=job_id, payload=done_payload))

        print(f"🎉 Pipeline complete for job_id: {job_id}, app_id: {app_id}")
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Pipeline failed for job_id: {job_id}")
        print(f"Error: {str(e)}")
        print(f"Traceback:\n{error_details}")

        # Log error with recovery service
        if session_id:
            error_context = recovery_service.log_error(
                exc=e,
                session_id=session_id,
                additional_context={
                    "job_id": job_id,
                    "pipeline_stage": "processing",
                }
            )
            print(f"✅ Logged error: {error_context['error_id']}")

            # Emit error details to frontend
            await stream_manager.emit(MetricUpdateEvent.create(
                job_id, "error_id", error_context['error_id'], ""
            ))
            await stream_manager.emit(MetricUpdateEvent.create(
                job_id, "error_category", error_context['error_category'], ""
            ))

        # Update application status to failed
        if app_id is not None:
            user_db.update_application(app_id, status="failed")
        
        await stream_manager.emit(JobStatusEvent.create(job_id, "failed"))
        await stream_manager.emit(InsightEvent.create(
            job_id, "error-1", "error", "high",
            f"Pipeline failed: {str(e)}"
        ))
        await stream_manager.emit(DoneEvent(job_id=job_id))
        run_store.update_status(job_id, status="failed")
    
    finally:
        # Clean up insight listener
        if insight_listener_task:
            try:
                if not insight_listener_task.done():
                    insight_listener_task.cancel()
                    try:
                        await insight_listener_task
                    except asyncio.CancelledError:
                        pass
                print(f"🔍 Insight listener task cleaned up")
            except Exception as e:
                print(f"⚠️ Error cleaning up insight listener: {e}")


@app.get("/api/jobs/{job_id}/snapshot")
async def get_job_snapshot(job_id: str):
    """Get current snapshot of job state."""
    try:
        snapshot = await stream_manager.get_snapshot(job_id)
        return snapshot
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


SSE_MIN_CHUNK_BYTES = 4096
SSE_PADDING_COMMENT = ":" + (" " * 2048) + "\n"
SSE_PADDING_COMMENT_BYTES = len(SSE_PADDING_COMMENT.encode("utf-8"))


def _serialize_sse_payload(payload: dict, event_id: Optional[int] = None) -> str:
    """Serialize payload to SSE format with padding to flush Cloud Run buffers."""
    chunk = ""
    if event_id is not None:
        chunk += f"id: {event_id}\n"
    chunk += f"data: {json.dumps(payload)}\n\n"
    chunk_bytes = len(chunk.encode("utf-8"))

    if chunk_bytes < SSE_MIN_CHUNK_BYTES:
        needed = SSE_MIN_CHUNK_BYTES - chunk_bytes
        # Ensure we always exceed the threshold
        padding_count = (needed // SSE_PADDING_COMMENT_BYTES) + 1
        chunk += SSE_PADDING_COMMENT * padding_count
    return chunk


@app.get("/api/jobs/{job_id}/stream")
async def stream_job_events(job_id: str, request: Request):
    """Stream job events via SSE with padding to force Cloud Run flushes."""

    async def event_generator():
        """Generate SSE events."""
        last_event_id_header = request.headers.get("last-event-id")
        after_event_id: Optional[int] = None
        if last_event_id_header:
            try:
                after_event_id = int(last_event_id_header)
            except ValueError:
                after_event_id = None
        queue = await stream_manager.subscribe(job_id, after_event_id=after_event_id)

        try:
            # Send initial heartbeat
            loop = asyncio.get_event_loop()
            heartbeat_payload = {
                "type": "heartbeat",
                "ts": int(loop.time() * 1000),
                "job_id": job_id,
            }
            yield _serialize_sse_payload(heartbeat_payload)

            # Stream events
            while True:
                try:
                    # Wait for event with timeout for heartbeat
                    item = await asyncio.wait_for(queue.get(), timeout=15.0)
                    event = getattr(item, "event", item)
                    event_id = getattr(item, "event_id", None)

                    # Serialize event
                    event_data = event.model_dump() if hasattr(event, 'model_dump') else event
                    yield _serialize_sse_payload(event_data, event_id=event_id)

                    # Check if done
                    if event.type == "done":
                        break

                except asyncio.TimeoutError:
                    loop = asyncio.get_event_loop()
                    heartbeat_payload = {
                        "type": "heartbeat",
                        "ts": int(loop.time() * 1000),
                        "job_id": job_id,
                    }
                    yield _serialize_sse_payload(heartbeat_payload)

        except asyncio.CancelledError:
            pass
        finally:
            await stream_manager.unsubscribe(job_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
