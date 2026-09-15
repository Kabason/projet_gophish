# Landing Pages — Simulation GoPhish

Ce dossier contient les pages HTML autonomes (CSS inclus) à importer dans
GoPhish pour la campagne de simulation. Chaque fichier est indépendant :
aucun framework, aucune dépendance externe, aucun asset à héberger.

## Contenu

| Fichier | Rôle | Usage dans GoPhish |
|---|---|---|
| `microsoft365_login.html` | Faux portail de connexion type Microsoft 365 / Cloud Workspace | Landing page principale pour les emails "compte compromis / vérification de connexion" |
| `hr_portal_login.html` | Faux portail RH interne (congés, paie, documents) | Landing page pour les emails "RH / virement / bulletin de paie" |
| `session_expired.html` | Écran neutre de "session expirée, reconnexion en cours…" | Page de redirection après soumission, pour retarder la prise de conscience de la cible |

## Comment les importer dans GoPhish

1. Se connecter à l'interface GoPhish.
2. Aller dans **Landing Pages** → **New Page**.
3. Donner un nom (ex. `Microsoft 365 — Login`).
4. Cocher **Import Site** → coller le contenu du fichier `.html` choisi
   (ou utiliser l'onglet **Source** et coller directement le HTML).
5. Vérifier que le champ `action` du formulaire contient bien `{{.URL}}`
   (c'est la variable GoPhish qui capture les identifiants soumis).
6. Sauvegarder, puis associer la page au template d'email correspondant
   dans le **Campaign**.

## Points d'attention

- **Ne pas modifier** `{{.URL}}` dans l'attribut `action` du `<form>` :
  c'est GoPhish qui l'injecte dynamiquement.
- Les champs s'appellent `username` et `password` — GoPhish capture
  tout ce qui est soumis, quels que soient les noms, mais on reste
  cohérent avec la convention habituelle.
- Les logos sont **génériques et originaux** (carrés colorés abstraits,
  pastille "RH", dégradés) : aucune marque déposée n'est reproduite à
  l'identique, pour éviter tout problème de droits.
- Les pages sont responsives (mobile + desktop).
- Pour utiliser `session_expired.html` comme page de redirection :
  dans GoPhish, renseigner **Redirect URL** de la landing page principale
  vers l'URL hébergée de cette page, ou l'utiliser via l'option
  **Redirect to** d'une autre landing page.

## À faire côté Membre A

- Héberger / importer ces pages dans GoPhish.
- Faire le lien entre chaque template d'email et la landing page cohérente
  (thème "connexion compte" → `microsoft365_login.html` ; thème "RH / paie"
  → `hr_portal_login.html`).