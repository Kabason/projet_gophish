"""
train_models.py

Trains and compares Naive Bayes, Random Forest, and Logistic Regression
on the preprocessed hybrid dataset, with stratified cross-validation and
hyperparameter search. Saves the best-performing model + vectorizer for
the API and the demo dashboard.

Usage:
    python train_models.py
"""

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score, precision_score, recall_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.naive_bayes import MultinomialNB

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
MODELS_DIR = Path(__file__).resolve().parent / "saved"
INPUT_PATH = PROCESSED_DIR / "dataset_hybride_preprocessed.csv"

PARAM_GRIDS = {
    "naive_bayes": (MultinomialNB(), {"alpha": [0.1, 0.5, 1.0]}),
    "random_forest": (RandomForestClassifier(random_state=42), {"n_estimators": [100, 200], "max_depth": [None, 20]}),
    "logistic_regression": (LogisticRegression(max_iter=1000), {"C": [0.1, 1.0, 10.0]}),
}


def main():
    if not INPUT_PATH.exists():
        print(f"[error] {INPUT_PATH} not found. Run nlp_pipeline.py first.")
        return

    df = pd.read_csv(INPUT_PATH).dropna(subset=["clean_text"])

    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
    X = vectorizer.fit_transform(df["clean_text"])
    y = df["label"]

    X_train, X_test, y_train, y_test, type_train, type_test = train_test_split(
        X, y, df["type"], test_size=0.2, random_state=42, stratify=y
    )

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    best_models, results = {}, {}
    for name, (model, params) in PARAM_GRIDS.items():
        grid = GridSearchCV(model, params, cv=cv, scoring="f1", n_jobs=-1)
        grid.fit(X_train, y_train)
        best_models[name] = grid.best_estimator_

        y_pred = grid.best_estimator_.predict(X_test)
        results[name] = {
            "best_params": grid.best_params_,
            "precision": precision_score(y_test, y_pred),
            "recall": recall_score(y_test, y_pred),
            "f1": f1_score(y_test, y_pred),
        }
        print(f"\n--- {name} ({grid.best_params_}) ---")
        print(classification_report(y_test, y_pred))

    best_name = max(results, key=lambda n: results[n]["f1"])
    print(f"\nBest model: {best_name} (F1={results[best_name]['f1']:.3f})")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_models[best_name], MODELS_DIR / "model_final.pkl")
    joblib.dump(vectorizer, MODELS_DIR / "vectorizer_final.pkl")
    joblib.dump(best_models, MODELS_DIR / "all_models.pkl")

    with open(MODELS_DIR / "results.json", "w") as f:
        json.dump({"best_model": best_name, "results": results}, f, indent=2)

    print(f"\nSaved model, vectorizer, and results to {MODELS_DIR}")


if __name__ == "__main__":
    main()
