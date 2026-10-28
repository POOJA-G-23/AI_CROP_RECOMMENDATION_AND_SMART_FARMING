"""
retrain_model.py
================
Re-trains the Random Forest model using:
  1. Original dataset  (dataset/crop_dataset.csv)
  2. Community feedback data from MongoDB (community_data collection)

Run this periodically to improve prediction accuracy with real farmer data.

Usage:
  python retrain_model.py
"""

import pandas as pd
import numpy as np
import joblib, os, json
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report

DATASET_PATH  = "dataset/crop_dataset.csv"
MODEL_PATH    = "../model/crop_model.pkl"
SCALER_PATH   = "../model/scaler.pkl"
FEATURES      = ["N","P","K","temperature","humidity","ph","rainfall"]
LABEL         = "label"

# ── Load original dataset ─────────────────────────────────────────────────────
print("Loading original dataset...")
df = pd.read_csv(DATASET_PATH)
# Normalise column names
df.columns = [c.strip().lower() for c in df.columns]
if "crop" in df.columns and LABEL not in df.columns:
    df.rename(columns={"crop": LABEL}, inplace=True)
print(f"  Original rows: {len(df)}")
print(f"  Crops: {sorted(df[LABEL].unique())}")

# ── Load community data from MongoDB ─────────────────────────────────────────
community_rows = []
try:
    from pymongo import MongoClient
    import os
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    db = client["ai_crop_advisor"]
    docs = list(db["community_data"].find(
        {"actual_crop": {"$ne": None}, "N": {"$ne": None}},
        {"_id":0, "N":1, "P":1, "K":1, "temperature":1, "humidity":1,
         "ph":1, "rainfall":1, "actual_crop":1}
    ))
    for d in docs:
        if all(d.get(f) is not None for f in FEATURES) and d.get("actual_crop"):
            community_rows.append({
                "n": d["N"], "p": d["P"], "k": d["K"],
                "temperature": d["temperature"], "humidity": d["humidity"],
                "ph": d["ph"], "rainfall": d["rainfall"],
                LABEL: d["actual_crop"]
            })
    print(f"  Community rows from MongoDB: {len(community_rows)}")
except Exception as e:
    print(f"  MongoDB not available: {e} — training on original data only")

# ── Combine datasets ──────────────────────────────────────────────────────────
if community_rows:
    df_community = pd.DataFrame(community_rows)
    df = pd.concat([df, df_community], ignore_index=True)
    print(f"  Combined total rows: {len(df)}")

# ── Clean data ────────────────────────────────────────────────────────────────
df = df.dropna(subset=FEATURES + [LABEL])
df = df[df["n"] < 300]
df = df[df["ph"].between(3, 11)]
df = df[df["temperature"].between(0, 55)]
print(f"  After cleaning: {len(df)} rows")
print(f"  Class distribution:\n{df[LABEL].value_counts().to_string()}")

# ── Prepare features ──────────────────────────────────────────────────────────
X = df[["n","p","k","temperature","humidity","ph","rainfall"]].values
y = df[LABEL].values

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ── Scale ─────────────────────────────────────────────────────────────────────
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s  = scaler.transform(X_test)

# ── Train ─────────────────────────────────────────────────────────────────────
print("\nTraining Random Forest...")
model = RandomForestClassifier(
    n_estimators=150,
    max_depth=None,
    min_samples_split=2,
    random_state=42,
    n_jobs=-1
)
model.fit(X_train_s, y_train)

# ── Evaluate ──────────────────────────────────────────────────────────────────
y_pred = model.predict(X_test_s)
acc    = accuracy_score(y_test, y_pred)
print(f"\n{'='*50}")
print(f"  Accuracy  : {acc*100:.2f}%")
print(f"  Train size: {len(X_train)}")
print(f"  Test size : {len(X_test)}")
print(f"{'='*50}")
print("\nPer-crop report:")
print(classification_report(y_test, y_pred))

# ── Save ──────────────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
joblib.dump(model,  MODEL_PATH)
joblib.dump(scaler, SCALER_PATH)
print(f"✅ Model saved  → {MODEL_PATH}")
print(f"✅ Scaler saved → {SCALER_PATH}")
print("\nRe-training complete!")
