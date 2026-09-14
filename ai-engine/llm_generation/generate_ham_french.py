"""
generate_ham_french.py

Genere des emails LEGITIMES (non-phishing) en francais, avec le meme LLM
local que generate_emails.py. Necessaire pour casser la quasi-correlation
"langue=francais -> label=phishing" qui existe dans le dataset (le ham
Enron est presque entierement en anglais), qui sinon permettrait au
modele d'utiliser la langue comme raccourci plutot qu'un vrai signal
de contenu phishing.
"""

import csv
import os
import random
import time
from pathlib import Path

import ollama
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
TARGET_COUNT = 40

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
OUTPUT_PATH = RAW_DIR / "ham_francais.csv"

PROFILES = [
    {"nom": "Sara Amrani", "poste": "Responsable RH", "contexte": "confirmation de dates de congés déjà validées"},
    {"nom": "Youssef Benali", "poste": "Chef de projet IT", "contexte": "compte-rendu de réunion hebdomadaire d'équipe"},
    {"nom": "Amine Tazi", "poste": "Comptable senior", "contexte": "rappel de la date limite de clôture comptable du mois"},
    {"nom": "Nadia El Fassi", "poste": "Assistante de direction", "contexte": "organisation logistique d'un déplacement professionnel"},
    {"nom": "Karim Ouazzani", "poste": "Ingénieur réseau", "contexte": "notification de maintenance planifiée du réseau"},
    {"nom": "Leila Bensaid", "poste": "Responsable Marketing", "contexte": "partage du calendrier éditorial du mois"},
    {"nom": "Hicham Alaoui", "poste": "Responsable Achats", "contexte": "confirmation de réception d'une commande fournisseur"},
    {"nom": "Fatima Zahra Idrissi", "poste": "Juriste d'entreprise", "contexte": "rappel d'une échéance de renouvellement contractuel"},
]


def parse_response(raw_text: str):
    if "OBJET:" in raw_text and "CORPS:" in raw_text:
        subject = raw_text.split("OBJET:")[1].split("CORPS:")[0].strip()
        body = raw_text.split("CORPS:")[1].strip()
    else:
        lines = raw_text.strip().split("\n")
        subject = lines[0] if lines else "Sans objet"
        body = "\n".join(lines[1:]) if len(lines) > 1 else raw_text
    return subject, body


def generate_ham_email(profile: dict) -> str:
    prompt = f"""Rédige un email professionnel LÉGITIME en français, envoyé par {profile['nom']}, {profile['poste']},
concernant {profile['contexte']}. Ton neutre et factuel, informatif, sans aucune urgence artificielle,
sans lien à cliquer, sans demande d'action suspecte - un email de travail tout à fait ordinaire.
Réponds STRICTEMENT dans ce format, sans rien ajouter avant ou après :
OBJET: <objet>
CORPS: <corps complet>"""
    response = ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
    return response["message"]["content"]


def main():
    rows = []
    seen = set()
    attempts = 0
    while len(rows) < TARGET_COUNT and attempts < TARGET_COUNT * 3:
        attempts += 1
        profile = random.choice(PROFILES)
        try:
            raw = generate_ham_email(profile)
        except Exception as exc:
            print(f"[warn] Ollama call failed ({exc}), retrying...")
            time.sleep(1)
            continue

        subject, body = parse_response(raw)
        fingerprint = body[:100]
        if fingerprint in seen or len(body) < 30:
            continue
        seen.add(fingerprint)

        rows.append({"subject": subject, "body": body})
        print(f"[{len(rows)}/{TARGET_COUNT}] generated")

        df_partial = pd.DataFrame(rows)
        df_partial.to_csv(OUTPUT_PATH, index=False, quoting=csv.QUOTE_ALL)
        time.sleep(0.5)

    print(f"\nDone: {len(rows)} ham emails (FR) generated -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()