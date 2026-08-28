"""
train_model.py
Trains a landslide-risk classifier on data/ner_landslide_data.csv and saves
the model, encoders, and feature importances for the dashboard to reuse.
Run generate_data.py first.
"""

import pandas as pd
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score

DATA_PATH = "data/ner_landslide_data.csv"
MODEL_DIR = "model"

FEATURES_NUMERIC = [
    "elevation_m", "slope_angle_deg", "soil_moisture_pct",
    "rainfall_last_7d_mm", "rainfall_last_30d_mm", "vegetation_cover_pct",
    "historical_landslide_count", "nearby_population",
]
FEATURES_CATEGORICAL = ["state", "location_type"]


def main():
    df = pd.read_csv(DATA_PATH)

    encoders = {}
    df_encoded = df.copy()
    for col in FEATURES_CATEGORICAL:
        le = LabelEncoder()
        df_encoded[col + "_enc"] = le.fit_transform(df[col])
        encoders[col] = le

    feature_cols = FEATURES_NUMERIC + [c + "_enc" for c in FEATURES_CATEGORICAL]
    X = df_encoded[feature_cols]
    y = df_encoded["high_risk_alert"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=7, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=200, max_depth=8, random_state=7, class_weight="balanced"
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    proba = model.predict_proba(X_test)[:, 1]

    print("=== Model evaluation ===")
    print(f"Accuracy: {accuracy_score(y_test, preds):.3f}")
    print(f"ROC-AUC:  {roc_auc_score(y_test, proba):.3f}")
    print(classification_report(y_test, preds, target_names=["Normal", "High risk"]))

    importances = pd.Series(
        model.feature_importances_, index=feature_cols
    ).sort_values(ascending=False)
    print("=== Feature importances (what drives landslide risk) ===")
    print(importances.round(3).to_string())

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, f"{MODEL_DIR}/risk_model.pkl")
    joblib.dump(encoders, f"{MODEL_DIR}/encoders.pkl")
    joblib.dump(feature_cols, f"{MODEL_DIR}/feature_cols.pkl")
    joblib.dump(importances, f"{MODEL_DIR}/feature_importances.pkl")
    print(f"\nSaved model + encoders to {MODEL_DIR}/")


if __name__ == "__main__":
    main()
