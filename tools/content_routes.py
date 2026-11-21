"""Les 6 itinéraires, lus dans content/itineraires.json (partagés par build.py et pages.py).
Les identifiants (id, color) sont liés aux tracés de la carte : ils ne se modifient pas dans l'admin."""
from content import load, image

ROUTES = [image({k: v for k, v in r.items() if k != 'page'}) for r in load('itineraires.json')['itineraires']]


# ---------------------------------------------------------------- carte : tracés continus, flux animé, points de vue
import json as _json, math as _math, os as _os, re as _re, html as _html

_B = _json.load(open(_os.path.join(_os.path.dirname(__file__), 'data', 'bounds.json')))['b']
_W = 1000
_my = lambda la: _math.log(_math.tan(_math.pi / 4 + _math.radians(la) / 2))
_H = _W * (_my(_B[3]) - _my(_B[1])) / _math.radians(_B[2] - _B[0])


def project(lon, lat):
    """Longitude/latitude -> coordonnées du fond de carte (même projection que tools/geo2.py)."""
    return ((lon - _B[0]) / (_B[2] - _B[0]) * _W, (_my(_B[3]) - _my(lat)) / (_my(_B[3]) - _my(_B[1])) * _H)


_MAP_TXT = {
    'en': ("Map of cycle routes from Nantes",
           "Six cycle routes start from Nantes: the Loire à Vélo towards Angers and Saumur, the Vélodyssée towards Pornic and Les Sables-d'Olonne, the Régalante and the Traversée bretonne towards Mont-Saint-Michel, the Nantes-Brest Canal and the Nantes vineyards towards Clisson."),
    'nl': ("Kaart van de fietsroutes vanuit Nantes",
           "Zes fietsroutes vertrekken vanuit Nantes: de Loire à Vélo naar Angers en Saumur, de Vélodyssée naar Pornic en Les Sables-d'Olonne, de Régalante en de Traversée bretonne naar de Mont-Saint-Michel, het kanaal van Nantes naar Brest en de wijngaarden van Nantes naar Clisson."),
    'de': ("Karte der Radrouten ab Nantes",
           "Sechs Radrouten starten in Nantes: die Loire à Vélo nach Angers und Saumur, die Vélodyssée nach Pornic und Les Sables-d'Olonne, die Régalante und die Traversée bretonne zum Mont-Saint-Michel, der Kanal von Nantes nach Brest und das Weinland von Nantes nach Clisson."),
    'es': ("Mapa de las rutas en bicicleta desde Nantes",
           "Seis rutas ciclistas salen de Nantes: la Loire à Vélo hacia Angers y Saumur, la Vélodyssée hacia Pornic y Les Sables-d'Olonne, la Régalante y la Traversée bretonne hacia el Mont-Saint-Michel, el canal de Nantes a Brest y los viñedos de Nantes hacia Clisson."),
}


def map_svg(lang='fr'):
    """Carte prête à l'emploi : chaque tracé en un seul morceau (le pointillé du dessin ne crée plus de trous),
    une couche « flux » animée au-dessus de l'itinéraire actif et les points de vue de chaque itinéraire."""
    svg = open(_os.path.join(_os.path.dirname(__file__), 'map.inc')).read()
    if lang in _MAP_TXT:
        t, d = _MAP_TXT[lang]
        svg = _re.sub(r'(<title id="map-title">)[^<]*', lambda m: m.group(1) + t, svg, count=1)
        svg = _re.sub(r'(<desc id="map-desc">)[^<]*', lambda m: m.group(1) + d, svg, count=1)

    def route(m):
        d = m.group(1)
        joined = 'M' + _re.sub(r'\s*M', ' ', d[1:])  # sous-tracés reliés : une seule ligne continue
        return (f'<path class="route-line" d="{joined}" pathLength="1000"/>'
                f'<path class="route-flow" d="{joined}"/>')
    svg = _re.sub(r'<path class="route-line" d="([^"]+)" pathLength="1000"/>', route, svg)
    svg = _re.sub(r'(<path class="route-(?:casing|hit)" d=")([^"]+)"', lambda m: m.group(1) + 'M' + _re.sub(r'\s*M', ' ', m.group(2)[1:]) + '"', svg)

    seen, items = {}, []
    for r in ROUTES:
        for p in r.get('points') or []:
            try:
                x, y = project(float(p['lon']), float(p['lat']))
            except (KeyError, TypeError, ValueError):
                continue
            key = (round(x, 1), round(y, 1))
            if key in seen:  # même lieu sur deux itinéraires (ex. Nort-sur-Erdre)
                seen[key]['routes'].append(r['id'])
                continue
            seen[key] = dict(p, x=x, y=y, routes=[r['id']])
            items.append(seen[key])
    out = []
    for p in items:
        name, text = _html.escape(p['nom']), _html.escape(p.get('texte') or '')
        inner = (f'<title>{name} – {text}</title><circle class="poi-halo" cx="{p["x"]:.1f}" cy="{p["y"]:.1f}" r="7"/>'
                 f'<circle class="poi-dot" cx="{p["x"]:.1f}" cy="{p["y"]:.1f}" r="3.2"/>'
                 f'<text x="{p["x"] + 7:.1f}" y="{p["y"] - 6:.1f}">{name}</text>')
        if p.get('article') and lang == 'fr':
            inner = f'<a href="/post/{p["article"]}">{inner}</a>'
        out.append(f'<g class="poi" data-routes="{" ".join(p["routes"])}">{inner}</g>')
    return svg.replace('<g class="rider"', '<g class="pois">' + ''.join(out) + '</g>\n<g class="rider"', 1)
