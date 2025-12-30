"""Query application data from database."""

import sqlite3
from pathlib import Path

db_path = "./data/applications.db"

if not Path(db_path).exists():
    print(f"❌ Database not found at: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# Query application 46
cursor = conn.cursor()
cursor.execute("""
    SELECT id, company_name, job_title, optimized_resume_text, status, created_at
    FROM applications 
    WHERE id = 46
""")

row = cursor.fetchone()

if row:
    print("=" * 80)
    print(f"Application ID: {row['id']}")
    print(f"Company: {row['company_name']}")
    print(f"Job Title: {row['job_title']}")
    print(f"Status: {row['status']}")
    print(f"Created: {row['created_at']}")
    print("=" * 80)
    print("\nGenerated DOCX Code:")
    print("=" * 80)
    code = row['optimized_resume_text'] or ""
    print(code)
    print("=" * 80)
    print(f"\nCode length: {len(code)} characters")
    
    # Check for common syntax issues
    print("\n🔍 Checking for common issues:")
    if "1.5year" in code.lower() or "1+year" in code.lower():
        print("  ⚠️  Found potential invalid number format (e.g., '1.5year')")
    if code.count('"') % 2 != 0:
        print("  ⚠️  Unmatched double quotes")
    if code.count("'") % 2 != 0:
        print("  ⚠️  Unmatched single quotes")
        
else:
    print(f"❌ Application 46 not found in database")

conn.close()
