# DIRECTIVES — SUITE DU PROJET (Membre B)
## Pour Nathan, après le pull des dernières modifications

---

## 1. Que faire avec le repo que tu viens de télécharger

Tu n'as pas besoin de tout recompiler à l'aveugle — mais dans ce cas précis, **oui, il faut relancer toute la chaîne dans l'ordre**, parce que presque chaque script a été modifié en cascade : le nettoyage des données à la source a changé, donc tout ce qui en dépend doit être régénéré derrière.

Ce qui a changé et pourquoi :

| Fichier | Ce qui a changé |
|---|---|
| `preprocessing/clean_datasets.py` | Ajout d'un filtre qui supprime les lignes au texte corrompu (encodage binaire cassé dans Enron/Nazario) — 134 lignes retirées |
| `llm_generation/generate_emails.py` | Profils élargis (12 au lieu de 5), variation de style ajoutée, sauvegarde incrémentale |
| `preprocessing/filter_leaked_emails.py` | **Nouveau script** — filtre les emails où le LLM a recopié le contexte du prompt ("test d'ingénierie sociale", "PFE universitaire") au lieu de générer un vrai contenu. 300 → 175 emails IA propres |
| `preprocessing/build_hybrid_dataset.py` | Utilise maintenant le fichier filtré, + intègre un nouveau bloc de ham en français |
| `models/train_models.py` | Correction d'une fuite : le TF-IDF était calculé sur tout le dataset avant le split train/test, maintenant fit uniquement sur le train |
| `models/robustness_analysis.py` | Correction d'une fuite plus importante : le taux de détection par tactique était calculé sur tout le dataset (y compris des emails déjà vus à l'entraînement), maintenant uniquement sur le test set |
| `api/main.py`, `dashboard/*` | Types TypeScript corrigés pour matcher la nouvelle structure de `robustness_report.json` |

### Étapes à relancer, dans l'ordre exact

```bash
cd ai-engine
python -m venv venv          # si pas deja fait
venv\Scripts\activate        # Windows -- ou source venv/bin/activate sous Mac/Linux
pip install -r requirements.txt
```

**Vérifie d'abord que tu as bien les fichiers sources bruts** :
```bash
dir ..\data\raw\Enron.csv
dir ..\data\raw\Nazario.csv
```
S'ils manquent, retélécharge le dataset Kaggle *"Phishing Email Dataset"* (Naser Abdullah Alam) et place `Enron.csv`/`Nazario.csv` dans `data/raw/` (comme indiqué dans le docstring de `clean_datasets.py`).

Puis, dans l'ordre :
```bash
cd preprocessing
python clean_datasets.py
python build_hybrid_dataset.py --total 1000
python nlp_pipeline.py
cd ..\models
python train_models.py
python robustness_analysis.py
cd ..\explainability
python shap_analysis.py
```

**Ce que tu dois obtenir approximativement** (pour vérifier que tout s'est bien passé, sur ta machine les chiffres exacts peuvent légèrement varier selon l'échantillonnage) :
- Dataset final : ~875 lignes (300 ham Enron / 400 phishing réel Nazario / 175 phishing IA / 30 ham français)
- F1 du meilleur modèle (régression logistique) : autour de 0,96-0,97
- Détection du phishing IA sur le test set : élevée (autour de 100%), sur un échantillon d'environ 35-40 emails jamais vus à l'entraînement
- SHAP : les mots les plus influents doivent être du vocabulaire de phishing normal (`account`, `password`, `vérifier`, `sécurité`...) — si tu vois un mot bizarre ressortir en tête (genre une suite de lettres sans sens), c'est probablement un nouvel artefact d'encodage à traquer avec la même méthode qu'avant

Une fois ça fait, lance l'API et vérifie qu'elle démarre :
```bash
cd ..\api
uvicorn main:app --reload --port 8000
```
Teste sur `http://localhost:8000/docs`.

---

## 2. Nouvelle tâche : test de généralisation sur des emails externes

**Le problème qu'on veut vérifier** : jusqu'ici, le modèle n'a été testé que sur des emails issus de nos propres sources (Enron, Nazario, notre IA). Rien ne prouve qu'il généralise à des emails de phishing qu'il n'a jamais vus, produits par quelqu'un d'autre, avec un style différent. C'est une vraie faiblesse si un jury demande *"votre modèle marche-t-il sur autre chose que votre propre dataset ?"*.

### Ce que tu dois construire

Un petit dataset "externe" fait à la main (10-20 emails), complètement en dehors du pipeline d'entraînement :
- 5-8 vrais exemples de phishing que tu trouves toi-même (des emails suspects reçus par toi ou des proches, avec leur accord — anonymise les vraies coordonnées ; ou des exemples publics de sensibilisation à la cybersécurité, disponibles sur des sites comme celui de la CNIL, de l'ANSSI, ou des captures d'exemples pédagogiques)
- 5-8 emails légitimes ordinaires (les tiens, anonymisés, ou inventés à la main, sans passer par le LLM cette fois — écris-les toi-même pour être sûr qu'ils ne ressemblent à rien de ce que le modèle connaît déjà)

Crée `data/raw/external_test_emails.csv` avec les colonnes :
```
text,true_label
"<contenu de l'email>",1
"<contenu de l'email>",0
```
(`true_label` : 1 = phishing, 0 = légitime)

### Le script de test

Crée `ai-engine/models/test_external_generalization.py` :

```python
"""
test_external_generalization.py

Teste le modele sur un jeu d'emails totalement externe au pipeline
d'entrainement (ni Enron, ni Nazario, ni notre IA) - une vraie mesure
de generalisation, distincte du test set habituel qui reste dans la
meme distribution que le train.

Usage:
    python test_external_generalization.py
"""

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

MODELS_DIR = Path(__file__).resolve().parent / "saved"
DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "raw" / "external_test_emails.csv"

from nlp_pipeline_utils import clean_text  # reutilise EXACTEMENT le meme nettoyage que l'entrainement
# Si cet import echoue, copie la fonction clean_text depuis preprocessing/nlp_pipeline.py
# directement dans ce fichier - il est crucial d'utiliser un pretraitement identique.


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
```

**Important** : ce script importe `clean_text` depuis un fichier `nlp_pipeline_utils.py` qui n'existe probablement pas encore chez toi — si l'import échoue, copie-colle directement la fonction `clean_text()` de `preprocessing/nlp_pipeline.py` en haut de ce nouveau script. Le point essentiel : **le nettoyage du texte doit être identique à celui utilisé à l'entraînement**, sinon la comparaison n'a aucun sens.

### Pourquoi c'est important pour le rapport

Si l'accuracy externe reste élevée (>80-85%), c'est un argument fort de robustesse. Si elle chute nettement par rapport aux ~96% internes, ce n'est pas grave — **documente-le honnêtement**, ça montre une vraie limite du modèle (sur-apprentissage sur le style particulier de nos sources) et ouvre une piste de travail futur légitime. Dans les deux cas, c'est un résultat scientifiquement intéressant à présenter.

---

## 3. Nouvelle tâche : landing pages GoPhish soignées

Vu ton niveau sur le dashboard (Next.js, design propre), on te confie la partie visuelle qui manque le plus à la simulation actuelle : les pages piégées que verront les cibles après un clic. Actuellement, la landing page côté Membre A est un formulaire basique — l'objectif est de la rendre bien plus crédible.

### Ce qu'il faut livrer

**2 à 3 pages HTML/CSS autonomes** (un seul fichier `.html` avec le CSS inclus dedans, pas de framework — GoPhish importe du HTML statique tel quel), imitant des portails d'authentification d'entreprise réalistes :

1. **Un faux portail Microsoft 365 / Office** — écran de connexion classique (logo, champ email/mot de passe, mise en page fidèle)
2. **Un faux portail RH interne** — cohérent avec le thème des emails générés (plusieurs parlent de congés, paie, virements...) : un écran "Reconnectez-vous pour accéder à votre espace RH"
3. **(Optionnel, bonus)** Une page de confirmation/redirection après soumission — un écran neutre du type "Votre session a expiré, reconnexion en cours..." pour ne pas éveiller les soupçons immédiatement après le clic

### Contraintes techniques

- Le formulaire doit soumettre vers `{{.URL}}` (variable injectée automatiquement par GoPhish — laisse-la telle quelle dans l'attribut `action` du `<form>`)
- Champs `username`/`password` nommés simplement (GoPhish capture tout ce qui est soumis, peu importe les noms exacts)
- Responsive de base (que ça s'affiche correctement sur mobile et desktop)
- Reste dans un vrai style visuel professionnel — pas de logo officiel Microsoft copié à l'identique (évite un vrai problème de droits sur une marque déposée), plutôt un design **très proche visuellement** mais avec des éléments légèrement génériques (couleurs similaires, mise en page identique, mais pas le logo exact)

### Livraison

Dépose les fichiers dans `infrastructure/landing_pages/` (le dossier réservé à Membre A dans le repo officiel) sous forme de fichiers `.html` autonomes, avec un court `README.md` dans ce même dossier expliquant à quoi correspond chaque page. Ton binôme les importera directement dans GoPhish (`Landing Pages` → `New Page` → coller le code HTML).

---

## 4. Pendant ce temps, côté Membre A

Pendant que tu avances sur ces 3 points, le travail continue en parallèle sur l'injection des 175 emails IA dans GoPhish et le lancement de la vraie campagne comparative. Prochaine synchro prévue pour croiser vos résultats (stats de clic par tactique + taux de détection par tactique) — garde tes fichiers `external_generalization_report.json` et les landing pages prêtes pour cet échange.
