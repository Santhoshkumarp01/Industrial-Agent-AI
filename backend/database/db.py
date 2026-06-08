"""
SQLite database setup.

Single file: maintenance_wizard.db
Tables: incidents, logbook_entries, feedback, reports
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path("maintenance_wizard.db")


def init_db():
    """Create all tables if they don't exist. Call once at startup."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS incidents (
                id TEXT PRIMARY KEY,
                equipment_id TEXT NOT NULL,
                equipment_name TEXT NOT NULL,
                triggered_by TEXT NOT NULL,     -- 'alert' or 'chat'
                alert_id TEXT,                  -- links to sensor alert if triggered by ML
                session_id TEXT,
                sensor_readings TEXT,           -- JSON string of sensor values at time of incident
                timestamp TEXT NOT NULL,
                status TEXT DEFAULT 'open'      -- 'open' | 'resolved' | 'escalated'
            );

            CREATE TABLE IF NOT EXISTS logbook_entries (
                id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                equipment_id TEXT NOT NULL,
                equipment_name TEXT NOT NULL,
                fault_description TEXT,
                root_cause TEXT,
                risk_level TEXT,
                urgency_hours REAL,
                immediate_actions TEXT,         -- JSON array of strings
                repair_steps TEXT,              -- JSON array of strings
                long_term_recommendations TEXT, -- JSON array of strings
                parts_required TEXT,            -- JSON array of strings
                parts_available INTEGER,        -- 1 or 0
                rul_hours REAL,
                confidence_score REAL,
                evidence_sources TEXT,          -- JSON array of citation refs
                report_id TEXT,
                created_at TEXT NOT NULL,
                resolved_at TEXT,
                technician TEXT,
                FOREIGN KEY (incident_id) REFERENCES incidents(id)
            );

            CREATE TABLE IF NOT EXISTS feedback (
                id TEXT PRIMARY KEY,
                logbook_entry_id TEXT NOT NULL,
                engineer_name TEXT,
                verdict TEXT NOT NULL,          -- 'confirmed' | 'incorrect' | 'partial'
                actual_root_cause TEXT,         -- engineer's correction if incorrect
                actual_action_taken TEXT,
                outcome TEXT,                   -- 'resolved' | 'escalated' | 'pending'
                downtime_hours REAL,
                feedback_timestamp TEXT NOT NULL,
                FOREIGN KEY (logbook_entry_id) REFERENCES logbook_entries(id)
            );

            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                logbook_entry_id TEXT NOT NULL,
                equipment_id TEXT NOT NULL,
                report_json TEXT NOT NULL,      -- full report as JSON string
                created_at TEXT NOT NULL,
                FOREIGN KEY (incident_id) REFERENCES incidents(id)
            );
        """)
    print("✓ SQLite database initialized: maintenance_wizard.db")


@contextmanager
def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row   # returns dict-like rows
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
