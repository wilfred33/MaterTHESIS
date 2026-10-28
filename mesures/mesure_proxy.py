# Étape 3 : temps de réponse sans proxy / avec proxy.
# Usage : python3 mesures/mesure_proxy.py [nombre_de_requetes]
import statistics
import sys
import time
import urllib.request

N = int(sys.argv[1]) if len(sys.argv) > 1 else 1000

CIBLES = [
    ("notes    sans proxy", "http://localhost:8001/projects/p1/notes"),
    ("notes    avec proxy", "http://localhost:8080/projects/p1/notes"),
    ("projets  sans proxy", "http://localhost:8002/projects/p1"),
    ("projets  avec proxy", "http://localhost:8080/projects/p1"),
]


def mesurer(url):
    # Une requête d'échauffement, non comptée
    urllib.request.urlopen(url).read()
    durees = []
    for _ in range(N):
        debut = time.perf_counter()
        urllib.request.urlopen(url).read()
        durees.append((time.perf_counter() - debut) * 1000)
    return durees


print(f"{N} requêtes GET par cible (temps en ms)\n")
print(f"{'cible':<22}{'médiane':>10}{'p99':>10}")
for nom, url in CIBLES:
    d = mesurer(url)
    p99 = statistics.quantiles(d, n=100)[98]
    print(f"{nom:<22}{statistics.median(d):>10.2f}{p99:>10.2f}")
