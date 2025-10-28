"""Fix application 54's DOCX code by removing problematic table.paragraph_format calls."""

import sqlite3
from pathlib import Path

db_path = Path("./data/applications.db")
conn = sqlite3.connect(db_path)

cursor = conn.cursor()
cursor.execute("SELECT optimized_resume_text FROM applications WHERE id = 54")
row = cursor.fetchone()

if not row:
    print("❌ Application 54 not found")
    exit(1)

code = row[0]
print(f"✅ Found application 54 with {len(code)} chars of code")

# Check what errors exist
has_table_paragraph_format = "table.paragraph_format" in code
has_early_rows_access = False

if "add_table(rows=0" in code:
    lines = code.split('\n')
    for i, line in enumerate(lines):
        if "add_table(rows=0" in line:
            for j in range(i+1, min(i+5, len(lines))):
                if "add_header_row" in lines[j]:
                    break
                if "table.rows[0]" in lines[j]:
                    has_early_rows_access = True
                    break

print(f"Issues found:")
print(f"  - table.paragraph_format: {has_table_paragraph_format}")
print(f"  - Early table.rows[0] access: {has_early_rows_access}")

# Fix the code
fixed_code = code

# Remove table.paragraph_format lines (tables don't have this attribute)
if has_table_paragraph_format:
    print("\n🔧 Removing table.paragraph_format lines...")
    lines = fixed_code.split('\n')
    fixed_lines = []
    for line in lines:
        if "table.paragraph_format" in line:
            # Comment it out instead of removing
            fixed_lines.append("# " + line.strip() + "  # REMOVED: tables don't have paragraph_format")
            print(f"   Removed: {line.strip()}")
        else:
            fixed_lines.append(line)
    fixed_code = '\n'.join(fixed_lines)

# Remove early table.rows[0] access
if has_early_rows_access:
    print("\n🔧 Removing early table.rows[0] access...")
    lines = fixed_code.split('\n')
    fixed_lines = []
    in_table_section = False
    for i, line in enumerate(lines):
        if "add_table(rows=0" in line:
            in_table_section = True
            fixed_lines.append(line)
        elif in_table_section and "add_header_row" in line:
            in_table_section = False
            fixed_lines.append(line)
        elif in_table_section and "table.rows[0]" in line:
            # Comment it out
            fixed_lines.append("# " + line.strip() + "  # REMOVED: accessing rows[0] before add_header_row")
            print(f"   Removed: {line.strip()}")
        else:
            fixed_lines.append(line)
    fixed_code = '\n'.join(fixed_lines)

# Update database
cursor.execute(
    "UPDATE applications SET optimized_resume_text = ? WHERE id = 54",
    (fixed_code,)
)
conn.commit()
conn.close()

print(f"\n✅ Fixed application 54's DOCX code")
print(f"   Original: {len(code)} chars")
print(f"   Fixed: {len(fixed_code)} chars")
print("\n🔄 Try downloading the DOCX again")
