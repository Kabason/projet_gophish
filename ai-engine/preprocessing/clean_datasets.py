"""
clean_datasets.py

Cleans the Enron (ham) and Nazario (real historic phishing) CSVs from
the Kaggle "Phishing Email Dataset" (Naser Abdullah Alam) into a single
normalized file: columns text, label, type, language.

Uses the two SEPARATE source files (Enron.csv, Nazario.csv), not the
combined phishing_email.csv - the combined file also pools in CEAS_08,
Ling, Nigerian_Fraud and SpamAssassin, which this project's 30/40/30
recipe (Enron ham / Nazario phishing / AI phishing) doesn't call for.

Manual step before running this:
  1. Download "Phishing Email Dataset" by Naser Abdullah Alam from
     kaggle.com and extract the zip.
  2. Place the two files at:
     data/raw/Enron.csv
     data/raw/Nazario.csv

Usage:
    python clean_datasets.py
"""

import sys
from pathlib import Path

import pandas as pd
from langdetect import detect

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
ENRON_PATH = RAW_DIR / "Enron.csv"
NAZARIO_PATH = RAW_DIR / "Nazario.csv"
OUTPUT_PATH = RAW_DIR / "enron_nazario_clean.csv"

# Common text-column names seen across this dataset's per-source files.
# If detection fails below, the script prints the real columns so you
# can add the right one here - same advice the project guide gives.
CANDIDATE_TEXT_COLUMNS = ["text_combined", "text", "body", "Body", "email", "content", "Text"]


def detect_lang_safe(text: str) -> str:
    try:
        return detect(str(text)[:500])
    except Exception:
        return "unknown"


def find_text_column(df: pd.DataFrame, source_name: str) -> str:
    for col in CANDIDATE_TEXT_COLUMNS:
        if col in df.columns:
            return col
    print(f"[error] Could not auto-detect a text column in {source_name}.")
    print(f"        Columns found: {df.columns.tolist()}")
    print("        Add the correct one to CANDIDATE_TEXT_COLUMNS above and rerun.")
    sys.exit(1)


def load_source(path: Path, fixed_label: int, type_name: str) -> pd.DataFrame:
    if not path.exists():
        print(f"[error] {path} not found.")
        sys.exit(1)

    df_raw = pd.read_csv(path)
    print(f"{path.name} columns: {df_raw.columns.tolist()} ({len(df_raw)} rows)")

    text_col = find_text_column(df_raw, path.name)
    df = df_raw.rename(columns={text_col: "text"})[["text"]].dropna()
    df["label"] = fixed_label
    df["type"] = type_name
    return df


def main():
    df_ham = load_source(ENRON_PATH, fixed_label=0, type_name="enron_ham")
    df_phish = load_source(NAZARIO_PATH, fixed_label=1, type_name="nazario_real_phishing")

    df_clean = pd.concat([df_ham, df_phish], ignore_index=True)

    print("\nDetecting language (niveau 1 traceability - can take a minute)...")
    df_clean["language"] = df_clean["text"].apply(detect_lang_safe)

    df_clean.to_csv(OUTPUT_PATH, index=False)

    print("\nLabel distribution:")
    print(df_clean["label"].value_counts())
    print("\nLanguage distribution (top 5):")
    print(df_clean["language"].value_counts().head(5))
    print(f"\nSaved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()