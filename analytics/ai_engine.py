import pandas as pd
import joblib
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from django.utils import timezone
from token_queue.models import Token
import os

MODEL_PATH = "analytics/model.pkl"

# ==========================================
# FEATURE ENGINEERING
# ==========================================
def build_features(tokens):
    data = []

    for t in tokens:
        dt = t.booked_at

        data.append({
            "day": dt.weekday(),
            "hour": dt.hour,
            "is_weekend": 1 if dt.weekday() >= 5 else 0,
            "month": dt.month,
        })

    return pd.DataFrame(data)


# ==========================================
# TRAIN MODEL
# ==========================================
def train_model(hospital):

    tokens = Token.objects.filter(hospital=hospital)

    if tokens.count() < 20:
        return None  # not enough data

    df = build_features(tokens)

    df["count"] = 1
    df = df.groupby(["day", "hour", "is_weekend", "month"]).count().reset_index()

    X = df[["day", "hour", "is_weekend", "month"]]
    y = df["count"]

    model = RandomForestRegressor(n_estimators=100)
    model.fit(X, y)

    joblib.dump(model, MODEL_PATH)

    return model


# ==========================================
# LOAD MODEL
# ==========================================
def load_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return None


# ==========================================
# PREDICT
# ==========================================
def predict_rush(hospital):

    model = load_model()

    if not model:
        model = train_model(hospital)

    if not model:
        return None

    today = datetime.now()

    predictions = []

    for hour in range(9, 21):

        features = pd.DataFrame([{
            "day": today.weekday(),
            "hour": hour,
            "is_weekend": 1 if today.weekday() >= 5 else 0,
            "month": today.month
        }])

        pred = model.predict(features)[0]

        predictions.append((hour, int(pred)))

    best_hour = min(predictions, key=lambda x: x[1])[0]
    worst_hour = max(predictions, key=lambda x: x[1])[0]

    total_load = sum([p[1] for p in predictions])

    return {
        "total_load": total_load,
        "best_hour": best_hour,
        "peak_hour": worst_hour
    }