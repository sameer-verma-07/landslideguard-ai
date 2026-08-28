"""
generate_data.py
Creates a synthetic dataset of landslide-risk monitoring points across
India's North Eastern Region for SIH PS 26001 (AI-Based Early Warning and
Landslide Risk Monitoring System in NER).

Real Bhuvan/IMD feeds require registration and aren't scriptable without
credentials, so this builds a realistic synthetic dataset with a genuine
underlying risk pattern - same approach used for the PS 26017 backup.
"""

import numpy as np
import pandas as pd
import os

np.random.seed(7)

N = 300

# Approximate NER state capitals used as geographic anchors
STATE_ANCHORS = {
    "Assam": (26.14, 91.73),
    "Arunachal Pradesh": (27.10, 93.62),
    "Meghalaya": (25.57, 91.88),
    "Mizoram": (23.73, 92.72),
    "Manipur": (24.82, 93.94),
    "Nagaland": (25.67, 94.12),
    "Tripura": (23.84, 91.28),
    "Sikkim": (27.33, 88.61),
}

LOCATION_TYPES = ["Village", "Highway segment", "School zone", "Market area", "Residential cluster"]


def generate_dataset(n=N):
    states = np.random.choice(list(STATE_ANCHORS.keys()), n)
    lat, lon = [], []
    for s in states:
        base_lat, base_lon = STATE_ANCHORS[s]
        lat.append(base_lat + np.random.uniform(-0.8, 0.8))
        lon.append(base_lon + np.random.uniform(-0.8, 0.8))

    data = {
        "location_id": [f"NER-{1000 + i}" for i in range(n)],
        "state": states,
        "location_type": np.random.choice(LOCATION_TYPES, n),
        "latitude": np.round(lat, 4),
        "longitude": np.round(lon, 4),
        "elevation_m": np.random.randint(50, 2200, n),
        "slope_angle_deg": np.round(np.random.gamma(shape=3.0, scale=8, size=n), 1),
        "soil_moisture_pct": np.round(np.random.beta(2.2, 2, n) * 100, 1),
        "rainfall_last_7d_mm": np.round(np.random.gamma(shape=2.5, scale=25, size=n), 1),
        "rainfall_last_30d_mm": np.round(np.random.gamma(shape=3.0, scale=60, size=n), 1),
        "vegetation_cover_pct": np.round(np.random.beta(3, 2, n) * 100, 1),
        "historical_landslide_count": np.random.poisson(lam=1.4, size=n),
        "nearby_population": np.random.randint(50, 8000, n),
    }
    df = pd.DataFrame(data)
    df["slope_angle_deg"] = df["slope_angle_deg"].clip(upper=70)

    # --- genuine underlying risk pattern, so the model has real signal ---
    hist_max = max(df["historical_landslide_count"].max(), 1)
    risk = (
        0.28 * (df["slope_angle_deg"] / 70)
        + 0.22 * (df["soil_moisture_pct"] / 100)
        + 0.18 * (df["rainfall_last_7d_mm"] / df["rainfall_last_7d_mm"].max())
        + 0.12 * (1 - df["vegetation_cover_pct"] / 100)
        + 0.12 * (df["historical_landslide_count"] / hist_max)
        + 0.08 * (df["rainfall_last_30d_mm"] / df["rainfall_last_30d_mm"].max())
    )
    risk = (risk - risk.min()) / (risk.max() - risk.min())
    noise = np.random.normal(0, 0.06, n)
    risk = np.clip(risk + noise, 0, 1)

    df["true_risk"] = np.round(risk, 3)
    df["high_risk_alert"] = (risk > 0.55).astype(int)

    return df


if __name__ == "__main__":
    df = generate_dataset()
    os.makedirs("data", exist_ok=True)
    out_path = "data/ner_landslide_data.csv"
    df.to_csv(out_path, index=False)
    print(f"Generated {len(df)} monitoring points across NER -> {out_path}")
    print(f"High-risk alert rate: {df['high_risk_alert'].mean():.1%}")
    print("\nSample rows:")
    print(df.head(3).to_string())
