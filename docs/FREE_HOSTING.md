# Mode gratuit et hébergement

## Ce qui est réellement gratuit

Le site frontend est statique et peut être publié sur une offre gratuite d'hébergement compatible. La génération audio n'est pas exécutée par Vercel : le bouton ouvre la démonstration ACE-Step 1.5 hébergée sur Hugging Face.

La documentation Hugging Face précise que les espaces gratuits peuvent s'endormir après une période d'inactivité et que le matériel GPU peut être soumis à des limites. Le fonctionnement de la démonstration dépend de son propriétaire et de l'offre active.

## Pour une expérience intégrée plus tard

Pour intégrer la génération directement dans Djibouti Music AI, il faudra :
- disposer d'un endpoint ACE-Step stable et autorisé ;
- définir une politique d'utilisation et des quotas par visiteur ;
- empêcher l'exposition de clés d'accès dans le navigateur ;
- tester les routes de génération et de suivi avec le serveur réel ;
- afficher clairement les limites et l'état du service.

Ne pas activer le backend comme service public sans authentification et contrôle de consommation.
