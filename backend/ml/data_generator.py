"""
Generates synthetic sensor data for training the anomaly detection model.

Run: python -m ml.data_generator
Output: data/raw/sensor_data.csv
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Equipment profiles to simulate
EQUIPMENT_PROFILES = {
    "RM1": {
        "name": "Rolling Mill #1",
        "sensors": {
            "vibration":    {"normal": (1.5, 3.0),  "unit": "mm/s",  "anomaly_multiplier": 3.2},
            "temperature":  {"normal": (65.0, 78.0), "unit": "C",    "anomaly_multiplier": 1.6},
            "current":      {"normal": (38.0, 46.0), "unit": "A",    "anomaly_multiplier": 1.5},
            "pressure":     {"normal": (4.2, 5.1),   "unit": "bar",  "anomaly_multiplier": 0.4},
        }
    },
    "RM3": {
        "name": "Rolling Mill #3",
        "sensors": {
            "vibration":    {"normal": (1.8, 3.2),  "unit": "mm/s",  "anomaly_multiplier": 3.0},
            "temperature":  {"normal": (68.0, 80.0), "unit": "C",    "anomaly_multiplier": 1.5},
            "current":      {"normal": (40.0, 48.0), "unit": "A",    "anomaly_multiplier": 1.4},
            "pressure":     {"normal": (4.0, 5.0),   "unit": "bar",  "anomaly_multiplier": 0.35},
        }
    },
    "BF1": {
        "name": "BF Blower #1",
        "sensors": {
            "vibration":    {"normal": (0.8, 2.0),  "unit": "mm/s",  "anomaly_multiplier": 3.5},
            "temperature":  {"normal": (55.0, 70.0), "unit": "C",    "anomaly_multiplier": 1.7},
            "current":      {"normal": (52.0, 62.0), "unit": "A",    "anomaly_multiplier": 1.6},
            "pressure":     {"normal": (6.1, 7.4),   "unit": "bar",  "anomaly_multiplier": 0.3},
        }
    },
    "COMP_A": {
        "name": "Compressor A",
        "sensors": {
            "vibration":    {"normal": (1.2, 2.8),  "unit": "mm/s",  "anomaly_multiplier": 3.0},
            "temperature":  {"normal": (72.0, 88.0), "unit": "C",    "anomaly_multiplier": 1.5},
            "current":      {"normal": (28.0, 36.0), "unit": "A",    "anomaly_multiplier": 1.5},
            "pressure":     {"normal": (8.5, 10.2),  "unit": "bar",  "anomaly_multiplier": 0.4},
        }
    }
}


def generate_sensor_data():
    """Generate synthetic sensor data with normal and anomaly readings."""
    rows = []
    start_time = datetime(2024, 1, 1, 0, 0, 0)
    interval_seconds = 5       # reading every 5 seconds
    normal_readings = 5000     # per equipment
    anomaly_readings = 60      # per equipment (injected at random positions)

    for equip_id, profile in EQUIPMENT_PROFILES.items():
        timestamps = [
            start_time + timedelta(seconds=i * interval_seconds)
            for i in range(normal_readings + anomaly_readings)
        ]

        # Choose random anomaly positions (not at start or end)
        anomaly_positions = sorted(
            np.random.choice(
                range(500, normal_readings + anomaly_readings - 100),
                size=anomaly_readings,
                replace=False
            )
        )
        anomaly_set = set(anomaly_positions)

        for i, ts in enumerate(timestamps):
            is_anomaly = i in anomaly_set
            row = {
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "equipment_id": equip_id,
                "equipment_name": profile["name"],
                "label": "anomaly" if is_anomaly else "normal"
            }

            for sensor_key, sensor_cfg in profile["sensors"].items():
                lo, hi = sensor_cfg["normal"]
                base_value = np.random.uniform(lo, hi)

                # Add realistic noise (±3%)
                noise = base_value * np.random.uniform(-0.03, 0.03)
                value = base_value + noise

                if is_anomaly:
                    multiplier = sensor_cfg["anomaly_multiplier"]
                    if multiplier < 1:
                        # Pressure drops during anomaly
                        value = lo * multiplier * np.random.uniform(0.8, 1.0)
                    else:
                        # Other sensors spike up
                        value = hi * multiplier * np.random.uniform(0.9, 1.1)

                row[sensor_key] = round(value, 3)

            rows.append(row)

    df = pd.DataFrame(rows)

    # Save to data/raw/
    output_path = Path("data/raw/sensor_data.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"✓ Generated {len(df)} rows → {output_path}")
    print(f"  Normal: {len(df[df.label == 'normal'])}")
    print(f"  Anomaly: {len(df[df.label == 'anomaly'])}")
    return df


if __name__ == "__main__":
    generate_sensor_data()
