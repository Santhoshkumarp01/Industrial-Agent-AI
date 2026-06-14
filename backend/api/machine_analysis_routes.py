"""
Machine Analysis API

  GET  /machine-analysis/logs/{machine_tag}         — latest dynamic logs
  GET  /machine-analysis/summary/{machine_tag}      — latest reading + thresholds
  POST /machine-analysis/analyze/{machine_tag}      — full RAG analysis (logs + PDF) + logbook entry
  POST /machine-analysis/inject-anomaly/{machine_tag} — demo: spike a sensor

The analysis endpoint:
1. Generates / retrieves latest machine logs
2. Looks up the mapped equipment document in Qdrant
3. Runs the full retrieval → rerank → parent-section → LLM pipeline
4. Returns a dynamically generated, document-grounded answer with citations
5. Creates a logbook entry for CRITICAL/WARNING anomalies

No static/predefined answers are used.
"""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from sensors.machine_logs import (
    MACHINE_CONFIG, MACHINE_DOC_MAP, MACHINE_TAG_TO_EQUIPMENT_TAG,
    get_latest_logs, generate_log_entry, format_logs_for_llm, get_machine_summary,
)
from retrieval.retriever import retrieve
from llm.answerer import generate_answer
from database.logbook import create_entry, get_all_entries
from database.db import get_connection
from reports.report_generator import _store_report
from models.schemas import LogbookEntryCreate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/machine-analysis", tags=["machine-analysis"])


# ── helpers ───────────────────────────────────────────────────────────────────

def _get_historical_context(machine_tag: str) -> str:
    """
    Pull the last 5 logbook entries for this machine and format them
    as a brief historical summary block for the LLM.
    This enables learning from historical data — the LLM sees past
    faults and resolutions for this specific machine.
    """
    try:
        entries = get_all_entries(equipment_id=machine_tag, limit=5)
        if not entries:
            return ""

        lines = ["=== HISTORICAL MAINTENANCE RECORDS FOR THIS MACHINE ==="]
        for e in entries:
            ts = (e.get("created_at") or "")[:10]
            lines.append(
                f"[{ts}] {e.get('risk_level','?')} — "
                f"Root cause: {e.get('root_cause','N/A')}. "
                f"Actions: {'; '.join((e.get('immediate_actions') or [])[:2])}."
            )
        lines.append("=== END HISTORICAL RECORDS ===\n")
        return "\n".join(lines)
    except Exception as ex:
        logger.warning(f"[MachineAnalysis] Could not load historical context: {ex}")
        return ""


def _build_analysis_query(machine_tag: str, logs: list) -> str:
    """
    Build the natural language query for the retrieval pipeline.
    Uses the latest sensor anomalies to form a targeted question.
    """
    latest = logs[-1] if logs else {}
    severity   = latest.get("severity", "UNKNOWN")
    fault_code = latest.get("fault_code", "")
    alert_type = latest.get("alert_type", "NOMINAL")
    anomaly_sensors = latest.get("anomaly_sensors", [])
    display = MACHINE_CONFIG[machine_tag]["display_name"]

    if not anomaly_sensors or severity == "NORMAL":
        return (
            f"The {display} is operating normally. "
            f"What are the standard maintenance checks and inspection procedures "
            f"recommended for this equipment? "
            f"What are the normal operating thresholds for vibration, temperature, and current?"
        )

    sensor_text = " and ".join(s.replace("_", " ") for s in anomaly_sensors)
    vib  = latest.get("vibration_mm_s")
    temp = latest.get("bearing_temp_c")
    curr = latest.get("motor_current_a")
    pres = latest.get("lube_pressure_bar")
    rpm  = latest.get("rpm")

    return (
        f"The {display} has a {severity} fault (code {fault_code}). "
        f"Current readings: vibration {vib} mm/s, bearing temperature {temp}°C, "
        f"motor current {curr} A, lube pressure {pres} bar, RPM {rpm}. "
        f"Anomaly detected on: {sensor_text}. "
        f"What is the likely cause of this fault? "
        f"What does the manual recommend for {alert_type.replace('_', ' ').lower()} condition? "
        f"What immediate corrective actions should be taken?"
    )


# ── routes ────────────────────────────────────────────────────────────────────

@router.get("/logs/{machine_tag}")
async def get_machine_logs(machine_tag: str, count: int = 10):
    """Return the latest dynamic log entries for a machine."""
    if machine_tag not in MACHINE_CONFIG:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown machine tag: {machine_tag}. "
                   f"Valid tags: {list(MACHINE_CONFIG.keys())}"
        )
    logs = get_latest_logs(machine_tag, count=count)
    return {
        "machine_tag":    machine_tag,
        "display_name":   MACHINE_CONFIG[machine_tag]["display_name"],
        "mapped_document":MACHINE_DOC_MAP.get(machine_tag, ""),
        "log_count":      len(logs),
        "logs":           logs,
    }


@router.get("/summary/{machine_tag}")
async def get_summary(machine_tag: str):
    """Return latest reading + threshold context for the machine."""
    if machine_tag not in MACHINE_CONFIG:
        raise HTTPException(status_code=404, detail=f"Unknown machine tag: {machine_tag}")
    return get_machine_summary(machine_tag)


@router.post("/inject-anomaly/{machine_tag}")
async def inject_anomaly(machine_tag: str):
    """Demo: spike a random sensor on this machine into the critical range using PDF-grounded fault scenario."""
    if machine_tag not in MACHINE_CONFIG:
        raise HTTPException(status_code=404, detail=f"Unknown machine tag: {machine_tag}")
    
    from sensors.machine_logs import inject_demo_anomaly
    scenario = inject_demo_anomaly(machine_tag)
    
    if not scenario:
        # Fallback to old method
        entry = generate_log_entry(machine_tag, inject_anomaly=True)
        return {"injected": True, "entry": entry}
    
    return {
        "injected": True,
        "fault_code": scenario["fault_code"],
        "fault_name": scenario["fault_name"],
        "entry": scenario["log_entry"]
    }


@router.post("/reset/{machine_tag}")
async def reset_machine(machine_tag: str):
    """Reset machine sensors to normal operating baseline."""
    if machine_tag not in MACHINE_CONFIG:
        raise HTTPException(status_code=404, detail=f"Unknown machine tag: {machine_tag}")
    
    from sensors.machine_logs import reset_to_normal
    result = reset_to_normal(machine_tag)
    
    return result


class AnalyzeRequest(BaseModel):
    include_logs: Optional[int] = 10         # how many log entries to include
    inject_anomaly: Optional[bool] = False   # spike sensors first (demo)


@router.post("/analyze/{machine_tag}")
async def analyze_machine(machine_tag: str, request: AnalyzeRequest = None):
    """
    Full RAG analysis for a machine:
    1. Get/generate dynamic logs
    2. Build a query from the anomaly state
    3. Retrieve relevant chunks from the mapped equipment PDF
    4. Generate a document-grounded LLM answer (no predefined text)
    5. Return answer + citations + logs used

    The answer is NEVER static — it is generated fresh from:
      a) current machine sensor logs
      b) retrieved PDF chunks via the existing RAG pipeline
    """
    if machine_tag not in MACHINE_CONFIG:
        raise HTTPException(status_code=404, detail=f"Unknown machine tag: {machine_tag}")

    if request is None:
        request = AnalyzeRequest()

    log_count    = request.include_logs or 10
    inject_anom  = request.inject_anomaly or False

    logger.info(f"[MachineAnalysis] Starting analysis for {machine_tag}")

    # Step 1: Generate latest entry (optionally with injected anomaly)
    if inject_anom:
        generate_log_entry(machine_tag, inject_anomaly=True)

    logs = get_latest_logs(machine_tag, count=log_count)
    logger.info(f"[MachineAnalysis] Got {len(logs)} log entries")

    # Step 2: Build retrieval query from log anomaly state
    query = _build_analysis_query(machine_tag, logs)
    logger.info(f"[MachineAnalysis] Query: {query[:120]}...")

    # Step 3: Retrieve chunks from the mapped equipment PDF
    # CRITICAL: Use the correct equipment_tag that matches Qdrant's stored values
    equipment_tag = MACHINE_TAG_TO_EQUIPMENT_TAG.get(machine_tag, machine_tag)
    logger.info(f"[MachineAnalysis] Using equipment_tag for Qdrant filter: '{equipment_tag}'")
    try:
        chunks, retrieval_metadata = retrieve(
            query=query,
            equipment_tag=equipment_tag,
            use_query_rewriting=True,
            use_parent_retrieval=True,
        )
        logger.info(
            f"[MachineAnalysis] Retrieved {len(chunks)} chunks "
            f"(confidence={retrieval_metadata.get('confidence_level')} "
            f"{retrieval_metadata.get('confidence_score', 0):.2f})"
        )
    except Exception as e:
        logger.error(f"[MachineAnalysis] Retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Document retrieval failed: {str(e)}")

    if not chunks:
        logger.warning(f"[MachineAnalysis] No chunks retrieved for {machine_tag}")
        # Fall back to a no-context answer
        chunks = []

    # Step 4: Prepend machine logs + historical context to the user message
    log_block = format_logs_for_llm(machine_tag, logs)
    historical_block = _get_historical_context(machine_tag)
    full_query = (
        f"{log_block}\n\n"
        f"{historical_block}"
        f"---\nManual context will be provided below."
    )

    # Step 5: Generate answer through existing answerer pipeline (no static text)
    try:
        answer_response, answer_metadata = generate_answer(
            query=full_query,
            chunks=chunks,
            confidence_score=retrieval_metadata.get("confidence_score"),
            confidence_level=retrieval_metadata.get("confidence_level"),
            confidence_details=retrieval_metadata.get("confidence_details"),
        )
        logger.info(f"[MachineAnalysis] Answer generated ({len(answer_response.answer)} chars)")
    except Exception as e:
        logger.error(f"[MachineAnalysis] Answer generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Answer generation failed: {str(e)}")

    # Step 6: Return full result
    latest_log = logs[-1] if logs else {}
    
    # Step 7: Create logbook entry + incident + report for anomalies
    logbook_entry_id = None
    if latest_log.get("severity") in ["CRITICAL", "WARNING"]:
        try:
            import re
            answer_text = answer_response.answer or ""
            immediate_actions = re.findall(r'^\d+\.\s*(.+)$', answer_text, re.MULTILINE)[:5] or [
                "Review machine logs and manual guidance",
                "Verify sensor readings are accurate",
                f"Consult {MACHINE_DOC_MAP.get(machine_tag, 'equipment manual')}"
            ]

            incident_id = f"MACHINE-{machine_tag}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # Create incident row so report_generator can find it
            with get_connection() as conn:
                import json as _json
                conn.execute("""
                    INSERT OR IGNORE INTO incidents
                    (id, equipment_id, equipment_name, triggered_by, sensor_readings, timestamp, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    incident_id,
                    machine_tag,
                    MACHINE_CONFIG[machine_tag]["display_name"],
                    "live_monitor",
                    _json.dumps({
                        "vibration_mm_s":    latest_log.get("vibration_mm_s"),
                        "bearing_temp_c":    latest_log.get("bearing_temp_c"),
                        "motor_current_a":   latest_log.get("motor_current_a"),
                        "lube_pressure_bar": latest_log.get("lube_pressure_bar"),
                        "rpm":               latest_log.get("rpm"),
                    }),
                    datetime.now().isoformat(),
                    "open"
                ))

            logbook_entry = LogbookEntryCreate(
                incident_id=incident_id,
                equipment_id=machine_tag,
                equipment_name=MACHINE_CONFIG[machine_tag]["display_name"],
                fault_description=latest_log.get("event_summary", "Anomaly detected"),
                root_cause=f"{latest_log.get('alert_type', 'UNKNOWN')} condition detected on {', '.join(latest_log.get('anomaly_sensors', []))}",
                risk_level=latest_log.get("severity", "UNKNOWN"),
                urgency_hours=24.0 if latest_log.get("severity") == "CRITICAL" else 72.0,
                immediate_actions=immediate_actions,
                repair_steps=[],
                long_term_recommendations=[],
                parts_required=[],
                parts_available=False,
                rul_hours=None,
                confidence_score=retrieval_metadata.get("confidence_score", 0.0),
                evidence_sources=[
                    f"Machine logs: {machine_tag}",
                    f"Manual: {MACHINE_DOC_MAP.get(machine_tag, 'N/A')}",
                ] + [f"[{c.ref}] {c.section_heading}" for c in answer_response.citations[:3]],
                report_id=None,
                fault_code=latest_log.get("fault_code", "—")  # PDF-grounded fault code
            )

            logbook_entry_id = create_entry(logbook_entry)
            logger.info(f"[MachineAnalysis] Created logbook entry: {logbook_entry_id}")

            # Auto-generate report so it appears in Analysis Reports panel
            import json as _json2
            report = {
                "report_id": incident_id,
                "report_type": "MACHINE_ANALYSIS",
                "generated_at": datetime.now().isoformat(),
                "incident_summary": {
                    "incident_id": incident_id,
                    "equipment_id": machine_tag,
                    "equipment_name": MACHINE_CONFIG[machine_tag]["display_name"],
                    "timestamp": datetime.now().isoformat(),
                    "triggered_by": "live_monitor",
                    "status": "open",
                    "alert_id": None,
                    "session_id": None,
                },
                "sensor_data": {
                    "vibration_mm_s":    latest_log.get("vibration_mm_s"),
                    "bearing_temp_c":    latest_log.get("bearing_temp_c"),
                    "motor_current_a":   latest_log.get("motor_current_a"),
                    "lube_pressure_bar": latest_log.get("lube_pressure_bar"),
                    "rpm":               latest_log.get("rpm"),
                    "fault_code":        latest_log.get("fault_code"),
                    "alert_type":        latest_log.get("alert_type"),
                },
                "diagnosis": {
                    "fault_description": latest_log.get("event_summary", ""),
                    "root_cause": f"{latest_log.get('alert_type', 'UNKNOWN')} condition detected",
                    "confidence_score": retrieval_metadata.get("confidence_score", 0.0),
                    "evidence_sources": [c.section_heading for c in answer_response.citations[:3]],
                    "llm_answer": answer_response.answer,
                    "citations": [{"ref": c.ref, "page": c.page_number, "section": c.section_heading} for c in answer_response.citations],
                },
                "risk_assessment": {
                    "risk_level": latest_log.get("severity", "UNKNOWN"),
                    "urgency_hours": 24.0 if latest_log.get("severity") == "CRITICAL" else 72.0,
                    "rul_hours": None,
                    "parts_required": [],
                    "parts_available": False,
                },
                "maintenance_plan": {
                    "immediate_actions": immediate_actions,
                    "repair_steps": [],
                    "long_term_recommendations": [],
                },
                "status": {
                    "created_at": datetime.now().isoformat(),
                    "resolved_at": None,
                    "technician": None,
                }
            }
            _store_report(incident_id, logbook_entry_id, report)
            logger.info(f"[MachineAnalysis] Created report: {incident_id}")

        except Exception as e:
            logger.error(f"[MachineAnalysis] Failed to create logbook/report entry: {e}")
    
    return {
        "machine_tag":      machine_tag,
        "display_name":     MACHINE_CONFIG[machine_tag]["display_name"],
        "mapped_document":  MACHINE_DOC_MAP.get(machine_tag, ""),
        "current_severity": latest_log.get("severity", "UNKNOWN"),
        "fault_code":       latest_log.get("fault_code", "—"),
        "event_summary":    latest_log.get("event_summary", ""),
        "latest_readings": {
            "vibration_mm_s":    latest_log.get("vibration_mm_s"),
            "bearing_temp_c":    latest_log.get("bearing_temp_c"),
            "motor_current_a":   latest_log.get("motor_current_a"),
            "lube_pressure_bar": latest_log.get("lube_pressure_bar"),
            "rpm":               latest_log.get("rpm"),
        },
        "analysis": {
            "answer":     answer_response.answer,
            "citations":  [
                {
                    "ref":     c.ref,
                    "page":    c.page_number,
                    "section": c.section_heading,
                    "snippet": c.snippet,
                }
                for c in answer_response.citations
            ],
            "confidence_level": answer_metadata.get("confidence_level", ""),
            "grounded_in_doc": len(answer_response.citations) > 0,
        },
        "logs_used":       logs,
        "retrieval_query": query,
        "logbook_entry_id": logbook_entry_id,  # For frontend to show logbook link
    }


@router.get("/machines")
async def list_machines():
    """List all configured machines with their document mappings."""
    return [
        {
            "machine_tag":    tag,
            "display_name":   cfg["display_name"],
            "mapped_document":MACHINE_DOC_MAP.get(tag, ""),
            "rpm_nominal":    cfg["rpm_nominal"],
        }
        for tag, cfg in MACHINE_CONFIG.items()
    ]
