"""Debug script to see the full generated code for application 49."""

import sqlite3
from pathlib import Path

db_path = "./data/applications.db"

if not Path(db_path).exists():
    print(f"❌ Database not found at: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

cursor = conn.cursor()
cursor.execute("""
    SELECT id, company_name, job_title, optimized_resume_text
    FROM applications 
    WHERE id = 49
""")

row = cursor.fetchone()

if row:
    print("=" * 80)
    print(f"Application ID: {row['id']}")
    print(f"Company: {row['company_name']}")
    print(f"Job Title: {row['job_title']}")
    print("=" * 80)
    print("\nGenerated DOCX Code:")
    print("=" * 80)
    code = row['optimized_resume_text'] or ""
    print(code)
    print("=" * 80)
    
    # Try to identify the problematic line
    print("\n🔍 Looking for potential issues:")
    lines = code.split('\n')
    for i, line in enumerate(lines, 1):
        if '[' in line and ']' in line:
            print(f"  Line {i}: {line.strip()[:100]}")
else:
    print(f"❌ Application 49 not found")

conn.close()
