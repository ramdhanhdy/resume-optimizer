"""Fix application 49's DOCX code by removing problematic table.rows[0] access."""

import sqlite3
from pathlib import Path

db_path = "./data/applications.db"
conn = sqlite3.connect(db_path)

cursor = conn.cursor()
cursor.execute("SELECT optimized_resume_text FROM applications WHERE id = 49")
row = cursor.fetchone()

if not row:
    print("❌ Application 49 not found")
    exit(1)

code = row[0]

# Remove the problematic lines that access table.rows[0] before rows exist
fixed_code = code.replace(
    "table.rows[0].cells[0].paragraphs[0].paragraph_format.space_before = Pt(6)",
    "# Removed: table.rows[0] access before rows exist"
).replace(
    "table.rows[0].cells[0].paragraphs[0].paragraph_format.space_before = Pt(4)",
    "# Removed: table.rows[0] access before rows exist"
)

# Update database
cursor.execute(
    "UPDATE applications SET optimized_resume_text = ? WHERE id = 49",
    (fixed_code,)
)
conn.commit()
conn.close()

print("✅ Fixed application 49's DOCX code")
print("🔄 Try downloading the DOCX again")
