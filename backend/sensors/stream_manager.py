"""
In-memory buffer of recent sensor readings.

Stores last 200 readings per sensor per equipment.
Thread-safe with asyncio.Lock.
"""

import asyncio
from collections import deque
from models.schemas import SensorReading, PredictionResult
from datetime import datetime

# Buffer: { equipment_id: { sensor_key: deque([...last 200 values...]) } }
_buffers: dict[str, dict[str, deque]] = {}
_lock = asyncio.Lock()

# Latest prediction per equipment
_latest_predictions: dict[str, PredictionResult] = {}

# Latest raw reading per equipment
_latest_readings: dict[str, SensorReading] = {}

BUFFER_SIZE = 200


async def add_reading(reading: SensorReading, prediction: PredictionResult):
    """Add a new reading to the buffer."""
    async with _lock:
        equip = reading.equipment_id
        if equip not in _buffers:
            _buffers[equip] = {
                "vibration":   deque(maxlen=BUFFER_SIZE),
                "temperature": deque(maxlen=BUFFER_SIZE),
                "current":     deque(maxlen=BUFFER_SIZE),
                "pressure":    deque(maxlen=BUFFER_SIZE),
            }

        _buffers[equip]["vibration"].append(reading.vibration)
        _buffers[equip]["temperature"].append(reading.temperature)
        _buffers[equip]["current"].append(reading.current)
        _buffers[equip]["pressure"].append(reading.pressure)

        _latest_predictions[equip] = prediction
        _latest_readings[equip] = reading


def get_recent_values(equipment_id: str, sensor_key: str) -> list[float]:
    """Get recent values for a specific sensor."""
    buf = _buffers.get(equipment_id, {}).get(sensor_key, deque())
    return list(buf)


def get_all_equipment_status() -> dict:
    """Get current status of all equipment."""
    result = {}
    for equip_id, pred in _latest_predictions.items():
        reading = _latest_readings.get(equip_id)
        result[equip_id] = {
            "equipment_id": equip_id,
            "risk_level": pred.risk_level,
            "anomaly_score": pred.anomaly_score,
            "is_anomaly": pred.is_anomaly,
            "latest_reading": reading.dict() if reading else None,
            "last_updated": pred.timestamp
        }
    return result
