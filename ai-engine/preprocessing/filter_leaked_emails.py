"""
filter_leaked_emails.py

Filtre les emails generes par le LLM ou le modele a recopie le contexte
du prompt (meta-fuite) plutot que de generer un vrai contenu de phishing.
Probleme observe avec llama3.2:1b (instruction-following faible sur petit modele).
"""

import re
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
INPUT_PATH = DATA_DIR / "ai_generated_phishing.csv"
INPUT_FULL_PATH = DATA_DIR / "ai_generated_phishing_full.csv"
OUTPUT_PATH = DATA_DIR / "ai_generated_phishing_clean.csv"
OUTPUT_FULL_PATH = DATA_DIR / "ai_generated_phishing_full_clean.csv"

META_LEAK_PATTERNS = [
    r"\(urgence\)", r"\(autorité\)", r"\(autorite\)", r"\(curiosité\)", r"\(curiosite\)",
    r"\(réciprocité\)", r"\(reciprocite\)", r"\(routine\)",
    r"tactique (de |d')", r"technique (de |d')", r"stratégie (de |d')",
    r"psychologique", r"ingénierie sociale", r"simulation de sécurité",
    r"pfe universitaire", r"lab isolé", r"exercice académique",
]


def is_leaked(row_text: str) -> bool:
    text = row_text.lower()
    return any(re.search(pattern, text) for pattern in META_LEAK_PATTERNS)


def filter_file(input_path: Path, output_path: Path, text_cols: list[str]) -> None:
    df = pd.read_csv(input_path)
    combined = df[text_cols].astype(str).agg(" ".join, axis=1)
    leak_mask = combined.apply(is_leaked)

    df_clean = df[~leak_mask].reset_index(drop=True)

    print(f"{input_path.name} : {len(df)} -> {len(df_clean)} apres filtrage ({leak_mask.sum()} fuites retirees)")
    print(df_clean["tactic"].value_counts() if "tactic" in df_clean.columns else "")

    df_clean.to_csv(output_path, index=False)


if __name__ == "__main__":
    filter_file(INPUT_PATH, OUTPUT_PATH, ["subject", "body"])
    filter_file(INPUT_FULL_PATH, OUTPUT_FULL_PATH, ["subject", "body"])
    print(f"\nFichiers propres ecrits :\n  {OUTPUT_PATH}\n  {OUTPUT_FULL_PATH}")