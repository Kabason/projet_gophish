"""
generate_emails.py

Generates synthetic phishing emails with a local LLM (Ollama) across 5
psychological tactics, for the "PFE Phishing IA" hybrid detection dataset.

Academic / lab context: this produces training data for a phishing
DETECTION model (Member B), and is the delivery contract to Member A
(GoPhish operator) for a supervised, consented simulation exercise.

Usage:
    python generate_emails.py
    python generate_emails.py --count 100
"""

import argparse
import csv
import os
import random
import time
from pathlib import Path

import ollama
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
RANDOM_SEED = int(os.getenv("RANDOM_SEED", "42"))
DEFAULT_TARGET_COUNT = int(os.getenv("TARGET_EMAIL_COUNT", "60"))

# ai-engine/llm_generation/generate_emails.py -> ai-engine/ -> project root -> data/raw/
OUTPUT_PATH = Path(__file__).resolve().parents[2] / "data" / "raw" / "ai_generated_phishing.csv"

client = ollama.Client(host=OLLAMA_HOST)
random.seed(RANDOM_SEED)

TARGET_PROFILES = [
    {"nom": "Sara Amrani", "poste": "Responsable RH", "contexte": "gestion des congés et de la paie"},
    {"nom": "Youssef Benali", "poste": "Chef de projet IT", "contexte": "migration du serveur de fichiers"},
    {"nom": "Amine Tazi", "poste": "Comptable senior", "contexte": "validation de virements fournisseurs"},
    {"nom": "Nadia El Fassi", "poste": "Assistante de direction", "contexte": "organisation du comité de direction"},
    {"nom": "Karim Ouazzani", "poste": "Ingénieur réseau", "contexte": "mise à jour des accès VPN"},
]

TACTIC_PROMPTS = {
    "urgence": "crée un sentiment d'URGENCE (délai très court, menace de blocage de compte)",
    "autorite": "invoque l'AUTORITÉ (message qui semble venir directement de la direction générale)",
    "curiosite": "exploite la CURIOSITÉ (référence vague à un document confidentiel ou une info RH)",
    "reciprocite": "utilise la RÉCIPROCITÉ (fait référence à un service rendu ou une faveur passée)",
    "routine": "simule une COMMUNICATION ROUTINIÈRE, très discrète, qui ressemble à un échange interne normal",
}
TACTICS = list(TACTIC_PROMPTS.keys())


def build_prompt(profile: dict, tactic_key: str) -> str:
    return f"""Tu es un générateur de contenu pour un exercice académique encadré de simulation de sécurité
(test d'ingénierie sociale autorisé, environnement de lab isolé, PFE universitaire).

Rédige un email professionnel en français, à destination de {profile['nom']}, {profile['poste']},
en lien avec {profile['contexte']}.

L'email doit {TACTIC_PROMPTS[tactic_key]}.
Il doit sembler légitime, sans aucune faute d'orthographe, imiter un ton professionnel interne,
et se terminer par une phrase d'appel à l'action claire du type "Cliquez ici pour vérifier/confirmer".

Réponds STRICTEMENT dans ce format, sans rien ajouter avant ou après :
OBJET: <objet de l'email>
CORPS: <corps complet de l'email>"""


def generate_phishing_email(profile: dict, tactic_key: str) -> str:
    response = client.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": build_prompt(profile, tactic_key)}],
    )
    return response["message"]["content"]


def parse_response(raw_text: str) -> tuple[str, str]:
    if "OBJET:" in raw_text and "CORPS:" in raw_text:
        subject = raw_text.split("OBJET:")[1].split("CORPS:")[0].strip()
        body = raw_text.split("CORPS:")[1].strip()
    else:
        lines = raw_text.strip().split("\n")
        subject = lines[0] if lines else "Sans objet"
        body = "\n".join(lines[1:]) if len(lines) > 1 else raw_text
    return subject, body


def generate_dataset(target_count: int, max_attempts_multiplier: int = 3) -> pd.DataFrame:
    rows = []
    seen_bodies = set()
    attempts = 0
    max_attempts = target_count * max_attempts_multiplier

    while len(rows) < target_count and attempts < max_attempts:
        attempts += 1
        profile = random.choice(TARGET_PROFILES)
        tactic_key = random.choice(TACTICS)

        try:
            raw = generate_phishing_email(profile, tactic_key)
        except Exception as exc:
            print(f"[warn] Ollama call failed ({exc}), retrying...")
            time.sleep(1)
            continue

        subject, body = parse_response(raw)
        fingerprint = body[:100]

        if fingerprint in seen_bodies or len(body) < 30:
            continue

        seen_bodies.add(fingerprint)
        rows.append(
            {
                "subject": subject,
                "body": body,
                "tactic": tactic_key,
                "target_poste": profile["poste"],
            }
        )
        print(f"[{len(rows)}/{target_count}] generated - tactic: {tactic_key}")
        time.sleep(0.5)

    if len(rows) < target_count:
        print(
            f"[warn] Only {len(rows)}/{target_count} emails generated after {attempts} attempts "
            "(likely too many near-duplicates). Document the real ratio in the report rather than hiding it."
        )

    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic phishing emails via a local LLM.")
    parser.add_argument("--count", type=int, default=DEFAULT_TARGET_COUNT, help="Number of emails to generate")
    args = parser.parse_args()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    df = generate_dataset(args.count)

    if df.empty:
        print("[error] No emails generated. Check that Ollama is running and the model is pulled.")
        return

    # Full internal copy - keeps target_poste for your own robustness analysis later
    internal_path = OUTPUT_PATH.parent / "ai_generated_phishing_full.csv"
    df.to_csv(internal_path, index=False, quoting=csv.QUOTE_ALL)

    # Delivery contract with Member A: subject, body, tactic only
    df[["subject", "body", "tactic"]].to_csv(OUTPUT_PATH, index=False, quoting=csv.QUOTE_ALL)

    print(f"\nDone: {len(df)} emails generated")
    print(f"Delivered to Member A: {OUTPUT_PATH}")
    print(f"Full internal copy:    {internal_path}")


if __name__ == "__main__":
    main()