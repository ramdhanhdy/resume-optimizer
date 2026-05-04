"""Focused tests for application review ownership and schema migration."""

from pathlib import Path
import sqlite3
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.db import ApplicationDatabase


def test_application_reviews_are_scoped_to_the_current_user(tmp_path):
    db = ApplicationDatabase(db_path=str(tmp_path / "applications.db"), user_id="user-a")
    owner_db = db.for_user("user-a")
    other_db = db.for_user("user-b")

    application_id = owner_db.create_application(
        company_name="Acme",
        job_title="Backend Engineer",
        job_posting_text="Build APIs",
        original_resume_text="resume",
    )

    owner_db.save_application_review(
        application_id=application_id,
        plain_text="plain review",
        markdown="# review",
        filename="review.docx",
        summary_points=["one", "two"],
    )

    owner_review = owner_db.get_application_review(application_id)
    assert owner_review is not None
    assert owner_review["status"] == "in_progress"
    assert owner_review["summary_points"] == ["one", "two"]

    assert owner_db.get_application(application_id)["user_id"] == "user-a"
    assert [row["id"] for row in owner_db.get_all_applications()] == [application_id]

    assert other_db.get_application(application_id) is None
    assert other_db.get_application_review(application_id) is None
    assert other_db.get_all_applications() == []

    with pytest.raises(ValueError, match="not found or not owned"):
        other_db.save_application_review(
            application_id=application_id,
            plain_text="cross-tenant write",
            markdown="# no",
            filename="no.docx",
            summary_points=[],
        )


def test_latest_completed_application_with_review_filters_and_orders(tmp_path):
    db = ApplicationDatabase(db_path=str(tmp_path / "applications.db"), user_id="user-a")
    owner_db = db.for_user("user-a")
    other_db = db.for_user("user-b")

    in_progress_id = owner_db.create_application("Acme", "Backend", "Build APIs", "resume")
    completed_without_review_id = owner_db.create_application(
        "Beta", "Platform", "Scale APIs", "resume"
    )
    older_completed_id = owner_db.create_application("Cobalt", "Data", "Build ETL", "resume")
    latest_completed_id = owner_db.create_application("Delta", "ML", "Build AI", "resume")
    other_completed_id = other_db.create_application("Other", "ML", "Build AI", "resume")

    for application_id in (older_completed_id, latest_completed_id, other_completed_id):
        (other_db if application_id == other_completed_id else owner_db).save_application_review(
            application_id=application_id,
            plain_text=f"plain {application_id}",
            markdown=f"# review {application_id}",
            filename=f"review-{application_id}.docx",
            summary_points=[f"point {application_id}"],
        )

    owner_db.save_application_review(
        application_id=in_progress_id,
        plain_text="plain in-progress",
        markdown="# in-progress",
        filename="in-progress.docx",
        summary_points=["skip"],
    )
    owner_db.update_application(completed_without_review_id, status="completed")
    owner_db.update_application(older_completed_id, status="completed")
    owner_db.update_application(latest_completed_id, status="completed")
    other_db.update_application(other_completed_id, status="completed")

    cursor = owner_db.conn.cursor()
    cursor.execute(
        "UPDATE applications SET updated_at = '2026-01-01 00:00:00' WHERE id = ?",
        (older_completed_id,),
    )
    cursor.execute(
        "UPDATE applications SET updated_at = '2026-01-02 00:00:00' WHERE id = ?",
        (completed_without_review_id,),
    )
    cursor.execute(
        "UPDATE applications SET updated_at = '2026-01-03 00:00:00' WHERE id = ?",
        (latest_completed_id,),
    )
    owner_db.conn.commit()

    review = owner_db.get_latest_completed_application_with_review()
    assert review is not None
    assert review["application_id"] == latest_completed_id
    assert review["status"] == "completed"
    assert review["summary_points"] == [f"point {latest_completed_id}"]

    assert db.for_user("missing-user").get_latest_completed_application_with_review() is None


def test_application_review_schema_upgrade_adds_owner_and_foreign_key(tmp_path):
    db_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            company_name TEXT,
            job_title TEXT,
            job_url TEXT,
            job_posting_text TEXT,
            original_resume_text TEXT,
            optimized_resume_text TEXT,
            model_used TEXT,
            total_cost REAL DEFAULT 0.0,
            status TEXT DEFAULT 'in_progress',
            notes TEXT
        );

        CREATE TABLE application_reviews (
            application_id INTEGER PRIMARY KEY,
            plain_text TEXT NOT NULL,
            markdown TEXT NOT NULL,
            filename TEXT NOT NULL,
            summary_points TEXT NOT NULL DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        INSERT INTO applications (company_name, job_title, job_posting_text, original_resume_text)
        VALUES ('Acme', 'Backend Engineer', 'Build APIs', 'resume');

        INSERT INTO application_reviews (application_id, plain_text, markdown, filename, summary_points)
        VALUES
            (1, 'plain', '# review', 'review.docx', '["kept"]'),
            (999, 'orphan', '# orphan', 'orphan.docx', '[]');
        """
    )
    conn.close()

    db = ApplicationDatabase(db_path=str(db_path), user_id="local")
    cursor = db.conn.cursor()

    cursor.execute("PRAGMA table_info(applications)")
    application_columns = {row["name"] for row in cursor.fetchall()}
    assert "user_id" in application_columns

    cursor.execute("PRAGMA table_info(application_reviews)")
    review_columns = {row["name"] for row in cursor.fetchall()}
    assert "user_id" in review_columns

    cursor.execute("PRAGMA foreign_key_list(application_reviews)")
    foreign_keys = cursor.fetchall()
    assert any(
        row["table"] == "applications"
        and row["from"] == "application_id"
        and row["to"] == "id"
        and str(row["on_delete"]).upper() == "CASCADE"
        for row in foreign_keys
    )

    cursor.execute(
        "SELECT application_id, user_id, plain_text FROM application_reviews ORDER BY application_id"
    )
    rows = cursor.fetchall()
    assert [dict(row) for row in rows] == [
        {"application_id": 1, "user_id": "local", "plain_text": "plain"}
    ]
