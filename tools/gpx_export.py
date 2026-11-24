"""Traces GPX des 6 itinéraires, limitées au parcours au départ de Nantes (même découpage que la carte, tools/geo2.py).
Écrit assets/gpx/bikentour-<id>.gpx ; recalculé seulement si les données sources ont changé.
Usage : python3 gpx_export.py (appelé aussi par generate.py)."""
import json, math, os, re

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
DATA = os.path.join(TOOLS, 'data')
OUT = os.path.join(ROOT, 'assets', 'gpx')
NANTES = (-1.5536, 47.2173)
NAMES = {'loire': "La Loire à Vélo, de Nantes à Saumur", 'velodyssee': "La Vélodyssée, de Nantes aux Sables-d'Olonne",
         'regalante': "La Régalante, de Nantes au Mont-Saint-Michel", 'traversee': "La Traversée bretonne, de Nantes au Mont-Saint-Michel",
         'canal': "Le Canal de Nantes à Brest, de Nantes à Châteaulin", 'vignoble': "Le Vignoble nantais, boucle au départ de Nantes"}


def hav(a, b):
    la1, la2 = math.radians(a[1]), math.radians(b[1])
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(math.radians(b[0] - a[0]) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def gpx_points(name):
    s = open(os.path.join(DATA, name + '.gpx')).read()
    out = []
    for seg in re.findall(r'<trkseg>(.*?)</trkseg>', s, re.S):
        out.append([(float(m.group(2)), float(m.group(1)), float(m.group(3) or 0))
                    for m in re.finditer(r'<trkpt lat="([-\d.]+)" lon="([-\d.]+)"[^>]*>(?:\s*<ele>([-\d.]+)</ele>)?', seg)])
    return out


def chain(segs):
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
        _, i, rev = best
        s = segs.pop(i)
        line += s[::-1] if rev else s
    return line


def cut(line, a, b):
    near = lambda p: min(range(len(line)), key=lambda i: hav(line[i], p))
    i, j = near(a), near(b)
    return line[i:j + 1] if i <= j else line[j:i + 1][::-1]


def simplify(pts, tol=0.00004):
    """Douglas-Peucker (≈ 4 m) : fichier léger, tracé identique sur un GPS."""
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts); keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        (x1, y1, _), (x2, y2, _) = pts[a], pts[b]
        dx, dy = x2 - x1, y2 - y1
        n = math.hypot(dx, dy) or 1e-12
        best, idx = 0, None
        for i in range(a + 1, b):
            if n < 1e-9:  # boucle : départ = arrivée, on mesure la distance au point de départ
                d = math.hypot(pts[i][0] - x1, pts[i][1] - y1)
            else:
                d = abs(dy * pts[i][0] - dx * pts[i][1] + x2 * y1 - y2 * x1) / n
            if d > best:
                best, idx = d, i
        if idx is not None and best > tol:
            keep[idx] = True
            stack += [(a, idx), (idx, b)]
    return [p for p, k in zip(pts, keep) if k]


def compute():
    r = {}
    r['loire'] = cut(chain(gpx_points('loire')), NANTES, (-0.0770, 47.2600))
    velo = chain(gpx_points('velodyssee'))
    r['velodyssee'] = cut(velo, NANTES, (-1.7830, 46.4970))
    r['canal'] = cut(velo, NANTES, (-3.5869, 48.2452)) + chain(gpx_points('canal'))[::-1]
    r['regalante'] = cut(chain(gpx_points('regalante')), NANTES, (-1.5110, 48.6350))
    for rid in ('traversee', 'vignoble'):
        f = json.load(open(os.path.join(DATA, rid + '.geojson')))['features'][0]
        r[rid] = [tuple(c) if len(c) == 3 else (c[0], c[1], 0) for c in f['geometry']['coordinates']]
    return r


def path(rid):
    return os.path.join(OUT, f'bikentour-{rid}.gpx')


def write_all(force=False):
    src = max(os.path.getmtime(os.path.join(DATA, f)) for f in os.listdir(DATA) if f.endswith(('.gpx', '.geojson')))
    if not force and all(os.path.exists(path(k)) and os.path.getmtime(path(k)) >= src for k in NAMES):
        return
    os.makedirs(OUT, exist_ok=True)
    for rid, pts in compute().items():
        pts = simplify(pts)
        km = sum(hav(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
        name = "Bike'N Tour – " + NAMES[rid]
        trk = '\n'.join(f'      <trkpt lat="{la:.6f}" lon="{lo:.6f}"><ele>{e:.0f}</ele></trkpt>' for lo, la, e in pts)
        open(path(rid), 'w').write(f'''<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1" creator="Bike'N Tour – www.bikentour.com">
  <metadata>
    <name>{name}</name>
    <desc>Trace préparée par Bike'N Tour, 27 quai de Versailles, 44000 Nantes (06 52 62 94 64). Environ {km:.0f} km. Données : France Vélo Tourisme, OpenStreetMap (BRouter).</desc>
    <link href="https://www.bikentour.com"><text>Bike'N Tour</text></link>
  </metadata>
  <trk>
    <name>{name}</name>
    <trkseg>
{trk}
    </trkseg>
  </trk>
</gpx>
''')
        print(f'  gpx {rid}: {len(pts)} points, {km:.0f} km')


def points(rid):
    """Points (lon, lat, altitude) d'une trace déjà écrite."""
    s = open(path(rid)).read()
    return [(float(m.group(2)), float(m.group(1)), float(m.group(3))) for m in re.finditer(r'<trkpt lat="([-\d.]+)" lon="([-\d.]+)"><ele>([-\d.]+)</ele>', s)]


if __name__ == '__main__':
    write_all(force=True)
