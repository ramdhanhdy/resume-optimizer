"""Shared test environment defaults."""

import os


os.environ.setdefault("USE_SUPABASE_DB", "true")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SECRET_KEY", "sb_secret_test")
