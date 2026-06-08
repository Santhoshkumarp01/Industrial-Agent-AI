"""
Trains Isolation Forest anomaly detection models.

Run: python -m ml.trainer
Input: data/raw/sensor_data.csv
Output: ml/saved_models/isolation_forest_{equip_id}.pkl
"""

import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report

FEATURE_COLUMNS = ["vibration", "temperature", "current", "pressure"]
MODEL_DIR = Path("ml/saved_models")
DATA_PATH = Path("data/raw/sensor_data.csv")


def train_all():
    """Train Isolation Forest models for all equipment types."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA_PATH)

    equipment_ids = df["equipment_id"].unique()

    for equip_id in equipment_ids:
        print(f"\n→ Training model for {equip_id}...")
        equip_df = df[df["equipment_id"] == equip_id].copy()

        # Train ONLY on normal data
        normal_df = equip_df[equip_df["label"] == "normal"]
        X_train = normal_df[FEATURE_COLUMNS].values

        # Validation set = all data (normal + anomaly)
        X_val = equip_df[FEATURE_COLUMNS].values
        y_val = (equip_df["label"] == "anomaly").astype(int).values

        # Pipeline: StandardScaler + IsolationForest
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("model", IsolationForest(
                n_estimators=200,
                max_samples="auto",
                contamination=0.01,   # ~1% anomaly rate expected
                random_state=42,
                n_jobs=-1
            ))
        ])

        pipeline.fit(X_train)

        # Evaluate on validation set
        # IsolationForest returns -1 for anomaly, 1 for normal
        preds = pipeline.predict(X_val)
        # Convert to binary: anomaly=1, normal=0
        preds_binary = (preds == -1).astype(int)

        print(classification_report(
            y_val, preds_binary,
            target_names=["normal", "anomaly"],
            zero_division=0
        ))

        # Save model pipeline
        model_path = MODEL_DIR / f"isolation_forest_{equip_id.lower()}.pkl"
        joblib.dump(pipeline, model_path)
        print(f"✓ Saved → {model_path}")

    print("\n✓ All models trained and saved.")


if __name__ == "__main__":
    train_all()
