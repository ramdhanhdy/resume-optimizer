"""Quick script to inspect the evals database."""
import sqlite3
import json

db_path = "data/resume_evals.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# List tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print(f"Tables: {tables}\n")

# Count rows in each table
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"{table}: {count} rows")

print("\n--- Scenarios ---")
cursor.execute("SELECT * FROM eval_scenarios LIMIT 5")
for row in cursor.fetchall():
    print(dict(row))

print("\n--- Stage Runs ---")
cursor.execute("SELECT * FROM eval_stage_runs LIMIT 5")
for row in cursor.fetchall():
    print(dict(row))

print("\n--- Candidates ---")
cursor.execute("SELECT * FROM eval_candidates LIMIT 10")
for row in cursor.fetchall():
    print(dict(row))

print("\n--- Judgments ---")
cursor.execute("SELECT * FROM eval_judgments")
for row in cursor.fetchall():
    d = dict(row)
    print(d)

print("\n--- Judgments with model info ---")
cursor.execute("""
    SELECT 
        j.id,
        j.stage_run_id,
        sr.stage_id,
        c.model_id as winner_model_id,
        j.scores,
        j.tags
    FROM eval_judgments j
    JOIN eval_stage_runs sr ON j.stage_run_id = sr.id
    JOIN eval_candidates c ON j.chosen_candidate_id = c.id
""")
for row in cursor.fetchall():
    print(dict(row))

conn.close()
