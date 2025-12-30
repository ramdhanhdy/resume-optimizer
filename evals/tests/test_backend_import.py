#!/usr/bin/env python
"""Test backend imports for eval suite.

Run with: uv run python tests/test_backend_import.py
"""
import sys
from pathlib import Path

# Adjust path for tests directory
backend_root = Path(__file__).parent.parent.parent / "backend"
backend_src = backend_root / "src"
sys.path.insert(0, str(backend_root))
sys.path.insert(0, str(backend_src))

# Load .env
from dotenv import load_dotenv
load_dotenv(backend_root / ".env")

print("Testing imports...")

try:
    from src.api.client_factory import create_client
    print("✓ create_client imported")
except Exception as e:
    print(f"✗ create_client failed: {e}")

try:
    from src.agents import JobAnalyzerAgent
    print("✓ JobAnalyzerAgent imported")
except Exception as e:
    print(f"✗ JobAnalyzerAgent failed: {e}")

try:
    client = create_client()
    print(f"✓ client created: {type(client)}")
except Exception as e:
    print(f"✗ client creation failed: {e}")
