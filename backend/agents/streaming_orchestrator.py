"""
Streaming Agent Orchestrator with Real-Time Progress Updates

This orchestrator yields progress updates as each agent runs, allowing
the frontend to show real-time status like:
- "🔍 Agent 1: Analyzing root cause..."
- "✅ Agent 1: Root cause identified"
- "⚠️ Agent 2: Assessing risk level..."
- etc.
"""

import logging
import uuid
from datetime import datetime
from typing import Generator, Dict, Any
from agents.root_cause_agent import analyze_root_cause
from agents.risk_agent import analyze_risk
from agents.maintenance_agent import generate_maintenance_plan
from database.db import get_connection
from database.logbook import create_entry
from models.schemas import LogbookEntryCreate
import json

logger = logging.getLogger(__name__)


def run_analysis_streaming(
    equipment_id: str,
    equipment_name: str,
    alert_description: str,
    sensor_data: dict,
    anomaly_score: float,
    risk_level_raw: str,
    rul_hours: float = None,
    triggered_by: str = "alert",
    alert_id: str = None,
    session_id: str = None,
    severity: str = None,
    fault_code: str = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Orchestrates all three agents with real-time streaming updates.
    
    Yields progress updates in the format:
    {
        "type": "progress" | "agent_complete" | "complete",
        "agent": "root_cause" | "risk" | "maintenance" | None,
        "status": "starting" | "running" | "complete",
        "message": "Human-readable status message",
        "data": {...}  # Agent output when complete
    }
    
    Final yield is the complete analysis result.
    """
    
    # Initialize
    incident_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    yield {
        "type": "progress",
        "agent": None,
        "status": "starting",
        "message": f"Starting 3-agent analysis for {equipment_name}",
        "data": {"incident_id": incident_id}
    }
    
    # Store incident
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
    
    # ============================================================
    # AGENT 1: Root Cause Analysis
    # ============================================================
    yield {
        "type": "progress",
        "agent": "root_cause",
        "status": "starting",
        "message": "Analyzing root cause from sensor data and historical incidents",
        "data": None
    }
    
    logger.info(f"[StreamingOrchestrator] Agent 1 (Root Cause) starting for {equipment_id}")
    
    root_cause_result = analyze_root_cause(
        equipment_id=equipment_id,
        equipment_name=equipment_name,
        sensor_data=sensor_data,
        alert_description=alert_description,
        rul_hours=rul_hours
    )
    
    yield {
        "type": "agent_complete",
        "agent": "root_cause",
        "status": "complete",
        "message": f"Root cause identified: {root_cause_result['root_cause'][:100]}{'...' if len(root_cause_result['root_cause']) > 100 else ''}",
        "data": {
            "root_cause": root_cause_result["root_cause"],
            "fault_description": root_cause_result["fault_description"],
            "confidence": root_cause_result["confidence"],
            "evidence": root_cause_result["evidence"][:3],  # Top 3 evidence sources
            "similar_incidents_count": len(root_cause_result.get("similar_incidents", []))
        }
    }
    
    # ============================================================
    # AGENT 2: Risk Assessment
    # ============================================================
    yield {
        "type": "progress",
        "agent": "risk",
        "status": "starting",
        "message": "Assessing risk level, urgency, and spare parts availability",
        "data": None
    }
    
    logger.info(f"[StreamingOrchestrator] Agent 2 (Risk) starting for {equipment_id}")
    
    risk_result = analyze_risk(
        equipment_id=equipment_id,
        equipment_name=equipment_name,
        root_cause=root_cause_result["root_cause"],
        anomaly_score=anomaly_score,
        rul_hours=rul_hours,
        sensor_data=sensor_data,
        severity=severity or risk_level_raw,  # Use severity or fall back to risk_level_raw
        fault_code=fault_code
    )
    
    risk_badge = {
        "CRITICAL": "Critical",
        "HIGH": "High",
        "MEDIUM": "Medium",
        "LOW": "Low"
    }.get(risk_result["risk_level"], "Unknown")
    
    yield {
        "type": "agent_complete",
        "agent": "risk",
        "status": "complete",
        "message": f"Risk assessed as {risk_badge} with {risk_result['urgency_hours']}h urgency",
        "data": {
            "risk_level": risk_result["risk_level"],
            "urgency_hours": risk_result["urgency_hours"],
            "rul_hours": risk_result.get("rul_hours"),
            "parts_required": risk_result["parts_required"],
            "parts_available": risk_result["parts_available"],
            "parts_stock": risk_result.get("parts_stock", {})
        }
    }
    
    # ============================================================
    # AGENT 3: Maintenance Planning
    # ============================================================
    yield {
        "type": "progress",
        "agent": "maintenance",
        "status": "starting",
        "message": "Generating maintenance plan and repair steps",
        "data": None
    }
    
    logger.info(f"[StreamingOrchestrator] Agent 3 (Maintenance) starting for {equipment_id}")
    
    maintenance_result = generate_maintenance_plan(
        equipment_id=equipment_id,
        equipment_name=equipment_name,
        root_cause=root_cause_result["root_cause"],
        risk_level=risk_result["risk_level"],
        parts_required=risk_result["parts_required"]
    )
    
    yield {
        "type": "agent_complete",
        "agent": "maintenance",
        "status": "complete",
        "message": f"Maintenance plan generated with {len(maintenance_result['immediate_actions'])} immediate actions and {len(maintenance_result['repair_steps'])} repair steps",
        "data": {
            "immediate_actions": maintenance_result["immediate_actions"],
            "repair_steps": maintenance_result["repair_steps"],
            "long_term_recommendations": maintenance_result["long_term_recommendations"]
        }
    }
    
    # ============================================================
    # Finalize: Store in Database
    # ============================================================
    yield {
        "type": "progress",
        "agent": None,
        "status": "running",
        "message": "Saving analysis to logbook and generating report",
        "data": None
    }
    
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
        "rul_hours": risk_result.get("rul_hours"),
        "parts_required": risk_result["parts_required"],
        "parts_available": risk_result["parts_available"],
        "parts_stock": risk_result.get("parts_stock", {}),
        
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
        report_id=incident_id
    )
    
    logbook_entry_id = create_entry(logbook_entry)
    analysis_result["logbook_entry_id"] = logbook_entry_id
    
    # Generate formal report
    try:
        from reports.report_generator import generate_report
        report = generate_report(incident_id, logbook_entry_id)
        analysis_result["report_id"] = report.get("report_id")
    except Exception as e:
        logger.error(f"[StreamingOrchestrator] Failed to generate report: {e}")
        analysis_result["report_id"] = None
    
    # ============================================================
    # COMPLETE
    # ============================================================
    yield {
        "type": "complete",
        "agent": None,
        "status": "complete",
        "message": "Analysis complete. Logbook entry and report generated.",
        "data": analysis_result
    }
    
    logger.info(f"[StreamingOrchestrator] Analysis complete for {equipment_id}")


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
