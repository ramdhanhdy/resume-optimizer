"""Utilities for handling file uploads and extraction."""

import tempfile
import os
from typing import Optional, Tuple
from pathlib import Path


def save_uploaded_file(uploaded_file) -> Tuple[str, str]:
    """Save uploaded file to temporary location.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        
    Returns:
        Tuple of (file_path, mime_type)
    """
    # Create temp file with same extension
    suffix = Path(uploaded_file.name).suffix
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    
    temp_file.write(uploaded_file.getbuffer())
    temp_file.close()
    
    return temp_file.name, uploaded_file.type


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
