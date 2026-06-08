"""
Remaining Useful Life estimator.

Uses linear regression on recent sensor trend to project when a reading
will cross the failure threshold.
"""

import numpy as np
from typing import Optional

# Failure thresholds per sensor (beyond these = imminent failure)
FAILURE_THRESHOLDS = {
    "RM1":    {"vibration": 9.0,  "temperature": 100.0, "current": 65.0,  "pressure": 2.0},
    "RM3":    {"vibration": 9.5,  "temperature": 105.0, "current": 68.0,  "pressure": 1.8},
    "BF1":    {"vibration": 7.0,  "temperature": 95.0,  "current": 80.0,  "pressure": 3.5},
    "COMP_A": {"vibration": 8.5,  "temperature": 115.0, "current": 52.0,  "pressure": 5.0},
}


def estimate_rul(
    equipment_id: str,
    sensor_key: str,
    recent_values: list[float],
    interval_seconds: int = 5
) -> Optional[float]:
    """
    Estimate remaining useful life in HOURS.

    Args:
        equipment_id: e.g. "RM3"
        sensor_key: e.g. "vibration"
        recent_values: last N readings for this sensor (chronological order)
        interval_seconds: seconds between readings

    Returns:
        Estimated hours until failure threshold is reached.
        None if trend is stable (not degrading).
    """
    if len(recent_values) < 10:
        return None  # Not enough data to estimate trend

    thresholds = FAILURE_THRESHOLDS.get(equipment_id.upper())
    if not thresholds:
        return None

    threshold = thresholds.get(sensor_key)
    if not threshold:
        return None

    # Fit linear regression on recent values
    x = np.arange(len(recent_values))
    y = np.array(recent_values)
    slope, intercept = np.polyfit(x, y, 1)

    # If sensor is not increasing toward threshold, no RUL concern
    current_value = recent_values[-1]

    # For pressure: failure = dropping below threshold (negative slope is bad)
    if sensor_key == "pressure":
        if slope >= 0:
            return None  # Pressure stable or rising — OK
        # Time (in readings) until pressure drops below threshold
        if abs(slope) < 1e-6:
            return None
        readings_to_failure = (current_value - threshold) / abs(slope)
    else:
        if slope <= 0:
            return None  # Stable or decreasing — OK
        if slope < 1e-6:
            return None
        # Time (in readings) until value reaches failure threshold
        readings_to_failure = (threshold - current_value) / slope

    if readings_to_failure <= 0:
        return 0.0  # Already past threshold

    # Convert readings to hours
    hours_to_failure = (readings_to_failure * interval_seconds) / 3600
    return round(hours_to_failure, 1)
