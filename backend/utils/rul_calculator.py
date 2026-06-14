"""
Remaining Useful Life (RUL) Calculator

Estimates equipment failure time based on sensor readings and severity.
Uses rule-based heuristics and trend analysis.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def calculate_rul(
    sensor_data: dict,
    severity: str,
    fault_code: str = None,
    equipment_type: str = "motor"
) -> Optional[float]:
    """
    Calculate Remaining Useful Life in hours.
    
    Logic:
    1. CRITICAL severity → Immediate failure risk (12-48h)
    2. WARNING severity → Short-term degradation (48-168h)  
    3. Sensor-specific degradation rates
    4. Fault code patterns
    
    Args:
        sensor_data: Dict with sensor readings
        severity: "NORMAL" | "WARNING" | "CRITICAL"
        fault_code: Optional fault code (FC-TH-01, FC-VB-01, etc.)
        equipment_type: "motor" | "compressor" | "blower"
    
    Returns:
        RUL in hours, or None if no degradation detected
    """
    
    if severity == "NORMAL":
        # No imminent failure
        return None
    
    # Base RUL by severity
    if severity == "CRITICAL":
        base_rul = 24.0  # 1 day
    elif severity == "WARNING":
        base_rul = 120.0  # 5 days
    else:
        base_rul = 336.0  # 14 days
    
    # Adjust by fault type
    if fault_code:
        if "TH" in fault_code:  # Thermal faults
            # High temperature → faster degradation
            base_rul *= 0.7
            logger.info(f"[RUL] Thermal fault detected - reduced RUL by 30%")
        
        elif "VB" in fault_code:  # Vibration faults
            # Mechanical failures can be sudden
            base_rul *= 0.6
            logger.info(f"[RUL] Vibration fault detected - reduced RUL by 40%")
        
        elif "CR" in fault_code or "SY" in fault_code:  # Electrical faults
            # Electrical issues can escalate quickly
            base_rul *= 0.8
            logger.info(f"[RUL] Electrical fault detected - reduced RUL by 20%")
        
        elif "LP" in fault_code:  # Low pressure/lubrication
            # Lubrication failures cause rapid wear
            base_rul *= 0.5
            logger.info(f"[RUL] Lubrication fault detected - reduced RUL by 50%")
    
    # Sensor-specific adjustments
    temp_factor = _analyze_temperature(sensor_data)
    vibration_factor = _analyze_vibration(sensor_data)
    
    # Use the most pessimistic factor
    degradation_factor = min(temp_factor, vibration_factor)
    final_rul = base_rul * degradation_factor
    
    # Floor at minimum 6 hours (time for emergency response)
    final_rul = max(final_rul, 6.0)
    
    logger.info(
        f"[RUL] Calculated RUL: {final_rul:.1f}h "
        f"(severity={severity}, fault={fault_code}, "
        f"temp_factor={temp_factor:.2f}, vib_factor={vibration_factor:.2f})"
    )
    
    return round(final_rul, 1)


def _analyze_temperature(sensor_data: dict) -> float:
    """
    Analyze temperature severity and return degradation factor.
    
    Returns:
        1.0 = normal operation
        0.5 = severe overheating (50% RUL reduction)
    """
    bearing_temp = sensor_data.get("bearing_temp_c") or sensor_data.get("bearing_temp_drive_end_c")
    winding_temp = sensor_data.get("winding_temp_c") or sensor_data.get("stator_winding_temp_c")
    
    if not bearing_temp and not winding_temp:
        return 1.0
    
    # Bearing temperature thresholds (typical motor bearings)
    if bearing_temp:
        if bearing_temp > 120:  # Critical overheating
            return 0.5
        elif bearing_temp > 110:  # High temperature
            return 0.7
        elif bearing_temp > 90:  # Elevated
            return 0.85
    
    # Winding temperature thresholds
    if winding_temp:
        if winding_temp > 155:  # Critical (Class F insulation limit)
            return 0.4
        elif winding_temp > 145:  # High
            return 0.6
        elif winding_temp > 130:  # Elevated
            return 0.8
    
    return 1.0


def _analyze_vibration(sensor_data: dict) -> float:
    """
    Analyze vibration severity and return degradation factor.
    
    Returns:
        1.0 = normal operation
        0.4 = severe vibration (60% RUL reduction)
    """
    vibration = sensor_data.get("vibration_mm_s") or sensor_data.get("vibration_velocity_mm_s")
    
    if not vibration:
        return 1.0
    
    # Vibration thresholds (ISO 10816 for industrial machines)
    if vibration > 11.0:  # Unacceptable - immediate action
        return 0.4
    elif vibration > 7.1:  # Critical zone
        return 0.6
    elif vibration > 4.5:  # Warning zone
        return 0.8
    elif vibration > 2.8:  # Slightly elevated
        return 0.95
    
    return 1.0


def format_rul_message(rul_hours: Optional[float]) -> str:
    """
    Format RUL into human-readable message.
    
    Returns:
        "Estimated failure within 24 hours"
        "Estimated RUL: 5 days"
        None (if no RUL)
    """
    if rul_hours is None:
        return None
    
    if rul_hours < 12:
        return f"⚠️ Estimated failure within {int(rul_hours)} hours - IMMEDIATE ACTION REQUIRED"
    elif rul_hours < 48:
        return f"Estimated RUL: {int(rul_hours)} hours (~{rul_hours/24:.1f} days)"
    elif rul_hours < 168:  # 1 week
        days = rul_hours / 24
        return f"Estimated RUL: {days:.1f} days"
    else:
        weeks = rul_hours / 168
        return f"Estimated RUL: {weeks:.1f} weeks"
