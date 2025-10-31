"""Quick script to check what DOCX code was generated for an application."""

from src.database import ApplicationDatabase

db = ApplicationDatabase()

# Replace with your application ID
app_id = 67

app_data = db.get_application(app_id)
if app_data:
    final_resume = app_data.get("optimized_resume_text", "")
    print("=" * 80)
    print(f"Generated DOCX code for application {app_id}:")
    print("=" * 80)
    print(final_resume)
    print("=" * 80)
else:
    print(f"Application {app_id} not found")
