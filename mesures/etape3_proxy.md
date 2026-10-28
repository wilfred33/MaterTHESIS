# Étape 3 : coût du proxy nginx

## Expérience

- Montage : CouchDB, service notes, service projets et nginx, chacun dans un conteneur Docker, sur la même machine.
- Script : [mesure_proxy.py](mesure_proxy.py) envoie 1000 requêtes GET à la suite pour chaque cible, après une requête d'échauffement qui n'est pas comptée.
- Sans proxy : on appelle les services directement (ports 8001 et 8002).
- Avec proxy : on passe par nginx (port 8080).
- Requêtes : lecture des notes du projet `p1` (`GET /projects/p1/notes`) et lecture du projet `p1` (`GET /projects/p1`).
- On relève la médiane et le 99e percentile (p99) du temps de réponse.

## Résultats (en ms)

| Cible | Médiane | p99 |
|---|---|---|
| notes, sans proxy | 5.85 | 7.70 |
| notes, avec proxy | 6.37 | 7.78 |
| projets, sans proxy | 4.08 | 5.70 |
| projets, avec proxy | 4.70 | 6.20 |

## Ce qu'on en retient

- Le proxy ajoute environ 0,5 à 0,6 ms en médiane. C'est faible par rapport au temps de traitement des services (4 à 6 ms).
- Le p99 reste proche de la médiane : les temps sont stables, et le proxy ne crée pas de pics de lenteur.
- La lecture des notes est plus lente que celle d'un projet. Elle passe par une recherche CouchDB (`_find`), alors qu'un projet est lu directement par son identifiant.

## Limites

- Tout tourne sur une seule machine : il n'y a pas de vrai réseau entre les composants.
- Chaque requête ouvre une nouvelle connexion.
- Une seule exécution, sans répétition : les chiffres varient un peu d'un passage à l'autre.

Pour relancer la mesure : `python3 mesures/mesure_proxy.py 1000`
