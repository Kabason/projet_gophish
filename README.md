# PFE Phishing IA - Generation par IA Generative & Detection NLP

Sujet initial : Campagne de phishing simulee avec GoPhish.
Extension : generation de phishing par IA generative (attaque) + detection par NLP (defense).

## Equipe

| Membre | Role |
|---|---|
| Membre A (Perou Diono) | Plateforme GoPhish, reseau/messagerie, execution des campagnes, analyse comportementale humaine |
| Membre B (Nathan) | Dataset, generation LLM du phishing, modele NLP de detection, explicabilite, dashboards |

## Structure du repo

pfe-phishing-ia/
  data/                  Datasets partages (raw + processed)
  ai-engine/             Tout le travail IA du Membre B (Python)
    llm_generation/      Generation des emails de phishing via Ollama/Llama3
    preprocessing/        Nettoyage + fusion du dataset hybride
    models/               Entrainement + comparaison des classifieurs
    explainability/       SHAP
    api/                  FastAPI de serving (remplace Streamlit)
    notebooks/
  dashboard/             Frontend Next.js/TypeScript (Membre B)
  infrastructure/        GoPhish, reseau, messagerie (Membre A)
  docs/rapport_final_soutenance/

## Contrat d'integration Membre A / Membre B

Fichier livre : data/raw/ai_generated_phishing.csv
Colonnes : subject, body, tactic

## Setup rapide

### ai-engine (Python)

    cd ai-engine
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt

### dashboard (Next.js/TypeScript)

    npx create-next-app@latest dashboard --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"
    cd dashboard
    npm install recharts axios lucide-react

### Ollama (generation LLM locale)

    ollama pull llama3
    ollama serve
