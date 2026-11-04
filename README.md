# Djibouti Music AI

Une interface web mobile-first pour découvrir la génération musicale avec ACE-Step 1.5.

## Mode gratuit actuel

La branche `feature/free-public-demo` propose un accès simple à la démonstration publique ACE-Step 1.5 sur Hugging Face. Les visiteurs peuvent ouvrir l'atelier depuis un téléphone Android ou un ordinateur, sans installer l'application.

- Application frontend : React + Vite, adaptée aux petits écrans.
- Démonstration de génération : [ACE-Step 1.5 sur Hugging Face](https://huggingface.co/spaces/ACE-Step/Ace-Step-v1.5).
- Modèle et code : [ACE-Step 1.5 sur GitHub](https://github.com/ACE-Step/ACE-Step-1.5).
- Aucun serveur GPU payant n'est provisionné par ce dépôt.

**Limites importantes :** l'atelier externe est soumis à ses propres quotas, files d'attente, périodes de veille et conditions d'utilisation. Le dépôt ne garantit pas une génération gratuite et disponible 24 h/24. Les textes saisis sont envoyés au service externe ; ne pas y saisir de données personnelles ou confidentielles.

## Déploiement du site

Le frontend peut être déployé comme site statique sur Vercel :

1. Importer le dépôt GitHub `djama77/Djibouti-Music-AI`.
2. Choisir la branche `feature/free-public-demo`.
3. Root Directory : `frontend`.
4. Build Command : `npm run build`.
5. Output Directory : `dist`.
6. Framework : Vite.

Aucune clé API ni variable secrète n'est nécessaire pour cette version du frontend.

## API optionnelle

Le dossier `backend/` conserve un adaptateur FastAPI expérimental pour un serveur ACE-Step que l'administrateur héberge séparément. Il n'est pas appelé par le frontend public dans cette version. Avant toute activation publique, il faudra valider les routes avec une instance réelle, ajouter authentification individuelle, quotas, limitation de débit, journalisation minimale et protections contre les abus.

## Développement local

```bash
cd frontend
npm install
npm run dev
```

## Tests backend

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

## Licence

Vérifier les fichiers de licence du dépôt et les conditions du modèle ACE-Step avant toute redistribution.
