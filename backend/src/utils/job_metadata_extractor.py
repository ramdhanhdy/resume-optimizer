"""Extract job metadata (company name, job title) from job postings using LLM."""

import json
import os
from typing import Tuple, Optional, Dict, Any

# Default model for metadata extraction (fast and cheap)
# Using Gemini 3 Flash Preview via Gemini API
DEFAULT_EXTRACTION_MODEL = os.getenv("METADATA_EXTRACTION_MODEL", "gemini::gemini-3-flash-preview")

EXTRACTION_PROMPT = """Extract the company name and job title from the following job posting.

Return ONLY a JSON object with exactly these two fields:
{
  "company_name": "The company name",
  "job_title": "The job title/position"
}

Rules:
- If you cannot determine the company name, use "Unknown Company"
- If you cannot determine the job title, use "Unknown Position"
- Do not include location, remote status, or other details in the job title
- Do not include Inc., LLC, Corp., etc. in the company name
- Return ONLY the JSON object, no other text

Job Posting:
"""


def extract_job_metadata(
    job_text: str, 
    analysis_text: Optional[str] = None,
    client: Optional[Any] = None,
    model: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Extract company name and job title from job posting using LLM.
    
    Args:
        job_text: Raw job posting text
        analysis_text: Optional job analysis output (not used, kept for API compatibility)
        client: Optional LLM client (will create one if not provided)
        model: Optional model to use (defaults to METADATA_EXTRACTION_MODEL env var)
        
    Returns:
        Tuple of (company_name, job_title)
    """
    if not job_text or not job_text.strip():
        return "Unknown Company", "Unknown Position"
    
    # Use provided model or default
    extraction_model = model or DEFAULT_EXTRACTION_MODEL
    
    # Create client if not provided
    if client is None:
        from src.api.client_factory import create_client
        client = create_client()
    
    try:
        # Truncate job text if too long (keep first 4000 chars for efficiency)
        truncated_text = job_text[:4000] if len(job_text) > 4000 else job_text
        
        # Build prompt
        prompt = EXTRACTION_PROMPT + truncated_text
        
        # Call LLM (non-streaming for simplicity)
        result = ""
        metadata = {}
        
        for chunk in client.stream_completion(
            prompt=prompt,
            model=extraction_model,
            text_content=None,
            temperature=0.1,  # Low temperature for consistent extraction
            max_tokens=200,   # Short response expected
        ):
            result += chunk
        
        # Get metadata from generator return
        if hasattr(client, 'last_request_cost'):
            metadata = {
                "cost": getattr(client, 'last_request_cost', 0),
                "input_tokens": getattr(client, 'last_input_tokens', 0),
                "output_tokens": getattr(client, 'last_output_tokens', 0),
            }
        
        # Parse JSON response
        company_name, job_title = _parse_llm_response(result)
        
        print(f"📋 LLM extracted: company='{company_name}', title='{job_title}'")
        return company_name, job_title
        
    except Exception as e:
        print(f"⚠️ LLM metadata extraction failed: {e}, falling back to defaults")
        return "Unknown Company", "Unknown Position"


def _parse_llm_response(response: str) -> Tuple[str, str]:
    """Parse the LLM JSON response to extract company and title."""
    company = "Unknown Company"
    title = "Unknown Position"
    
    try:
        # Try to find JSON in the response
        response = response.strip()
        
        # Handle markdown code blocks
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            response = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            response = response[start:end].strip()
        
        # Find JSON object
        start_idx = response.find("{")
        end_idx = response.rfind("}") + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = response[start_idx:end_idx]
            data = json.loads(json_str)
            
            if "company_name" in data and data["company_name"]:
                company = str(data["company_name"]).strip()[:80]
            if "job_title" in data and data["job_title"]:
                title = str(data["job_title"]).strip()[:100]
                
    except json.JSONDecodeError as e:
        print(f"⚠️ Failed to parse LLM JSON response: {e}")
    except Exception as e:
        print(f"⚠️ Error parsing LLM response: {e}")
    
    return company, title


async def extract_job_metadata_async(
    job_text: str,
    client: Optional[Any] = None,
    model: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Async version of extract_job_metadata for use in async pipelines.
    
    Args:
        job_text: Raw job posting text
        client: Optional LLM client
        model: Optional model to use
        
    Returns:
        Tuple of (company_name, job_title)
    """
    import asyncio
    
    # Run sync version in executor
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: extract_job_metadata(job_text, None, client, model)
    )
