# Validation réelle d'ACE-Step 1.5

## Ce que la CI vérifie

La CI vérifie le contrat d'intégration côté Djibouti Music AI avec des réponses simulées :
- envoi des paramètres documentés à `POST /release_task` ;
- lecture de l'identifiant de tâche ;
- rejet des enveloppes ACE-Step indiquant une erreur ;
- interrogation de `POST /query_result` ;
- validation de la référence `/v1/audio?path=...` et du téléchargement protégé.

Ces tests ne prouvent pas qu'un GPU ou un serveur ACE-Step réel est disponible.

## Test de bout en bout sur un serveur GPU

Installer les dépendances du backend puis définir les variables d'environnement dans le terminal (ne jamais les committer) :

- `ACESTEP_BASE_URL` : URL HTTPS du serveur ACE-Step, sans slash final.
- `ACESTEP_API_KEY` : facultatif, selon la configuration du serveur.

Depuis le dossier `backend` :

```bash
pip install -r requirements.txt
python scripts/smoke_ace_step.py --language so --duration 10
python scripts/smoke_ace_step.py --language aa --duration 10
```

Le script soumet une génération courte, attend son résultat et télécharge le fichier audio. Il retourne un code d'erreur si le serveur n'est pas configuré, si la génération échoue ou si aucun fichier audio valide n'est retourné.

## Critères de validation

- Le serveur accepte `POST /release_task` et retourne un `task_id`.
- `POST /query_result` retourne success (`status=1`) avant l'expiration du délai.
- Le résultat contient une référence audio relative `/v1/audio?path=...`.
- `GET /v1/audio` retourne un fichier non vide avec un type MIME audio.
- Les tests somali (`so`) et afar (`aa`) sont évalués séparément : la prise en charge du code langue par l'API ne garantit pas la qualité du chant.

## Limite actuelle

Aucun endpoint GPU ni secret ACE-Step opérationnel n'a été fourni ou validé dans ce dépôt. Le test réel doit donc être exécuté depuis un environnement qui dispose de ces paramètres. Tant que ces deux tests ne sont pas réussis, le moteur doit rester marqué « non validé en production ».
