"""
main.py

FastAPI serving layer for the phishing detector - replaces the
Streamlit demo suggested in the original guide. Consumed by the
Next.js dashboard (dashboard/).

Usage:
    uvicorn main:app --reload --port 8000
"""

import json
import sys
from pathlib import Path

import joblib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Make the shared nlp_pipeline module importable without packaging it
sys.path.append(str(Path(__file__).resolve().parents[1] / "preprocessing"))
from nlp_pipeline import clean_text  # noqa: E402

MODELS_DIR = Path(__file__).resolve().parents[1] / "models" / "saved"

app = FastAPI(title="Phishing Detector API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_model = None
_vectorizer = None


def get_model():
    global _model, _vectorizer
    if _model is None:
        model_path = MODELS_DIR / "model_final.pkl"
        vectorizer_path = MODELS_DIR / "vectorizer_final.pkl"
        if not model_path.exists() or not vectorizer_path.exists():
            raise HTTPException(status_code=503, detail="Model not trained yet. Run train_models.py first.")
        _model = joblib.load(model_path)
        _vectorizer = joblib.load(vectorizer_path)
    return _model, _vectorizer


class PredictRequest(BaseModel):
    email_text: str


class PredictResponse(BaseModel):
    prediction: str
    confidence: float


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    model, vectorizer = get_model()
    cleaned = clean_text(request.email_text)
    X = vectorizer.transform([cleaned])
    pred = model.predict(X)[0]
    proba = model.predict_proba(X)[0]
    label = "phishing" if pred == 1 else "legitimate"
    confidence = float(proba[1] if pred == 1 else proba[0])
    return PredictResponse(prediction=label, confidence=confidence)


@app.get("/metrics")
def metrics():
    results_path = MODELS_DIR / "results.json"
    robustness_path = MODELS_DIR / "robustness_report.json"

    if not results_path.exists():
        raise HTTPException(status_code=503, detail="No results yet. Run train_models.py first.")

    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    robustness = {}
    if robustness_path.exists():
        with open(robustness_path, "r", encoding="utf-8") as f:
            robustness = json.load(f)

    return {"model_results": results, "robustness": robustness}
