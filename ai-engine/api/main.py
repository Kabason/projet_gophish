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
from typing import Literal

import joblib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Make the shared nlp_pipeline module importable without packaging it
sys.path.append(str(Path(__file__).resolve().parents[1] / "preprocessing"))
from nlp_pipeline import clean_text  # noqa: E402

MODELS_DIR = Path(__file__).resolve().parents[1] / "models" / "saved"

app = FastAPI(title="Phishing Detector API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_model = None
_vectorizer = None
_all_models = None


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


def get_all_models():
    global _all_models
    if _all_models is None:
        path = MODELS_DIR / "all_models.pkl"
        if not path.exists():
            raise HTTPException(status_code=503, detail="Models not trained yet. Run train_models.py first.")
        _all_models = joblib.load(path)
    return _all_models


class PredictRequest(BaseModel):
    email_text: str


class FeatureContribution(BaseModel):
    term: str
    weight: float
    direction: Literal["phishing", "legitimate"]


class ModelVote(BaseModel):
    model: str
    prediction: Literal["phishing", "legitimate"]
    confidence: float


class PredictResponse(BaseModel):
    prediction: Literal["phishing", "legitimate"]
    confidence: float
    model_used: str
    top_features: list[FeatureContribution]
    model_comparison: list[ModelVote]


def explain_with_logistic_regression(cleaned_text: str, vectorizer, all_models, top_n: int = 8):
    """
    Per-prediction explanation: for a LINEAR model, each feature's
    contribution to the decision is simply (its TF-IDF value in this
    email) x (its learned coefficient). This is cheap enough to compute
    on every request, unlike a live SHAP explainer, and is exact for a
    linear model - it's the same underlying logic as the offline SHAP
    analysis, just computed directly rather than via the shap library.

    Always explains via logistic_regression specifically, regardless of
    which model is used for the headline prediction, so the explanation
    stays consistent with the project's SHAP analysis chapter.
    """
    lr_model = all_models.get("logistic_regression")
    if lr_model is None or not hasattr(lr_model, "coef_"):
        return []

    X = vectorizer.transform([cleaned_text])
    coef = lr_model.coef_[0]
    feature_names = vectorizer.get_feature_names_out()

    contributions = [(feature_names[i], float(X[0, i] * coef[i])) for i in X.nonzero()[1]]
    contributions.sort(key=lambda item: abs(item[1]), reverse=True)

    return [
        FeatureContribution(
            term=term,
            weight=round(weight, 4),
            direction="phishing" if weight > 0 else "legitimate",
        )
        for term, weight in contributions[:top_n]
    ]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    model, vectorizer = get_model()
    all_models = get_all_models()
    cleaned = clean_text(request.email_text)
    X = vectorizer.transform([cleaned])

    pred = model.predict(X)[0]
    proba = model.predict_proba(X)[0]
    label = "phishing" if pred == 1 else "legitimate"
    confidence = float(proba[1] if pred == 1 else proba[0])
    model_used = type(model).__name__

    top_features = explain_with_logistic_regression(cleaned, vectorizer, all_models)

    model_comparison = []
    for name, m in all_models.items():
        m_pred = m.predict(X)[0]
        m_proba = m.predict_proba(X)[0]
        model_comparison.append(
            ModelVote(
                model=name,
                prediction="phishing" if m_pred == 1 else "legitimate",
                confidence=round(float(m_proba[1] if m_pred == 1 else m_proba[0]), 4),
            )
        )

    return PredictResponse(
        prediction=label,
        confidence=confidence,
        model_used=model_used,
        top_features=top_features,
        model_comparison=model_comparison,
    )


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