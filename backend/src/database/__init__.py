"""Database module for application tracking."""

from .supabase_db import SupabaseDatabase, get_database

__all__ = ["ApplicationDatabase", "SupabaseDatabase", "get_database"]


def __getattr__(name: str):
    if name == "ApplicationDatabase":
        from .db import ApplicationDatabase
        return ApplicationDatabase
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
