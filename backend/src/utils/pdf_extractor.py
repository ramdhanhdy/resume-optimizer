"""PDF text extraction using Gemini 2.5 Flash model for document understanding."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types


async def extract_text_from_pdf_gemini(
    file_path: str,
    api_key: Optional[str] = None,
    model: str = "gemini-2.5-flash",
) -> str:
    """Extract text from PDF using Gemini 2.5 Flash document understanding.

    Uses Gemini's native PDF processing capabilities for high-quality extraction
    that preserves structure, tables, and formatting.

    Args:
        file_path: Path to PDF file
        api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
        model: Gemini model to use (default: gemini-2.5-flash)

    Returns:
        Extracted text content from PDF

    Raises:
        ValueError: If API key is not provided or found in environment
        Exception: If PDF processing fails
    """
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "Gemini API key required for PDF extraction. "
            "Set GEMINI_API_KEY environment variable or pass api_key parameter."
        )

    try:
        client = genai.Client(api_key=api_key)
        file_size = os.path.getsize(file_path)

        # Determine extraction method based on file size
        if file_size > 20_000_000:  # 20MB threshold
            # Use File API for large files
            return await _extract_via_file_api(client, file_path, model)
        else:
            # Use inline bytes for smaller files
            return await _extract_inline(client, file_path, model)

    except Exception as e:
        raise Exception(f"Gemini PDF extraction failed: {str(e)}") from e


async def _extract_via_file_api(
    client: genai.Client,
    file_path: str,
    model: str,
) -> str:
    """Extract PDF text using Gemini File API (for files > 20MB).

    Args:
        client: Gemini client instance
        file_path: Path to PDF file
        model: Model identifier

    Returns:
        Extracted text content
    """
    # Upload file to Gemini
    uploaded_file = client.files.upload(
        file=file_path,
        config=dict(mime_type="application/pdf"),
    )

    # Wait for file processing to complete
    max_wait = 60  # seconds
    wait_time = 0
    while uploaded_file.state == "PROCESSING" and wait_time < max_wait:
        time.sleep(2)
        wait_time += 2
        uploaded_file = client.files.get(name=uploaded_file.name)

    if uploaded_file.state == "FAILED":
        raise Exception("Gemini file processing failed")

    if uploaded_file.state == "PROCESSING":
        raise Exception("Gemini file processing timeout")

    # Extract text with structured prompt
    prompt = """Extract all text content from this document. 

Requirements:
- Preserve the original structure and formatting
- Include all sections, headings, and bullet points
- Maintain the hierarchical organization
- Include table contents if present
- Output clean, readable text

Do not add any commentary or analysis - just extract the text as-is."""

    response = client.models.generate_content(
        model=model,
        contents=[uploaded_file, prompt],
    )

    # Cleanup uploaded file
    try:
        client.files.delete(name=uploaded_file.name)
    except Exception:
        pass  # Ignore cleanup errors

    return response.text


async def _extract_inline(
    client: genai.Client,
    file_path: str,
    model: str,
) -> str:
    """Extract PDF text using inline bytes (for files < 20MB).

    Args:
        client: Gemini client instance
        file_path: Path to PDF file
        model: Model identifier

    Returns:
        Extracted text content
    """
    file_bytes = Path(file_path).read_bytes()

    prompt = """Extract all text content from this document. 

Requirements:
- Preserve the original structure and formatting
- Include all sections, headings, and bullet points
- Maintain the hierarchical organization
- Include table contents if present
- Output clean, readable text

Do not add any commentary or analysis - just extract the text as-is."""

    response = client.models.generate_content(
        model=model,
        contents=[
            types.Part.from_bytes(
                data=file_bytes,
                mime_type="application/pdf",
            ),
            prompt,
        ],
    )

    return response.text


def extract_text_from_pdf_fallback(file_path: str) -> str:
    """Fallback PDF text extraction using pypdf library.

    Used when Gemini API is unavailable or fails. Provides basic text extraction
    without advanced formatting preservation.

    Args:
        file_path: Path to PDF file

    Returns:
        Extracted text content

    Raises:
        ImportError: If pypdf is not installed
        Exception: If PDF reading fails
    """
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise ImportError(
            "pypdf library required for fallback extraction. "
            "Install with: pip install pypdf"
        ) from e

    try:
        reader = PdfReader(file_path)
        text_parts = []

        for page_num, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            if page_text.strip():
                text_parts.append(f"--- Page {page_num} ---\n{page_text}")

        if not text_parts:
            raise Exception("No text content found in PDF")

        return "\n\n".join(text_parts)

    except Exception as e:
        raise Exception(f"PDF extraction failed: {str(e)}") from e


__all__ = [
    "extract_text_from_pdf_gemini",
    "extract_text_from_pdf_fallback",
]
