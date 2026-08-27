"""
nlp_pipeline.py

Text cleaning / normalization for the hybrid phishing dataset.
Import clean_text() from other scripts, or run this file directly to
preprocess data/processed/dataset_hybride_phishing_2026.csv into
dataset_hybride_preprocessed.csv.

Also strips known corpus-identity leakage found via SHAP analysis:
the model was partly learning to fingerprint WHICH SOURCE FILE an
email came from rather than genuine phishing/ham content.
  - "ect" / "hou": Enron corpus internal routing/division codes that
    appear across a huge share of Enron emails' headers/signatures -
    an artifact of the corpus, not a property of legitimate email.
  - "enron": the corpus's own company name leaking in as a ham
    predictor.
  - bare domain mentions like "monkey.org" (the Nazario corpus's own
    archive source URL) leaking into email bodies as a phishing
    predictor, even without a "http://" prefix to catch it.

Usage:
    python nlp_pipeline.py
"""

import re
from pathlib import Path

import nltk
import pandas as pd
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

for resource, path in [
    ("stopwords", "corpora/stopwords"),
    ("wordnet", "corpora/wordnet"),
    ("punkt", "tokenizers/punkt"),
    ("punkt_tab", "tokenizers/punkt_tab"),
]:
    try:
        nltk.data.find(path)
    except LookupError:
        nltk.download(resource, quiet=True)

LEMMATIZER = WordNetLemmatizer()

# Corpus-identity artifacts identified via SHAP - not phishing/ham signal,
# just tells about which source file the row came from. See docstring.
CORPUS_LEAKAGE_TOKENS = {
    "enron", "ect", "hou",           # Enron corpus header/routing artifacts
    "vince", "kaminski",             # Enron corpus is dominated by Vince Kaminski's mailbox -
                                      # a well-documented artifact of this specific dataset
    "jose", "nazario", "monkey",     # Nazario corpus citation (Jose Nazario / monkey.org)
    "com", "org",                    # leftover bare-domain fragments as a safety net
}

STOP_WORDS = set(stopwords.words("english")) | set(stopwords.words("french")) | CORPUS_LEAKAGE_TOKENS

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
INPUT_PATH = PROCESSED_DIR / "dataset_hybride_phishing_2026.csv"
OUTPUT_PATH = PROCESSED_DIR / "dataset_hybride_preprocessed.csv"


def clean_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"http\S+|www\S+", " URLTOKEN ", text)
    # Bare domain mentions without a protocol prefix, INCLUDING any trailing
    # URL path (e.g. "monkey.org/~jose/phishing/fraud123.html" - without this,
    # only "monkey.org" gets stripped and "jose"/"phishing"/"html" leak through
    # as ordinary word tokens, which is what happened on the first pass).
    text = re.sub(r"\b[a-z0-9-]+\.(com|org|net|fr|gov|edu|info)(/\S*)?", " URLTOKEN ", text)
    text = re.sub(r"\S+@\S+", " EMAILTOKEN ", text)
    text = re.sub(r"[^a-zàâäéèêëïîôöùûüç\s]", " ", text)
    tokens = word_tokenize(text)
    tokens = [LEMMATIZER.lemmatize(t) for t in tokens if t not in STOP_WORDS and len(t) > 2]
    return " ".join(tokens)


def main():
    if not INPUT_PATH.exists():
        print(f"[error] {INPUT_PATH} not found. Run build_hybrid_dataset.py first.")
        return

    df = pd.read_csv(INPUT_PATH)
    df["clean_text"] = df["text"].apply(clean_text)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved: {OUTPUT_PATH} ({len(df)} rows)")


if __name__ == "__main__":
    main()