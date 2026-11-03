"""Carte réaliste pour la proposition 3.
Fond : Natural Earth 10 m (domaine public). Tracés : GPX officiels France Vélo Tourisme
(Loire à Vélo, Vélodyssée, Canal de Nantes à Brest, Régalante) et calcul BRouter sur les
données OpenStreetMap (Traversée bretonne, Vignoble nantais)."""
import json, math, re
from shapely.geometry import shape, box, LineString, mapping
from shapely.ops import unary_union

G = 'data/'
B = json.load(open('data/bounds.json'))['b']  # ouest, sud, est, nord du fond de carte
LON0, LAT0, LON1, LAT1 = B
W = 1000
def _my(la):
    return math.log(math.tan(math.pi / 4 + math.radians(la) / 2))
H = W * (_my(LAT1) - _my(LAT0)) / math.radians(LON1 - LON0)
BBOX = box(-7.5, 44.6, 3.5, 50.8)


def P(lon, lat):
    return ((lon - LON0) / (LON1 - LON0) * W, (_my(LAT1) - _my(lat)) / (_my(LAT1) - _my(LAT0)) * H)


def proj_geom(g):
    from shapely.ops import transform
    return transform(lambda x, y, z=None: P(x, y), g)


def path_d(g, closed):
    out = []
    geoms = getattr(g, 'geoms', [g])
    for part in geoms:
        if part.is_empty:
            continue
        if part.geom_type == 'Polygon':
            rings = [part.exterior] + list(part.interiors)
            for r in rings:
                cs = list(r.coords)
                if len(cs) < 4:
                    continue
                out.append('M' + ' '.join(f'{x:.1f},{y:.1f}' for x, y in cs) + 'Z')
        elif part.geom_type == 'LineString':
            cs = list(part.coords)
            if len(cs) < 2:
                continue
            out.append('M' + ' '.join(f'{x:.1f},{y:.1f}' for x, y in cs))
        elif hasattr(part, 'geoms'):
            out.append(path_d(part, closed))
    return ''.join(out)


def load(name):
    return [f for f in json.load(open(G + name + '.geojson'))['features'] if f.get('geometry')]


# ---------- tracés
def hav(a, b):
    R = 6371.0
    la1, la2 = math.radians(a[1]), math.radians(b[1])
    dla, dlo = la2 - la1, math.radians(b[0] - a[0])
    h = math.sin(dla / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlo / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def gpx_points(name):
    s = open(G + name + '.gpx').read()
    segs = re.findall(r'<trkseg>(.*?)</trkseg>', s, re.S)
    out = []
    for seg in segs:
        pts = []
        for m in re.finditer(r'<trkpt lat="([-\d.]+)" lon="([-\d.]+)"[^>]*>(?:\s*<ele>([-\d.]+)</ele>)?', seg):
            pts.append((float(m.group(2)), float(m.group(1)), float(m.group(3) or 0)))
        out.append(pts)
    return out


def chain(segs):
    """Assemble les segments GPX en une seule ligne continue (le plus proche voisin)."""
    segs = [s for s in segs if len(s) > 1]
    line = segs.pop(0)
    while segs:
        best = None
        for i, s in enumerate(segs):
            for rev in (False, True):
                c = s[::-1] if rev else s
                d = hav(line[-1], c[0])
                if best is None or d < best[0]:
                    best = (d, i, rev)
        d, i, rev = best
        s = segs.pop(i)
        line += s[::-1] if rev else s
    return line


def nearest(line, lon, lat):
    return min(range(len(line)), key=lambda i: hav(line[i], (lon, lat)))


def cut(line, a, b):
    i, j = nearest(line, *a), nearest(line, *b)
    seg = line[i:j + 1] if i <= j else line[j:i + 1][::-1]
    return seg


NANTES = (-1.5536, 47.2173)
routes = {}
loire = chain(gpx_points('loire'))
routes['loire'] = cut(loire, NANTES, (-0.0770, 47.2600))
velo = chain(gpx_points('velodyssee'))
routes['velodyssee'] = cut(velo, NANTES, (-1.7830, 46.4970))
canal = chain(gpx_points('canal'))
# le GPX « Canal » ne couvre que Châteaulin → Carhaix ; de Carhaix à Nantes, la Vélodyssée suit le canal
routes['canal'] = cut(velo, NANTES, (-3.5869, 48.2452)) + canal[::-1]
reg = chain(gpx_points('regalante'))
routes['regalante'] = cut(reg, NANTES, (-1.5110, 48.6350))
for rid in ('traversee', 'vignoble'):
    f = json.load(open(G + rid + '.geojson'))['features'][0]
    routes[rid] = [tuple(c) if len(c) == 3 else (c[0], c[1], 0) for c in f['geometry']['coordinates']]

stats = {}
route_paths = {}
ICONS = {}
for rid, pts in routes.items():
    km = sum(hav(pts[k], pts[k + 1]) for k in range(len(pts) - 1))
    # profil altimétrique : 80 échantillons à distance régulière
    cum = [0.0]
    for k in range(len(pts) - 1):
        cum.append(cum[-1] + hav(pts[k], pts[k + 1]))
    prof = []
    n = 80
    idx = 0
    for s in range(n + 1):
        target = km * s / n
        while idx < len(cum) - 1 and cum[idx + 1] < target:
            idx += 1
        prof.append(pts[idx][2])
    prof = [round(sum(prof[max(0, q - 3):q + 4]) / len(prof[max(0, q - 3):q + 4])) for q in range(len(prof))]
    eles = [p[2] for p in pts if p[2]]
    gain = 0.0
    sm = None
    for p in pts:
        e = p[2]
        if sm is None:
            sm = e
            continue
        if e - sm > 3:
            gain += e - sm
            sm = e
        elif sm - e > 3:
            sm = e
    stats[rid] = dict(km=round(km), gain=round(gain), emax=round(max(eles)) if eles else 0, emin=round(min(eles)) if eles else 0, profile=prof)
    line = LineString([P(p[0], p[1]) for p in pts]).simplify(0.18)
    route_paths[rid] = path_d(line, False)
    xs = [c[0] for c in line.coords]; ys = [c[1] for c in line.coords]
    bw, bh = max(xs) - min(xs), max(ys) - min(ys)
    sc = 26 / max(bw, bh, 1e-6)
    ox = (32 - bw * sc) / 2 - min(xs) * sc; oy = (32 - bh * sc) / 2 - min(ys) * sc
    small = LineString([(x * sc + ox, y * sc + oy) for x, y in line.coords]).simplify(0.35)
    ICONS[rid] = dict(d='M' + ' '.join(f'{x:.1f},{y:.1f}' for x, y in small.coords),
                      start=[round(small.coords[0][0], 1), round(small.coords[0][1], 1)],
                      end=[round(small.coords[-1][0], 1), round(small.coords[-1][1], 1)])
    print(rid, stats[rid]['km'], 'km', 'D+', stats[rid]['gain'], len(line.coords), 'pts')



json.dump(stats, open('routes_stats.json', 'w'))
json.dump(ICONS, open('route_icons.json', 'w'))

towns = [
    ('Nantes', -1.5536, 47.2173, 'big', 'w'), ('Angers', -0.554, 47.472, '', 'e'), ('Saumur', -0.077, 47.26, '', 's'),
    ("Les Sables-d'Olonne", -1.783, 46.497, '', 'w'), ('Pornic', -2.103, 47.115, '', 'w'), ('Mont-Saint-Michel', -1.511, 48.636, '', 'e'),
    ('Rennes', -1.678, 48.111, '', 'e'), ('Redon', -2.085, 47.651, '', 'w'), ('Brest', -4.486, 48.390, '', 'e'), ('Saint-Malo', -2.008, 48.649, '', 'w'),
    ('Saint-Nazaire', -2.214, 47.273, '', 'w'), ('Châteaubriant', -1.376, 47.717, '', 'e'), ('Pontivy', -2.962, 48.068, '', 'n'), ('Clisson', -1.282, 47.087, '', 'e'),
    ('Ancenis', -1.177, 47.366, '', 'n'), ('Vitré', -1.204, 48.124, '', 'e'), ('Fougères', -1.201, 48.352, '', 'e'), ('Dinan', -2.040, 48.452, '', 'w'),
    ('Josselin', -2.547, 47.954, '', 'n'), ('Carhaix', -3.574, 48.276, '', 'n'), ('Châteaulin', -4.091, 48.196, '', 's'), ('Saint-Jean-de-Monts', -2.063, 46.791, '', 'w'),
    ('Guérande', -2.428, 47.328, '', 'w'),
]

parts = [f'<svg class="map-svg" data-extent="0 0 {W} {H:.1f}" viewBox="0 0 {W} {H:.1f}" preserveAspectRatio="xMidYMid meet" role="img" aria-labelledby="map-title map-desc">',
         '<title id="map-title">Carte des itinéraires à vélo au départ de Nantes</title>',
         "<desc id=\"map-desc\">Six véloroutes partent de Nantes : la Loire à Vélo vers Angers et Saumur, la Vélodyssée vers Pornic et Les Sables-d'Olonne, la Régalante et la Traversée bretonne vers le Mont-Saint-Michel, le Canal de Nantes à Brest et le Vignoble nantais vers Clisson.</desc>",
         f'<image class="basemap" href="/assets/img/carte-ouest.webp" x="0" y="0" width="{W}" height="{H:.1f}" preserveAspectRatio="none"/>']
lbl = [('Océan Atlantique', -3.9, 46.75, 'sea-label'), ('Manche', -3.3, 49.12, 'sea-label'), ('la Loire', -0.95, 47.335, 'river-label'),
       ('BRETAGNE', -3.0, 48.25, 'region-label'), ('PAYS DE LA LOIRE', -0.75, 47.75, 'region-label'), ('NORMANDIE', -0.70, 48.85, 'region-label'), ('VENDÉE', -1.35, 46.62, 'region-label')]
for t, lo, la, c in lbl:
    x, y = P(lo, la)
    parts.append(f'<text class="{c}" x="{x:.1f}" y="{y:.1f}">{t}</text>')
for rid, d in route_paths.items():
    parts.append(f'<g class="route" data-route="{rid}"><path class="route-hit" d="{d}"/><path class="route-casing" d="{d}"/><path class="route-line" d="{d}" pathLength="1000"/></g>')
parts.append('<g class="rider" aria-hidden="true"><circle r="9"/><circle r="4" class="rider-core"/></g>')
parts.append('<g class="pin-end" aria-hidden="true"><circle r="10" class="pin-ring"/><circle r="5" class="pin-dot"/></g>')
for name, lon, lat, cls, pos in towns:
    x, y = P(lon, lat)
    off = {'e': (9, 5, 'start'), 'w': (-9, 5, 'end'), 'n': (0, -10, 'middle'), 's': (0, 20, 'middle')}[pos]
    if cls == 'big':
        parts.append(f'<g class="town town-big" data-x="{x:.1f}" data-y="{y:.1f}"><circle cx="{x:.1f}" cy="{y:.1f}" r="22" class="pulse"/><circle cx="{x:.1f}" cy="{y:.1f}" r="10"/><text x="{x + 14:.1f}" y="{y - 12:.1f}" text-anchor="start">{name}</text></g>')
    else:
        parts.append(f'<g class="town" data-x="{x:.1f}" data-y="{y:.1f}"><circle cx="{x:.1f}" cy="{y:.1f}" r="4.5"/><text x="{x + off[0]:.1f}" y="{y + off[1]:.1f}" text-anchor="{off[2]}">{name.replace(chr(39), "&#39;")}</text></g>')
parts.append('</svg>')
svg = '\n'.join(parts)
open('map.inc', 'w').write(svg)
print('svg', len(svg) // 1024, 'Ko', W, round(H, 1))
