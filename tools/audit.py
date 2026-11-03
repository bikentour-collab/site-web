"""Audit automatique du site généré (serveur local requis : PORT=4180 node server.js).
Usage : cd tools && python3 audit.py  -> rapport dans tools/.audit.json et résumé à l'écran."""
import glob, os, re, json, html, http.client, collections

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SITE = 'https://www.bikentour.com'
HOST = ('localhost', 4180)
FR_WORDS = re.compile(r"\b(le|la|les|des|du|pour|avec|vous|votre|nos|notre|est|sont|dans|sur|jusqu|vélo|vélos|réserver|journée|semaine|itinéraire|balade)\b", re.I)


def get(path):
    c = http.client.HTTPConnection(*HOST, timeout=10)
    c.request('GET', path, headers={'Accept-Encoding': 'br, gzip'})
    r = c.getresponse(); r.read()
    return r.status, {k.lower(): v for k, v in r.getheaders()}


files = ['index.html'] + [f for d in ('fr', 'post', 'en', 'nl', 'de') for f in glob.glob(os.path.join(ROOT, d, '**', '*.html'), recursive=True)]
files = [os.path.relpath(f, ROOT) if os.path.isabs(f) else f for f in files]
pages = {}
for f in files:
    s = open(os.path.join(ROOT, f), encoding='utf-8').read()
    url = '/' + f[:-5]
    url = '/' if url == '/index' else re.sub(r'/index$', '', url)
    lang = re.search(r'<html lang="(\w+)"', s).group(1)
    main = re.search(r'<main.*?</main>', s, re.S).group(0)
    text = html.unescape(re.sub(r'<[^>]+>', ' ', re.sub(r'<(script|style|svg)[^>]*>.*?</\1>', '', main, flags=re.S)))
    pages[url] = dict(
        lang=lang, title=html.unescape(re.search(r'<title>(.*?)</title>', s).group(1)),
        desc=html.unescape((re.search(r'<meta name="description" content="([^"]*)"', s) or [None, ''])[1]),
        h1=len(re.findall(r'<h1[\s>]', s)), canonical=(re.search(r'<link rel="canonical" href="([^"]+)"', s) or [None, ''])[1],
        hreflang=dict(re.findall(r'<link rel="alternate" hreflang="([\w-]+)" href="([^"]+)"', s)),
        imgs_noalt=len(re.findall(r'<img(?![^>]*\balt=)[^>]*>', s)),
        links=set(re.findall(r'href="(/[^"#?]*)', main)) | set(re.findall(r'href="(/[^"#?]*)', s)),
        ld_ok=all(_ok for _ok in [True] + [bool(json.loads(j)) for j in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)]),
        brief='id="en-bref"' in s, faq='"FAQPage"' in s, words=len(text.split()),
        fr_ratio=(len(FR_WORDS.findall(text)) / max(1, len(text.split()))) if lang != 'fr' else 0,
        md=os.path.exists(os.path.join(ROOT, f[:-5] + '.md')))

R = collections.OrderedDict()
titles = collections.Counter(p['title'] for p in pages.values())
descs = collections.Counter(p['desc'] for p in pages.values())
R['pages'] = len(pages)
R['titres_trop_longs'] = [u for u, p in pages.items() if len(p['title']) > 65]
R['titres_dupliques'] = [t for t, n in titles.items() if n > 1]
R['descriptions_absentes'] = [u for u, p in pages.items() if not p['desc'] and u != '/404']
R['descriptions_trop_longues'] = [u for u, p in pages.items() if len(p['desc']) > 160]
R['descriptions_dupliquees'] = [d[:60] for d, n in descs.items() if n > 1 and d]
R['h1_incorrects'] = [u for u, p in pages.items() if p['h1'] != 1]
R['images_sans_alt'] = [u for u, p in pages.items() if p['imgs_noalt']]
R['canonical_incorrects'] = [u for u, p in pages.items() if u != '/404' and p['canonical'] not in (SITE + u, SITE + '/' if u == '/' else None)]
# réciprocité hreflang
bad = []
for u, p in pages.items():
    for l, h in p['hreflang'].items():
        if l == 'x-default':
            continue
        target = h[len(SITE):] or '/'
        q = pages.get(target)
        if not q or SITE + u not in [v if v != SITE + '/' else SITE + '/' for v in q['hreflang'].values()] and not (u == '/' and SITE + '/' in q['hreflang'].values()):
            bad.append(f'{u} -> {l}')
R['hreflang_non_reciproques'] = bad
R['jsonld_invalides'] = [u for u, p in pages.items() if not p['ld_ok']]
R['pages_traduites_avec_francais'] = sorted([(u, round(p['fr_ratio'], 3)) for u, p in pages.items() if p['fr_ratio'] > 0.02], key=lambda x: -x[1])[:15]
R['pages_sans_markdown'] = [u for u, p in pages.items() if not p['md'] and u != '/404']
R['pages_minces_<300_mots'] = [u for u, p in pages.items() if p['words'] < 300 and not u.startswith(('/post/', '/404')) and 'mentions' not in u and 'cookies' not in u]
R['en_bref'] = sum(p['brief'] for p in pages.values())
R['faqpage'] = sum(p['faq'] for p in pages.values())
links = set().union(*(p['links'] for p in pages.values()))
links = {l for l in links if not l.startswith(('/assets/', '/admin', '/cms'))}
R['liens_internes_testes'] = len(links)
R['liens_internes_en_erreur'] = [(l, s) for l in sorted(links) if (s := get(l)[0]) not in (200,)]
st, h = get('/')
R['entetes'] = {k: h.get(k, 'ABSENT') for k in ('strict-transport-security', 'x-content-type-options', 'x-frame-options', 'referrer-policy', 'content-encoding', 'cache-control')}
st, h = get('/assets/css/style.css?v=1')
R['cache_css'] = h.get('cache-control')
R['admin_sans_session'] = get('/admin/')[0]
R['dossiers_proteges'] = {p: get(p)[0] for p in ('/tools/build.py', '/content/fr/site.json', '/.github/workflows/generer-le-site.yml', '/server.js')}
json.dump(R, open(os.path.join(os.path.dirname(__file__), '.audit.json'), 'w'), ensure_ascii=False, indent=1, default=list)
for k, v in R.items():
    n = len(v) if isinstance(v, (list, dict)) and k not in ('entetes', 'dossiers_proteges') else v
    print(f'{k:32} {n if not isinstance(v, (list,)) or not v else str(len(v)) + "  " + str(v[:4])[:150]}')
