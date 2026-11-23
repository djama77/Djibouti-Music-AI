# Djibouti Music AI

Studio web responsive de création musicale assistée par **ACE-Step 1.5**.

## Architecture

- `frontend/` : React + Vite, interface adaptée aux téléphones et ordinateurs.
- `backend/` : API FastAPI qui protège la clé du service ACE-Step et relaie les tâches de génération.
- Le moteur ACE-Step et ses modèles doivent fonctionner sur un serveur disposant des ressources GPU nécessaires.
- Vercel peut héberger le frontend ; il ne remplace pas le serveur GPU.

## Démarrage local

1. Copier `.env.example` vers `.env`.
2. Renseigner `APP_ACCESS_TOKEN`, `ACESTEP_BASE_URL` et, si nécessaire, `ACESTEP_API_KEY`.
3. Lancer l'API : `docker compose up --build`.
4. Dans un autre terminal : `cd frontend && npm install && npm run dev`.
5. Ouvrir l'adresse locale Vite et saisir le jeton d'accès fourni par l'administrateur.

Le backend refuse les demandes de génération tant que le jeton d'application et l'URL ACE-Step ne sont pas configurés. Le jeton d'accès n'est pas inclus dans le code frontend ni dans le dépôt.

## Résultat audio

Après la génération, actualiser le statut du projet. Lorsque ACE-Step indique que le travail est terminé et fournit un fichier, l'interface affiche un lecteur audio HTML5 et un lien de téléchargement. Le backend valide la référence audio renvoyée par ACE-Step et relaie le fichier via une route protégée par le jeton d'application. Taille maximale du fichier relayé : 100 MB.

## Tests backend

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

## Déploiement

Pour Vercel, définir le répertoire racine du projet sur `frontend` et la commande de build sur `npm run build`. Configurer `VITE_API_BASE_URL` avec l'URL HTTPS du backend. Sur le backend, définir `CORS_ORIGINS` avec le domaine exact du frontend.

Cette version est un socle bêta, pas encore un service public prêt à accueillir tous les utilisateurs. Avant ouverture publique, ajouter une vraie authentification par utilisateur, quotas, limitation de débit, suivi des coûts, supervision, politique de confidentialité et protection contre les abus. Ne jamais placer `ACESTEP_API_KEY` dans une variable `VITE_*` ni dans le navigateur.

## API ACE-Step

Le backend utilise le flux asynchrone documenté par ACE-Step : `POST /release_task`, puis `POST /query_result`. Voir la [documentation API ACE-Step 1.5](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/API.md).

## Licence

Voir `LICENSE`. Vérifier séparément la licence et les conditions d'utilisation d'ACE-Step 1.5 et des modèles téléchargés.
