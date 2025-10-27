"""Test script for PDF extraction functionality using Gemini 2.5 Flash."""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_pdf_extraction_module():
    """Test the PDF extraction module directly."""
    print("=" * 60)
    print("Testing PDF Extraction Module")
    print("=" * 60)
    
    from src.utils.pdf_extractor import extract_text_from_pdf_fallback
    
    # Check if Gemini API key is available
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        print("✓ GEMINI_API_KEY found")
    else:
        print("✗ GEMINI_API_KEY not found - will use fallback extraction")
    
    # Test fallback extraction (pypdf)
    print("\n" + "-" * 60)
    print("Testing Fallback Extraction (pypdf)")
    print("-" * 60)
    
    # Create a simple test PDF for testing
    test_pdf_path = Path(__file__).parent / "test_sample.pdf"
    
    if not test_pdf_path.exists():
        print(f"✗ Test PDF not found at: {test_pdf_path}")
        print("  Skipping fallback extraction test")
    else:
        try:
            text = extract_text_from_pdf_fallback(str(test_pdf_path))
            print(f"✓ Successfully extracted {len(text)} characters")
            print(f"  Preview: {text[:200]}...")
        except Exception as e:
            print(f"✗ Fallback extraction failed: {str(e)}")
    
    # Test Gemini extraction if API key available
    if api_key:
        print("\n" + "-" * 60)
        print("Testing Gemini 2.5 Flash Extraction")
        print("-" * 60)
        
        if not test_pdf_path.exists():
            print(f"✗ Test PDF not found at: {test_pdf_path}")
            print("  Skipping Gemini extraction test")
        else:
            try:
                from src.utils.pdf_extractor import extract_text_from_pdf_gemini
                
                text = await extract_text_from_pdf_gemini(str(test_pdf_path))
                print(f"✓ Successfully extracted {len(text)} characters using Gemini")
                print(f"  Preview: {text[:200]}...")
            except Exception as e:
                print(f"✗ Gemini extraction failed: {str(e)}")
    
    print("\n" + "=" * 60)


async def test_file_handler():
    """Test the file handler extract_text_from_file function."""
    print("=" * 60)
    print("Testing File Handler")
    print("=" * 60)
    
    from src.utils import extract_text_from_file
    
    test_files = {
        "test_sample.pdf": "PDF file",
        "test_sample.txt": "Text file",
        "test_sample.docx": "DOCX file",
    }
    
    for filename, file_type in test_files.items():
        file_path = Path(__file__).parent / filename
        
        print(f"\n{file_type}: {filename}")
        print("-" * 60)
        
        if not file_path.exists():
            print(f"✗ Test file not found - skipping")
            continue
        
        try:
            text = await extract_text_from_file(str(file_path))
            print(f"✓ Successfully extracted {len(text)} characters")
            print(f"  Preview: {text[:150]}...")
        except Exception as e:
            print(f"✗ Extraction failed: {str(e)}")
    
    print("\n" + "=" * 60)


async def test_server_endpoint():
    """Test the server API endpoint (if server is running)."""
    print("=" * 60)
    print("Testing Server API Endpoint")
    print("=" * 60)
    
    try:
        import httpx
        
        # Check if server is running
        try:
            response = httpx.get("http://localhost:8000/", timeout=2.0)
            print("✓ Server is running")
        except Exception:
            print("✗ Server is not running at http://localhost:8000")
            print("  Start the server with: python backend/server.py")
            return
        
        # Test the upload endpoint
        test_pdf = Path(__file__).parent / "test_sample.pdf"
        if not test_pdf.exists():
            print("✗ Test PDF not found - skipping endpoint test")
            return
        
        print(f"\nTesting POST /api/upload-resume with: {test_pdf.name}")
        print("-" * 60)
        
        with open(test_pdf, "rb") as f:
            files = {"file": (test_pdf.name, f, "application/pdf")}
            response = httpx.post(
                "http://localhost:8000/api/upload-resume",
                files=files,
                timeout=30.0,
            )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Upload successful")
            print(f"  Filename: {data.get('filename')}")
            print(f"  Text length: {data.get('length')}")
            print(f"  Extraction method: {data.get('extraction_method')}")
            if data.get('text'):
                print(f"  Preview: {data['text'][:150]}...")
        else:
            print(f"✗ Upload failed with status {response.status_code}")
            print(f"  Response: {response.text}")
    
    except ImportError:
        print("✗ httpx not installed - skipping server test")
        print("  Install with: pip install httpx")
    except Exception as e:
        print(f"✗ Server test failed: {str(e)}")
    
    print("\n" + "=" * 60)


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("PDF EXTRACTION FUNCTIONALITY TESTS")
    print("=" * 60 + "\n")
    
    await test_pdf_extraction_module()
    await test_file_handler()
    await test_server_endpoint()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
    print("\nNote: To fully test PDF extraction with Gemini:")
    print("1. Set GEMINI_API_KEY in backend/.env")
    print("2. Place a test PDF as backend/test_sample.pdf")
    print("3. Run this script: python backend/test_pdf_extraction.py")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
