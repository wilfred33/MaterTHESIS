# Plan d'implémentation : mini-éditeur de notes partagées (inspiré de ShareLatex)

Décidé le 14 octobre 2026, après la réunion avec l'encadreur. Consigne : avancer pas à pas, rester simple au début.

## Idée
- Des projets, chacun contenant des notes. Deux microservices (projets, notes), une base CouchDB, un proxy devant.
- Deux régions A et B. Chaque projet (shard) ne vit que dans UNE région. Si un utilisateur de A demande un projet de B, le proxy de A envoie la requête vers la région B.
- Table de routage du proxy : projet (ou préfixe de clé) -> région, avec une destination par défaut.
- Note = petit document JSON (project, author, text, created_at). Projet = document JSON (_id, name, region).
- Les utilisateurs sont simulés : curl à la main au début, puis un script qui joue plusieurs utilisateurs pour les mesures.

## Décisions
- 28 octobre 2026 : reverse proxy = nginx (comme dans Split and Migrate, §4.2).
  - Étapes 3 et 4 : nginx avec une table de routage fixe (directive map sur l'identifiant de projet lu dans l'URL).
  - Pour la migration (plus tard) : la table devra changer pendant que le système tourne. Options : nginx + petit service de routage (comme Koala), ou proxy écrit à la main. À décider le moment venu.
- 28 octobre 2026 : langage des services = Python avec FastAPI (page de test automatique /docs). Node.js + Express envisagé puis écarté.

## Étapes (chacune testée avant la suivante)
0. Environnement : Docker, Docker Compose, CouchDB en conteneur, test à la main avec curl.
1. Service notes seul (Python/FastAPI) : POST et GET /projects/{id}/notes, stockage dans CouchDB.
2. Service projets (Python/FastAPI) : POST /projects, GET /projects/{id}.
3. Proxy nginx devant les deux services (transmet /projects/{id}/notes au service notes, le reste au service projets). Mesure : temps de réponse sans proxy / avec proxy.
4. Deux régions A et B + table de routage dans nginx (identifiant de projet lu dans l'URL ; local -> services locaux, sinon -> proxy de l'autre région).
5. Latence artificielle entre A et B (ex. 50 ms) + script de mesure : lecture locale vs lecture distante (médiane, 99e percentile, graphique). Pour les mesures : par exemple 100 à 1000 notes par projet.
6. PLUS TARD : migration d'un projet de B vers A, sur des machines virtuelles dans le cloud.

## Migration (pour plus tard) : pré-copie avec suivi des clés modifiées
1. Chaque clé du shard a un marqueur à 0 (non modifiée).
2. Copie complète du shard de A vers B ; A continue de répondre.
3. Toute clé modifiée sur A pendant la copie passe à 1.
4. Rattrapage : on recopie seulement les clés à 1, on remet à 0 ; on répète tant qu'il en reste beaucoup.
5. Bascule : blocage très bref des écritures, copie des dernières clés, mise à jour de la table de routage.
- Piste CouchDB : numéros de révision, journal _changes, réplication incrémentale.
- Méthodes à comparer éventuellement : arrêter puis copier, pré-copie, double écriture (Akkio), renvoi des requêtes (Shard Manager).
- Mesures : durée totale, nombre de tours, durée du blocage final, requêtes en erreur, données transférées, temps de réponse pendant la migration.

## Encore à décider
- Outil pour ajouter la latence (étape 5).
- Cloud ou infrastructure pour les VM (étape 6) : à demander à l'encadreur.
