"""
Migration: Add fault_code column to existing logbook_entries table
"""
import sqlite3

DB_PATH = "industrial_agent.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Checking if fault_code column exists...")
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(logbook_entries)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "fault_code" in columns:
        print("✅ fault_code column already exists")
    else:
        print("Adding fault_code column...")
        cursor.execute("ALTER TABLE logbook_entries ADD COLUMN fault_code TEXT")
        conn.commit()
        print("✅ fault_code column added successfully")
    
    conn.close()
    print("\n✓ Migration complete!")

if __name__ == "__main__":
    migrate()
