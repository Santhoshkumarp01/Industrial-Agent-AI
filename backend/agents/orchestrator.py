"""
Agent Orchestrator — coordinates the three specialized agents.

Workflow:
1. Receive analysis request (equipment anomaly + sensor data)
2. Call Root Cause Agent → get diagnosis
3. Call Risk Agent → get urgency assessment
4. Call Maintenance Agent → get work order
5. Combine results into unified report
6. Store in database and return to frontend

This is the main entry point for the agentic system.
"""

import logging
import uuid
from datetime import datetime
from agents.root_cause_agent import analyze_root_cause
from agents.risk_agent import analyze_risk
from agents.maintenance_agent import generate_maintenance_plan
from database.db import get_connection
import json

logger = logging.getLogger(__name__)


def run_analysis(
    equipment_id: str,
    equipment_name: str,
    alert_description: str,
    sensor_data: dict,
    anomaly_score: float,
    risk_level_raw: str,
    rul_hours: float = None,
    triggered_by: str = "alert",
    alert_id: str = None,
    session_id: str = None
) -> dict:
    """
    Orchestrates all three agents to produce a complete analysis.

    Args:
        equipment_id: "RM1", "RM3", etc.
        equipment_name: Human-readable name
        alert_description: Description of the anomaly
        sensor_data: Dict of current sensor readings
        anomaly_score: 0.0-1.0 from ML model
        risk_level_raw: Initial risk level from ML ("LOW"/"MEDIUM"/"HIGH"/"CRITICAL")
        rul_hours: Estimated hours to failure
        triggered_by: "alert" or "chat"
        alert_id: If triggered by sensor alert
        session_id: If triggered by chat

    Returns:
        Complete analysis result with all agent outputs
    """
    logger.info(f"[Orchestrator] Starting analysis for {equipment_id}...")

    # Generate incident ID
    incident_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()

    # Store incident record
    _store_incident(
        incident_id=incident_id,
        equipment_id=equipment_id,
        equipment_name=equipment_name,
        triggered_by=triggered_by,
        alert_id=alert_id,
        session_id=session_id,
        sensor_data=sensor_data,
        timestamp=timestamp
    )

    # AGENT 1: Root Cause Analysis
    logger.info("[Orchestrator] Calling Root Cause Agent...")
    root_cause_result = analyze_root_cause(
        equipment_id=equipment_id,
        equipment_name=equipment_name,
        sensor_data=sensor_data,
        alert_description=alert_description,
        rul_hours=rul_hours
    )

    # AGENT 2: Risk Assessment
    logger.info("[Orchestrator] Calling Risk Agent...")
    risk_result = analyze_risk(
        equipment_id=equipment_id,
        equipment_name=equipment_name,
        root_cause=root_cause_result["root_cause"],
        anomaly_score=anomaly_score,
        rul_hours=rul_hours,
        sensor_data=sensor_data
    )

    # AGENT 3: Maintenance Planning
    logger.info("[Orchestrator] Calling Maintenance Agent...")
    maintenance_result = generate_maintenance_plan(
        equipment_id=equipment_id,
        equipment_name=equipment_name,
        root_cause=root_cause_result["root_cause"],
        risk_level=risk_result["risk_level"],
        parts_required=risk_result["parts_required"]
    )

    # Combine all results
    analysis_result = {
        "incident_id": incident_id,
        "equipment_id": equipment_id,
        "equipment_name": equipment_name,
        "timestamp": timestamp,
        "triggered_by": triggered_by,
        
        # Root cause analysis
        "fault_description": root_cause_result["fault_description"],
        "root_cause": root_cause_result["root_cause"],
        "confidence_score": root_cause_result["confidence"],
        "evidence_sources": root_cause_result["evidence"],
        "similar_incidents": root_cause_result["similar_incidents"],
        
        # Risk assessment
        "risk_level": risk_result["risk_level"],
        "urgency_hours": risk_result["urgency_hours"],
        "parts_required": risk_result["parts_required"],
        "parts_available": risk_result["parts_available"],
        "parts_stock": risk_result["parts_stock"],
        
        # Maintenance plan
        "immediate_actions": maintenance_result["immediate_actions"],
        "repair_steps": maintenance_result["repair_steps"],
        "long_term_recommendations": maintenance_result["long_term_recommendations"],
        
        # Additional context
        "rul_hours": rul_hours,
        "sensor_data": sensor_data,
        "anomaly_score": anomaly_score
    }

    # Store logbook entry
    from database.logbook import create_entry
    from models.schemas import LogbookEntryCreate

    logbook_entry = LogbookEntryCreate(
        incident_id=incident_id,
        equipment_id=equipment_id,
        equipment_name=equipment_name,
        fault_description=root_cause_result["fault_description"],
        root_cause=root_cause_result["root_cause"],
        risk_level=risk_result["risk_level"],
        urgency_hours=risk_result["urgency_hours"],
        immediate_actions=maintenance_result["immediate_actions"],
        repair_steps=maintenance_result["repair_steps"],
        long_term_recommendations=maintenance_result["long_term_recommendations"],
        parts_required=risk_result["parts_required"],
        parts_available=risk_result["parts_available"],
        rul_hours=rul_hours,
        confidence_score=root_cause_result["confidence"],
        evidence_sources=root_cause_result["evidence"],
        report_id=incident_id  # Will be replaced when formal report is generated
    )

    logbook_entry_id = create_entry(logbook_entry)
    analysis_result["logbook_entry_id"] = logbook_entry_id

    # Generate formal report
    logger.info("[Orchestrator] Generating formal report...")
    from reports.report_generator import generate_report
    try:
        report = generate_report(incident_id, logbook_entry_id)
        analysis_result["report_id"] = report.get("report_id")
        logger.info(f"[Orchestrator] Report {report.get('report_id')} generated successfully")
    except Exception as e:
        logger.error(f"[Orchestrator] Failed to generate report: {e}")
        # Don't fail the entire analysis if report generation fails
        analysis_result["report_id"] = None

    logger.info(
        f"[Orchestrator] Analysis complete. "
        f"Incident: {incident_id}, Logbook: {logbook_entry_id}"
    )

    return analysis_result


def _store_incident(
    incident_id: str,
    equipment_id: str,
    equipment_name: str,
    triggered_by: str,
    alert_id: str,
    session_id: str,
    sensor_data: dict,
    timestamp: str
):
    """Store incident record in database."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO incidents (
                id, equipment_id, equipment_name, triggered_by,
                alert_id, session_id, sensor_readings, timestamp, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open')
        """, (
            incident_id,
            equipment_id,
            equipment_name,
            triggered_by,
            alert_id,
            session_id,
            json.dumps(sensor_data),
            timestamp
        ))
    logger.info(f"[Orchestrator] Incident {incident_id} stored in database")
