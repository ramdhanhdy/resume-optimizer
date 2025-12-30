"""Quick script to check what DOCX code was generated for an application."""

from pathlib import Path
from src.database import ApplicationDatabase


def main(app_id: int = 67):
    """Print optimized DOCX code for a given application ID."""
    db = ApplicationDatabase()
    app_data = db.get_application(app_id)
    if not app_data:
        print(f"Application {app_id} not found")
        return

    final_resume = app_data.get("optimized_resume_text", "")
    print("=" * 80)
    print(f"Generated DOCX code for application {app_id}:")
    print("=" * 80)
    print(final_resume)
    print("=" * 80)


if __name__ == "__main__":
    main()
