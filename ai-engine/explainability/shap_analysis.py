"""
shap_analysis.py

SHAP explainability for the logistic regression model - which words push
the classifier toward "phishing".

Usage:
    python shap_analysis.py
"""

from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
import shap
from sklearn.model_selection import train_test_split

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
MODELS_DIR = Path(__file__).resolve().parents[1] / "models" / "saved"
OUTPUT_DIR = Path(__file__).resolve().parent
INPUT_PATH = PROCESSED_DIR / "dataset_hybride_preprocessed.csv"


def main():
    all_models_path = MODELS_DIR / "all_models.pkl"
    if not INPUT_PATH.exists() or not all_models_path.exists():
        print("[error] Missing preprocessed dataset or trained models. Run train_models.py first.")
        return

    df = pd.read_csv(INPUT_PATH).dropna(subset=["clean_text"])
    vectorizer = joblib.load(MODELS_DIR / "vectorizer_final.pkl")
    best_models = joblib.load(all_models_path)

    if "logistic_regression" not in best_models:
        print("[error] No logistic_regression model found in all_models.pkl.")
        return

    X = vectorizer.transform(df["clean_text"])
    y = df["label"]
    X_train, X_test, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    explainer = shap.LinearExplainer(
        best_models["logistic_regression"], X_train, feature_names=vectorizer.get_feature_names_out()
    )
    X_sample = X_test[:100]
    shap_values = explainer.shap_values(X_sample)

    # Dense array for the sample - sparse input here silently breaks
    # SHAP's color-by-feature-value scale (the grey/uncolored dots issue).
    shap.summary_plot(
        shap_values, X_sample.toarray(), feature_names=vectorizer.get_feature_names_out(), show=False
    )
    plt.tight_layout()
    output_path = OUTPUT_DIR / "shap_summary.png"
    plt.savefig(output_path, dpi=200)
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()