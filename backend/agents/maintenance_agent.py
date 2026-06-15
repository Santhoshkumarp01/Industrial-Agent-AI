"""
Maintenance Agent — generates step-by-step work orders.

Searches SOP documents and generates:
- Immediate safety actions
- Detailed repair steps
- Long-term preventive measures

Uses RAG to pull relevant SOP procedures.
Powered by fine-tuned Phi-3.5 Mini maintenance model.
"""

import logging
import re
from retrieval.retriever import retrieve
from pathlib import Path
from llm.local_llm import generate as llm_generate

logger = logging.getLogger(__name__)


def generate_maintenance_plan(
    equipment_id: str,
    equipment_name: str,
    root_cause: str,
    risk_level: str,
    parts_required: list[str]
) -> dict:
    """
    Generates structured maintenance plan with step-by-step instructions.

    Args:
        equipment_id: Equipment identifier
        equipment_name: Human-readable name
        root_cause: Diagnosed failure mode
        risk_level: Risk assessment result
        parts_required: List of spare parts needed

    Returns:
        {
            "immediate_actions": list[str],  # Safety first
            "repair_steps": list[str],       # Detailed procedure
            "long_term_recommendations": list[str]  # Preventive measures
        }
    """
    logger.info(f"[Maintenance Agent] Generating plan for {equipment_id}...")

    # Build search query for SOP documents
    query = (
        f"{equipment_name} {root_cause} maintenance procedure. "
        f"Step-by-step repair instructions."
    )

    # Search RAG for relevant SOPs
    try:
        sop_results, _ = retrieve(query, equipment_tag=equipment_id, top_k=6)
        
        # Handle empty results gracefully
        if not sop_results or len(sop_results) == 0:
            logger.warning(f"SOP retrieval returned empty results for equipment {equipment_id}")
            sop_text = ""
        else:
            sop_text = "\n\n".join([chunk.text for chunk in sop_results])
    except Exception as e:
        logger.error(f"SOP retrieval failed: {e}")
        sop_text = ""

    # Generate immediate actions based on risk level
    immediate_actions = _generate_immediate_actions(risk_level, root_cause)

    # Generate repair steps using fine-tuned model + retrieved SOPs
    repair_steps = _generate_repair_steps_with_ai(root_cause, parts_required, sop_text, equipment_name)

    # Generate long-term recommendations
    long_term_recommendations = _generate_long_term_actions(root_cause, equipment_id)

    logger.info(
        f"[Maintenance Agent] Plan generated: "
        f"{len(immediate_actions)} immediate actions, "
        f"{len(repair_steps)} repair steps"
    )

    return {
        "immediate_actions": immediate_actions,
        "repair_steps": repair_steps,
        "long_term_recommendations": long_term_recommendations
    }


def _generate_immediate_actions(risk_level: str, root_cause: str) -> list[str]:
    """Generate safety-first immediate actions."""
    actions = []

    # Always start with safety
    actions.append("Notify maintenance supervisor and log incident")

    if risk_level in ["CRITICAL", "HIGH"]:
        actions.append("STOP equipment operation immediately")
        actions.append("Lock out / Tag out (LOTO) procedure - ensure zero energy state")
        actions.append("Evacuate non-essential personnel from area")

    if "bearing" in root_cause.lower() or "vibration" in root_cause.lower():
        actions.append("Monitor for unusual noise or further vibration increase")
        actions.append("Prepare bearing replacement kit")

    if "temperature" in root_cause.lower() or "thermal" in root_cause.lower():
        actions.append("Allow equipment to cool down before inspection")
        actions.append("Check cooling system and lubrication immediately")

    if "electrical" in root_cause.lower() or "current" in root_cause.lower():
        actions.append("Disconnect electrical power and verify de-energization")
        actions.append("Test for residual voltage before proceeding")

    if "pressure" in root_cause.lower() or "leak" in root_cause.lower():
        actions.append("Depressurize system and isolate fluid lines")
        actions.append("Check for visible leaks or damage")

    if risk_level in ["MEDIUM", "LOW"]:
        actions.append("Schedule maintenance window within urgency timeframe")
        actions.append("Arrange spare parts and tooling")

    return actions


def _generate_repair_steps_with_ai(root_cause: str, parts_required: list[str], sop_text: str, equipment_name: str) -> list[str]:
    """Generate detailed repair procedure using fine-tuned model + SOPs."""
    
    # If we have SOP documentation, use fine-tuned model to extract steps
    if sop_text and len(sop_text) > 100:
        try:
            SYSTEM_PROMPT = "You are an expert industrial maintenance engineer creating repair procedures."
            
            user_prompt = f"""Equipment: {equipment_name}
Root Cause: {root_cause}
Parts Required: {', '.join(parts_required) if parts_required else 'None specified'}

Standard Operating Procedures (SOPs):
{sop_text}

Create a detailed step-by-step repair procedure. Each step should be:
- Clear and actionable
- Include safety considerations
- Reference proper tools/equipment
- Specify torque values or measurements where applicable

Provide 8-12 numbered steps. Do not include JSON formatting, just numbered steps."""

            raw = llm_generate(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
                max_tokens=1500
            )
            
            # Parse numbered steps from response
            steps = []
            for line in raw.split('\n'):
                line = line.strip()
                # Match lines starting with number and dot/parenthesis
                if line and (line[0].isdigit() or line.startswith('-')):
                    # Remove leading number/bullet
                    step = line.lstrip('0123456789.-) ').strip()
                    if step:
                        steps.append(step)
            
            if steps:
                # Always end with verification
                steps.extend([
                    "Perform functional test and verify normal operation",
                    "Document all work performed in maintenance logbook",
                    "Update equipment maintenance history"
                ])
                logger.info(f"[Maintenance Agent] Generated {len(steps)} steps from SOPs using fine-tuned model")
                return steps
                
        except Exception as e:
            logger.error(f"Fine-tuned model repair step generation failed: {e}")
    
    # Fallback to rule-based procedure
    return _generate_repair_steps_fallback(root_cause, parts_required)


def _generate_repair_steps_fallback(root_cause: str, parts_required: list[str]) -> list[str]:
    """Fallback rule-based repair procedure."""
    steps = []

    root_cause_lower = root_cause.lower()

    # Bearing replacement procedure
    if "bearing" in root_cause_lower:
        steps.extend([
            "Remove protective guards and access panels",
            "Disconnect coupling from motor shaft",
            "Remove bearing housing bolts (use proper torque wrench)",
            "Extract old bearing using bearing puller (avoid hammering)",
            "Clean bearing seat and inspect for wear or damage",
            "Install new bearing - ensure proper orientation and seating",
            "Apply recommended grease (check equipment manual for type and quantity)",
            "Reinstall bearing housing and torque bolts to specification",
            "Reconnect coupling and verify alignment (use dial indicator)",
            "Rotate shaft manually to check for smooth operation"
        ])

    # Lubrication issues
    elif "lubrication" in root_cause_lower or "oil" in root_cause_lower:
        steps.extend([
            "Drain old lubricant completely and inspect for contamination",
            "Check lubrication lines for blockages",
            "Replace oil filter if equipped",
            "Refill with manufacturer-specified lubricant",
            "Verify lubrication level using sight glass or dipstick",
            "Run equipment and check for proper oil circulation",
            "Monitor temperature to confirm cooling improvement"
        ])

    # Motor/electrical issues
    elif "motor" in root_cause_lower or "electrical" in root_cause_lower or "winding" in root_cause_lower:
        steps.extend([
            "Disconnect all electrical connections and tag",
            "Test motor windings for continuity and insulation resistance (megger test)",
            "Inspect for signs of overheating, discoloration, or burning",
            "If motor failed, remove and send to motor shop for rewind or replacement",
            "If motor OK, inspect and clean electrical connections",
            "Check starter contactors and overload relays",
            "Verify proper voltage and phase balance at motor terminals",
            "Reconnect motor and test run unloaded"
        ])

    # Pressure/valve issues
    elif "pressure" in root_cause_lower or "valve" in root_cause_lower:
        steps.extend([
            "Isolate and depressurize system completely",
            "Inspect valve seat and sealing surfaces",
            "Replace worn valve components or entire valve assembly",
            "Check pressure relief valves for proper operation",
            "Inspect all pressure gauges for accuracy",
            "Repressurize system slowly and check for leaks",
            "Test valve operation under normal pressure"
        ])

    # Generic steps if no specific match
    if not steps:
        steps.extend([
            "Perform detailed visual inspection of equipment",
            f"Replace identified worn components: {', '.join(parts_required)}",
            "Clean and inspect all related systems",
            "Verify all fasteners are properly torqued",
            "Test equipment operation under load",
            "Monitor closely during initial restart"
        ])

    # Always end with verification
    steps.extend([
        "Perform functional test and verify normal operation",
        "Document all work performed in maintenance logbook",
        "Update equipment maintenance history"
    ])

    return steps


def _generate_repair_steps(root_cause: str, parts_required: list[str], sop_text: str) -> list[str]:
    """Deprecated - kept for backward compatibility."""
    return _generate_repair_steps_fallback(root_cause, parts_required)


def _generate_long_term_actions(root_cause: str, equipment_id: str) -> list[str]:
    """Generate preventive maintenance recommendations."""
    recommendations = []

    root_cause_lower = root_cause.lower()

    if "bearing" in root_cause_lower:
        recommendations.extend([
            "Implement vibration monitoring program for early detection",
            "Schedule bearing inspection every 6 months",
            "Review lubrication schedule - may need more frequent greasing"
        ])

    if "temperature" in root_cause_lower or "lubrication" in root_cause_lower:
        recommendations.extend([
            "Install continuous temperature monitoring sensor",
            "Increase lubrication check frequency to weekly",
            "Consider upgrading to synthetic lubricant for better thermal stability"
        ])

    if "motor" in root_cause_lower or "electrical" in root_cause_lower:
        recommendations.extend([
            "Implement quarterly motor current analysis",
            "Check electrical connections during monthly PM",
            "Consider installing motor protection relay with thermal monitoring"
        ])

    if "pressure" in root_cause_lower:
        recommendations.extend([
            "Install continuous pressure monitoring",
            "Inspect seals and gaskets during quarterly maintenance",
            "Calibrate pressure sensors annually"
        ])

    # Always include these
    recommendations.extend([
        "Train operators on early warning signs of equipment degradation",
        "Review and update equipment maintenance schedule based on this failure",
        "Consider root cause analysis (5 Whys / Fishbone) to prevent recurrence"
    ])

    return recommendations
