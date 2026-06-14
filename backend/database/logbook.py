"""
Logbook CRUD — stores and retrieves maintenance incident log entries.
"""

import uuid
import json
from datetime import datetime
from database.db import get_connection
from models.schemas import LogbookEntryCreate


def create_entry(entry: LogbookEntryCreate) -> str:
    """Create a new logbook entry."""
    entry_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO logbook_entries (
                id, incident_id, equipment_id, equipment_name,
                fault_description, root_cause, risk_level, urgency_hours,
                immediate_actions, repair_steps, long_term_recommendations,
                parts_required, parts_available, rul_hours, confidence_score,
                evidence_sources, report_id, created_at, fault_code
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry_id,
            entry.incident_id,
            entry.equipment_id,
            entry.equipment_name,
            entry.fault_description,
            entry.root_cause,
            entry.risk_level,
            entry.urgency_hours,
            json.dumps(entry.immediate_actions),
            json.dumps(entry.repair_steps),
            json.dumps(entry.long_term_recommendations),
            json.dumps(entry.parts_required),
            1 if entry.parts_available else 0,
            entry.rul_hours,
            entry.confidence_score,
            json.dumps(entry.evidence_sources),
            entry.report_id,
            now,
            getattr(entry, 'fault_code', None)
        ))

    return entry_id


def get_all_entries(equipment_id: str = None, limit: int = 50) -> list[dict]:
    """Get all logbook entries, optionally filtered by equipment."""
    with get_connection() as conn:
        if equipment_id:
            rows = conn.execute("""
                SELECT * FROM logbook_entries
                WHERE equipment_id = ?
                ORDER BY created_at DESC LIMIT ?
            """, (equipment_id, limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM logbook_entries
                ORDER BY created_at DESC LIMIT ?
            """, (limit,)).fetchall()

    entries = []
    for row in rows:
        entry = dict(row)
        # Deserialize JSON fields
        for field in ["immediate_actions", "repair_steps",
                      "long_term_recommendations", "parts_required",
                      "evidence_sources"]:
            if entry.get(field):
                entry[field] = json.loads(entry[field])
        entries.append(entry)
    return entries


def get_entry(entry_id: str) -> dict | None:
    """Get a single logbook entry by ID."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM logbook_entries WHERE id = ?", (entry_id,)
        ).fetchone()

    if not row:
        return None

    entry = dict(row)
    for field in ["immediate_actions", "repair_steps",
                  "long_term_recommendations", "parts_required",
                  "evidence_sources"]:
        if entry.get(field):
            entry[field] = json.loads(entry[field])
    return entry


def mark_resolved(entry_id: str, technician: str):
    """Mark a logbook entry as resolved."""
    with get_connection() as conn:
        conn.execute("""
            UPDATE logbook_entries
            SET resolved_at = ?, technician = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), technician, entry_id))
