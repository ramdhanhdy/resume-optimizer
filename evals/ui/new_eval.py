"""New Evaluation page - create scenarios using the same flow as main app.

This page allows you to:
1. Upload a resume (PDF/DOCX)
2. Enter job posting URL or paste text
3. Optionally add GitHub/LinkedIn
4. Select which stage to evaluate
5. Select which models to compare
6. Run the pipeline and generate candidate outputs
"""

import streamlit as st
import asyncio
import time
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

# Add project root to path for evals namespace imports
evals_root = Path(__file__).parent.parent
project_root = evals_root.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Ensure backend is importable for agents and fetchers
backend_root = project_root / "backend"
backend_src = backend_root / "src"
for p in (backend_root, backend_src):
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Load backend/.env so EXA_API_KEY is available
backend_env = backend_root / ".env"
if backend_env.exists():
    try:
        from dotenv import load_dotenv

        load_dotenv(backend_env)
    except Exception:
        pass

from evals.db.eval_db import EvalDatabase
from evals.framework.runner import EvalRunner
from evals.framework.schemas import CandidateConfig, Scenario
from evals.framework.config_resume import (
    RESUME_STAGES,
    CANDIDATE_MODELS,
    get_resume_eval_config,
)


def render_new_eval_page(db: EvalDatabase, evaluator_id: str):
    """Render the new evaluation creation page."""
    st.header("Create New Evaluation")
    st.caption(
        "Run the resume optimization pipeline with multiple models and compare outputs."
    )

    # Initialize session state
    if "eval_resume_text" not in st.session_state:
        st.session_state.eval_resume_text = ""
    if "eval_job_text" not in st.session_state:
        st.session_state.eval_job_text = ""
    if "eval_running" not in st.session_state:
        st.session_state.eval_running = False

    # --- Step 1: Resume Input ---
    st.subheader("1. Resume")
    
    resume_tab1, resume_tab2 = st.tabs(["Upload File", "Paste Text"])
    
    with resume_tab1:
        uploaded_file = st.file_uploader(
            "Upload your resume (PDF or DOCX)",
            type=["pdf", "docx", "doc", "txt"],
            key="eval_resume_upload",
        )
        if uploaded_file:
            resume_text = extract_resume_text(uploaded_file)
            if resume_text:
                st.session_state.eval_resume_text = resume_text
                st.success(f"Extracted {len(resume_text)} characters from {uploaded_file.name}")
    
    with resume_tab2:
        pasted_resume = st.text_area(
            "Or paste your resume text",
            height=200,
            key="eval_resume_paste",
            placeholder="Paste your resume content here...",
        )
        if pasted_resume:
            st.session_state.eval_resume_text = pasted_resume

    # Show current resume preview
    if st.session_state.eval_resume_text:
        with st.expander("Resume Preview", expanded=False):
            st.text(st.session_state.eval_resume_text[:1000] + "..." 
                   if len(st.session_state.eval_resume_text) > 1000 
                   else st.session_state.eval_resume_text)

    st.divider()

    # --- Step 2: Job Posting ---
    st.subheader("2. Job Posting")
    
    job_tab1, job_tab2 = st.tabs(["Enter URL", "Paste Text"])
    
    with job_tab1:
        job_url = st.text_input(
            "Job posting URL",
            key="eval_job_url",
            placeholder="https://linkedin.com/jobs/view/...",
        )
        if job_url and st.button("Fetch Job Posting", key="fetch_job"):
            with st.spinner("Fetching job posting..."):
                job_text, fetch_error = fetch_job_posting(job_url)
                if job_text:
                    st.session_state.eval_job_text = job_text
                    st.success(f"Fetched {len(job_text)} characters")
                else:
                    st.error(
                        fetch_error
                        or "Failed to fetch job posting. Check EXA_API_KEY and URL accessibility."
                    )
    
    with job_tab2:
        pasted_job = st.text_area(
            "Or paste job posting text",
            height=200,
            key="eval_job_paste",
            placeholder="Paste the job description here...",
        )
        if pasted_job:
            st.session_state.eval_job_text = pasted_job

    # Show current job preview
    if st.session_state.eval_job_text:
        with st.expander("Job Posting Preview", expanded=False):
            st.text(st.session_state.eval_job_text[:1000] + "..." 
                   if len(st.session_state.eval_job_text) > 1000 
                   else st.session_state.eval_job_text)

    st.divider()

    # --- Step 3: Optional Integrations ---
    st.subheader("3. Additional Context (Optional)")
    
    col1, col2 = st.columns(2)
    with col1:
        github_username = st.text_input(
            "GitHub Username",
            key="eval_github",
            placeholder="e.g., octocat",
        )
        github_token = st.text_input(
            "GitHub Token",
            key="eval_github_token",
            type="password",
            placeholder="ghp_... (required for GitHub integration)",
            help="Personal access token with 'repo' scope. Required to fetch repository data.",
        )
    with col2:
        linkedin_url = st.text_input(
            "LinkedIn Profile URL",
            key="eval_linkedin",
            placeholder="https://linkedin.com/in/...",
        )
    
    if github_username and not github_token:
        st.warning("⚠️ GitHub token is required when using GitHub username. The pipeline will fail without it.")

    st.divider()

    # --- Step 4: Evaluation Settings ---
    st.subheader("4. Evaluation Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        stage_to_eval = st.selectbox(
            "Stage to Evaluate",
            options=list(RESUME_STAGES.keys()),
            format_func=lambda x: RESUME_STAGES[x].display_name,
            key="eval_stage",
            help="Which pipeline stage to compare models on",
        )
    
    with col2:
        st.write("**Models to Compare**")
        
    # Model selection
    available_models = [m.model_id for m in CANDIDATE_MODELS]
    
    # Add custom model option
    use_custom = st.checkbox("Add custom model IDs", key="use_custom_models")
    
    if use_custom:
        custom_models = st.text_area(
            "Custom model IDs (one per line)",
            placeholder="openrouter::anthropic/claude-sonnet-4-20250514\ngoogle/gemini-2.0-flash",
            key="custom_model_ids",
        )
        if custom_models:
            available_models.extend([m.strip() for m in custom_models.split("\n") if m.strip()])
    
    selected_models = st.multiselect(
        "Select models to compare",
        options=available_models,
        default=available_models[:2] if len(available_models) >= 2 else available_models,
        key="eval_models",
        help="Select 2+ models to compare their outputs",
    )

    st.divider()

    # --- Step 5: Run Evaluation ---
    st.subheader("5. Run Evaluation")
    
    # Validation
    can_run = (
        st.session_state.eval_resume_text 
        and st.session_state.eval_job_text 
        and len(selected_models) >= 2
    )
    
    if not st.session_state.eval_resume_text:
        st.warning("Please provide a resume")
    if not st.session_state.eval_job_text:
        st.warning("Please provide a job posting")
    if len(selected_models) < 2:
        st.warning("Please select at least 2 models to compare")

    # Run button
    if st.button(
        "Run Evaluation",
        type="primary",
        disabled=not can_run or st.session_state.eval_running,
        key="run_eval_btn",
    ):
        st.session_state.eval_running = True
        
        with st.spinner("Running evaluation pipeline..."):
            try:
                result = run_evaluation(
                    db=db,
                    resume_text=st.session_state.eval_resume_text,
                    job_text=st.session_state.eval_job_text,
                    stage_id=stage_to_eval,
                    model_ids=selected_models,
                    github_username=github_username if github_username else None,
                    github_token=github_token if github_token else None,
                    linkedin_url=linkedin_url if linkedin_url else None,
                )
                
                if result["success"]:
                    st.success(
                        f"Evaluation created! Scenario: {result['scenario_id']}\n\n"
                        f"Generated {result['num_candidates']} candidate outputs for stage '{stage_to_eval}'.\n\n"
                        f"Go to **Pending Queue** to judge the outputs."
                    )
                    # Clear inputs for next run
                    st.session_state.eval_resume_text = ""
                    st.session_state.eval_job_text = ""
                else:
                    st.error(f"Evaluation failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                st.error(f"Error running evaluation: {e}")
            finally:
                st.session_state.eval_running = False


def extract_resume_text(uploaded_file) -> Optional[str]:
    """Extract text from uploaded resume file."""
    try:
        filename = uploaded_file.name.lower()
        
        if filename.endswith(".txt"):
            return uploaded_file.read().decode("utf-8")
        
        elif filename.endswith(".pdf"):
            # Try to use backend's PDF extraction
            try:
                import tempfile
                from src.utils import extract_text_from_file
                
                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                
                # Extract text (this uses Gemini for PDFs)
                text = asyncio.run(extract_text_from_file(tmp_path))
                
                # Cleanup
                os.unlink(tmp_path)
                return text
                
            except ImportError:
                # Fallback: try PyPDF2
                try:
                    import PyPDF2
                    reader = PyPDF2.PdfReader(uploaded_file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    return text
                except ImportError:
                    st.error("PDF extraction not available. Please paste text instead.")
                    return None
        
        elif filename.endswith((".docx", ".doc")):
            try:
                import docx
                doc = docx.Document(uploaded_file)
                text = "\n".join([para.text for para in doc.paragraphs])
                return text
            except ImportError:
                st.error("DOCX extraction not available. Please paste text instead.")
                return None
        
        else:
            st.error(f"Unsupported file type: {filename}")
            return None
            
    except Exception as e:
        st.error(f"Error extracting text: {e}")
        return None


def fetch_job_posting(url: str) -> Tuple[Optional[str], Optional[str]]:
    """Fetch job posting text from URL with error details."""
    # First, try backend helper (lean import to avoid heavy dependencies)
    fetch_job_posting_text = None
    ExaContentError = None  # type: ignore
    try:
        from src.api.exa_client import fetch_job_posting_text, ExaContentError  # type: ignore
    except Exception:
        # Fallback handled below
        fetch_job_posting_text = None
        ExaContentError = None  # type: ignore

    if fetch_job_posting_text:
        try:
            text = fetch_job_posting_text(url)
            if not text:
                return None, "No content returned for this URL."
            return text, None
        except RuntimeError as e:
            # Commonly missing EXA_API_KEY
            return None, str(e)
        except Exception as e:  # noqa: BLE001 - we surface the string to UI
            err_msg = str(e)
            if ExaContentError and isinstance(e, ExaContentError):  # type: ignore[arg-type]
                return None, err_msg
            return None, f"Error fetching job posting via backend: {err_msg}"

    # Fallback: use exa-py directly
    try:
        from exa_py import Exa
    except ImportError:
        return None, "Backend fetcher unavailable and exa-py not installed."

    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        return None, "EXA_API_KEY is not set. Add it to backend/.env or environment."

    try:
        client = Exa(api_key=api_key)
        resp = client.get_contents([url], text=True, livecrawl="fallback")
        results = getattr(resp, "results", None)
        if results and getattr(results[0], "text", None):
            text = results[0].text.strip()
            if not text:
                return None, "Exa returned empty content for this URL."
            if len(text) > 20000:
                text = text[:20000]
            return text, None
        return None, "Exa did not return content for this URL."
    except Exception as e:  # noqa: BLE001
        return None, f"Error fetching job posting via Exa: {e}"


def run_evaluation(
    db: EvalDatabase,
    resume_text: str,
    job_text: str,
    stage_id: str,
    model_ids: List[str],
    github_username: Optional[str] = None,
    github_token: Optional[str] = None,
    linkedin_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the evaluation pipeline with multiple models.
    
    This runs the pipeline up to the selected stage, then runs that stage
    with multiple model candidates for comparison.
    """
    runner = EvalRunner(db)
    
    # Create scenario
    scenario = runner.create_scenario(
        user_profile=resume_text,
        job_posting=job_text,
        metadata={
            "github_username": github_username,
            "has_github_token": bool(github_token),  # Don't store token in DB
            "linkedin_url": linkedin_url,
            "source": "ui",
        },
    )
    
    # Build context based on stage
    # For now, we pass the raw inputs. In production, you'd run earlier stages first.
    context = build_stage_context(
        stage_id=stage_id,
        resume_text=resume_text,
        job_text=job_text,
        github_username=github_username,
        github_token=github_token,
        linkedin_url=linkedin_url,
    )
    
    # Build candidate configs
    candidates = [CandidateConfig(model_id=m) for m in model_ids]
    
    # Create a runner function that calls the actual agents
    def model_runner(cfg: CandidateConfig, ctx: Dict[str, Any]) -> str:
        return run_agent_for_stage(stage_id, cfg, ctx)
    
    # Run evaluation
    try:
        stage_eval = runner.run_stage_eval_sync(
            scenario_id=scenario.scenario_id,
            stage_id=stage_id,
            context=context,
            candidates=candidates,
            runner_fn=model_runner,
            randomize=True,
        )
        
        return {
            "success": True,
            "scenario_id": scenario.scenario_id,
            "stage_run_id": stage_eval.id,
            "num_candidates": len(stage_eval.candidates),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def build_stage_context(
    stage_id: str,
    resume_text: str,
    job_text: str,
    github_username: Optional[str] = None,
    github_token: Optional[str] = None,
    linkedin_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Build the context needed for a specific stage.
    
    For stages that depend on earlier stages, we'd need to run those first.
    For now, we provide the raw inputs.
    """
    context = {
        "resume_text": resume_text,
        "job_text": job_text,
        "job_posting": job_text,  # Alias
        "profile": resume_text,   # Alias
    }
    
    if github_username:
        context["github_username"] = github_username
    if github_token:
        context["github_token"] = github_token
    if linkedin_url:
        context["linkedin_url"] = linkedin_url
    
    # For optimizer stage, we'd ideally run job_analyzer first
    # For now, we'll use the job text directly as "analysis"
    if stage_id == "optimizer":
        context["job_analysis"] = job_text  # Simplified
    
    return context


def run_agent_for_stage(
    stage_id: str,
    cfg: CandidateConfig,
    context: Dict[str, Any],
) -> str:
    """Run the appropriate agent for a stage with the given model.
    
    This connects to the actual backend agents.
    """
    import os
    
    # Change to backend directory so prompt files are found
    original_cwd = os.getcwd()
    os.chdir(backend_root)
    
    try:
        from src.api.client_factory import create_client
        
        client = create_client()
        
        if stage_id == "profile":
            from src.agents.profile_agent import ProfileAgent
            
            # Fetch GitHub repos if username and token provided
            profile_repos = context.get("profile_repos")
            github_username = context.get("github_username")
            github_token = context.get("github_token")
            
            if github_username and github_token and not profile_repos:
                try:
                    from src.agents.github_projects_agent import fetch_github_repos
                    profile_repos = fetch_github_repos(github_username, github_token, max_repos=20)
                except Exception as e:
                    # Log but continue without repos
                    profile_repos = None
            
            agent = ProfileAgent(client=client)
            result = ""
            gen = agent.index_profile(
                model=cfg.model_id,
                profile_text=context.get("resume_text", ""),
                profile_repos=profile_repos,
                temperature=cfg.temperature,
            )
            try:
                while True:
                    chunk = next(gen)
                    result += chunk
            except StopIteration:
                pass
            return result
            
        elif stage_id == "job_analyzer":
            from src.agents import JobAnalyzerAgent
            agent = JobAnalyzerAgent(client=client)
            result = ""
            gen = agent.analyze_job(
                job_posting=context.get("job_text", ""),
                model=cfg.model_id,
                temperature=cfg.temperature,
            )
            try:
                while True:
                    chunk = next(gen)
                    result += chunk
            except StopIteration:
                pass
            return result
            
        elif stage_id == "optimizer":
            from src.agents import ResumeOptimizerAgent
            agent = ResumeOptimizerAgent(client=client)
            result = ""
            gen = agent.optimize_resume(
                resume_text=context.get("resume_text", ""),
                job_analysis=context.get("job_analysis", context.get("job_text", "")),
                model=cfg.model_id,
                temperature=cfg.temperature,
            )
            try:
                while True:
                    chunk = next(gen)
                    result += chunk
            except StopIteration:
                pass
            return result
            
        elif stage_id == "qa":
            from src.agents import ValidatorAgent
            agent = ValidatorAgent(client=client)
            result = ""
            gen = agent.validate_resume(
                optimized_resume=context.get("optimized_resume", context.get("resume_text", "")),
                job_posting=context.get("job_text", ""),
                job_analysis=context.get("job_analysis", ""),
                profile_index=context.get("profile_index"),
                model=cfg.model_id,
                temperature=cfg.temperature,
            )
            try:
                while True:
                    chunk = next(gen)
                    result += chunk
            except StopIteration:
                pass
            return result
            
        elif stage_id == "polish":
            from src.agents import PolishAgent
            agent = PolishAgent(client=client, output_format="docx")
            result = ""
            gen = agent.polish_resume(
                optimized_resume=context.get("optimized_resume", context.get("resume_text", "")),
                validation_report=context.get("validation_report", ""),
                model=cfg.model_id,
                temperature=cfg.temperature,
            )
            try:
                while True:
                    chunk = next(gen)
                    result += chunk
            except StopIteration:
                pass
            return result
            
        else:
            return f"[Stage '{stage_id}' not implemented yet]"
            
    except ImportError as e:
        # Backend not available, return mock output
        return f"""[Mock output - backend not available]

Model: {cfg.model_id}
Stage: {stage_id}
Error: {e}

This is a placeholder output. To get real outputs:
1. Ensure the backend is properly installed
2. Set up API keys in .env
3. Run from the evals directory with backend in path

Context received:
- Resume: {len(context.get('resume_text', ''))} chars
- Job: {len(context.get('job_text', ''))} chars
"""
    except Exception as e:
        return f"[Error running {cfg.model_id}]: {type(e).__name__}: {e}"
    finally:
        # Restore original working directory
        os.chdir(original_cwd)
