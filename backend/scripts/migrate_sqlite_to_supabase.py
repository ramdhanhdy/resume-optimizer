#!/usr/bin/env python3
"""
Migrate existing SQLite data to Supabase PostgreSQL.

This script reads data from the local SQLite database and inserts it into Supabase.
It requires:
1. A valid Supabase project with the schema already applied
2. SUPABASE_URL and SUPABASE_SECRET_KEY environment variables
3. A default user_id to assign to migrated records (since SQLite didn't have user_id)

Usage:
    python scripts/migrate_sqlite_to_supabase.py --user-id <uuid>
    
Or set DEFAULT_MIGRATION_USER_ID environment variable.
"""

import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client, Client


def get_sqlite_connection(db_path: str) -> sqlite3.Connection:
    """Connect to SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_supabase_client() -> Client:
    """Create Supabase client."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SECRET_KEY must be set")
    
    return create_client(url, key)


def migrate_applications(sqlite_conn: sqlite3.Connection, supabase: Client, user_id: str) -> dict:
    """Migrate applications table."""
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT * FROM applications")
    rows = cursor.fetchall()
    
    migrated = 0
    skipped = 0
    id_mapping = {}  # old_id -> new_id
    
    for row in rows:
        old_id = row["id"]
        
        # Map SQLite status to Supabase status
        status = row["status"] or "pending"
        if status == "in_progress":
            status = "processing"
        
        data = {
            "user_id": user_id,
            "company_name": row["company_name"],
            "job_title": row["job_title"],
            "job_url": row.get("job_url"),
            "job_posting_text": row["job_posting_text"],
            "original_resume_text": row["original_resume_text"],
            "optimized_resume_text": row["optimized_resume_text"],
            "total_cost_usd": row["total_cost"] or 0,
            "status": status,
            "model_used": row["model_used"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        
        try:
            result = supabase.table("applications").insert(data).execute()
            if result.data:
                new_id = result.data[0]["id"]
                id_mapping[old_id] = new_id
                migrated += 1
                print(f"  ✓ Application {old_id} -> {new_id}")
        except Exception as e:
            print(f"  ✗ Application {old_id} failed: {e}")
            skipped += 1
    
    return {"migrated": migrated, "skipped": skipped, "id_mapping": id_mapping}


def migrate_agent_outputs(sqlite_conn: sqlite3.Connection, supabase: Client, user_id: str, app_id_mapping: dict) -> dict:
    """Migrate agent_outputs table."""
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT * FROM agent_outputs")
    rows = cursor.fetchall()
    
    migrated = 0
    skipped = 0
    
    for row in rows:
        old_app_id = row["application_id"]
        new_app_id = app_id_mapping.get(old_app_id)
        
        if not new_app_id:
            print(f"  ⚠ Skipping agent_output {row['id']}: application {old_app_id} not migrated")
            skipped += 1
            continue
        
        # Parse model info
        model_used = row.get("model_used") or ""
        model_provider = None
        model_name = model_used
        if "::" in model_used:
            parts = model_used.split("::", 1)
            model_provider = parts[0]
            model_name = parts[1] if len(parts) > 1 else model_used
        
        data = {
            "application_id": new_app_id,
            "user_id": user_id,
            "agent_name": row["agent_name"],
            "agent_number": row["agent_number"],
            "model_provider": model_provider,
            "model_name": model_name,
            "input_tokens": row.get("input_tokens") or 0,
            "output_tokens": row.get("output_tokens") or 0,
            "cost_usd": row.get("cost") or 0,
            "execution_time_ms": row.get("execution_time_ms"),
            "output_data": {"text": row.get("output_text")},
            "created_at": row["created_at"],
        }
        
        try:
            result = supabase.table("agent_outputs").insert(data).execute()
            if result.data:
                migrated += 1
        except Exception as e:
            print(f"  ✗ Agent output {row['id']} failed: {e}")
            skipped += 1
    
    return {"migrated": migrated, "skipped": skipped}


def migrate_validation_scores(sqlite_conn: sqlite3.Connection, supabase: Client, user_id: str, app_id_mapping: dict) -> dict:
    """Migrate validation_scores table."""
    cursor = sqlite_conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='validation_scores'")
    if not cursor.fetchone():
        print("  ⚠ validation_scores table not found in SQLite")
        return {"migrated": 0, "skipped": 0}
    
    cursor.execute("SELECT * FROM validation_scores")
    rows = cursor.fetchall()
    
    migrated = 0
    skipped = 0
    
    for row in rows:
        old_app_id = row["application_id"]
        new_app_id = app_id_mapping.get(old_app_id)
        
        if not new_app_id:
            skipped += 1
            continue
        
        data = {
            "application_id": new_app_id,
            "user_id": user_id,
            "requirements_match": row.get("requirements_match"),
            "ats_optimization": row.get("ats_optimization"),
            "cultural_fit": row.get("cultural_fit"),
            "overall_score": row.get("overall_score"),
            "created_at": row["created_at"],
        }
        
        try:
            result = supabase.table("validation_scores").insert(data).execute()
            if result.data:
                migrated += 1
        except Exception as e:
            print(f"  ✗ Validation score {row['id']} failed: {e}")
            skipped += 1
    
    return {"migrated": migrated, "skipped": skipped}


def migrate_profiles(sqlite_conn: sqlite3.Connection, supabase: Client, user_id: str) -> dict:
    """Migrate profiles table."""
    cursor = sqlite_conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='profiles'")
    if not cursor.fetchone():
        print("  ⚠ profiles table not found in SQLite")
        return {"migrated": 0, "skipped": 0}
    
    cursor.execute("SELECT * FROM profiles")
    rows = cursor.fetchall()
    
    migrated = 0
    skipped = 0
    
    for row in rows:
        # Parse sources JSON
        sources = []
        try:
            sources = json.loads(row.get("sources") or "[]")
        except:
            pass
        
        # Try to extract linkedin_url and github_username from sources
        linkedin_url = row.get("linkedin_url")
        github_username = row.get("github_username")
        
        for source in sources:
            if isinstance(source, str):
                if source.startswith("linkedin:"):
                    linkedin_url = linkedin_url or source.replace("linkedin:", "")
                elif source.startswith("github:"):
                    github_username = github_username or source.replace("github:", "")
        
        # Parse profile_index - could be JSON or text
        profile_index = row.get("profile_index")
        if profile_index and isinstance(profile_index, str):
            try:
                profile_index = json.loads(profile_index)
            except:
                profile_index = {"text": profile_index}
        
        data = {
            "user_id": user_id,
            "linkedin_url": linkedin_url,
            "github_username": github_username,
            "sources": sources,
            "profile_text": row.get("profile_text"),
            "profile_index": profile_index,
            "created_at": row["created_at"],
            "updated_at": row.get("updated_at") or row["created_at"],
        }
        
        try:
            result = supabase.table("profiles").insert(data).execute()
            if result.data:
                migrated += 1
                print(f"  ✓ Profile {row['id']} migrated")
        except Exception as e:
            print(f"  ✗ Profile {row['id']} failed: {e}")
            skipped += 1
    
    return {"migrated": migrated, "skipped": skipped}


def main():
    parser = argparse.ArgumentParser(description="Migrate SQLite data to Supabase")
    parser.add_argument(
        "--user-id",
        default=os.getenv("DEFAULT_MIGRATION_USER_ID"),
        help="UUID of the user to assign migrated records to"
    )
    parser.add_argument(
        "--db-path",
        default="data/applications.db",
        help="Path to SQLite database file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without actually migrating"
    )
    
    args = parser.parse_args()
    
    if not args.user_id:
        print("Error: --user-id is required (or set DEFAULT_MIGRATION_USER_ID)")
        print("You can get your user ID from Supabase Dashboard > Authentication > Users")
        sys.exit(1)
    
    db_path = Path(args.db_path)
    if not db_path.exists():
        print(f"Error: SQLite database not found at {db_path}")
        sys.exit(1)
    
    print(f"🔄 Migrating SQLite data to Supabase")
    print(f"   Source: {db_path}")
    print(f"   Target user: {args.user_id}")
    print()
    
    if args.dry_run:
        print("🔍 DRY RUN - no data will be migrated")
        print()
    
    # Connect to databases
    sqlite_conn = get_sqlite_connection(str(db_path))
    
    if args.dry_run:
        # Just count records
        cursor = sqlite_conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM applications")
        app_count = cursor.fetchone()[0]
        print(f"   Applications: {app_count}")
        
        cursor.execute("SELECT COUNT(*) FROM agent_outputs")
        output_count = cursor.fetchone()[0]
        print(f"   Agent outputs: {output_count}")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='validation_scores'")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM validation_scores")
            score_count = cursor.fetchone()[0]
            print(f"   Validation scores: {score_count}")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='profiles'")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM profiles")
            profile_count = cursor.fetchone()[0]
            print(f"   Profiles: {profile_count}")
        
        print()
        print("Run without --dry-run to migrate data")
        return
    
    supabase = get_supabase_client()
    
    # Migrate tables in order (respecting foreign keys)
    print("📦 Migrating applications...")
    app_result = migrate_applications(sqlite_conn, supabase, args.user_id)
    print(f"   Migrated: {app_result['migrated']}, Skipped: {app_result['skipped']}")
    print()
    
    print("📦 Migrating agent_outputs...")
    output_result = migrate_agent_outputs(sqlite_conn, supabase, args.user_id, app_result["id_mapping"])
    print(f"   Migrated: {output_result['migrated']}, Skipped: {output_result['skipped']}")
    print()
    
    print("📦 Migrating validation_scores...")
    score_result = migrate_validation_scores(sqlite_conn, supabase, args.user_id, app_result["id_mapping"])
    print(f"   Migrated: {score_result['migrated']}, Skipped: {score_result['skipped']}")
    print()
    
    print("📦 Migrating profiles...")
    profile_result = migrate_profiles(sqlite_conn, supabase, args.user_id)
    print(f"   Migrated: {profile_result['migrated']}, Skipped: {profile_result['skipped']}")
    print()
    
    print("✅ Migration complete!")
    print()
    print("Summary:")
    print(f"   Applications: {app_result['migrated']} migrated")
    print(f"   Agent outputs: {output_result['migrated']} migrated")
    print(f"   Validation scores: {score_result['migrated']} migrated")
    print(f"   Profiles: {profile_result['migrated']} migrated")


if __name__ == "__main__":
    main()
