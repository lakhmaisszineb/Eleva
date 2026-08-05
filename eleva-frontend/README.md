# Eleva — Frontend (V1 / POC)

Interface web pour l'agent de décision marketing Eleva. Construite en **React + TypeScript + Vite + Tailwind CSS v4**, elle consomme l'API FastAPI existante (`GET /health`, `POST /analyze`).

## Démarrage

```bash
npm install
npm run dev       # http://localhost:5173
```

Par défaut, le frontend appelle l'API sur `http://localhost:8000` (config modifiable dans l'écran **Paramètres**, stockée en `localStorage`). Démarrez le backend avec :

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

`npm run build` génère un bundle statique dans `dist/` (déployable sur n'importe quel hébergeur statique / serveur interne).

## Structure

```
src/
  api/client.ts          -> client HTTP vers l'API Eleva (fetch + gestion d'erreurs)
  types.ts                -> types TS calqués 1:1 sur api/schemas.py (backend)
  lib/format.ts            -> libellés/couleurs priorité & statut, formatage KPI
  lib/storage.ts           -> historique local, entreprises connues, décisions locales
  components/              -> briques UI réutilisables (cartes, badges, graphes, tiroir d'explication)
  pages/
    AnalysePage.tsx         -> écran principal (formulaire + résultats + explicabilité)
    ImportPage.tsx           -> écran d'import CSV (prêt, backend à brancher — voir plus bas)
    HistoriquePage.tsx       -> historique local des analyses
    ParametresPage.tsx       -> configuration URL API + test /health
  App.tsx / components/Layout.tsx -> navigation par onglets (sidebar)
```

Pas de router : la navigation est gérée par un état React simple (`Screen`) dans `App.tsx`, suffisant pour 4 écrans en V1. À migrer vers `react-router` si l'app grossit (deep-linking, permaliens vers une analyse, etc.).

## Ce qui est branché sur l'API réelle

| Écran | Endpoint(s) utilisés |
|---|---|
| Analyse | `POST /analyze` (formulaire → réponse complète : KPIs, segments, insights, issues, playbooks, recommandations, explication) |
| Paramètres | `GET /health` |

## Ce qui est une simulation locale (le backend ne l'expose pas encore)

Le frontend est conçu pour être honnête sur les limites actuelles du backend plutôt que de bricoler un mock silencieux :

1. **Import CSV** — Le module `data/importer/` (mapping LLM des colonnes, nettoyage, validation, rapport) existe côté backend mais **aucun endpoint HTTP ne l'expose**. L'écran Import permet de glisser un CSV et d'en prévisualiser les colonnes localement, mais le bouton « Confirmer l'import » est désactivé avec une infobulle explicite. Pour l'activer, il faut exposer un endpoint côté API, par ex. :
   ```
   POST /companies/{company_id}/import   (multipart/form-data, champ "file")
   -> renvoie le rapport produit par data/importer/report.py
   ```

2. **Approbation / rejet d'une recommandation** — Le modèle `RecommendationStatus` (draft / pending_approval / approved / rejected) existe côté backend, mais il n'y a pas d'endpoint pour faire transitionner ce statut. Les boutons Approuver/Rejeter de l'UI stockent la décision **en local (localStorage)**, uniquement pour la session du navigateur — clairement un point à créer côté backend avant toute mise en production :
   ```
   POST /recommendations/{id}/decision   { decision: "approved" | "rejected" }
   ```

3. **Explication par recommandation** — `explain_recommendation(state)` n'est actuellement appelée que pour **la première recommandation** de l'analyse (pas de paramètre `recommendation_id` exposé). L'UI ne montre donc le tiroir d'explicabilité que sur la recommandation prioritaire, et affiche un message clair sur les autres plutôt que d'inventer une explication. À corriger en exposant :
   ```
   POST /analyze/{analysis_id}/explain   { recommendation_id }
   ```
   (ce qui suppose aussi de persister un `analysis_id` côté backend, actuellement stateless).

4. **Liste des entreprises** — Pas d'endpoint `/companies`. L'UI mémorise localement les `company_id` déjà utilisés (autocomplete), avec `company_001` / `company_002` par défaut (données de démo présentes dans `data/sample_data/`).

5. **Historique des analyses** — Conservé en `localStorage` (30 dernières), à migrer vers un stockage serveur si le multi-poste / multi-utilisateur devient un besoin.

Ces points sont documentés dans le rapport de conception (section 7 : MVP vs nice-to-have) fourni séparément.
