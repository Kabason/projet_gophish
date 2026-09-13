"""
robustness_analysis.py

The project's central result: accuracy broken down by data type
(enron_ham / nazario_real_phishing / ai_phishing_2026), by language,
and - for the AI-generated emails specifically - by psychological
tactic.

Uses ACCURACY per subset, not F1. F1-for-the-positive-class is
mathematically undefined/near-zero on a subset that is entirely one
class (e.g. enron_ham is 100% label=0), regardless of how well the
model actually performs - it would report ~0 even for a perfect
model. Accuracy (fraction correctly classified) is well-defined
whether the subset is pure or mixed, and for a pure-positive subset
it's equivalent to recall/detection rate.

IMPORTANT: the tactic breakdown below is computed on the TEST SPLIT
ONLY (not the full dataset). Evaluating on the full dataset would
include AI-phishing rows the model already saw during training,
inflating detection rates through memorization rather than genuine
generalization. The trade-off: with ~175 AI-phishing rows total,
the test split leaves only ~35 rows spread across 5 tactics (a
handful per tactic) - small sample sizes, documented as a limitation
rather than papered over with a larger but leaked evaluation set.

Run this after train_models.py.

Usage:
    python robustness_analysis.py
"""

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
MODELS_DIR = Path(__file__).resolve().parent / "saved"
INPUT_PATH = PROCESSED_DIR / "dataset_hybride_preprocessed.csv"


def accuracy_breakdown(df_test: pd.DataFrame, group_col: str, model_names: list[str]) -> dict:
    breakdown = {}
    for name in model_names:
        breakdown[name] = {}
        for g in df_test[group_col].dropna().unique():
            subset = df_test[df_test[group_col] == g]
            if len(subset) == 0:
                continue
            acc = (subset["true"] == subset[f"pred_{name}"]).mean()
            breakdown[name][str(g)] = {"accuracy": round(acc, 3), "n": int(len(subset))}
    return breakdown


def main():
    if not INPUT_PATH.exists() or not (MODELS_DIR / "all_models.pkl").exists():
        print("[error] Missing preprocessed dataset or trained models. Run nlp_pipeline.py and train_models.py first.")
        return

    df = pd.read_csv(INPUT_PATH).dropna(subset=["clean_text"])
    vectorizer = joblib.load(MODELS_DIR / "vectorizer_final.pkl")
    best_models = joblib.load(MODELS_DIR / "all_models.pkl")

    X = vectorizer.transform(df["clean_text"])
    y = df["label"]

    # Same split as train_models.py (identical random_state + stratify -> identical test set)
    _, X_test, _, y_test, train_idx, test_idx = train_test_split(
        X, y, df.index, test_size=0.2, random_state=42, stratify=y
    )

    df_test = df.loc[test_idx, ["type", "language", "tactic"]].copy()
    df_test["true"] = y_test.values
    for name, model in best_models.items():
        df_test[f"pred_{name}"] = model.predict(X_test)

    model_names = list(best_models.keys())

    print("=== Accuracy by data type ===")
    acc_by_type = accuracy_breakdown(df_test, "type", model_names)
    for name in model_names:
        print(f"\n{name}:")
        for t, stats in acc_by_type[name].items():
            print(f"  {t}: accuracy = {stats['accuracy']:.3f} (n={stats['n']})")

    print("\n=== Accuracy by language ===")
    acc_by_language = accuracy_breakdown(df_test, "language", model_names)
    for name in model_names:
        print(f"\n{name}:")
        for lang, stats in sorted(acc_by_language[name].items(), key=lambda kv: -kv[1]["n"])[:5]:
            print(f"  {lang}: accuracy = {stats['accuracy']:.3f} (n={stats['n']})")

    # Detectability by psychological tactic, on the TEST SPLIT ONLY - see module
    # docstring for why this matters (avoids memorization inflating the result)
    detection_by_tactic = {}
    best_name = max(
        model_names,
        key=lambda n: (df_test["true"] == df_test[f"pred_{n}"]).mean(),
    )
    df_ai_test = df_test[df_test["type"] == "ai_phishing_2026"]
    if len(df_ai_test) > 0:
        print(f"\n=== Detection rate by tactic on TEST SPLIT ONLY (best model: {best_name}) ===")
        print(f"[note] n total AI-phishing in test split: {len(df_ai_test)} - small samples per tactic, interpret with caution")
        for tactic in df_ai_test["tactic"].dropna().unique():
            subset = df_ai_test[df_ai_test["tactic"] == tactic]
            taux_detection = (subset[f"pred_{best_name}"] == 1).mean() * 100
            detection_by_tactic[tactic] = {"rate": round(taux_detection, 1), "n": int(len(subset))}
            print(f"  {tactic}: {taux_detection:.1f}% detected (n={len(subset)})")
    else:
        print("\n[info] No AI-phishing rows in the test split - tactic breakdown skipped.")

    report = {
        "best_model": best_name,
        "accuracy_by_type": acc_by_type,
        "accuracy_by_language": acc_by_language,
        "detection_rate_by_tactic": detection_by_tactic,
        "detection_by_tactic_methodology": "computed on test split only, not full dataset - see module docstring",
    }
    with open(MODELS_DIR / "robustness_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved: {MODELS_DIR / 'robustness_report.json'}")


if __name__ == "__main__":
    main()