"""Inspect the current SQLite database structure and sample data."""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "backend" / "data" / "applications.db"

def inspect_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all tables (exclude sqlite internal tables)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    tables = [r[0] for r in cursor.fetchall()]
    print(f"=== Tables ({len(tables)}) ===")
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        count = cursor.fetchone()[0]
        print(f"  - {t} ({count} rows)")
    
    print("\n" + "="*60)
    
    # Detailed analysis of key tables
    key_tables = ['applications', 'agent_outputs', 'validation_scores', 'run_metadata', 'profiles']
    
    for table in key_tables:
        if table not in tables:
            continue
            
        print(f"\n### {table} ###")
        
        # Schema
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        print("Columns:")
        for col in columns:
            print(f"  {col['name']:30} {col['type']:15} {'NOT NULL' if col['notnull'] else 'NULL':10} {'PK' if col['pk'] else ''}")
        
        # Row count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"\nRow count: {count}")
        
        # Data quality checks
        print("\nData Quality Issues:")
        
        if table == 'applications':
            # Check for missing company names
            cursor.execute("SELECT COUNT(*) FROM applications WHERE company_name IS NULL OR company_name = 'Company'")
            bad_company = cursor.fetchone()[0]
            print(f"  - Missing/placeholder company_name: {bad_company}/{count}")
            
            # Check for missing job titles
            cursor.execute("SELECT COUNT(*) FROM applications WHERE job_title IS NULL OR job_title = 'Position'")
            bad_title = cursor.fetchone()[0]
            print(f"  - Missing/placeholder job_title: {bad_title}/{count}")
            
            # Check status distribution
            cursor.execute("SELECT status, COUNT(*) FROM applications GROUP BY status")
            print("  - Status distribution:")
            for row in cursor.fetchall():
                print(f"      {row[0]}: {row[1]}")
            
            # Check for zero costs
            cursor.execute("SELECT COUNT(*) FROM applications WHERE total_cost = 0 OR total_cost IS NULL")
            zero_cost = cursor.fetchone()[0]
            print(f"  - Zero/null total_cost: {zero_cost}/{count}")
            
        if table == 'agent_outputs':
            # Check for zero tokens
            cursor.execute("SELECT COUNT(*) FROM agent_outputs WHERE input_tokens = 0 AND output_tokens = 0")
            zero_tokens = cursor.fetchone()[0]
            print(f"  - Zero tokens (both input & output): {zero_tokens}/{count}")
            
            # Check for zero cost
            cursor.execute("SELECT COUNT(*) FROM agent_outputs WHERE cost = 0 OR cost IS NULL")
            zero_cost = cursor.fetchone()[0]
            print(f"  - Zero/null cost: {zero_cost}/{count}")
            
            # Agent distribution
            cursor.execute("SELECT agent_name, COUNT(*) FROM agent_outputs GROUP BY agent_name ORDER BY COUNT(*) DESC")
            print("  - Agent distribution:")
            for row in cursor.fetchall():
                print(f"      {row[0]}: {row[1]}")
        
        if table == 'run_metadata':
            # Check client_id patterns
            cursor.execute("SELECT DISTINCT client_id FROM run_metadata LIMIT 10")
            print("  - Sample client_ids:")
            for row in cursor.fetchall():
                print(f"      {row[0]}")
        
        print("\n" + "-"*60)
    
    # Check for orphaned records
    print("\n### Orphan Check ###")
    cursor.execute("""
        SELECT COUNT(*) FROM agent_outputs ao 
        LEFT JOIN applications a ON ao.application_id = a.id 
        WHERE a.id IS NULL
    """)
    orphan_outputs = cursor.fetchone()[0]
    print(f"  - agent_outputs without application: {orphan_outputs}")
    
    cursor.execute("""
        SELECT COUNT(*) FROM validation_scores vs 
        LEFT JOIN applications a ON vs.application_id = a.id 
        WHERE a.id IS NULL
    """)
    orphan_scores = cursor.fetchone()[0]
    print(f"  - validation_scores without application: {orphan_scores}")
    
    conn.close()

if __name__ == "__main__":
    inspect_db()
