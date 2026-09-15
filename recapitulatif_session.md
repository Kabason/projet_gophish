# Récapitulatif de session & feuille de route — PFE Phishing IA

*Document de suivi — état au [date à compléter avant envoi]*

---

## 1. Ce qui a été fait cette session (Membre B)

### 1.1 Dashboard (Next.js / TypeScript)

- **Explication par prédiction** : section « Pourquoi ce verdict ? » sur `/analyze`, termes les plus influents avec contribution (TF-IDF × poids de la régression logistique), barre rouge = pousse vers phishing / verte = pousse vers légitime.
- **Comparaison multi-modèles** : chaque email analysé est passé dans les 3 modèles entraînés, verdict et confiance affichés côte à côte.
- **Thème clair/sombre** : bouton bascule, persistance `localStorage`, script anti-flash (`src/lib/theme.tsx`, `src/components/ThemeToggle.tsx`).
- Migration de la syntaxe Tailwind vers le raccourci v4 (`text-(--x)`), cosmétique uniquement.

### 1.2 API FastAPI

- `/predict` retourne désormais verdict + confiance + modèle utilisé + `top_features` (explication) + `model_comparison` (vote des 3 modèles).

### 1.3 Incidents d'environnement résolus

| Problème | Cause | Correction |
|---|---|---|
| `AttributeError: _ARRAY_API not found` | Conflit `pyarrow`/NumPy 2.x | Non utilisé par le projet, avertissement inoffensif |
| `OSError` au chargement NLTK | `nltk.data.find()` lève parfois `OSError` au lieu de `LookupError`, non intercepté | Appel direct et inconditionnel à `nltk.download()` |
| `NotFittedError: idf vector is not fitted` | Le venv n'était pas activé dans le terminal servant l'API → scikit-learn 1.4.2 système au lieu de 1.9.0 du venv | Toujours vérifier le préfixe `(venv)` avant `uvicorn` |
| Dataset revenu à Enron/Nazario uniquement | `build_hybrid_dataset.py` pointait vers un nom de fichier inexistant | Script corrigé ; les 300 emails IA n'avaient jamais été perdus |

### 1.4 Test de généralisation externe — nouveau

- `ai-engine/models/test_external_generalization.py` + `data/raw/external_test_emails.csv` (30 emails hors distribution : ni Enron, ni Nazario, ni nos emails IA).
- **Résultat : 63,3 % d'accuracy** (contre ~98 % sur le test set interne — attendu, le test interne reste dans la même distribution que l'entraînement).

**Découverte principale, chiffrée pour la première fois** : biais de langue confirmé.
- Ham français : 4 erreurs sur 5 (80 %) classées à tort comme phishing.
- Ham anglais : 2 erreurs sur 10 (20 %) seulement.
- Cause : le dataset d'entraînement ne contient **aucun ham en français** — impossible à détecter plus tôt faute de cas à tester.

Deux limites secondaires identifiées :
- Faux positif à 89 % de confiance sur un email de confirmation de commande légitime (chevauchement lexical naturel avec le phishing — limite inhérente au TF-IDF, pas un bug).
- Faux négatifs concentrés sur des sous-types de phishing absents de l'entraînement (loterie, remboursement fiscal, colis/douane, support technique).

### 1.5 Tâche écartée

Demande de pages de connexion GoPhish imitant Microsoft 365 / un portail RH, formulée séparément par le Membre A. Non réalisée avec l'aide de Claude — pages de capture d'identifiants par usurpation visuelle, catégorie de contenu hors périmètre de l'assistant même en cadre académique encadré. Voir section 3.2 pour la marche à suivre alternative.

---

## 2. État d'avancement global du projet

| Volet | Statut |
|---|---|
| Génération emails IA (Membre B) | Fait — 300 emails, 5 tactiques |
| Dataset hybride 30/40/30 (Membre B) | Fait |
| Prétraitement NLP + correction des fuites de données (Membre B) | Fait — 3 itérations SHAP documentées |
| Entraînement + comparaison de 3 modèles (Membre B) | Fait |
| Analyse de robustesse interne (type/langue/tactique) (Membre B) | Fait |
| Test de généralisation externe (Membre B) | Fait — biais de langue confirmé |
| Dashboard + API de démonstration (Membre B) | Fonctionnel |
| Ham français pour combler le biais (Membre B) | À faire |
| Landing pages GoPhish (Membre A) | À faire — voir 3.2 |
| Campagne GoPhish lancée (Membre A) | Statut à confirmer avec le Membre A |
| Statistiques comportementales, taux de clic par tactique (Membre A) | À livrer à Membre B |
| Tableau croisé tactique / clic / détection | Bloqué en attente des stats du Membre A |
| Rapport final / soutenance | À mettre à jour avec les résultats ci-dessus |

---

## 3. Tâches restantes

### 3.1 Membre B (Nathan) — par ordre de priorité suggéré

- [ ] **Générer `ham_francais.csv`** : reprendre `generate_emails.py` avec un prompt inversé (email professionnel légitime, même profils cibles), sauvegarder dans `data/raw/ham_francais.csv`. `build_hybrid_dataset.py` le détecte déjà automatiquement s'il existe.
- [ ] **Réentraîner et revalider** après ajout du ham français : relancer `build_hybrid_dataset.py` puis `nlp_pipeline.py` puis `train_models.py` puis `robustness_analysis.py`, puis **relancer `test_external_generalization.py`** pour vérifier que l'écart français/anglais s'est effectivement réduit — c'est la preuve qu'il faut pour le rapport, pas une supposition.
- [ ] **Documenter dans le rapport** : le test de généralisation externe, le biais de langue mesuré (80 % vs 20 %), les deux limites secondaires (faux positif transactionnel, sous-types de phishing absents), et l'effet de l'ajout du ham français une fois mesuré.
- [ ] **Limite des 5 profils cibles** (déjà notée dans le rapport LaTeX) : envisager d'élargir `TARGET_PROFILES` dans `generate_emails.py` si le temps le permet, pour réduire le risque de sur-apprentissage sur `congés`/`virements`.
- [ ] **Finaliser le dashboard** : test de bout en bout (génération, prédiction, métriques), vérifier que `shap_summary.png` est bien copié dans `dashboard/public/`.
- [ ] **Une fois les stats du Membre A reçues** : construire le tableau croisé tactique / taux de clic / taux de détection (section 7 du guide original) — c'est le résultat central et le plus original du projet, à ne pas traiter comme une tâche secondaire.

### 3.2 Membre A (coéquipier) — à transmettre

- [ ] **Importer les emails IA dans GoPhish** : `data/raw/ai_generated_phishing.csv` (colonnes `subject`, `body`, `tactic`) est livré et à jour — 300 emails, 5 tactiques. Insérer `{{.URL}}` dans chaque template au moment de l'import, comme prévu dans le contrat d'intégration.
- [ ] **Pages de destination (landing pages)** : à construire sans l'aide de Claude pour cette partie spécifique (voir 1.5). Sources recommandées, déjà vérifiées pour un usage de simulation autorisée :
  - Galerie de templates officielle GoPhish (importable directement dans l'outil).
  - Ressources gratuites KnowBe4 (plateforme de sensibilisation à la sécurité, templates prêts à l'emploi).
  - Alternative : demander à l'encadrant du PFE s'il existe une ressource interne à l'établissement pour ce type de simulation.
- [ ] **Configurer les groupes cibles** dans GoPhish en cohérence avec les 5 profils utilisés côté génération (Responsable RH, Chef de projet IT, Comptable senior, Assistante de direction, Ingénieur réseau) — assure la cohérence entre les deux volets pour l'analyse croisée finale.
- [ ] **Lancer la campagne** et collecter, au minimum :
  - Taux de clic par email et par tactique.
  - Délai de réaction (temps entre envoi et clic).
- [ ] **Livrer les statistiques comportementales à Nathan** dès que disponibles — c'est l'élément bloquant pour le tableau croisé final (section 3.1, dernier point).

---

## 4. Le résultat central attendu

Le projet n'atteint son objectif de recherche qu'une fois les deux jeux de données croisés :

```
Tactique psychologique -> Taux de clic humain (Membre A)
                       -> Taux de détection IA (Membre B)
```

Si une même tactique (par exemple « urgence ») obtient à la fois le taux de clic humain le plus élevé et le taux de détection le plus bas côté modèle, c'est la conclusion la plus forte et la plus originale du rapport : la tactique qui trompe le plus les humains est aussi celle qui trompe le plus le modèle de détection. Tout le travail de robustesse et d'explicabilité mené jusqu'ici prépare directement cette synthèse — elle ne peut cependant pas être produite sans les données du Membre A.

---

## 5. Points de vigilance pour la suite

- Ne pas présenter les métriques de test interne (~98 %) comme résultat principal sans mentionner le test de généralisation externe (63,3 %) à côté — la différence est elle-même une partie du résultat scientifique, pas une faiblesse à cacher.
- Vérifier que le Membre A utilise bien la version la plus récente de `ai_generated_phishing.csv` (300 lignes, 5 tactiques) et non une version antérieure à 60 lignes.
- Garder une trace écrite (capture d'écran ou export) des statistiques du Membre A dès réception, pour éviter un incident de perte de données comme celui rencontré cette session côté Membre B.
- Prévoir suffisamment de temps avant la soutenance pour le tableau croisé final — c'est la pièce la plus originale du rapport mais aussi la plus dépendante du travail d'autrui.
