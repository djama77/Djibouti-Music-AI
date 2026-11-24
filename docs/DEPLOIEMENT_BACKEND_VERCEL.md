# Déploiement du backend — Djibouti Music AI

## Architecture retenue

Vercel héberge l'interface React/Vite. Le backend FastAPI et le moteur ACE-Step sont deux services distincts :

1. **Frontend Vercel** : interface web et variables publiques de configuration.
2. **API FastAPI** : authentification par jeton, création/suivi des tâches et transfert des fichiers audio.
3. **ACE-Step 1.5** : moteur de génération exécuté sur un serveur disposant d'un GPU compatible.

Le projet Vercel actuel est configuré en Vite et ne fournit pas le service FastAPI. Le déploiement de l'interface ne signifie donc pas que la génération audio est opérationnelle.

## Pourquoi ne pas placer tout le backend dans une fonction Vercel ?

Le backend actuel relaie des fichiers audio pouvant atteindre 100 MB et effectue des appels amont dont les délais peuvent être longs. Une API conteneurisée avec des limites de temps et de transfert adaptées est préférable. Vercel reste le point d'hébergement du frontend ; l'API FastAPI est publiée sur un hébergeur de conteneurs, et ACE-Step reste sur une machine GPU.

## Déployer l'API FastAPI sur un hébergeur de conteneurs

Utiliser le dépôt GitHub `djama77/Djibouti-Music-AI`, branche validée, et configurer :

- **Répertoire de construction** : `backend`
- **Dockerfile** : `backend/Dockerfile`
- **Port HTTP** : `8000`
- **Commande** : déjà définie dans le Dockerfile avec Uvicorn.

L'hébergeur doit prendre en charge les conteneurs Docker, les variables d'environnement, HTTPS et les requêtes longues. Ne pas choisir une offre payante ni activer une ressource facturée sans validation du propriétaire du compte.

## Variables d'environnement du backend

Définir ces valeurs dans le panneau sécurisé de l'hébergeur, jamais dans GitHub :

| Variable | Valeur attendue |
| --- | --- |
| `APP_ACCESS_TOKEN` | Secret long et aléatoire généré par l'administrateur |
| `ACESTEP_BASE_URL` | URL HTTPS du serveur ACE-Step, sans slash final |
| `ACESTEP_API_KEY` | Clé amont si le serveur ACE-Step l'exige |
| `CORS_ORIGINS` | Origines exactes du frontend, séparées par des virgules |

Origines Vercel à autoriser après vérification du domaine actif :

- `https://djibouti-music-ai.vercel.app`
- `https://djibouti-music-ai-git-fix-ace-step-engi-300789-diasporajog-7042.vercel.app`

Ne pas mettre de clé API, de jeton d'accès ou de secret dans une variable `VITE_*` : ces variables sont intégrées au JavaScript envoyé au navigateur.

## Raccordement du frontend Vercel

Une fois l'API FastAPI déployée et son adresse HTTPS vérifiée :

1. Ouvrir le projet Vercel `djibouti-music-ai`.
2. Ajouter `VITE_API_BASE_URL` avec l'origine HTTPS de l'API (sans slash final), dans l'environnement Preview.
3. Redéployer la branche de prévisualisation.
4. Vérifier `https://ADRESSE-API/api/health` : la réponse attendue est HTTP 200 avec `status: ok`.
5. Vérifier ensuite que le navigateur peut appeler l'API depuis le domaine Vercel (CORS).
6. Garder la production inchangée jusqu'à validation complète.

Le jeton `APP_ACCESS_TOKEN` doit être saisi dans le champ d'accès de l'application ; il ne doit jamais être enregistré dans le dépôt ni dans une variable publique Vercel.

## Validation avant ouverture

- [ ] L'API FastAPI répond en HTTPS sur `/api/health`.
- [ ] `generation_configured` indique que le service est configuré.
- [ ] Le serveur ACE-Step répond réellement à `/release_task`.
- [ ] Le suivi `/query_result` retourne un résultat terminé.
- [ ] Le téléchargement audio retourne un fichier non vide et un type MIME audio.
- [ ] Les tests réels sont passés séparément pour les langues visées.
- [ ] Les limites d'utilisation, quotas et protections contre les abus sont définis.
- [ ] La prévisualisation Vercel est validée avant toute mise en production.

## État au moment de la rédaction

- Frontend Vercel : déployé en prévisualisation.
- Backend FastAPI public : pas encore déployé.
- Endpoint GPU ACE-Step : non fourni / non vérifié.
- Génération audio de bout en bout : non validée.
- Production et branche `main` : non modifiées.
