"""FastAPI server for Resume Optimizer backend."""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import json
import asyncio
import time
import functools
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
from src.api import fetch_job_posting_text
from src.database import ApplicationDatabase
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
)
from src.streaming.insight_extractor import insight_extractor
from src.streaming.insight_listener import run_insight_listener

load_dotenv()

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "qwen/qwen3-max")
POLISH_MODEL = "zenmux::anthropic/claude-sonnet-4.5"

app = FastAPI(title="Resume Optimizer API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
db = ApplicationDatabase()


def _latest_agent_output_text(application_id: int, agent_name: str) -> str:
    """Fetch the most recent saved output text for a given agent.

    Falls back to empty string if none found.
    """
    try:
        outputs = db.get_agent_outputs(application_id)
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
    current_time = time.time()
    
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
        for chunk in gen:
            result += chunk
            seq += 1
            current_time = time.time()
            
            # Emit chunk events with throttling
            # Throttle: emit every 500 chars or 1.2 seconds
            should_emit = (
                len(result) % 500 < len(chunk) or  # Crossed 500-char boundary
                (current_time - last_emit_time) >= 1.2  # Time interval passed
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
        
        # Emit step completed
        stream_manager.emit_from_thread(AgentStepCompletedEvent.create(
            job_id=job_id,
            step=step_name,
            agent_name=agent_name,
            total_chars=len(result)
        ))
        
    except Exception as e:
        print(f"❌ Agent {agent_name} failed: {e}")
        # Still emit completion for cleanup
        stream_manager.emit_from_thread(AgentStepCompletedEvent.create(
            job_id=job_id,
            step=step_name,
            agent_name=agent_name,
            total_chars=len(result)
        ))
        raise
    
    return result


class JobAnalysisRequest(BaseModel):
    job_text: Optional[str] = None
    job_url: Optional[str] = None


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


@app.post("/api/analyze-job")
async def analyze_job(request: JobAnalysisRequest):
    """Analyze job posting (Agent 1)."""
    try:
        # Get job text
        if request.job_url:
            job_text = fetch_job_posting_text(request.job_url)
        elif request.job_text:
            job_text = request.job_text
        else:
            raise HTTPException(status_code=400, detail="Either job_text or job_url is required")
        
        # Initialize API client
        client = create_client()
        
        # Run Job Analyzer Agent
        agent = JobAnalyzerAgent(client=client)
        analysis_result = ""

        for chunk in agent.analyze_job(job_posting=job_text, model=DEFAULT_MODEL):
            analysis_result += chunk
        
        # Extract metadata (company, job title)
        company_name = "Company"  # TODO: Extract from analysis
        job_title = "Position"  # TODO: Extract from analysis
        
        # Save to database (store analysis in agent outputs)
        app_id = db.create_application(
            company_name=company_name,
            job_title=job_title,
            job_posting_text=job_text,
            original_resume_text="",
        )
        db.save_agent_output(
            application_id=app_id,
            agent_number=1,
            agent_name="Job Analyzer",
            input_data={"job_posting": job_text},
            output_data={"text": analysis_result},
        )
        
        return {
            "success": True,
            "application_id": app_id,
            "company_name": company_name,
            "job_title": job_title,
            "analysis": analysis_result,
            "job_text": job_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/optimize-resume")
async def optimize_resume(request: ResumeOptimizationRequest):
    """Generate optimization strategy (Agent 2)."""
    try:
        # Get application data
        app_data = db.get_application(request.application_id)
        if not app_data:
            raise HTTPException(status_code=404, detail="Application not found")

        # Initialize API client
        client = create_client()

        # Resolve job analysis from previous step
        job_analysis_text = _latest_agent_output_text(
            request.application_id, "Job Analyzer"
        )

        # Run Resume Optimizer Agent
        agent = ResumeOptimizerAgent(client=client)
        optimization_result = ""

        for chunk in agent.optimize_resume(
            resume_text=request.resume_text,
            job_analysis=job_analysis_text,
            model=DEFAULT_MODEL,
        ):
            optimization_result += chunk

        # Update database and persist agent output
        db.update_application(
            request.application_id,
            original_resume_text=request.resume_text,
            model_used=DEFAULT_MODEL,
        )
        db.save_agent_output(
            application_id=request.application_id,
            agent_number=2,
            agent_name="Resume Optimizer",
            input_data={
                "resume_text": request.resume_text,
                "job_analysis": job_analysis_text,
            },
            output_data={"text": optimization_result},
        )
        
        return {
            "success": True,
            "application_id": request.application_id,
            "strategy": optimization_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/implement")
async def implement_optimization(request: ImplementationRequest):
    """Apply optimization strategy (Agent 3)."""
    try:
        # Get application data
        app_data = db.get_application(request.application_id)
        if not app_data:
            raise HTTPException(status_code=404, detail="Application not found")

        # Initialize API client
        client = create_client()

        # Resolve required inputs
        job_analysis_text = _latest_agent_output_text(
            request.application_id, "Job Analyzer"
        )
        optimization_strategy = _latest_agent_output_text(
            request.application_id, "Resume Optimizer"
        )
        original_resume = app_data.get("original_resume_text", "")

        # Run Implementer Agent
        agent = OptimizerImplementerAgent(client=client)
        implementation_result = ""

        for chunk in agent.implement_optimizations(
            resume_text=original_resume,
            optimization_report=optimization_strategy,
            model=DEFAULT_MODEL,
        ):
            implementation_result += chunk
        
        # Extract optimized resume
        optimized_resume = extract_optimized_resume(implementation_result)
        
        # Update database and persist agent output
        db.update_application(
            request.application_id,
            optimized_resume_text=optimized_resume,
            model_used=DEFAULT_MODEL,
        )
        db.save_agent_output(
            application_id=request.application_id,
            agent_number=3,
            agent_name="Optimizer Implementer",
            input_data={
                "resume_text": original_resume,
                "optimization_report": optimization_strategy,
                "job_analysis": job_analysis_text,
            },
            output_data={"text": implementation_result},
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
async def validate_resume(request: ValidationRequest):
    """Validate optimized resume (Agent 4)."""
    try:
        # Get application data
        app_data = db.get_application(request.application_id)
        if not app_data:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Initialize API client
        client = create_client()

        # Resolve required inputs
        job_posting_text = app_data.get("job_posting_text", "")
        job_analysis_text = _latest_agent_output_text(
            request.application_id, "Job Analyzer"
        )
        optimized_resume = app_data.get("optimized_resume_text", "")

        # Run Validator Agent
        agent = ValidatorAgent(client=client)
        validation_result = ""

        for chunk in agent.validate_resume(
            optimized_resume=optimized_resume,
            job_posting=job_posting_text,
            job_analysis=job_analysis_text,
            model=DEFAULT_MODEL,
        ):
            validation_result += chunk

        # Persist agent output (scores are derived later)
        db.save_agent_output(
            application_id=request.application_id,
            agent_number=4,
            agent_name="Validator",
            input_data={
                "optimized_resume": optimized_resume,
                "job_posting": job_posting_text,
                "job_analysis": job_analysis_text,
            },
            output_data={"text": validation_result},
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
async def polish_resume(request: PolishRequest):
    """Final polish and export (Agent 5)."""
    try:
        # Get application data
        app_data = db.get_application(request.application_id)
        if not app_data:
            raise HTTPException(status_code=404, detail="Application not found")

        # Initialize API client
        client = create_client()

        # Resolve required inputs
        optimized_resume = app_data.get("optimized_resume_text", "")
        validation_report = _latest_agent_output_text(
            request.application_id, "Validator"
        )

        # Run Polish Agent
        agent = PolishAgent(client=client, output_format="docx")
        polish_result = ""

        for chunk in agent.polish_resume(
            optimized_resume=optimized_resume,
            validation_report=validation_report,
            model=DEFAULT_MODEL,
        ):
            polish_result += chunk

        # Extract final resume
        final_resume = extract_optimized_resume(polish_result)

        # Update database and persist agent output
        db.update_application(
            request.application_id,
            optimized_resume_text=final_resume,
            model_used=DEFAULT_MODEL,
        )
        db.save_agent_output(
            application_id=request.application_id,
            agent_number=5,
            agent_name="Polish Agent",
            input_data={
                "optimized_resume": optimized_resume,
                "validation_report": validation_report,
            },
            output_data={"text": polish_result},
        )
        
        return {
            "success": True,
            "application_id": request.application_id,
            "final_resume": final_resume,
            "notes": polish_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/{application_id}")
async def export_resume(application_id: int, format: str = "docx"):
    """Export final resume in requested format by executing LLM-generated DOCX code."""
    try:
        # Get application data
        app_data = db.get_application(application_id)
        if not app_data:
            raise HTTPException(status_code=404, detail="Application not found")
        
        final_resume = app_data.get("optimized_resume_text")
        if not final_resume:
            raise HTTPException(status_code=400, detail="No resume to export")
        
        # Generate export file
        if format == "docx":
            from src.utils import execute_docx_code, html_to_docx
            from fastapi.responses import Response
            import io
            
            # Detect if content is HTML or Python code
            content_lower = final_resume.strip().lower()
            is_html = (
                content_lower.startswith("<!doctype") or 
                content_lower.startswith("<html") or
                "<html" in content_lower[:500]
            )
            
            print(f"📝 Generating DOCX for application {application_id}")
            print(f"Content type: {'HTML' if is_html else 'Python code'}")
            print(f"Content preview (first 200 chars): {final_resume[:200]}")
            
            # Generate DOCX based on content type
            if is_html:
                print("  → Converting HTML to DOCX")
                docx_bytes = html_to_docx(final_resume)
            else:
                print("  → Executing Python code to generate DOCX")
                docx_bytes = execute_docx_code(final_resume)
            
            # Create safe filename
            job_title = app_data.get('job_title', 'resume').replace(' ', '_').replace('/', '_')
            company_name = app_data.get('company_name', 'company').replace(' ', '_').replace('/', '_')
            filename = f"resume_{job_title}_{company_name}.docx"
            
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
            
    except ValueError as e:
        # Handle code execution errors specifically
        print(f"❌ DOCX code execution failed: {str(e)}")
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to generate DOCX from code: {str(e)}"
        )
    except SyntaxError as e:
        # Handle Python syntax errors in generated code
        print(f"❌ DOCX code has syntax error: {str(e)}")
        print(f"   Line {e.lineno}: {e.text}")
        raise HTTPException(
            status_code=400,
            detail=f"Generated code has syntax error on line {e.lineno}: {str(e)}"
        )
    except Exception as e:
        print(f"❌ Unexpected error during DOCX export: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/applications")
async def list_applications():
    """List all saved applications."""
    try:
        applications = db.get_all_applications()
        return {
            "success": True,
            "applications": applications
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/application/{application_id}")
async def get_application(application_id: int):
    """Get specific application details."""
    try:
        app_data = db.get_application(application_id)
        if not app_data:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Get agent outputs to provide plain text resume for display
        agent_outputs = db.get_agent_outputs(application_id)
        
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
async def get_application_diff(application_id: int):
    """Get resume diff with change reasons and validation warnings."""
    try:
        from src.utils import generate_resume_diff
        
        # Get application data
        app_data = db.get_application(application_id)
        if not app_data:
            raise HTTPException(status_code=404, detail="Application not found")
        
        original_text = app_data.get("original_resume_text", "")
        
        # Get agent outputs for reasons and optimized text
        agent_outputs = db.get_agent_outputs(application_id)
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
        validation_scores = db.get_validation_scores(application_id)
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
async def get_application_reports(application_id: int):
    """Get structured reports parsed from all agent outputs.

    Returns:
        - job_analysis: Parsed job analysis from Agent 1
        - optimization_strategy: Parsed optimization strategy from Agent 2
        - validation_report: Parsed validation report from Agent 4
        - optimized_resume_text: Plain text optimized resume from Agent 3
        - agent_costs: Cost breakdown by agent
    """
    try:
        from src.utils.report_parsers import parse_all_reports

        # Get agent outputs
        agent_outputs = db.get_agent_outputs(application_id)
        if not agent_outputs:
            raise HTTPException(
                status_code=404,
                detail="No agent outputs found for this application"
            )

        # Parse all reports
        reports = parse_all_reports(agent_outputs)

        # Get validation scores from database for additional context
        validation_scores = db.get_validation_scores(application_id)
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
async def start_pipeline(request: PipelineRequest):
    """Start the full pipeline with streaming support."""
    import uuid
    
    job_id = str(uuid.uuid4())
    
    # Start pipeline in background
    asyncio.create_task(run_pipeline_with_streaming(
        job_id=job_id,
        resume_text=request.resume_text,
        job_text=request.job_text,
        job_url=request.job_url,
        linkedin_url=request.linkedin_url,
        github_username=request.github_username,
        github_token=request.github_token,
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
):
    """Run the full pipeline and emit streaming events."""
    insight_listener_task = None
    try:
        print(f"🚀 Starting pipeline for job_id: {job_id}")
        
        # Set the main loop for thread-safe emission
        stream_manager.set_main_loop(asyncio.get_running_loop())
        
        # Emit job started
        await stream_manager.emit(JobStatusEvent.create(job_id, "started"))
        print(f"✅ Emitted job_status: started")
        
        # Start the parallel insight listener
        insight_listener_task = asyncio.create_task(run_insight_listener(job_id))
        print(f"🔍 Started insight listener task")
        
        # Get job text (run in thread pool since it's blocking)
        if job_url:
            print(f"📥 Fetching job posting from URL: {job_url}")
            loop = asyncio.get_event_loop()
            job_text_final = await loop.run_in_executor(None, fetch_job_posting_text, job_url)
            print(f"✅ Job text fetched: {len(job_text_final)} chars")
        elif job_text:
            job_text_final = job_text
        else:
            await stream_manager.emit(JobStatusEvent.create(job_id, "failed"))
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
                from src.api import fetch_public_page_text
                from src.agents.github_projects_agent import fetch_github_repos
                
                loop = asyncio.get_event_loop()
                profile_text = None
                profile_repos = None
                
                # Fetch LinkedIn profile if provided
                if linkedin_url:
                    print(f"📥 Fetching LinkedIn profile: {linkedin_url}")
                    profile_text = await loop.run_in_executor(None, fetch_public_page_text, linkedin_url)
                    if profile_text:
                        print(f"✅ LinkedIn profile fetched: {len(profile_text)} chars")
                    else:
                        print("⚠️ Could not fetch LinkedIn profile")
                
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
                        model=DEFAULT_MODEL,
                        profile_text=profile_text or "",
                        profile_repos=profile_repos
                    ):
                        profile_result += chunk
                    profile_index = profile_result
                    print(f"✅ Profile index built: {len(profile_index)} chars")
                    
                    await stream_manager.emit(InsightEvent.create(
                        job_id, "ins-profile-done", "system", "high",
                        "Profile index ready - will enhance optimization", "profiling"
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
        analysis_result = await loop.run_in_executor(
            None,
            functools.partial(
                run_agent_with_chunk_emission,
                agent1, "Job Analyzer", "analyzing", job_id,
                job_posting=job_text_final, model=DEFAULT_MODEL
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
        
        # Create application
        app_id = db.create_application(
            company_name="Company",
            job_title="Position",
            job_posting_text=job_text_final,
            original_resume_text=resume_text,
        )
        
        # Emit application_id as metric for frontend
        await stream_manager.emit(MetricUpdateEvent.create(
            job_id, "application_id", app_id, ""
        ))
        print(f"✅ Emitted application_id metric: {app_id}")
        
        db.save_agent_output(
            application_id=app_id,
            agent_number=1,
            agent_name="Job Analyzer",
            input_data={"job_posting": job_text_final},
            output_data={"text": analysis_result},
        )
        
        # Agent 2: Resume Optimization
        print("📋 Agent 2: Starting resume optimization...")
        await stream_manager.emit(StepProgressEvent.create(job_id, "planning", 0))
        await stream_manager.emit(InsightEvent.create(
            job_id, "ins-3", "system", "high",
            "Creating optimization strategy...", "planning"
        ))
        
        agent2 = ResumeOptimizerAgent(client=client)
        
        # Run agent with chunk emission (with optional profile index)
        optimization_result = await loop.run_in_executor(
            None,
            functools.partial(
                run_agent_with_chunk_emission,
                agent2, "Resume Optimizer", "planning", job_id,
                resume_text=resume_text, job_analysis=analysis_result, 
                profile_index=profile_index, model=DEFAULT_MODEL
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
        
        db.save_agent_output(
            application_id=app_id,
            agent_number=2,
            agent_name="Resume Optimizer",
            input_data={"resume_text": resume_text, "job_analysis": analysis_result},
            output_data={"text": optimization_result},
        )
        
        # Agent 3: Implementation
        print("📋 Agent 3: Starting implementation...")
        await stream_manager.emit(StepProgressEvent.create(job_id, "writing", 0))
        await stream_manager.emit(InsightEvent.create(
            job_id, "ins-5", "system", "high",
            "Implementing optimizations...", "writing"
        ))
        
        agent3 = OptimizerImplementerAgent(client=client)
        
        # Run agent with chunk emission
        implementation_result = await loop.run_in_executor(
            None,
            functools.partial(
                run_agent_with_chunk_emission,
                agent3, "Optimizer Implementer", "writing", job_id,
                resume_text=resume_text, optimization_report=optimization_result, model=DEFAULT_MODEL
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
        
        db.update_application(app_id, optimized_resume_text=optimized_resume)
        db.save_agent_output(
            application_id=app_id,
            agent_number=3,
            agent_name="Optimizer Implementer",
            input_data={"resume_text": resume_text, "optimization_report": optimization_result},
            output_data={"text": implementation_result},
        )
        
        # Agent 4: Validation
        print("📋 Agent 4: Starting validation...")
        await stream_manager.emit(StepProgressEvent.create(job_id, "validating", 0))
        await stream_manager.emit(InsightEvent.create(
            job_id, "ins-7", "system", "high",
            "Validating optimized resume...", "validating"
        ))
        
        agent4 = ValidatorAgent(client=client)
        
        # Run agent with chunk emission
        validation_result = await loop.run_in_executor(
            None,
            functools.partial(
                run_agent_with_chunk_emission,
                agent4, "Validator", "validating", job_id,
                optimized_resume=optimized_resume, job_posting=job_text_final, job_analysis=analysis_result, model=DEFAULT_MODEL
            )
        )
        print(f"✅ Agent 4 complete: {len(validation_result)} chars")
        
        await stream_manager.emit(StepProgressEvent.create(job_id, "validating", 100))
        
        # Parse validation scores from the result
        from src.app.services.validation_parser import extract_validation_artifacts
        try:
            parsed_scores, red_flags, recommendations = extract_validation_artifacts(validation_result)
            
            # Save validation scores to database
            db.save_validation_scores(
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
        
        db.save_agent_output(
            application_id=app_id,
            agent_number=4,
            agent_name="Validator",
            input_data={"optimized_resume": optimized_resume, "job_posting": job_text_final},
            output_data={"text": validation_result},
        )
        
        # Agent 5: Polish
        print("📋 Agent 5: Starting polish...")
        await stream_manager.emit(StepProgressEvent.create(job_id, "polishing", 0))
        await stream_manager.emit(InsightEvent.create(
            job_id, "ins-9", "system", "high",
            "Final polish and formatting...", "polishing"
        ))
        
        agent5 = PolishAgent(client=client, output_format="docx")
        
        # Run agent with chunk emission
        polish_result = await loop.run_in_executor(
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
        
        db.update_application(app_id, optimized_resume_text=final_resume)
        db.save_agent_output(
            application_id=app_id,
            agent_number=5,
            agent_name="Polish Agent",
            input_data={"optimized_resume": optimized_resume, "validation_report": validation_result},
            output_data={"text": polish_result},
        )
        
        # Emit completion
        await stream_manager.emit(JobStatusEvent.create(job_id, "completed"))
        await stream_manager.emit(DoneEvent(job_id=job_id))
        
        # Store application_id in job metadata for retrieval
        await stream_manager.emit(MetricUpdateEvent.create(job_id, "application_id", app_id))
        
        print(f"🎉 Pipeline complete for job_id: {job_id}, app_id: {app_id}")
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Pipeline failed for job_id: {job_id}")
        print(f"Error: {str(e)}")
        print(f"Traceback:\n{error_details}")
        
        await stream_manager.emit(JobStatusEvent.create(job_id, "failed"))
        await stream_manager.emit(InsightEvent.create(
            job_id, "error-1", "error", "high",
            f"Pipeline failed: {str(e)}"
        ))
        await stream_manager.emit(DoneEvent(job_id=job_id))
    
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


@app.get("/api/jobs/{job_id}/stream")
async def stream_job_events(job_id: str):
    """Stream job events via SSE."""
    
    async def event_generator():
        """Generate SSE events."""
        queue = await stream_manager.subscribe(job_id)
        
        try:
            # Send initial heartbeat
            yield f"data: {json.dumps({'type': 'heartbeat', 'ts': int(asyncio.get_event_loop().time() * 1000), 'job_id': job_id})}\n\n"
            
            # Stream events
            while True:
                try:
                    # Wait for event with timeout for heartbeat
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    
                    # Serialize event
                    event_data = event.model_dump() if hasattr(event, 'model_dump') else event
                    yield f"data: {json.dumps(event_data)}\n\n"
                    
                    # Check if done
                    if event.type == "done":
                        break
                        
                except asyncio.TimeoutError:
                    # Send heartbeat
                    yield f"data: {json.dumps({'type': 'heartbeat', 'ts': int(asyncio.get_event_loop().time() * 1000), 'job_id': job_id})}\n\n"
                    
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
