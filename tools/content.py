"""Contenu du site, lu dans content/*.json (modifiable dans l'admin /admin).
Expose les mêmes structures qu'avant pour les générateurs (build.py, pages.py, blog.py)."""
import json, os
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
C = os.path.join(ROOT, 'content')
SITE = 'https://www.bikentour.com'
LANG = os.environ.get('SITE_LANG', 'fr')


# champs jamais repris d'une traduction (identifiants, liens, photos, prix, niveaux)
KEEP = {'id', 'url', 'img', 'hero_image', 'color', 'dur', 'iso', 'good', 'level', 'grid', 'oneway', 'day', 'weekend', 'week',
        'extra', 'protect', 'deposit', 'prix', 'google_note', 'google_avis', 'tripadvisor_avis', 'reservation', 'telephone',
        'telephone_affiche', 'email', 'analytics_ga4', 'matomo_url', 'matomo_id', 'lat', 'lon', 'article'}


def merge(fr, tr, key=None):
    """Superpose une traduction (content/<langue>/x.json) au contenu français.
    Seuls les textes sont repris : prix, photos, identifiants et liens restent ceux du français."""
    if key in KEEP:
        return fr
    if isinstance(fr, dict) and isinstance(tr, dict):
        return {k: merge(v, tr[k], k) if k in tr else v for k, v in fr.items()}
    if isinstance(fr, list) and isinstance(tr, list):
        if fr and isinstance(fr[0], str):  # liste de textes : la traduction remplace la liste
            return tr if tr and all(isinstance(x, str) for x in tr) else fr
        return [merge(a, b) for a, b in zip(fr, tr)] + fr[len(tr):]
    if isinstance(fr, str) and isinstance(tr, str) and tr.strip():
        return tr
    return fr


def load(name, lang=None):
    lang = lang or LANG
    data = json.load(open(os.path.join(C, 'fr', name), encoding='utf-8'))
    path = os.path.join(C, lang, name)
    if lang != 'fr' and os.path.exists(path):
        data = merge(data, json.load(open(path, encoding='utf-8')))
    return data


def image(d, key='img'):
    """Chemin d'image de l'admin ('/assets/img/x.webp') -> 'x.webp' + dimensions réelles (iw, ih)."""
    name = str(d.get(key) or 'v2-bord-de-loire.webp').split('/assets/img/', 1)[-1].lstrip('/')
    d[key] = name
    try:
        d['iw'], d['ih'] = Image.open(os.path.join(ROOT, 'assets', 'img', name)).size
    except Exception:
        d['iw'], d['ih'] = 1200, 800
    return d


def pairs(items, a, b):
    return [(x.get(a, ''), x.get(b, '')) for x in (items or [])]


_s = load('site.json')
SITE_CFG = _s
BOOK, PHONE, PHONE_TXT, EMAIL = _s['reservation'], _s['telephone'], _s['telephone_affiche'], _s['email']

_v = load('velos.json')
BIKES = []
for _b in _v['velos']:
    _b = image(dict(_b))
    _b['specs'] = pairs(_b.get('specs'), 'label', 'valeur')
    _b.setdefault('grid', [])
    _b['grid'] = [int(x) for x in (_b['grid'] or [])]
    _b.setdefault('protect', None)
    _b.setdefault('good', [])
    BIKES.append(_b)
ACCESSORIES = pairs(_v['accessoires'], 'nom', 'prix')
INCLUDED = _v['inclus']

TOURS = []
for _t in load('visites.json')['visites']:
    _t = image(dict(_t))
    _t['stops'] = pairs(_t.get('stops'), 'lieu', 'texte')
    TOURS.append(_t)

GROUP_OFFERS = load('groupes.json')['offres']
BALADES = load('balades.json')['balades']

ROUTE_EXTRA = {}
for _r in load('itineraires.json')['itineraires']:
    _p = dict(_r['page'])
    _p['stages'] = pairs(_p.get('stages'), 'etape', 'texte')
    _p['faq'] = pairs(_p.get('faq'), 'question', 'reponse')
    ROUTE_EXTRA[_r['id']] = _p

FAQ_FULL = [(r['titre'], pairs(r['questions'], 'question', 'reponse')) for r in load('faq.json')['rubriques']]

HOME = image(load('accueil.json'), 'hero_image')
FAQ_HOME = pairs(HOME['faq'], 'question', 'reponse')

PRESS = [(a['media'], a['titre'], a['url']) for a in load('presse.json')['articles']]
REFS = [(a['media'], a['titre'], a['url']) for a in load('presse.json').get('references', [])]
