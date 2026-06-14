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

# ── Machine definitions — PDF-GROUNDED ────────────────────────────────────────
MACHINE_CONFIG = {
    "general-industrial-motor": {
        "display_name": "General Industrial Motor (Siemens SIMOTICS TN 1LA8)",
        "equipment_tag": "general-industrial-motor",
        "rpm_nominal": 1465,  # 4-pole 50Hz with 2.3% slip
        "thresholds": {
            "vibration_velocity_mm_s":   {"normal": (1.2, 2.8),  "warn": 4.5,  "critical": 7.1},
            "bearing_temp_drive_end_c":   {"normal": (55,  75),   "warn": 110.0, "critical": 120.0},
            "stator_winding_temp_c":  {"normal": (80,  110),   "warn": 145.0, "critical": 155.0},
            "stator_phase_current_a":  {"normal": (18,  26),   "warn": 30.0, "critical": 33.0},
            "bearing_lube_oil_pressure_bar":{"normal": (3.5, 5.0),  "warn": 1.5,  "critical": 1.0},
        },
        "fault_codes": {
            "vibration_velocity_mm_s":    "FC-VB-01",
            "bearing_temp_drive_end_c":    "FC-TH-01",
            "stator_winding_temp_c":    "FC-TH-02",
            "stator_phase_current_a":   "FC-CR-01",
            "bearing_lube_oil_pressure_bar": "FC-LP-01",
        },
    },
    "ac-drive-motor": {
        "display_name": "AC Drive Motor (Siemens 1PH7 series)",
        "equipment_tag": "ac-drive-motor",
        "rpm_nominal": 1800,  # Variable speed, shown at 1800
        "thresholds": {
            "vibration_velocity_mm_s":   {"normal": (0.8, 2.2),  "warn": 4.5,  "critical": 7.1},
            "bearing_temp_drive_end_c":   {"normal": (50,  70),   "warn": 110.0, "critical": 120.0},
            "stator_winding_temp_c":  {"normal": (70,  100),   "warn": 130.0, "critical": 145.0},
            "stator_phase_current_a":  {"normal": (15,  22),   "warn": 25.0, "critical": 28.0},
            "bearing_lube_oil_pressure_bar":{"normal": (3.0, 4.5),  "warn": 1.5,  "critical": 1.0},
        },
        "fault_codes": {
            "vibration_velocity_mm_s":    "FC-VB-01",
            "bearing_temp_drive_end_c":    "FC-TH-01",
            "stator_winding_temp_c":    "FC-TH-02",
            "stator_phase_current_a":   "FC-CR-01",
            "bearing_lube_oil_pressure_bar": "FC-LP-01",
        },
    },
    "synchronous-motor": {
        "display_name": "Synchronous Motor (WEG S Line with Brushes)",
        "equipment_tag": "synchronous-motor",
        "rpm_nominal": 1000,  # 6-pole 50Hz synchronous
        "thresholds": {
            "vibration_velocity_mm_s":   {"normal": (1.0, 2.5),  "warn": 4.5,  "critical": 7.1},
            "bearing_temp_drive_end_c":   {"normal": (55,  80),   "warn": 100.0, "critical": 110.0},
            "stator_winding_temp_c":  {"normal": (85,  115),   "warn": 145.0, "critical": 155.0},
            "stator_phase_current_a":  {"normal": (22,  35),   "warn": 40.0, "critical": 44.0},
            "bearing_lube_oil_pressure_bar":{"normal": (2.5, 4.0),  "warn": 1.5,  "critical": 1.0},
        },
        "fault_codes": {
            "vibration_velocity_mm_s":    "FC-VB-01",
            "bearing_temp_drive_end_c":    "FC-TH-01",
            "stator_winding_temp_c":    "FC-TH-02",
            "stator_phase_current_a":   "FC-SY-01",
            "bearing_lube_oil_pressure_bar": "FC-LP-01",
        },
    },
    "heavy-duty-industrial-motor": {
        "display_name": "Heavy-Duty Industrial Motor (WEG W60 Line)",
        "equipment_tag": "heavy-duty-industrial-motor",
        "rpm_nominal": 750,  # 8-pole 50Hz with slip
        "thresholds": {
            "vibration_velocity_mm_s":   {"normal": (1.5, 3.2),  "warn": 4.5,  "critical": 7.1},
            "bearing_temp_drive_end_c":   {"normal": (60,  85),   "warn": 110.0, "critical": 120.0},
            "stator_winding_temp_c":  {"normal": (90,  120),   "warn": 145.0, "critical": 155.0},
            "stator_phase_current_a":  {"normal": (28,  42),   "warn": 48.0, "critical": 53.0},
            "bearing_lube_oil_pressure_bar":{"normal": (3.0, 5.0),  "warn": 1.5,  "critical": 1.0},
        },
        "fault_codes": {
            "vibration_velocity_mm_s":    "FC-VB-01",
            "bearing_temp_drive_end_c":    "FC-TH-01",
            "stator_winding_temp_c":    "FC-TH-02",
            "stator_phase_current_a":   "FC-CR-01",
            "bearing_lube_oil_pressure_bar": "FC-LP-01",
        },
    },
}

# Equipment-tag → display doc name (matches what's in Qdrant)
# NOTE: Qdrant uses the PDF filenames as equipment_tag, not the dash-separated machine_tag
MACHINE_DOC_MAP = {
    "general-industrial-motor":       "General Industrial Motor.pdf",
    "ac-drive-motor":                 "AC Drive Motor.pdf",
    "synchronous-motor":              "Synchronous Motor.pdf",
    "heavy-duty-industrial-motor":    "Heavy-Duty Industrial Motor.pdf",
}

# Map machine_tag to Qdrant equipment_tag (for retrieval filtering)
MACHINE_TAG_TO_EQUIPMENT_TAG = {
    "general-industrial-motor":       "General Industrial Motor",
    "ac-drive-motor":                 "AC Drive Motor",
    "synchronous-motor":              "Synchronous Motor",
    "heavy-duty-industrial-motor":    "Heavy-Duty Industrial Motor",
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
    """Build a human-readable one-line event summary with PDF-grounded sensor names."""
    name = MACHINE_CONFIG[machine_tag]["display_name"]
    if not anomalies:
        return f"{name}: all sensors within normal operating range."
    
    # Use proper sensor display names
    DISPLAY_NAMES = {
        "vibration_velocity_mm_s": "Vibration Velocity",
        "bearing_temp_drive_end_c": "Bearing Temperature (Drive End)",
        "stator_winding_temp_c": "Stator Winding Temperature",
        "stator_phase_current_a": "Stator Phase Current",
        "bearing_lube_oil_pressure_bar": "Bearing Lube Oil Pressure"
    }
    
    parts = []
    for a in anomalies:
        sensor, value, severity = a
        label = DISPLAY_NAMES.get(sensor, sensor.replace("_", " ").title())
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
        "vibration_velocity_mm_s":    readings.get("vibration_velocity_mm_s"),
        "bearing_temp_drive_end_c":    readings.get("bearing_temp_drive_end_c"),
        "stator_winding_temp_c":   readings.get("stator_winding_temp_c"),
        "stator_phase_current_a":   readings.get("stator_phase_current_a"),
        "bearing_lube_oil_pressure_bar": readings.get("bearing_lube_oil_pressure_bar"),
        "shaft_speed_rpm":               rpm,
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
    Uses PDF-grounded sensor names and threshold citations.
    """
    cfg = MACHINE_CONFIG.get(machine_tag, {})
    display = cfg.get("display_name", machine_tag)
    thresholds = cfg.get("thresholds", {})

    # Sensor display names
    DISPLAY_NAMES = {
        "vibration_velocity_mm_s": "Vibration Velocity",
        "bearing_temp_drive_end_c": "Bearing Temperature (Drive End)",
        "stator_winding_temp_c": "Stator Winding Temperature",
        "stator_phase_current_a": "Stator Phase Current",
        "bearing_lube_oil_pressure_bar": "Bearing Lube Oil Pressure"
    }

    lines = [
        f"MACHINE DIAGNOSTIC REPORT",
        f"Machine: {display}",
        f"Equipment Tag: {machine_tag}",
        f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "=== THRESHOLD REFERENCE (from motor manual) ===",
    ]

    for sensor, th in thresholds.items():
        label = DISPLAY_NAMES.get(sensor, sensor.replace("_", " ").title())
        lo, hi = th["normal"]
        if "pressure" in sensor:
            lines.append(f"  {label}: Normal {lo}–{hi} bar  |  Alarm <{th['warn']}  |  Trip <{th['critical']}")
        else:
            lines.append(f"  {label}: Normal {lo}–{hi}  |  Alarm >{th['warn']}  |  Trip >{th['critical']}")

    lines += ["", "=== LATEST SENSOR READINGS (most recent first) ==="]

    for i, log in enumerate(reversed(logs[-10:]), 1):
        ts = log.get("timestamp", "")[:19]
        # Build one-line summary format for latest log
        latest_log = logs[-1] if logs else {}
        
        lines.append(
            f"[{i}] {ts}  "
            f"Vib={log.get('vibration_velocity_mm_s')} mm/s  "
            f"BearTemp={log.get('bearing_temp_drive_end_c')}°C  "
            f"WindTemp={log.get('stator_winding_temp_c')}°C  "
            f"Current={log.get('stator_phase_current_a')} A  "
            f"Pressure={log.get('bearing_lube_oil_pressure_bar')} bar  "
            f"RPM={log.get('shaft_speed_rpm')}  "
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
        "Cite the exact manual sections (Section X.X) that support your diagnosis.",
    ]

    return "\n".join(lines)



def inject_demo_anomaly(machine_tag: str) -> dict:
    """
    Inject a PDF-grounded fault scenario for demo purposes.
    
    Returns:
        Fault scenario metadata with sensor spikes and recommended actions.
    """
    from motor_config.fault_scenarios import FAULT_SCENARIOS
    
    if machine_tag not in MACHINE_CONFIG:
        raise ValueError(f"Unknown machine tag: {machine_tag}")
    
    scenarios = FAULT_SCENARIOS.get(machine_tag, [])
    if not scenarios:
        return None
    
    # Use first scenario (temperature fault) for consistent demo
    scenario = scenarios[0]
    
    # Spike the sensor state
    if machine_tag not in _sensor_state:
        _sensor_state[machine_tag] = _init_state(machine_tag)
    
    _sensor_state[machine_tag].update(scenario["sensor_spike"])
    
    # Generate log entry with the spiked values
    entry = generate_log_entry(machine_tag, inject_anomaly=False)
    
    # Return scenario metadata for agent pipeline
    return {
        "fault_code": scenario["fault_code"],
        "fault_name": scenario["fault_name"],
        "description": scenario["description"],
        "thresholds": scenario["thresholds"],
        "risk_level": scenario["risk_level"],
        "probable_root_causes": scenario["probable_root_causes"],
        "recommended_actions": scenario["recommended_actions"],
        "log_entry": entry
    }


def reset_to_normal(machine_tag: str) -> dict:
    """Reset machine sensors to normal operating baseline."""
    if machine_tag not in MACHINE_CONFIG:
        raise ValueError(f"Unknown machine tag: {machine_tag}")
    
    _sensor_state[machine_tag] = _init_state(machine_tag)
    entry = generate_log_entry(machine_tag)
    
    return {
        "reset": True,
        "machine_tag": machine_tag,
        "log_entry": entry
    }
