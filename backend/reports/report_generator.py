"""
Report Generator — formats analysis results into structured reports.

Generates JSON reports from agent analysis for:
- Export to CMMS systems
- Compliance documentation
- Historical trend analysis
"""

import json
from datetime import datetime
from database.db import get_connection


def generate_report(incident_id: str, logbook_entry_id: str) -> dict:
    """
    Generate a structured report from an incident and its analysis.

    Args:
        incident_id: Incident identifier
        logbook_entry_id: Logbook entry identifier

    Returns:
        Formatted report as dict (ready for JSON serialization)
    """
    # Fetch incident data
    with get_connection() as conn:
        incident_row = conn.execute(
            "SELECT * FROM incidents WHERE id = ?", (incident_id,)
        ).fetchone()
        
        logbook_row = conn.execute(
            "SELECT * FROM logbook_entries WHERE id = ?", (logbook_entry_id,)
        ).fetchone()

    if not incident_row or not logbook_row:
        raise ValueError(f"Incident or logbook entry not found")

    incident = dict(incident_row)
    logbook = dict(logbook_row)

    # Parse JSON fields
    sensor_readings = json.loads(incident.get("sensor_readings", "{}"))
    immediate_actions = json.loads(logbook.get("immediate_actions", "[]"))
    repair_steps = json.loads(logbook.get("repair_steps", "[]"))
    long_term_recommendations = json.loads(logbook.get("long_term_recommendations", "[]"))
    parts_required = json.loads(logbook.get("parts_required", "[]"))
    evidence_sources = json.loads(logbook.get("evidence_sources", "[]"))

    # Build report
    report = {
        "report_id": incident_id,  # Use incident_id as report_id
        "report_type": "MAINTENANCE_ANALYSIS",
        "generated_at": datetime.now().isoformat(),
        
        "incident_summary": {
            "incident_id": incident_id,
            "equipment_id": incident["equipment_id"],
            "equipment_name": incident["equipment_name"],
            "timestamp": incident["timestamp"],
            "triggered_by": incident["triggered_by"],
            "status": incident["status"],
            "alert_id": incident.get("alert_id"),
            "session_id": incident.get("session_id")
        },
        
        "sensor_data": sensor_readings,
        
        "diagnosis": {
            "fault_description": logbook["fault_description"],
            "root_cause": logbook["root_cause"],
            "confidence_score": logbook["confidence_score"],
            "evidence_sources": evidence_sources
        },
        
        "risk_assessment": {
            "risk_level": logbook["risk_level"],
            "urgency_hours": logbook["urgency_hours"],
            "rul_hours": logbook["rul_hours"],
            "parts_required": parts_required,
            "parts_available": bool(logbook["parts_available"])
        },
        
        "maintenance_plan": {
            "immediate_actions": immediate_actions,
            "repair_steps": repair_steps,
            "long_term_recommendations": long_term_recommendations
        },
        
        "status": {
            "created_at": logbook["created_at"],
            "resolved_at": logbook.get("resolved_at"),
            "technician": logbook.get("technician")
        }
    }

    # Store report in database
    _store_report(incident_id, logbook_entry_id, report)

    return report


def _store_report(incident_id: str, logbook_entry_id: str, report: dict):
    """Store report in database."""
    with get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO reports (
                id, incident_id, logbook_entry_id, equipment_id,
                report_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            incident_id,  # Use incident_id as report_id
            incident_id,
            logbook_entry_id,
            report["incident_summary"]["equipment_id"],
            json.dumps(report),
            datetime.now().isoformat()
        ))


def get_report(report_id: str) -> dict | None:
    """Retrieve a stored report by ID."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT report_json FROM reports WHERE id = ?", (report_id,)
        ).fetchone()

    if not row:
        return None

    return json.loads(row["report_json"])


def get_all_reports(equipment_id: str = None, limit: int = 50) -> list[dict]:
    """Get all reports, optionally filtered by equipment."""
    with get_connection() as conn:
        if equipment_id:
            rows = conn.execute("""
                SELECT report_json FROM reports
                WHERE equipment_id = ?
                ORDER BY created_at DESC LIMIT ?
            """, (equipment_id, limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT report_json FROM reports
                ORDER BY created_at DESC LIMIT ?
            """, (limit,)).fetchall()

    return [json.loads(row["report_json"]) for row in rows]
