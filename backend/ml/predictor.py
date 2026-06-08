"""
Loads trained Isolation Forest models and scores live sensor readings.
Used by the sensor API to classify each incoming reading.
"""

import joblib
import numpy as np
from pathlib import Path
from models.schemas import SensorReading, PredictionResult

MODEL_DIR = Path("ml/saved_models")
FEATURE_COLUMNS = ["vibration", "temperature", "current", "pressure"]

# Cache loaded models in memory (load once per process)
_models = {}


def _get_model(equipment_id: str):
    """Load and cache model for equipment."""
    key = equipment_id.upper()
    if key not in _models:
        model_path = MODEL_DIR / f"isolation_forest_{equipment_id.lower()}.pkl"
        if not model_path.exists():
            raise FileNotFoundError(
                f"No trained model found for {equipment_id}. "
                f"Run: python -m ml.trainer"
            )
        _models[key] = joblib.load(model_path)
        print(f"✓ Loaded model for {equipment_id}")
    return _models[key]


def predict(reading: SensorReading) -> PredictionResult:
    """
    Score a single sensor reading.
    Returns: is_anomaly, anomaly_score, risk_level
    """
    pipeline = _get_model(reading.equipment_id)

    X = np.array([[
        reading.vibration,
        reading.temperature,
        reading.current,
        reading.pressure
    ]])

    # predict: 1=normal, -1=anomaly
    prediction = pipeline.predict(X)[0]

    # decision_function: negative = more anomalous
    score = pipeline.decision_function(X)[0]

    # Normalize score to 0-1 (0 = very normal, 1 = very anomalous)
    # score ranges roughly from -0.5 to 0.5
    anomaly_score = float(np.clip(((-score) + 0.5) / 1.0, 0.0, 1.0))

    is_anomaly = prediction == -1

    # Risk level based on anomaly score
    if anomaly_score >= 0.75:
        risk_level = "CRITICAL"
    elif anomaly_score >= 0.55:
        risk_level = "HIGH"
    elif anomaly_score >= 0.35:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return PredictionResult(
        equipment_id=reading.equipment_id,
        is_anomaly=is_anomaly,
        anomaly_score=round(anomaly_score, 4),
        risk_level=risk_level,
        timestamp=reading.timestamp
    )
