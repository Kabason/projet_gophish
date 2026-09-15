"""
build_hybrid_dataset.py

Merges Enron ham, Nazario real phishing, and the AI-generated phishing
emails into the final hybrid training dataset (30/40/30 target ratio).

Runs fine even if ai_generated_phishing.csv does not exist yet - it
builds an Enron/Nazario-only dataset in that case and warns you.

Optionally also folds in a small block of AI-generated FRENCH HAM
(ham_francais.csv, same columns as ai_generated_phishing.csv but
legitimate content) if that file exists, to break the language
confound (currently all French text in the dataset is phishing).
This is purely additive - it doesn't touch the 30/40/30 ratio, it
adds a bonus block on top. Safe to leave absent; the script just
warns and continues without it.

Usage:
    python build_hybrid_dataset.py --total 1000
"""

import argparse
from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"

CLEAN_PATH = RAW_DIR / "enron_nazario_clean.csv"
AI_PATH = RAW_DIR / "ai_generated_phishing.csv"       # written by generate_emails.py
HAM_FR_PATH = RAW_DIR / "ham_francais.csv"             # optional - subject,body columns, legitimate French email
OUTPUT_PATH = PROCESSED_DIR / "dataset_hybride_phishing_2026.csv"

RATIO_HAM, RATIO_PHISH_REAL, RATIO_PHISH_AI = 0.30, 0.40, 0.30
RANDOM_STATE = 42


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--total", type=int, default=1000, help="Target total dataset size")
    args = parser.parse_args()

    if not CLEAN_PATH.exists():
        print(f"[error] {CLEAN_PATH} not found. Run clean_datasets.py first.")
        return

    df_source = pd.read_csv(CLEAN_PATH)
    df_ham = df_source[df_source["label"] == 0]
    df_phish_real = df_source[df_source["label"] == 1]

    if AI_PATH.exists():
        df_ai_raw = pd.read_csv(AI_PATH)
        df_ai = pd.DataFrame(
            {
                "text": df_ai_raw["subject"] + "\n" + df_ai_raw["body"],
                "label": 1,
                "type": "ai_phishing_2026",
                "tactic": df_ai_raw["tactic"],
                "language": "fr",  # known by construction - the generation prompt requires French
            }
        )
    else:
        print(f"[warn] {AI_PATH} not found - building an Enron/Nazario-only dataset for now.")
        print("[warn] Re-run this script after generate_emails.py to get the full 30/40/30 mix.")
        df_ai = pd.DataFrame(columns=["text", "label", "type", "tactic", "language"])

    n_ham = int(args.total * RATIO_HAM)
    n_phish_real = int(args.total * RATIO_PHISH_REAL)
    n_ai = min(len(df_ai), int(args.total * RATIO_PHISH_AI))

    df_ham_sample = df_ham.sample(n=min(n_ham, len(df_ham)), random_state=RANDOM_STATE)
    df_phish_real_sample = df_phish_real.sample(n=min(n_phish_real, len(df_phish_real)), random_state=RANDOM_STATE)
    df_ai_sample = df_ai.sample(n=n_ai, random_state=RANDOM_STATE) if n_ai > 0 else df_ai

    parts = [df_ham_sample, df_phish_real_sample, df_ai_sample]

    if HAM_FR_PATH.exists():
        df_ham_fr_raw = pd.read_csv(HAM_FR_PATH)
        df_ham_fr = pd.DataFrame(
            {
                "text": df_ham_fr_raw["subject"] + "\n" + df_ham_fr_raw["body"],
                "label": 0,
                "type": "ham_francais_ia",
                "tactic": None,
                "language": "fr",
            }
        )
        parts.append(df_ham_fr)
        print(f"[info] Added {len(df_ham_fr)} French ham rows from {HAM_FR_PATH.name}.")
    else:
        print(f"[warn] {HAM_FR_PATH} not found - dataset will keep the French/phishing language confound.")
        print("[warn] Optional: generate a small legitimate-French-email block to close this gap.")

    final_dataset = pd.concat(parts, ignore_index=True)
    final_dataset = final_dataset.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    final_dataset.to_csv(OUTPUT_PATH, index=False)

    print("\nHybrid dataset built:")
    print(final_dataset["type"].value_counts())
    print(f"\nSaved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()