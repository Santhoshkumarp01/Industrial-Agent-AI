"""
Alert dispatcher — stores active alerts when anomaly detected.

Frontend polls GET /sensors/alerts to get active alerts.
"""

from datetime import datetime
from models.schemas import SensorAlert
import uuid

# Active alerts in memory
_active_alerts: list[SensorAlert] = []
_alert_history: list[SensorAlert] = []

MAX_ACTIVE_ALERTS = 20


def fire_alert(
    equipment_id: str,
    equipment_name: str,
    sensor_key: str,
    sensor_value: float,
    anomaly_score: float,
    risk_level: str,
    rul_hours: float = None
) -> SensorAlert:
    """Fire a new alert."""
    
    alert = SensorAlert(
        alert_id=str(uuid.uuid4()),
        equipment_id=equipment_id,
        equipment_name=equipment_name,
        sensor_key=sensor_key,
        sensor_value=sensor_value,
        anomaly_score=anomaly_score,
        risk_level=risk_level,
        rul_hours=rul_hours,
        timestamp=datetime.now().isoformat(),
        acknowledged=False,
        # Auto-generate the chat message the frontend will send
        auto_chat_message=(
            f"ALERT: Anomaly detected on {equipment_name}. "
            f"Sensor: {sensor_key} = {sensor_value:.2f}. "
            f"Risk level: {risk_level}. "
            f"Anomaly score: {anomaly_score:.2f}. "
            + (f"Estimated time to failure: {rul_hours:.1f} hours. " if rul_hours else "")
            + "Please diagnose the root cause and recommend immediate action."
        )
    )

    _active_alerts.append(alert)
    _alert_history.append(alert)

    # Keep active alerts list bounded
    if len(_active_alerts) > MAX_ACTIVE_ALERTS:
        _active_alerts.pop(0)

    print(f"🚨 ALERT: {equipment_name} — {sensor_key} anomaly — {risk_level}")
    return alert


def get_active_alerts() -> list[SensorAlert]:
    """Get all unacknowledged alerts."""
    return [a for a in _active_alerts if not a.acknowledged]


def acknowledge_alert(alert_id: str) -> bool:
    """Mark an alert as acknowledged."""
    for alert in _active_alerts:
        if alert.alert_id == alert_id:
            alert.acknowledged = True
            return True
    return False


def get_alert_history() -> list[SensorAlert]:
    """Get full alert history."""
    return _alert_history
