"""Inspect and analyze the problematic code in application 65."""

from src.database import ApplicationDatabase
import ast

db = ApplicationDatabase()

app_id = 65
app_data = db.get_application(app_id)

if app_data:
    final_resume = app_data.get("optimized_resume_text", "")
    
    print("=" * 80)
    print(f"Generated code for application {app_id}:")
    print("=" * 80)
    print(final_resume[:500])  # First 500 chars
    print("\n... [truncated] ...\n")
    
    # Try to find line 56
    lines = final_resume.split('\n')
    if len(lines) >= 56:
        print(f"\nLine 56 (the problematic line):")
        print(f"  {repr(lines[55])}")
        
        # Show context around line 56
        print(f"\nContext (lines 54-58):")
        for i in range(53, min(58, len(lines))):
            print(f"  {i+1}: {repr(lines[i])}")
    
    # Try to parse it
    print("\n" + "=" * 80)
    print("Attempting to parse as Python code:")
    try:
        ast.parse(final_resume)
        print("✅ Code is valid Python!")
    except SyntaxError as e:
        print(f"❌ Syntax Error: {e}")
        print(f"   Line {e.lineno}: {e.text}")
        print(f"   Offset: {e.offset}")
        
        # Show the problematic line and surrounding context
        if e.lineno:
            lines = final_resume.split('\n')
            start = max(0, e.lineno - 3)
            end = min(len(lines), e.lineno + 2)
            print(f"\nContext around error (lines {start+1}-{end}):")
            for i in range(start, end):
                marker = ">>> " if i == e.lineno - 1 else "    "
                print(f"{marker}{i+1}: {lines[i]}")
else:
    print(f"Application {app_id} not found")
