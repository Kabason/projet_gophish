"""
build_hybrid_dataset.py

Merges Enron ham, Nazario real phishing, and (once available) the
AI-generated phishing emails into the final hybrid training dataset.

Runs fine even if ai_generated_phishing.csv does not exist yet - it
builds an Enron/Nazario-only dataset in that case and warns you, so
you can validate the rest of the pipeline before the Ollama step is
done. Re-run this once the AI CSV exists to get the full 30/40/30 mix.

Usage:
    python build_hybrid_dataset.py --total 1000
"""

import argparse
from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"

CLEAN_PATH = RAW_DIR / "enron_nazario_clean.csv"
AI_PATH = RAW_DIR / "ai_generated_phishing.csv"  # written by generate_emails.py
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

    has_ai_data = AI_PATH.exists()
    if has_ai_data:
        df_ai_raw = pd.read_csv(AI_PATH)
        df_ai = pd.DataFrame(
            {
                "text": df_ai_raw["subject"] + "\n" + df_ai_raw["body"],
                "label": 1,
                "type": "ai_phishing_2026",
                "tactic": df_ai_raw["tactic"],
                # Known by construction - the generation prompt requires French,
                # so no need to run langdetect on it. Keeps the language column
                # complete for robustness_analysis.py's per-language breakdown.
                "language": "fr",
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

    final_dataset = pd.concat([df_ham_sample, df_phish_real_sample, df_ai_sample], ignore_index=True)
    final_dataset = final_dataset.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    final_dataset.to_csv(OUTPUT_PATH, index=False)

    print("\nHybrid dataset built:")
    print(final_dataset["type"].value_counts())
    print(f"\nSaved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()