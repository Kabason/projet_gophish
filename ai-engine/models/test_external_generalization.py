"""
test_external_generalization.py

Teste le modele sur un jeu d'emails totalement externe au pipeline
d'entrainement (ni Enron, ni Nazario, ni notre IA) - une vraie mesure
de generalisation, distincte du test set habituel qui reste dans la
meme distribution que le train.

clean_text() est copiee ICI directement depuis preprocessing/nlp_pipeline.py
(comme suggere en commentaire dans la version originale de ce script) plutot
que importee - evite toute fragilite liee a l'emplacement exact du fichier
par rapport a preprocessing/. Si nlp_pipeline.py est modifie plus tard,
reporter le changement ici aussi.

Usage:
    python test_external_generalization.py
"""

import json
import re
from pathlib import Path

import joblib
import nltk
import pandas as pd
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sklearn.metrics import classification_report, confusion_matrix

MODELS_DIR = Path(__file__).resolve().parent / "saved"
DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "raw" / "external_test_emails.csv"

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
CORPUS_LEAKAGE_TOKENS = {
    "enron", "ect", "hou",
    "vince", "kaminski",
    "jose", "nazario", "monkey",
    "com", "org",
}
STOP_WORDS = set(stopwords.words("english")) | set(stopwords.words("french")) | CORPUS_LEAKAGE_TOKENS


def clean_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"http\S+|www\S+", " URLTOKEN ", text)
    text = re.sub(r"\b[a-z0-9-]+\.(com|org|net|fr|gov|edu|info)(/\S*)?", " URLTOKEN ", text)
    text = re.sub(r"\S+@\S+", " EMAILTOKEN ", text)
    text = re.sub(r"[^a-zàâäéèêëïîôöùûüç\s]", " ", text)
    tokens = word_tokenize(text)
    tokens = [LEMMATIZER.lemmatize(t) for t in tokens if t not in STOP_WORDS and len(t) > 2]
    return " ".join(tokens)


def main():
    if not DATA_PATH.exists():
        print(f"[error] {DATA_PATH} not found. Create it first (see directives).")
        return

    df = pd.read_csv(DATA_PATH)
    vectorizer = joblib.load(MODELS_DIR / "vectorizer_final.pkl")
    model = joblib.load(MODELS_DIR / "model_final.pkl")

    df["clean_text"] = df["text"].apply(clean_text)
    X = vectorizer.transform(df["clean_text"])
    df["predicted"] = model.predict(X)
    df["confidence"] = model.predict_proba(X).max(axis=1)

    print("=== Predictions detail ===")
    for _, row in df.iterrows():
        status = "OK" if row["predicted"] == row["true_label"] else "ERREUR"
        print(f"[{status}] vrai={row['true_label']} predit={row['predicted']} "
              f"(confiance={row['confidence']:.2f}) - {row['text'][:60]}...")

    print("\n=== Rapport de classification ===")
    print(classification_report(df["true_label"], df["predicted"]))

    print("=== Matrice de confusion ===")
    print(confusion_matrix(df["true_label"], df["predicted"]))

    accuracy = (df["true_label"] == df["predicted"]).mean()
    result = {"external_test_accuracy": round(accuracy, 3), "n": len(df)}
    with open(MODELS_DIR / "external_generalization_report.json", "w") as f:
        json.dump(result, f, indent=2)

    print(f"\nAccuracy sur donnees externes : {accuracy:.1%} (n={len(df)})")
    print("Sauvegarde : external_generalization_report.json")


if __name__ == "__main__":
    main()