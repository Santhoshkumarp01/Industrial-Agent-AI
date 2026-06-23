"""
Root Cause Agent — identifies likely failure modes using RAG + incident history.

Searches:
- Equipment manuals in Qdrant
- Historical incident database
- SOP documents

Returns structured diagnosis with confidence score and evidence.
Powered by fine-tuned Phi-3.5 Mini maintenance model.
"""

import logging
import re
import json
from retrieval.retriever import retrieve
from database.db import get_connection
from llm.local_llm import generate as llm_generate

logger = logging.getLogger(__name__)


def analyze_root_cause(
    equipment_id: str,
    equipment_name: str,
    sensor_data: dict,
    alert_description: str,
    rul_hours: float = None
) -> dict:
    """
    Searches RAG and incident database to identify likely root cause.

    Args:
        equipment_id: "RM1", "RM3", etc.
        equipment_name: Human-readable name
        sensor_data: Dict of current sensor readings
        alert_description: String describing the alert
        rul_hours: Estimated hours to failure

    Returns:
        {
            "root_cause": str,
            "fault_description": str,
            "confidence": float (0.0-1.0),
            "evidence": list[str],  # Citation refs
            "similar_incidents": list[dict]
        }
    """
    logger.info(f"[Root Cause Agent] Analyzing {equipment_id}...")

    # Build search query
    query = (
        f"{equipment_name} {alert_description}. "
        f"Sensor readings: vibration={sensor_data.get('vibration')}, "
        f"temperature={sensor_data.get('temperature')}, "
        f"current={sensor_data.get('current')}, "
        f"pressure={sensor_data.get('pressure')}. "
        f"What could be the root cause of this anomaly?"
    )

    # Search RAG system
    try:
        # Map machine_tag to Qdrant equipment_tag
        from sensors.machine_logs import MACHINE_TAG_TO_EQUIPMENT_TAG
        qdrant_equipment_tag = MACHINE_TAG_TO_EQUIPMENT_TAG.get(equipment_id, equipment_id)
        
        rag_results, _ = retrieve(query, equipment_tag=qdrant_equipment_tag, top_k=8)
        
        # Handle empty results gracefully
        if not rag_results or len(rag_results) == 0:
            logger.warning(f"RAG retrieval returned empty results for equipment {equipment_id}")
            evidence_citations = []
            evidence_text = "No knowledge base results available."
        else:
            # Return full citation objects, not just refs
            evidence_citations = [
                {
                    "ref": chunk.citation_ref,
                    "doc_id": chunk.doc_id,
                    "doc_name": chunk.doc_name,
                    "page": chunk.page_number,
                    "section": chunk.section_heading,
                    "snippet": chunk.text[:150] if chunk.text else ""
                }
                for chunk in rag_results[:8]  # Top 8 citations
            ]
            evidence_text = "\n\n".join([chunk.text for chunk in rag_results])
    except Exception as e:
        logger.error(f"RAG retrieval failed: {e}")
        evidence_citations = []
        evidence_text = "No knowledge base results available."

    # Search historical incidents
    similar_incidents = _search_incident_history(equipment_id, sensor_data)

    # Use fine-tuned model to synthesize diagnosis from retrieved evidence
    SYSTEM_PROMPT = "You are an expert industrial maintenance engineer analyzing equipment failure."
    
    # Build user prompt
    user_prompt = f"""Equipment: {equipment_name} ({equipment_id})
Alert: {alert_description}

Current Sensor Readings:
- Vibration: {sensor_data.get('vibration')} mm/s
- Temperature: {sensor_data.get('temperature')} °C
- Current: {sensor_data.get('current')} A
- Pressure: {sensor_data.get('pressure')} bar
{f"- Estimated remaining useful life: {rul_hours} hours" if rul_hours else ""}

Knowledge Base Evidence:
{evidence_text if evidence_text != "No knowledge base results available." else "No relevant documentation found in knowledge base."}

Historical Incidents:
{json.dumps(similar_incidents, indent=2) if similar_incidents else "No similar past incidents found."}

Based on the sensor readings and available evidence, provide:
1. The most probable root cause
2. A detailed fault description
3. Your confidence level (0.0 to 1.0)

Respond in plain text, not JSON. Be specific and cite the evidence if available."""

    try:
        raw = llm_generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=1000
        )
        
        diagnosis_text = raw
        
        # Parse model response (simple extraction)
        lines = diagnosis_text.split('\n')
        root_cause = "Analysis provided by AI"
        fault_description = diagnosis_text[:500]  # First 500 chars
        confidence = 0.75  # Default moderate confidence
        
        # Try to extract root cause from first line or paragraph
        for line in lines:
            if "root cause" in line.lower() or "cause:" in line.lower():
                root_cause = line.split(':', 1)[-1].strip() if ':' in line else line.strip()
                break
        
        # Check if we have evidence - boost confidence
        if evidence_citations:
            confidence = min(confidence + 0.15, 0.95)
        
        # Check if we have similar incidents - boost confidence slightly
        if similar_incidents:
            confidence = min(confidence + 0.05, 0.95)
            
    except Exception as e:
        logger.error(f"Fine-tuned model inference failed: {e}")
        # Fallback to rule-based diagnosis
        root_cause = "Unknown"
        confidence = 0.5
        fault_description = alert_description

        # Bearing failure patterns
        if sensor_data.get("vibration", 0) > 8.0:
            root_cause = "Bearing wear or misalignment"
            confidence = 0.85
            fault_description = f"Excessive vibration detected ({sensor_data.get('vibration')} mm/s). Likely bearing degradation."

        # Overheating patterns
        if sensor_data.get("temperature", 0) > 90:
            root_cause = "Thermal overload or insufficient lubrication"
            confidence = 0.80
            fault_description = f"High temperature ({sensor_data.get('temperature')}°C). Check lubrication and cooling system."

        # Current spikes
        if sensor_data.get("current", 0) > 60:
            root_cause = "Electrical overload or motor winding fault"
            confidence = 0.75
            fault_description = f"Current spike detected ({sensor_data.get('current')} A). Motor may be overloaded."

        # Pressure issues
        if sensor_data.get("pressure", 0) > 4.0 or sensor_data.get("pressure", 0) < 1.0:
            root_cause = "Pressure system leak or valve malfunction"
            confidence = 0.70
            fault_description = f"Abnormal pressure ({sensor_data.get('pressure')} bar). Check for leaks or valve issues."

        # Boost confidence if we have RAG evidence
        if evidence_citations:
            confidence = min(confidence + 0.10, 0.95)

    logger.info(f"[Root Cause Agent] Diagnosis: {root_cause} (confidence: {confidence})")

    return {
        "root_cause": root_cause,
        "fault_description": fault_description,
        "confidence": confidence,
        "evidence": evidence_citations,
        "similar_incidents": similar_incidents
    }


def _search_incident_history(equipment_id: str, sensor_data: dict) -> list[dict]:
    """Search incident database for similar past failures."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, equipment_id, equipment_name, sensor_readings, 
                   timestamp, status
            FROM incidents
            WHERE equipment_id = ?
            ORDER BY timestamp DESC LIMIT 5
        """, (equipment_id,)).fetchall()

    incidents = []
    for row in rows:
        incident = dict(row)
        # Parse sensor_readings JSON
        if incident.get("sensor_readings"):
            try:
                incident["sensor_readings"] = json.loads(incident["sensor_readings"])
            except:
                incident["sensor_readings"] = {}
        incidents.append(incident)

    return incidents
