"""Les 6 itinéraires, lus dans content/itineraires.json (partagés par build.py et pages.py).
Les identifiants (id, color) sont liés aux tracés de la carte : ils ne se modifient pas dans l'admin."""
from content import load, image

ROUTES = [image({k: v for k, v in r.items() if k != 'page'}) for r in load('itineraires.json')['itineraires']]
