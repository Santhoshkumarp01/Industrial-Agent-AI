"""
Sensor API routes:

  POST /sensors/reading     — receive a sensor reading, score it, return prediction
  GET  /sensors/status      — current health of all equipment
  GET  /sensors/alerts      — active (unacknowledged) alerts
  POST /sensors/alerts/{id}/acknowledge — mark alert as acknowledged
  GET  /sensors/history/{equipment_id}  — recent readings buffer
  POST /sensors/demo/inject — inject anomaly for demo (Ctrl+Shift+D equivalent)
"""

from fastapi import APIRouter
from models.schemas import SensorReading, PredictionResult, SensorAlert
from ml.predictor import predict
from ml.rul_estimator import estimate_rul
from sensors.stream_manager import add_reading, get_recent_values, get_all_equipment_status
from sensors.alert_dispatcher import (
    fire_alert, get_active_alerts, acknowledge_alert, get_alert_history
)
import asyncio
import time
from datetime import datetime
import random

router = APIRouter(prefix="/sensors", tags=["sensors"])

# Equipment ID → display name mapping
EQUIPMENT_NAMES = {
    "RM1": "Rolling Mill #1",
    "RM3": "Rolling Mill #3",
    "BF1": "BF Blower #1",
    "COMP_A": "Compressor A"
}

# Track which equipment already has an active unacknowledged alert
# to avoid duplicate alerts for same ongoing anomaly
_alert_cooldown: dict[str, float] = {}
ALERT_COOLDOWN_SECONDS = 30


@router.post("/reading", response_model=PredictionResult)
async def receive_reading(reading: SensorReading):
    """
    Frontend or IoT device sends a sensor reading.
    Backend scores it with ML model and returns prediction.
    If anomaly detected, fires an alert.
    """
    # Score with Isolation Forest
    result = predict(reading)

    # Store in buffer
    await add_reading(reading, result)

    # Estimate RUL for the most anomalous sensor
    if result.is_anomaly:
        # Find which sensor is most anomalous by checking thresholds
        sensor_values = {
            "vibration": reading.vibration,
            "temperature": reading.temperature,
            "current": reading.current,
            "pressure": reading.pressure
        }

        # Pick sensor with highest relative deviation from normal
        most_anomalous_sensor = "vibration"  # default
        rul_hours = None

        for sensor_key in sensor_values:
            recent = get_recent_values(reading.equipment_id, sensor_key)
            rul = estimate_rul(
                reading.equipment_id, sensor_key, recent
            )
            if rul is not None:
                rul_hours = rul
                most_anomalous_sensor = sensor_key
                break

        # Fire alert (with cooldown to avoid spam)
        now = time.time()
        cooldown_key = reading.equipment_id
        last_alert = _alert_cooldown.get(cooldown_key, 0)

        if now - last_alert > ALERT_COOLDOWN_SECONDS:
            fire_alert(
                equipment_id=reading.equipment_id,
                equipment_name=EQUIPMENT_NAMES.get(reading.equipment_id, reading.equipment_id),
                sensor_key=most_anomalous_sensor,
                sensor_value=sensor_values[most_anomalous_sensor],
                anomaly_score=result.anomaly_score,
                risk_level=result.risk_level,
                rul_hours=rul_hours
            )
            _alert_cooldown[cooldown_key] = now

    return result


@router.get("/status")
async def get_status():
    """Current health summary of all equipment."""
    return get_all_equipment_status()


@router.get("/alerts", response_model=list[SensorAlert])
async def get_alerts():
    """Active unacknowledged alerts."""
    return get_active_alerts()


@router.post("/alerts/{alert_id}/acknowledge")
async def ack_alert(alert_id: str):
    """Acknowledge an alert."""
    success = acknowledge_alert(alert_id)
    return {"acknowledged": success, "alert_id": alert_id}


@router.get("/history/{equipment_id}")
async def get_history(equipment_id: str):
    """Recent sensor readings buffer for an equipment."""
    return {
        "equipment_id": equipment_id,
        "vibration":    get_recent_values(equipment_id, "vibration"),
        "temperature":  get_recent_values(equipment_id, "temperature"),
        "current":      get_recent_values(equipment_id, "current"),
        "pressure":     get_recent_values(equipment_id, "pressure"),
    }


@router.post("/demo/inject")
async def inject_anomaly(equipment_id: str = "RM3", sensor: str = "vibration"):
    """
    Demo endpoint: injects an anomaly reading for the specified equipment.
    Called by frontend when Ctrl+Shift+D is pressed.
    This makes the anomaly come from the real ML backend — not just frontend threshold.
    """
    # Get current normal ranges and spike them
    spike_values = {
        "RM1":    {"vibration": 9.2,  "temperature": 94.0, "current": 61.0, "pressure": 1.9},
        "RM3":    {"vibration": 9.8,  "temperature": 98.0, "current": 65.0, "pressure": 1.7},
        "BF1":    {"vibration": 7.5,  "temperature": 92.0, "current": 78.0, "pressure": 3.2},
        "COMP_A": {"vibration": 9.0,  "temperature": 110.0,"current": 50.0, "pressure": 4.8},
    }

    values = spike_values.get(equipment_id.upper(), spike_values["RM3"])

    anomaly_reading = SensorReading(
        equipment_id=equipment_id.upper(),
        vibration=values["vibration"] * random.uniform(0.95, 1.05),
        temperature=values["temperature"] * random.uniform(0.95, 1.05),
        current=values["current"] * random.uniform(0.95, 1.05),
        pressure=values["pressure"] * random.uniform(0.95, 1.05),
        timestamp=datetime.now().isoformat()
    )

    result = await receive_reading(anomaly_reading)
    return {
        "message": f"Anomaly injected for {equipment_id}",
        "reading": anomaly_reading,
        "prediction": result
    }
