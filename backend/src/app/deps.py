import os
import streamlit as st

from src.database import ApplicationDatabase
from src.api.multiprovider import MultiProviderClient


@st.cache_resource
def get_database(schema_version: int = 2) -> ApplicationDatabase:
    """Get database instance (cached)."""
    db_path = os.getenv("DATABASE_PATH", "./data/applications.db")
    return ApplicationDatabase(db_path)


@st.cache_resource
def get_api_client() -> MultiProviderClient:
    """Get multi-provider client (cached) with lazy provider init."""
    # Provider API keys are validated on first use of a given model.
    return MultiProviderClient()

