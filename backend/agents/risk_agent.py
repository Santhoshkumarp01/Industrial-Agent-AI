"""
Risk Agent — scores urgency and checks spare parts availability.

Evaluates:
- Anomaly severity
- Equipment criticality
- RUL (Remaining Useful Life)
- Spare parts availability from CSV

Returns risk level (LOW/MEDIUM/HIGH/CRITICAL) and urgency window.
"""

import logging
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

# Load spare parts inventory
SPARE_PARTS_PATH = Path("data/knowledge/spare_parts.csv")
spare_parts_df = None

try:
    if SPARE_PARTS_PATH.exists():
        spare_parts_df = pd.read_csv(SPARE_PARTS_PATH)
        logger.info(f"✓ Loaded {len(spare_parts_df)} spare parts from inventory")
except Exception as e:
    logger.warning(f"Could not load spare parts CSV: {e}")


def analyze_risk(
    equipment_id: str,
    equipment_name: str,
    root_cause: str,
    anomaly_score: float,
    rul_hours: float = None,
    sensor_data: dict = None
) -> dict:
    """
    Scores risk level and urgency.

    Args:
        equipment_id: Equipment identifier
        equipment_name: Human-readable name
        root_cause: Diagnosis from root cause agent
        anomaly_score: 0.0-1.0 anomaly score from ML
        rul_hours: Estimated hours to failure
        sensor_data: Current sensor readings

    Returns:
        {
            "risk_level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
            "urgency_hours": float,  # hours until action required
            "parts_required": list[str],
            "parts_available": bool,
            "parts_stock": dict  # {part_name: quantity}
        }
    """
    logger.info(f"[Risk Agent] Assessing risk for {equipment_id}...")

    # Criticality mapping (production impact)
    criticality = {
        "RM1": "HIGH",      # Rolling mill - high production impact
        "RM3": "HIGH",
        "BF1": "CRITICAL",  # Blast furnace blower - critical safety equipment
        "COMP_A": "MEDIUM"  # Compressor - moderate impact
    }.get(equipment_id, "MEDIUM")

    # Determine risk level based on multiple factors
    risk_score = 0.0

    # Factor 1: Anomaly severity
    if anomaly_score >= 0.8:
        risk_score += 40
    elif anomaly_score >= 0.6:
        risk_score += 25
    elif anomaly_score >= 0.4:
        risk_score += 15
    else:
        risk_score += 5

    # Factor 2: RUL urgency
    if rul_hours is not None:
        if rul_hours < 24:
            risk_score += 40
        elif rul_hours < 72:
            risk_score += 25
        elif rul_hours < 168:  # 1 week
            risk_score += 15
        else:
            risk_score += 5

    # Factor 3: Equipment criticality
    if criticality == "CRITICAL":
        risk_score += 20
    elif criticality == "HIGH":
        risk_score += 15
    elif criticality == "MEDIUM":
        risk_score += 10

    # Map score to risk level
    if risk_score >= 80:
        risk_level = "CRITICAL"
        urgency_hours = 4.0
    elif risk_score >= 60:
        risk_level = "HIGH"
        urgency_hours = 24.0
    elif risk_score >= 40:
        risk_level = "MEDIUM"
        urgency_hours = 72.0
    else:
        risk_level = "LOW"
        urgency_hours = 168.0

    # Override urgency with RUL if RUL is shorter
    if rul_hours is not None and rul_hours < urgency_hours:
        urgency_hours = rul_hours * 0.8  # Act before predicted failure

    # Check spare parts availability
    parts_required = _identify_required_parts(root_cause)
    parts_available, parts_stock = _check_parts_availability(parts_required)

    logger.info(
        f"[Risk Agent] Risk: {risk_level}, "
        f"Urgency: {urgency_hours:.1f}h, "
        f"Parts available: {parts_available}"
    )

    return {
        "risk_level": risk_level,
        "urgency_hours": urgency_hours,
        "parts_required": parts_required,
        "parts_available": parts_available,
        "parts_stock": parts_stock
    }


def _identify_required_parts(root_cause: str) -> list[str]:
    """Map root cause to likely required spare parts."""
    parts = []

    root_cause_lower = root_cause.lower()

    if "bearing" in root_cause_lower:
        parts.extend(["Bearing", "Bearing Assembly", "Grease"])
    if "motor" in root_cause_lower or "winding" in root_cause_lower:
        parts.extend(["Motor", "Stator Winding", "Rotor"])
    if "lubrication" in root_cause_lower or "oil" in root_cause_lower:
        parts.extend(["Lubrication Oil", "Grease", "Oil Filter"])
    if "seal" in root_cause_lower or "leak" in root_cause_lower:
        parts.extend(["Seal", "Gasket"])
    if "valve" in root_cause_lower:
        parts.extend(["Valve", "Valve Seat"])
    if "pressure" in root_cause_lower:
        parts.extend(["Pressure Sensor", "Valve"])
    if "vibration" in root_cause_lower or "alignment" in root_cause_lower:
        parts.extend(["Coupling", "Bearing"])

    # Default parts for unknown issues
    if not parts:
        parts = ["General Maintenance Kit"]

    return list(set(parts))  # Remove duplicates


def _check_parts_availability(parts_required: list[str]) -> tuple[bool, dict]:
    """Check spare parts inventory."""
    if spare_parts_df is None:
        return False, {}

    parts_stock = {}
    all_available = True

    for part in parts_required:
        # Fuzzy match part name in inventory (check both description and part_number columns)
        matches = spare_parts_df[
            spare_parts_df["description"].str.contains(part, case=False, na=False) |
            spare_parts_df["part_number"].str.contains(part, case=False, na=False)
        ]

        if not matches.empty:
            # Sum quantities across all matches
            total_qty = matches["quantity_in_stock"].sum()
            parts_stock[part] = int(total_qty)
            if total_qty == 0:
                all_available = False
        else:
            parts_stock[part] = 0
            all_available = False

    return all_available, parts_stock
