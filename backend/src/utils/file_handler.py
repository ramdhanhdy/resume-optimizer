"""Utilities for handling file uploads and extraction."""

import tempfile
import os
from typing import Optional, Tuple, Union, BinaryIO
from pathlib import Path


def save_uploaded_file(uploaded_file, filename: Optional[str] = None) -> str:
    """Save uploaded file to temporary location.
    
    Args:
        uploaded_file: File-like object (Streamlit UploadedFile or similar)
        filename: Optional filename for extension detection
        
    Returns:
        Path to temporary file
    """
    # Detect file extension
    if filename:
        suffix = Path(filename).suffix
    elif hasattr(uploaded_file, 'name'):
        suffix = Path(uploaded_file.name).suffix
    else:
        suffix = ''
    
    # Create temp file with same extension
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    
    # Handle different file-like object types
    if hasattr(uploaded_file, 'getbuffer'):
        # Streamlit UploadedFile
        temp_file.write(uploaded_file.getbuffer())
    elif hasattr(uploaded_file, 'read'):
        # Standard file-like object
        content = uploaded_file.read()
        if isinstance(content, bytes):
            temp_file.write(content)
        else:
            temp_file.write(content.encode())
    else:
        raise ValueError("Unsupported file object type")
    
    temp_file.close()
    
    return temp_file.name


def cleanup_temp_file(file_path: str):
    """Remove temporary file.
    
    Args:
        file_path: Path to temporary file
    """
    try:
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)
    except Exception:
        pass  # Ignore cleanup errors


def get_file_icon(file_type: str) -> str:
    """Get emoji icon for file type.
    
    Args:
        file_type: MIME type
        
    Returns:
        Emoji icon
    """
    if file_type.startswith("image/"):
        return "🖼️"
    elif "pdf" in file_type:
        return "📄"
    elif "word" in file_type or "document" in file_type:
        return "📝"
    else:
        return "📎"


async def extract_text_from_file(
    file_path: str,
    use_gemini: bool = True,
    gemini_api_key: Optional[str] = None,
) -> str:
    """Extract text from uploaded file based on type.
    
    Supports:
    - PDF: Gemini 2.5 Flash (primary) or pypdf (fallback)
    - DOCX: python-docx extraction
    - TXT/MD: Direct reading
    - Images: Return filename reference (multimodal handled by agents)
    
    Args:
        file_path: Path to file
        use_gemini: Whether to use Gemini for PDF extraction (default: True)
        gemini_api_key: Optional Gemini API key for PDF extraction
        
    Returns:
        Extracted text content
        
    Raises:
        Exception: If extraction fails
    """
    file_ext = Path(file_path).suffix.lower()
    
    # PDF extraction
    if file_ext == '.pdf':
        if use_gemini:
            try:
                from src.utils.pdf_extractor import extract_text_from_pdf_gemini
                return await extract_text_from_pdf_gemini(
                    file_path,
                    api_key=gemini_api_key,
                )
            except Exception as e:
                # Fall back to pypdf if Gemini fails
                from src.utils.pdf_extractor import extract_text_from_pdf_fallback
                return extract_text_from_pdf_fallback(file_path)
        else:
            from src.utils.pdf_extractor import extract_text_from_pdf_fallback
            return extract_text_from_pdf_fallback(file_path)
    
    # DOCX extraction
    elif file_ext in ['.docx', '.doc']:
        try:
            from docx import Document
            doc = Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return '\n\n'.join(paragraphs)
        except Exception as e:
            raise Exception(f"DOCX extraction failed: {str(e)}") from e
    
    # Plain text files
    elif file_ext in ['.txt', '.md', '.text']:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
    
    # Image files - return reference
    elif file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
        filename = Path(file_path).name
        return f"[Image file: {filename}]\nNote: Image content will be processed by multimodal agents."
    
    else:
        raise Exception(f"Unsupported file type: {file_ext}")


def is_pdf(file_type: str) -> bool:
    """Check if file type is PDF.
    
    Args:
        file_type: MIME type or file extension
        
    Returns:
        True if PDF, False otherwise
    """
    file_type_lower = file_type.lower()
    return 'pdf' in file_type_lower or file_type_lower == '.pdf'
