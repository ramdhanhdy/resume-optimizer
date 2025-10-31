"""Extract code from app 65, show error, and allow manual fix."""

from src.database import ApplicationDatabase
import ast

db = ApplicationDatabase()
app_id = 65

# Get application data
app_data = db.get_application(app_id)
if not app_data:
    print(f"❌ Application {app_id} not found")
    exit(1)

code = app_data.get("optimized_resume_text", "")
if not code:
    print("❌ No code found")
    exit(1)

print("=" * 80)
print(f"Extracting code from application {app_id}")
print("=" * 80)

# Check for syntax errors
print("\n🔍 Checking for syntax errors...")
try:
    ast.parse(code)
    print("✅ Code is already valid!")
    exit(0)
except SyntaxError as e:
    print(f"❌ Syntax Error at line {e.lineno}: {e}")
    error_line_num = e.lineno

# Show error context
lines = code.split('\n')
if error_line_num and error_line_num <= len(lines):
    print(f"\n📍 Error context (lines {error_line_num-2} to {error_line_num+2}):")
    start = max(0, error_line_num - 3)
    end = min(len(lines), error_line_num + 2)
    for i in range(start, end):
        marker = ">>> " if i == error_line_num - 1 else "    "
        line_preview = lines[i][:100] + "..." if len(lines[i]) > 100 else lines[i]
        print(f"{marker}{i+1}: {line_preview}")

# Save to file
filename = f"app{app_id}_code.py"
with open(filename, "w", encoding="utf-8") as f:
    f.write(code)

print(f"\n💾 Code saved to: {filename}")
print("\n📝 To fix:")
print(f"   1. Open {filename} in your editor")
print(f"   2. Go to line {error_line_num}")
print(f"   3. Fix the unterminated string (likely an unescaped apostrophe or quote)")
print(f"   4. Run: python apply_fix_app65.py")

# Create the apply script
apply_script = f"""'''Apply the fixed code back to application {app_id}.'''

from src.database import ApplicationDatabase
import ast

db = ApplicationDatabase()
app_id = {app_id}

# Read the fixed code
with open('app{app_id}_code.py', 'r', encoding='utf-8') as f:
    fixed_code = f.read()

# Validate it
print("🔍 Validating fixed code...")
try:
    ast.parse(fixed_code)
    print("✅ Code is syntactically valid!")
    
    # Update database
    db.update_application(app_id, optimized_resume_text=fixed_code)
    print(f"✅ Updated application {{app_id}}")
    print("\\n🎉 Fix applied successfully!")
    
except SyntaxError as e:
    print(f"❌ Code still has syntax errors: {{e}}")
    print(f"   Line {{e.lineno}}: {{e.text}}")
    print("\\n💡 Please fix the errors and try again")
"""

with open("apply_fix_app65.py", "w", encoding="utf-8") as f:
    f.write(apply_script)

print(f"\n✅ Created apply_fix_app65.py for applying your fix")
