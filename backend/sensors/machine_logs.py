"""
Dynamic machine log generator for the 4 mapped industrial machines.

Each machine has:
- Specific sensor thresholds
- Dynamic readings that vary over time with random walk + drift
- Rule-based anomaly detection
- Structured log entries stored in memory (last 50 per machine)
- Fault code assignment based on which sensor triggered

Equipment → PDF mapping:
  general-industrial-motor         → General Industrial Motor Manual.pdf
  ac-drive-motor                   → AC Drive Motor Manual.pdf
  synchronous-motor                → Synchronous Motor Manual.pdf
  heavy-duty-industrial-motor      → Heavy-Duty Industrial Motor Manual.pdf
"""

import random
import math
import logging
from datetime import datetime, timedelta
from collections import deque
from typing import Optional

logger = logging.getLogger(__name__)

# ── Machine definitions ───────────────────────────────────────────────────────
MACHINE_CONFIG = {
    "general-industrial-motor": {
        "display_name": "General Industrial Motor",
        "equipment_tag": "general-industrial-motor",
        "rpm_nominal": 1450,
        "thresholds": {
            "vibration_mm_s":   {"normal": (1.0, 2.5),  "warn": 4.5,  "critical": 6.5},
            "bearing_temp_c":   {"normal": (60,  75),   "warn": 85.0, "critical": 92.0},
            "motor_current_a":  {"normal": (20,  30),   "warn": 38.0, "critical": 44.0},
            "lube_pressure_bar":{"normal": (3.8, 4.8),  "warn": 3.0,  "critical": 2.4},
        },
        "fault_codes": {
            "vibration_mm_s":    "FC-VM-01",
            "bearing_temp_c":    "FC-TH-01",
            "motor_current_a":   "FC-CU-01",
            "lube_pressure_bar": "FC-LP-01",
        },
    },
    "ac-drive-motor": {
        "display_name": "AC Drive Motor",
        "equipment_tag": "ac-drive-motor",
        "rpm_nominal": 1480,
        "thresholds": {
            "vibration_mm_s":   {"normal": (1.5, 3.0),  "warn": 5.0,  "critical": 7.5},
            "bearing_temp_c":   {"normal": (65,  78),   "warn": 88.0, "critical": 95.0},
            "motor_current_a":  {"normal": (38,  46),   "warn": 54.0, "critical": 62.0},
            "lube_pressure_bar":{"normal": (4.2, 5.1),  "warn": 3.5,  "critical": 2.8},
        },
        "fault_codes": {
            "vibration_mm_s":    "FC-VM-02",
            "bearing_temp_c":    "FC-TH-02",
            "motor_current_a":   "FC-CU-02",
            "lube_pressure_bar": "FC-LP-02",
        },
    },
    "synchronous-motor": {
        "display_name": "Synchronous Motor",
        "equipment_tag": "synchronous-motor",
        "rpm_nominal": 1500,
        "thresholds": {
            "vibration_mm_s":   {"normal": (1.2, 2.8),  "warn": 5.5,  "critical": 8.0},
            "bearing_temp_c":   {"normal": (70,  85),   "warn": 95.0, "critical": 105.0},
            "motor_current_a":  {"normal": (25,  35),   "warn": 42.0, "critical": 50.0},
            "lube_pressure_bar":{"normal": (4.0, 5.0),  "warn": 3.2,  "critical": 2.5},
        },
        "fault_codes": {
            "vibration_mm_s":    "FC-VM-03",
            "bearing_temp_c":    "FC-TH-03",
            "motor_current_a":   "FC-CU-03",
            "lube_pressure_bar": "FC-LP-03",
        },
    },
    "heavy-duty-industrial-motor": {
        "display_name": "Heavy-Duty Industrial Motor",
        "equipment_tag": "heavy-duty-industrial-motor",
        "rpm_nominal": 990,
        "thresholds": {
            "vibration_mm_s":   {"normal": (0.8, 2.0),  "warn": 4.0,  "critical": 6.5},
            "bearing_temp_c":   {"normal": (55,  70),   "warn": 82.0, "critical": 90.0},
            "motor_current_a":  {"normal": (52,  62),   "warn": 72.0, "critical": 82.0},
            "lube_pressure_bar":{"normal": (6.1, 7.4),  "warn": 4.8,  "critical": 3.5},
        },
        "fault_codes": {
            "vibration_mm_s":    "FC-VM-04",
            "bearing_temp_c":    "FC-TH-04",
            "motor_current_a":   "FC-CU-04",
            "lube_pressure_bar": "FC-LP-04",
        },
    },
}

# Equipment-tag → display doc name (matches what's in Qdrant)
MACHINE_DOC_MAP = {
    "general-industrial-motor":       "General Industrial Motor Manual.pdf",
    "ac-drive-motor":                 "AC Drive Motor Manual.pdf",
    "synchronous-motor":              "Synchronous Motor Manual.pdf",
    "heavy-duty-industrial-motor":    "Heavy-Duty Industrial Motor Manual.pdf",
}

# In-memory log buffer — last 50 entries per machine
_log_buffer: dict[str, deque] = {
    tag: deque(maxlen=50) for tag in MACHINE_CONFIG
}

# Sensor state per machine (random-walk simulation state)
_sensor_state: dict[str, dict] = {}


def _init_state(machine_tag: str) -> dict:
    """Initialise sensor state at nominal mid-range values."""
    cfg = MACHINE_CONFIG[machine_tag]["thresholds"]
    state = {}
    for sensor, thresholds in cfg.items():
        lo, hi = thresholds["normal"]
        state[sensor] = lo + (hi - lo) * 0.5
    return state


def _random_walk(current: float, lo: float, hi: float,
                 drift: float = 0.0, noise_pct: float = 0.03) -> float:
    """
    Advance sensor value by one step using a biased random walk.
    Drift > 0 pushes toward high end (simulates degradation).
    """
    noise = (random.random() * 2 - 1) * noise_pct * (hi - lo)
    new_val = current + drift + noise
    # Soft clamp — allow slight over/under for anomaly simulation
    return round(max(lo * 0.7, min(hi * 1.5, new_val)), 2)


def _classify_severity(value: float, thresholds: dict, sensor: str) -> tuple:
    """
    Returns (severity, alert_type, is_anomaly).
    For lube_pressure_bar low is bad; for all others high is bad.
    """
    is_low_bad = "pressure" in sensor

    if is_low_bad:
        if value <= thresholds["critical"]:
            return "CRITICAL", "LOW_LUBE_PRESSURE", True
        if value <= thresholds["warn"]:
            return "WARNING", "LOW_LUBE_PRESSURE", True
    else:
        if value >= thresholds["critical"]:
            return "CRITICAL", f"HIGH_{sensor.split('_')[0].upper()}", True
        if value >= thresholds["warn"]:
            return "WARNING", f"HIGH_{sensor.split('_')[0].upper()}", True

    return "NORMAL", "NOMINAL", False


def _event_summary(machine_tag: str, anomalies: list) -> str:
    """Build a human-readable one-line event summary."""
    name = MACHINE_CONFIG[machine_tag]["display_name"]
    if not anomalies:
        return f"{name}: all sensors within normal operating range."
    parts = []
    for a in anomalies:
        sensor, value, severity = a
        label = sensor.replace("_", " ").title()
        parts.append(f"{label}={value} ({severity})")
    return f"{name}: anomaly detected — {', '.join(parts)}."


def generate_log_entry(machine_tag: str, inject_anomaly: bool = False) -> dict:
    """
    Generate a single dynamic log entry for the given machine.

    Args:
        machine_tag: One of the 4 configured machine tags.
        inject_anomaly: If True, spike one sensor to critical level (for demo).

    Returns:
        Log entry dict.
    """
    if machine_tag not in MACHINE_CONFIG:
        raise ValueError(f"Unknown machine tag: {machine_tag}")

    cfg = MACHINE_CONFIG[machine_tag]
    thresholds = cfg["thresholds"]

    # Init state on first call
    if machine_tag not in _sensor_state:
        _sensor_state[machine_tag] = _init_state(machine_tag)

    state = _sensor_state[machine_tag]

    # Decide if we inject an anomaly in this tick
    anomaly_sensor = None
    if inject_anomaly:
        anomaly_sensor = random.choice(list(thresholds.keys()))

    readings = {}
    anomalies = []

    for sensor, th in thresholds.items():
        lo, hi = th["normal"]

        if sensor == anomaly_sensor:
            # Spike to 1.3–1.6× critical threshold
            if "pressure" in sensor:
                spiked = th["critical"] * random.uniform(0.5, 0.85)
            else:
                spiked = th["critical"] * random.uniform(1.1, 1.4)
            state[sensor] = round(spiked, 2)
        else:
            # Slow drift + noise — very slight upward drift to simulate wear
            drift = (hi - lo) * 0.002
            state[sensor] = _random_walk(state[sensor], lo, hi, drift=drift)

        val = state[sensor]
        readings[sensor] = val

        sev, alert_type, is_anom = _classify_severity(val, th, sensor)
        if is_anom:
            anomalies.append((sensor, val, sev))

    # Overall severity = worst across all sensors
    sev_order = {"NORMAL": 0, "WARNING": 1, "CRITICAL": 2}
    if anomalies:
        overall_severity = max(anomalies, key=lambda x: sev_order.get(x[2], 0))[2]
        primary_sensor = max(anomalies, key=lambda x: sev_order.get(x[2], 0))[0]
        alert_type = f"HIGH_{primary_sensor.split('_')[0].upper()}" if "pressure" not in primary_sensor else "LOW_LUBE_PRESSURE"
        fault_code = cfg["fault_codes"].get(primary_sensor, "FC-UNK")
    else:
        overall_severity = "NORMAL"
        alert_type = "NOMINAL"
        fault_code = "—"

    # RPM: slight variation from nominal
    rpm_nominal = cfg["rpm_nominal"]
    rpm = round(rpm_nominal * random.uniform(0.97, 1.03))
    if overall_severity == "CRITICAL":
        rpm = round(rpm_nominal * random.uniform(0.80, 0.93))
    elif overall_severity == "WARNING":
        rpm = round(rpm_nominal * random.uniform(0.93, 0.99))

    entry = {
        "machine_tag":       machine_tag,
        "display_name":      cfg["display_name"],
        "timestamp":         datetime.now().isoformat(),
        "vibration_mm_s":    readings.get("vibration_mm_s"),
        "bearing_temp_c":    readings.get("bearing_temp_c"),
        "motor_current_a":   readings.get("motor_current_a"),
        "lube_pressure_bar": readings.get("lube_pressure_bar"),
        "rpm":               rpm,
        "alert_type":        alert_type,
        "severity":          overall_severity,
        "fault_code":        fault_code,
        "event_summary":     _event_summary(machine_tag, anomalies),
        "anomaly_sensors":   [a[0] for a in anomalies],
        "mapped_document":   MACHINE_DOC_MAP.get(machine_tag, ""),
    }

    _log_buffer[machine_tag].append(entry)
    return entry


def get_latest_logs(machine_tag: str, count: int = 10) -> list:
    """
    Return the most recent `count` log entries for the given machine.
    Generates a fresh entry if the buffer is empty.
    """
    if machine_tag not in MACHINE_CONFIG:
        return []

    # Ensure there's at least 10 entries in buffer
    if len(_log_buffer[machine_tag]) < min(count, 10):
        for _ in range(10 - len(_log_buffer[machine_tag])):
            generate_log_entry(machine_tag)

    entries = list(_log_buffer[machine_tag])
    return entries[-count:]


def get_machine_summary(machine_tag: str) -> dict:
    """Return latest single log entry plus threshold context."""
    if machine_tag not in MACHINE_CONFIG:
        return {}

    latest = generate_log_entry(machine_tag)
    cfg = MACHINE_CONFIG[machine_tag]

    return {
        "machine_tag":    machine_tag,
        "display_name":   cfg["display_name"],
        "latest_reading": latest,
        "thresholds":     cfg["thresholds"],
        "mapped_document":MACHINE_DOC_MAP.get(machine_tag, ""),
    }


def format_logs_for_llm(machine_tag: str, logs: list) -> str:
    """
    Format machine logs into a structured text block for the LLM prompt.
    This becomes part of the user_message sent to the answerer.
    """
    cfg = MACHINE_CONFIG.get(machine_tag, {})
    display = cfg.get("display_name", machine_tag)
    thresholds = cfg.get("thresholds", {})

    lines = [
        f"MACHINE DIAGNOSTIC REPORT",
        f"Machine: {display}",
        f"Equipment Tag: {machine_tag}",
        f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "=== THRESHOLD REFERENCE ===",
    ]

    for sensor, th in thresholds.items():
        label = sensor.replace("_", " ").title()
        lo, hi = th["normal"]
        lines.append(
            f"  {label}: Normal {lo}–{hi}  |  Warn >{th['warn']}  |  Critical >{th['critical']}"
            if "pressure" not in sensor
            else f"  {label}: Normal {lo}–{hi}  |  Warn <{th['warn']}  |  Critical <{th['critical']}"
        )

    lines += ["", "=== LATEST SENSOR READINGS (most recent first) ==="]

    for i, log in enumerate(reversed(logs[-10:]), 1):
        ts = log.get("timestamp", "")[:19]
        lines.append(
            f"[{i}] {ts}  "
            f"Vib={log.get('vibration_mm_s')} mm/s  "
            f"Temp={log.get('bearing_temp_c')}°C  "
            f"Current={log.get('motor_current_a')} A  "
            f"Pressure={log.get('lube_pressure_bar')} bar  "
            f"RPM={log.get('rpm')}  "
            f"Severity={log.get('severity')}  "
            f"FaultCode={log.get('fault_code')}"
        )
        if log.get("severity") != "NORMAL":
            lines.append(f"     ↳ {log.get('event_summary')}")

    # Highlight current status
    latest = logs[-1] if logs else {}
    lines += [
        "",
        "=== CURRENT STATUS ===",
        f"Severity: {latest.get('severity', 'UNKNOWN')}",
        f"Active Fault Code: {latest.get('fault_code', '—')}",
        f"Alert Type: {latest.get('alert_type', '—')}",
        f"Event Summary: {latest.get('event_summary', '')}",
        "",
        "=== ANALYSIS REQUEST ===",
        "Based on the machine logs above and the equipment manual context provided,",
        "please explain:",
        "1. What is the likely fault or issue?",
        "2. Why did it happen (based on the sensor trend)?",
        "3. What does the manual recommend for this condition?",
        "4. What is the recommended immediate action?",
        "Cite the manual sections that support your diagnosis.",
    ]

    return "\n".join(lines)
