"""Génère les pages intérieures du site Bike'N Tour, le sitemap et les fichiers pour les IA.
Utilisé par generate.py"""
import json, re, html, os, datetime
from content import *
from content import SITE_CFG
from content_routes import ROUTES
import i18n
from i18n import T, LANG, FLAGS, CHEV, localize_html, replace_lang_switch, head_links

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SEMI = ' ; ' if LANG == 'fr' else '; '  # ponctuation française : espace avant le point-virgule
STATS = json.load(open(os.path.join(os.path.dirname(__file__), 'routes_stats.json')))
TODAY = datetime.date.today().isoformat()
BIZ = SITE + '/#business'
ROUTE = {r['id']: r for r in ROUTES}
BIKE = {b['id']: b for b in BIKES}
TOUR = {t['id']: t for t in TOURS}
OFFER = {o['id']: o for o in GROUP_OFFERS}
# Prix toujours lus dans content/ (modifiables dans l'admin) : jamais écrits en dur dans les textes
DAY = lambda i: BIKE[i]['day'] if i in BIKE else '?'
MIN_DAY = min(b['day'] for b in BIKES)
MAX_DAY = max(b['day'] for b in BIKES)
TOUR_MIN = min(t['price'] for t in TOURS)
TOUR_LABEL = {'panorama': 'panorama nantais', 'wine': 'Wine & Bike Tour', 'urbain': 'Culture urbaine'}
TOUR_MAX = max(t['price'] for t in TOURS)


def offer_price(i):
    p = OFFER.get(i, {}).get('price', 'sur devis')
    return p[0].lower() + p[1:]


def low(name):
    """Nom en minuscules au milieu d'une phrase (sauf en allemand : les noms gardent leur majuscule)."""
    return name if LANG == 'de' else name.lower()


def kind(b):
    """« Vélo électrique » -> « électrique » (pour « un vélo électrique ou gravel »)."""
    return re.sub(r'^vélo\s+', '', b['name'].lower())


def grouped(key, fmt):
    """« 2 € par jour pour un vélo de voyage ou enfant, 3 € par jour pour un vélo électrique ou gravel » à partir des données."""
    groups = {}
    for b in BIKES:
        if b.get(key) not in (None, ''):
            groups.setdefault(b[key], []).append(kind(b))
    if LANG != 'fr':  # « 2 € per day (touring bike, kids' bike) »
        names = {}
        for b in BIKES:
            if b.get(key) not in (None, ''):
                names.setdefault(b[key], []).append(low(b['name']))
        return ', '.join(f"{fmt(v)} ({', '.join(n)})" for v, n in names.items())
    return ', '.join(f"{fmt(v)} pour un vélo {enum(n).replace(' et ', ' ou ')}" for v, n in groups.items())
esc = html.escape

INDEX = open(os.path.join(ROOT, 'index.html' if LANG == 'fr' else f'{LANG}/index.html')).read()
HEADER = re.search(r'(<header class="hd".*?</header>)', INDEX, re.S).group(1)
FOOTER = re.search(r'(<footer class="ft">.*?</footer>)', INDEX, re.S).group(1)
MAP = open(os.path.join(os.path.dirname(__file__), 'map.inc')).read()
LEVELS = {'Facile': 1, 'Modéré': 2, 'Difficile': 3}
PAGES = []  # (url, priority)


def lvl(level):
    n = LEVELS[level]
    bars = ''.join(f'<rect x="{1 + k * 5}" y="{10 - (k + 1) * 3}" width="3.4" height="{(k + 1) * 3}" rx="1"{" class=\"on\"" if k < n else ""}/>' for k in range(3))
    return f'<span class="lvl lvl-{n}"><svg viewBox="0 0 16 11" aria-hidden="true">{bars}</svg>{T(level)}</span>'


def profile(rid, big=False):
    p = STATS[rid]['profile']
    lo, hi = min(p), max(p)
    span = max(hi - lo, 40)
    w, h = 300, 70 if big else 54
    pts = ' '.join(f'{k * w / (len(p) - 1):.1f},{h - 4 - (v - lo) / span * (h - 10):.1f}' for k, v in enumerate(p))
    return (f'<figure class="rc-profile{" rc-profile-big" if big else ""}"><svg viewBox="0 0 {w} {h}" preserveAspectRatio="none" aria-hidden="true">'
            f'<polygon points="0,{h} {pts} {w},{h}"/><polyline points="{pts}"/></svg>'
            f'<figcaption>Profil · altitude de {lo} à {hi} m · dénivelé positif cumulé ≈ {STATS[rid]["gain"]} m</figcaption></figure>')


def breadcrumb_ld(items, url):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + (u if u else url)} for i, (n, u) in enumerate(items)]}


def faq_block(qas, title='Questions fréquentes', h='h2'):
    det = '\n'.join(f'<details{" open" if i == 0 else ""}><summary><h3>{esc(q)}</h3></summary><p>{a}</p></details>' for i, (q, a) in enumerate(qas))
    return f'<section class="faq page-faq" aria-label="{esc(title)}"><{h}>{esc(title)}</{h}>\n{det}\n</section>'


def faq_ld(qas):
    return {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r'<[^>]+>', '', a)}} for q, a in qas]}


# Fiche complète de l'entreprise reprise de l'accueil : même identité sur toutes les pages (Google et moteurs IA)
_HOME_LD = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', INDEX, re.S).group(1))
BIZ_LD = next(n for n in _HOME_LD['@graph'] if n['@type'] == 'BikeStore')
WEBSITE_LD = next(n for n in _HOME_LD['@graph'] if n['@type'] == 'WebSite')


def page(url, title, meta, crumbs_items, body, ld_extra=(), img='v2-hero-vignoble.webp', priority='0.7', kind='WebPage', og_type='website', brief=None):
    out = i18n.url(url)
    if not out:  # page non traduite dans cette langue
        return
    PAGES.append((out, priority, url))
    meta = shorten(meta, 160)
    if brief:  # encadré « En bref » placé juste sous l'en-tête de page
        box = tldr(brief)
        i = body.find('</section>', body.find('<section class="phero')) if '<section class="phero' in body else -1
        body = body[:i + 10] + '\n' + box + body[i + 10:] if i >= 0 else box + body
    canon = SITE + url
    graph = [WEBSITE_LD, BIZ_LD, {"@type": kind, "@id": canon + '#webpage', "url": canon, "name": title, "description": meta, "inLanguage": "fr",
                      "isPartOf": {"@id": SITE + '/#website'}, "about": {"@id": BIZ}, "dateModified": TODAY,
                      "primaryImageOfPage": SITE + '/assets/img/' + img,
                      **({"speakable": {"@type": "SpeakableSpecification", "cssSelector": ["#en-bref"]}} if brief else {})},
             breadcrumb_ld(crumbs_items, url)] + list(ld_extra)
    ld = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=1)
    lis = ''.join(f'<li><a href="{u}">{esc(n)}</a></li>' if u else f'<li aria-current="page">{esc(n)}</li>' for n, u in crumbs_items)
    doc = f'''<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<script>document.documentElement.classList.add('js')</script>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(meta)}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<meta name="theme-color" content="#30336E">
<!--ALT-->
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="Bike'N Tour">
<meta property="og:locale" content="fr_FR">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(meta)}">
<meta property="og:image" content="{SITE}/assets/img/{img}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="alternate" type="text/markdown" href="/llms.txt" title="Bike'N Tour en bref pour les assistants IA">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Montserrat:wght@500..900&amp;display=swap">
<link rel="stylesheet" href="/assets/css/style.css">
<script src="/assets/js/main.js" defer></script>
<script type="application/ld+json">
{ld}
</script>
</head>
<body class="inner">
<a class="skip" href="#contenu">Aller au contenu</a>

{replace_lang_switch(HEADER, url, FLAGS, CHEV)}

<main id="contenu">
<nav class="crumbs wrap" aria-label="Fil d'Ariane"><ol>{lis}</ol></nav>
{body}
</main>

{FOOTER}
</body>
</html>
'''
    if LANG != 'fr':
        doc = localize_html(doc)
    doc = doc.replace('<!--ALT-->', head_links(url))
    path = os.path.join(ROOT, out.strip('/') + '.html')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w').write(doc)


MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']


def shorten(txt, limit):
    txt = re.sub(r'\s+', ' ', str(txt)).strip()
    return txt if len(txt) <= limit else txt[:limit - 1].rsplit(' ', 1)[0].rstrip(',;:') + '…'


def fr_date(iso):
    return i18n.date(datetime.date.fromisoformat(iso))


def tldr(text):
    upd = T("Mis à jour le {date} · Bike'N Tour, 19 rue Jean Jaurès, 44000 Nantes", date=f'<time datetime="{TODAY}">{fr_date(TODAY)}</time>')
    return (f'<div class="wrap"><div class="tldr" id="en-bref"><p><strong>{T("En bref.")}</strong> {text}</p>'
            f'<p class="tldr-date">{upd}</p></div></div>')


def eur(x):
    return f'{x:g} €'.replace('.', ',')


def phero(kicker, h1, lead, img, iw, ih, alt, actions='', aside=''):
    return f'''<section class="phero">
  <div class="wrap phero-inner">
    <div class="phero-text">
      <p class="eyebrow">{kicker}</p>
      <h1>{h1}</h1>
      <p class="lead">{lead}</p>
      {actions}
    </div>
    <figure class="phero-media"><img src="/assets/img/{img}" alt="{esc(alt)}" width="{iw}" height="{ih}" fetchpriority="high">{aside}</figure>
  </div>
</section>'''


def cta_band(text='Votre itinéraire est choisi ?', strong='Il ne manque que le vélo.'):
    return f'''<section class="cta-band"><div class="wrap cta-inner"><p>{text} <strong>{strong}</strong></p>
<div class="cta-actions"><a class="btn btn-yellow" href="{BOOK}">Réserver mes vélos</a><a class="btn btn-line" href="tel:{PHONE}">{PHONE_TXT}</a></div></div></section>'''


BOOK_BTN = f'<a class="btn btn-primary" href="{BOOK}">Réserver mes vélos</a>'
REASSURE = '<ul class="reassure"><li>Annulation gratuite jusqu\'à 48 h</li><li>Vélo réglé à votre taille</li><li>Livraison à votre hôtel</li></ul>'
CRUMB_HOME = ('Accueil', '/')
HUB = '/fr/itineraires-velo-depart-nantes'


# =================================================================== itinéraires
def route_pages():
    for r in ROUTES:
        x = ROUTE_EXTRA[r['id']]
        bikes = [b for b in BIKES if r['id'] in b['good']]
        others = [o for o in ROUTES if o['id'] != r['id']][:3]
        stages = ''.join(f'<li><span class="st-num">{i + 1}</span><div><h3>{esc(a)}</h3><p>{esc(t)}</p></div></li>' for i, (a, t) in enumerate(x['stages']))
        hl = ''.join(f'<li>{esc(h)}</li>' for h in x['highlights'])
        steps_ld = [{"@type": "ListItem", "position": i + 1, "item": {"@type": "Place", "name": s}} for i, s in enumerate(r['steps'])]
        trip = {"@type": "TouristTrip", "@id": SITE + r['url'] + '#trip', "name": r['name'] + ' au départ de Nantes', "description": x['intro'],
                "touristType": ["Cyclotourisme", "Voyage à vélo"], "provider": {"@id": BIZ},
                "itinerary": {"@type": "ItemList", "itemListElement": steps_ld},
                "offers": {"@type": "Offer", "url": BOOK, "price": str(DAY('voyage')), "priceCurrency": "EUR", "description": T("Location de vélo de voyage, à partir de {price} € la journée", price=DAY('voyage')), "seller": {"@id": BIZ}}}
        qas = x['faq'] + [(T('Peut-on louer un vélo en aller simple pour {name} ?', name=r['name']),
                           T("Oui, sur demande : vous partez de notre boutique à Nantes et laissez le vélo à l'arrivée, nous organisons le rapatriement avec nos partenaires, sur devis.") if r['oneway'] else T('Cet itinéraire est une boucle : vous revenez à la boutique à Nantes.'))]
        body = f'''
<section class="phero phero-route">
  <div class="wrap phero-inner">
    <div class="phero-text">
      <p class="eyebrow">Itinéraire au départ de Nantes</p>
      <h1>{esc(x['h1'])}</h1>
      <p class="lead">{esc(x['intro'])}</p>
      <ul class="facts">
        <li><span>{T('Distance')}</span><strong>{esc(r['dist'])}</strong></li>
        <li><span>{T('Durée conseillée')}</span><strong>{esc(r['days'])}</strong></li>
        <li><span>{T('Niveau')}</span><strong>{lvl(r['level'])}</strong></li>
        <li><span>{T('Aller simple')}</span><strong>{T('Oui, sur demande') if r['oneway'] else T('Boucle')}</strong></li>
      </ul>
      <div class="hero-actions">{BOOK_BTN}<a class="btn btn-ghost" href="#gpx">Recevoir la trace GPX</a></div>
      {REASSURE}
    </div>
    <div class="route-map" data-explorer data-single data-route="{r['id']}">
      <div class="map-wrap">
{MAP}
        <div class="map-ctrl" role="group" aria-label="Zoom de la carte"><button type="button" data-zoom="in" aria-label="Zoomer">+</button><button type="button" data-zoom="out" aria-label="Dézoomer">−</button></div>
      </div>
      <p class="map-credit">Fond de carte © contributeurs OpenStreetMap, OpenFreeMap · Tracé indicatif : France Vélo Tourisme, BRouter</p>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap two-col">
    <div class="prose">
      <h2>Les étapes conseillées</h2>
      <p class="muted">Découpage indicatif au départ de notre boutique, à adapter à votre rythme. On en parle ensemble au moment de régler votre vélo.</p>
      <ol class="stages">{stages}</ol>
      {profile(r['id'], True)}
      <h2>À ne pas manquer</h2>
      <ul class="ticks">{hl}</ul>
      <h2>Le retour</h2>
      <p>{esc(x['back'])}</p>
      {faq_block(qas)}
    </div>
    <aside class="side">
      <div class="side-card">
        <img src="/assets/img/{r['img']}" alt="{esc(r['alt'])}" width="{r['iw']}" height="{r['ih']}" loading="lazy" decoding="async">
        <div class="side-body">
          <p class="eyebrow">Vélo conseillé</p>
          <ul class="side-bikes">{''.join(f'<li><a href="{b["url"]}">{esc(b["name"])}</a><span>{T("dès {price} € / jour", price=b["day"])}</span></li>' for b in bikes)}</ul>
          <p class="small">Sacoches Ortlieb étanches en option (5 € / jour), livraison à votre hébergement à Nantes (10 €).</p>
          {BOOK_BTN}
        </div>
      </div>
      <form class="side-card gpx" id="gpx" action="mailto:{EMAIL}" method="post" data-mailto="{EMAIL}" data-subject="Fiche et trace GPX : {esc(r['name'])}" data-body="Bonjour,||Merci de m'envoyer la fiche de l'itinéraire et la trace GPX à cette adresse : {{email}}||Merci !" data-msg="Votre messagerie s'ouvre : envoyez le message, on vous répond sous 24 h.">
        <p class="eyebrow">Fiche PDF et trace GPX</p>
        <p class="small">Recevez par email la fiche de l'itinéraire, la trace GPX et nos bonnes adresses.</p>
        <label class="sr-only" for="gpx-{r['id']}">Votre email</label>
        <input id="gpx-{r['id']}" type="email" name="email" placeholder="Votre email" required>
        <button class="btn btn-yellow" type="submit">Recevoir la trace</button>
        <p class="small form-status" role="status" aria-live="polite"></p>
      </form>
    </aside>
  </div>
</section>

<section class="section section-tint">
  <div class="wrap">
    <h2>Les autres itinéraires au départ de Nantes</h2>
    <div class="cards cards-3">{''.join(route_tile(o) for o in others)}</div>
    <p class="more"><a class="arrow-link" href="{HUB}">Voir tous les itinéraires</a></p>
  </div>
</section>
{blog.blog_block('route', r['id'], 'À lire sur le blog : ' + r['name'], extra=BLOG_EXTRA.get(r['id'], ()))}
{cta_band()}'''
        page(r['url'], x['title'], x['meta'], [CRUMB_HOME, ('Itinéraires', HUB), (r['name'], None)], body,
             [trip, faq_ld(qas)], img=r['img'], priority='0.9', kind='WebPage', brief=route_brief(r, bikes))


PLURAL = {'voyage': 'vélos de voyage', 'electrique': 'vélos électriques', 'gravel': 'vélos gravel', 'enfant': 'vélos enfant', 'cargo': 'vélos cargo'}


def inline(name):
    """« La Régalante » -> « la Régalante » en milieu de phrase."""
    return name[0].lower() + name[1:] if name.split(' ')[0] in ('La', 'Le', 'Les') else name


def nb(n):
    return i18n.number(n)


def enum(items, sep=', '):
    return i18n.enum(items, sep=sep)


def level(l):
    """Niveau affiché (« Facile » -> « Easy »)."""
    return T(l)


def langs(txt):
    parts = [p.strip().lower() if LANG == 'fr' else p.strip() for p in txt.split(',')]
    return ', '.join(parts[:-1]) + f' {i18n.OR[LANG]} ' + parts[-1] if len(parts) > 1 else parts[0]


def route_brief(r, bikes):
    way = T("aller simple possible sur devis (vélos récupérés à l'arrivée)") if r['oneway'] else T('boucle avec retour à Nantes')
    bk = f' {i18n.OR[LANG]} '.join(T("{bike} dès {price} € la journée", bike=low(b['name']), price=b['day']) for b in bikes[:2])
    return T("{name} au départ de Nantes : {dist} depuis la boutique Bike'N Tour (19 rue Jean Jaurès), durée conseillée {days}, niveau {level}. "
             "Principales étapes : {steps}. Location : {bikes}, sacoches étanches en option (5 € par jour) ; {way}. Trace GPX et fiche de l'itinéraire envoyées par email.",
             name=r['name'], dist=r['dist'].lstrip('≈ '), days=r['days'], level=level(r['level']).lower(), steps=' → '.join(r['steps']), bikes=bk, way=way)


def fleet_brief():
    lst = SEMI.join(T("{bike} {day} € la journée, {week} € la semaine", bike=low(b['name']), day=b['day'], week=b['week']) for b in BIKES)
    return T("Tarifs {year} de location de vélos chez Bike'N Tour, 19 rue Jean Jaurès à Nantes : {list}. Antivol, kit anti-crevaison et éclairage inclus. "
             "Livraison dans la métropole nantaise 10 €, aller simple sur devis, annulation gratuite jusqu'à 48 h avant le départ.", year=datetime.date.today().year, list=lst)


def route_tile(o):
    return f'''<a class="tile" href="{o['url']}"><img src="/assets/img/{o['img']}" alt="" width="{o['iw']}" height="{o['ih']}" loading="lazy" decoding="async">
<span class="tile-body"><span class="tile-meta">{lvl(o['level'])}<span>{esc(o['km'])} · {esc(o['days'])}</span></span><strong>{esc(o['name'])}</strong><span class="small">{esc(o['short'])}</span></span></a>'''


def hub():
    rows = ''.join(f'<tr><th scope="row"><a href="{r["url"]}">{esc(r["name"])}</a></th><td>{esc(r["km"])}</td><td>{esc(r["days"])}</td><td>{lvl(r["level"])}</td><td>{"Oui" if r["oneway"] else "Boucle"}</td></tr>' for r in ROUTES)
    lst = {"@type": "ItemList", "name": "Itinéraires à vélo au départ de Nantes", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "url": SITE + r['url'], "name": r['name']} for i, r in enumerate(ROUTES)]}
    body = f'''
{phero('Au départ de la boutique', 'Itinéraires à vélo au départ de Nantes', "Six grandes véloroutes partent de notre boutique, en plein centre de Nantes : la Loire à Vélo, la Vélodyssée, la Régalante, la Traversée bretonne, le Canal de Nantes à Brest et le Vignoble nantais. Pour chacune, on vous prépare le vélo, les sacoches et la trace GPX.", 'v2-bord-de-loire.webp', 2000, 1500, 'Groupe de cyclistes au bord de la Loire', f'<div class="hero-actions">{BOOK_BTN}<a class="btn btn-ghost" href="/fr/idees-de-balades">Balades à la journée</a></div>')}
<section class="section">
  <div class="wrap">
    <h2>Les 6 véloroutes en un coup d'œil</h2>
    <div class="table-wrap"><table class="data"><thead><tr><th scope="col">Itinéraire</th><th scope="col">Distance</th><th scope="col">Durée conseillée</th><th scope="col">Niveau</th><th scope="col">Aller simple</th></tr></thead><tbody>{rows}</tbody></table></div>
    <p class="small muted">Distances calculées sur les tracés officiels France Vélo Tourisme depuis la boutique, durées indicatives sur une base de 40 à 60 km par jour.</p>
    <div class="cards cards-3">{''.join(route_tile(r) for r in ROUTES)}</div>
  </div>
</section>
<section class="section section-tint"><div class="wrap two-col">
  <div class="prose"><h2>Comment choisir son itinéraire ?</h2>
  <p><strong>Pour un premier voyage ou en famille</strong>, la <a href="{ROUTE['loire']['url']}">Loire à Vélo</a> est la plus simple : plate, très bien balisée et bien desservie par le train pour le retour.</p>
  <p><strong>Pour l'océan</strong>, la <a href="{ROUTE['velodyssee']['url']}">Vélodyssée</a> rejoint Pornic en deux jours et la côte vendéenne en quatre à cinq.</p>
  <p><strong>Pour le Mont-Saint-Michel</strong>, la <a href="{ROUTE['regalante']['url']}">Régalante</a> passe par les terres (275 km, très peu de dénivelé), la <a href="{ROUTE['traversee']['url']}">Traversée bretonne</a> par la côte, Rennes et Saint-Malo (485 km).</p>
  <p><strong>Pour un week-end</strong>, le <a href="{ROUTE['vignoble']['url']}">Vignoble nantais</a> en gravel ou le <a href="{ROUTE['canal']['url']}">Canal de Nantes à Brest</a> jusqu'à Redon.</p>
  <p>Prix, choix du vélo, aller simple, caution : toutes les réponses dans notre <a href="/fr/guide-location-velo-nantes">guide de la location de vélo à Nantes</a>.</p></div>
  <aside class="side"><div class="side-card side-body"><p class="eyebrow">Inclus avec chaque itinéraire</p><ul class="ticks"><li>Fiche PDF et trace GPX par email</li><li>Parcours sur Komoot</li><li>Accès en train et retour</li><li>Nos bonnes adresses</li></ul>{BOOK_BTN}</div></aside>
</div></section>
{blog.blog_block('hub', None, 'Préparer son voyage à vélo', extra=('le-voyage-a-velo', 'slow-tourisme', 'le-top-5'))}
{cta_band()}'''
    page(HUB, 'Itinéraires vélo au départ de Nantes | Bike\'N Tour',
         'Les 6 véloroutes au départ de Nantes : Loire à Vélo, Vélodyssée, Régalante, Traversée bretonne, Canal de Nantes à Brest, Vignoble nantais.',
         [CRUMB_HOME, ('Itinéraires', None)], body, [lst], img='v2-bord-de-loire.webp', priority='0.9', kind='CollectionPage',
         brief=T("Six grandes véloroutes partent de la boutique Bike'N Tour, au 19 rue Jean Jaurès dans le centre de Nantes : {list}. Pour un premier voyage à vélo ou en famille, la plus simple est la Loire à Vélo : plate, très bien balisée et desservie par le train pour le retour.",
                 list=SEMI.join(T("{name} ({km}, {days}, niveau {level})", name=inline(r['name']) if LANG == 'fr' else r['name'], km=r['km'], days=r['days'], level=level(r['level']).lower()) for r in ROUTES)))


BALADE_POST = {'Sèvre': 'balade-incontournable-la-sevre-nantaise', 'Oudon': 'les-bords-de-loire-oudon', 'Cordemais': 'la-loire-a-velo-de-nantes-a-cordemais',
               'Grand-Lieu': 'balade-incontournable-de-nantes-au-lac-de-grand-lieu', "L'Erdre": 'lerdre-a-velo', 'Mauves': 'la-loire-a-velo-de-nantes-a-mauves',
               'Pornic': 'pornic-a-velo', 'Pellerin': 'la-balade-des-2-bacs', 'Saint-Nazaire': 'parcours-de-lestuaire'}
# articles à mettre en avant sur certaines pages (en plus des articles liés automatiquement)
BLOG_EXTRA = {'loire': ('la-loire-a-velo-de-nantes-a-mauves', 'les-bords-de-loire-oudon', 'parcours-de-lestuaire'),
              'velodyssee': ('pornic-a-velo', 'grand-lieu', 'nantes-la-baule'), 'vignoble': ('la-sevre-nantaise', 'le-vignoble-nantais', 'chateau-de-chassay'),
              'canal': ('lerdre-a-velo', 'le-bassin-ceineray', 'le-voyage-a-velo'), 'regalante': ('le-voyage-a-velo', 'slow-tourisme', 'lerdre-a-velo'),
              'traversee': ('le-voyage-a-velo', 'slow-tourisme', 'guerande'), 'voyage': ('le-voyage-a-velo', 'slow-tourisme', 'le-top-5'),
              'gravel': ('le-vignoble-nantais', 'la-sevre-a-velo', 'marais-de-goulaine'), 'enfant': ('jardin-des-plantes', 'lile-de-nantes', 'le-top-5'),
              'wine': ('le-vignoble-nantais', 'la-sevre-nantaise', 'chateau-de-chassay'), 'urbain': ('little-atlantique', 'trentemoult', 'le-voyage-a-nantes-2021'),
              'panorama': ('les-titans', 'la-butte-saint-anne', 'une-ile-remplie')}


def balade_link(name):
    if LANG != 'fr' or os.environ.get('NO_BLOG'):  # les articles du blog sont en français
        return ''
    for k, part in BALADE_POST.items():
        if k in name:
            p = blog.by_slug(part)
            if p:
                return f'<p class="small"><a class="arrow-link" href="{p["url"]}">Lire l\'article : {esc(p["h1"])}</a></p>'
    return ''


def balades():
    items = ''.join(f'''<article class="balade"><div class="balade-head"><h3>{esc(b['name'])}</h3>{lvl(b['level'])}</div>
<p class="balade-meta"><span>{esc(b['km'])}</span><span>{esc(b['time'])}</span></p><p>{esc(b['text'])}</p><p class="small muted">{esc(b['back'])}</p>{balade_link(b['name'])}</article>''' for b in BALADES)
    lst = {"@type": "ItemList", "name": "Balades à vélo autour de Nantes", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "item": {"@type": "TouristTrip", "name": b['name'], "description": b['text'], "provider": {"@id": BIZ}}} for i, b in enumerate(BALADES)]}
    body = f'''
{phero('Idées de balades', 'Balades à vélo autour de Nantes', "Une journée ou un week-end : nos idées de balades autonomes au départ de la boutique, avec retour en TER quand c'est possible. Les distances et niveaux viennent de nos sorties avec l'équipe.", 'v2-pause-nantes.webp', 1200, 901, 'Pause à vélo dans le centre de Nantes', f'<div class="hero-actions">{BOOK_BTN}</div>')}
<section class="section"><div class="wrap"><div class="balades">{items}</div>
<p class="more"><a class="arrow-link" href="{HUB}">Envie de plus long ? Nos 6 grands itinéraires</a></p></div></section>
{blog.blog_block('hub', None, 'Encore plus de balades sur le blog', n=6, tint=True, extra=('le-top-5', 'jardin-des-plantes', 'lile-de-nantes', 'marais-de-goulaine', 'guerande', 'la-balade-des-2-bacs'))}
{cta_band('Une balade en tête ?', 'On vous prépare le vélo.')}'''
    page('/fr/idees-de-balades', 'Balades à vélo autour de Nantes | Bike\'N Tour',
         'Balades à vélo au départ de Nantes : Sèvre nantaise jusqu\'à Clisson, rives de Loire, Erdre, lac de Grand-Lieu, Pornic en deux jours. Distances et niveaux.',
         [CRUMB_HOME, ('Itinéraires', HUB), ('Idées de balades', None)], body, [lst], img='v2-pause-nantes.webp', priority='0.7', kind='CollectionPage',
         brief=T("{n} idées de balades à vélo d'une journée ou d'un week-end au départ de la boutique Bike'N Tour à Nantes : {list}. Location de vélo dès {day} € la journée, vélo électrique dès {eday} €.",
                 n=len(BALADES), list=', '.join(f"{b['name']} ({b['km']})" for b in BALADES), day=DAY('voyage'), eday=DAY('electrique')))


# =================================================================== vélos
def price_table(b):
    if b['grid']:
        head = ''.join(f'<th scope="col">{d} jour{"s" if d > 1 else ""}</th>' for d in range(1, 8))
        cells = ''.join(f'<td>{p} €</td>' for p in b['grid'])
        return f'<div class="table-wrap"><table class="data price"><thead><tr>{head}<th scope="col">Jour suppl.</th></tr></thead><tbody><tr>{cells}<td>+{b["extra"]} €</td></tr></tbody></table></div>'
    return f'<div class="table-wrap"><table class="data price"><thead><tr><th scope="col">1 jour</th><th scope="col">Week-end</th><th scope="col">Semaine</th></tr></thead><tbody><tr><td>{b["day"]} €</td><td>{b["weekend"]} €</td><td>{b["week"]} €</td></tr></tbody></table></div>'


def product_ld(b):
    return {"@type": "Product", "@id": SITE + b['url'] + '#product', "name": (lambda x: x[0].upper() + x[1:])(T("Location {bike} à Nantes", bike=low(b['name']))), "brand": {"@type": "Brand", "name": b['brand'].split(' (')[0]},
            "model": b['model'], "image": SITE + '/assets/img/' + b['img'], "description": b['lead'],
            "offers": {"@type": "AggregateOffer", "priceCurrency": "EUR", "lowPrice": str(b['day']), "highPrice": str(b['week']), "offerCount": "3",
                       "availability": "https://schema.org/InStock", "url": BOOK, "seller": {"@id": BIZ}}}


def bike_pages():
    for b in BIKES:
        specs = ''.join(f'<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in [('Marque', b['brand']), ('Modèle', b['model'])] + b['specs'])
        good = ''.join(route_tile(ROUTE[g]) for g in b['good'])
        prot = T('Protection casse et vol en option : {price} € par jour.', price=b['protect']) if b['protect'] else T('Protection casse et vol : nous consulter.')
        qas = [(T("Combien coûte la location d'un {bike} à Nantes ?", bike=low(b['name'])),
                T("{day} € la journée, {weekend} € le week-end et {week} € la semaine, avec un tarif dégressif. Caution : {deposit} €. {protection}",
                  day=b['day'], weekend=b['weekend'], week=b['week'], deposit=nb(b['deposit']), protection=prot)),
               (T("Qu'est-ce qui est inclus ?"), T("Antivol, kit anti-crevaison, pompe, porte-bagages, éclairage, chargeur et clé de batterie, ainsi que le réglage du vélo à votre taille et nos conseils d'itinéraire.") if b['id'] in ('electrique', 'cargo')
                else T("Antivol, kit anti-crevaison, pompe, porte-bagages et éclairage, ainsi que le réglage du vélo à votre taille et nos conseils d'itinéraire."))]
        body = f'''
{phero('Location de vélos à Nantes', esc(b['h1']), esc(b['lead']), b['img'], b['iw'], b['ih'], b['alt'], f'<p class="price-big">{T("Dès <strong>{price} €</strong> / jour", price=b["day"])}</p><div class="hero-actions">{BOOK_BTN}<a class="btn btn-ghost" href="/fr/nos-tarifs-reservation">Tous les tarifs</a></div>{REASSURE}')}
<section class="section"><div class="wrap two-col">
  <div class="prose">
    <h2>Caractéristiques</h2><dl class="specs">{specs}</dl>
    <h2>Tarifs</h2>{price_table(b)}
    <p class="small muted">{T("Caution {deposit} €. {protection} Annulation gratuite jusqu'à 48 h avant le départ.", deposit=nb(b['deposit']), protection=prot)}</p>
    <h2>Pour quels voyages ?</h2><p>{esc(b['why'])}</p>
    {faq_block(qas)}
  </div>
  <aside class="side"><div class="side-card side-body"><p class="eyebrow">Inclus</p><ul class="ticks">{''.join(f'<li>{esc(i)}</li>' for i in INCLUDED)}</ul>{BOOK_BTN}<p class="small">Ou au <a href="tel:{PHONE}">{PHONE_TXT}</a></p></div></aside>
</div></section>
<section class="section section-tint"><div class="wrap"><h2>Idéal pour</h2><div class="cards cards-3">{good}</div>
<p class="more"><a class="arrow-link" href="/fr/nos-velos-location">Comparer tous nos vélos</a></p></div></section>
{blog.blog_block('bike', b['id'], 'Sur le blog', extra=BLOG_EXTRA.get(b['id'], ()))}
{cta_band()}'''
        page(b['url'], b['title'], b['meta'], [CRUMB_HOME, ('Nos vélos', '/fr/nos-velos-location'), (b['name'], None)], body,
             [product_ld(b), faq_ld(qas)], img=b['img'], priority='0.8', kind='ItemPage',
             brief=T("Bike'N Tour loue à Nantes des {bikes} {brand} {model} : {day} € la journée, {weekend} € le week-end et {week} € la semaine, tarifs dégressifs, caution de {deposit} €. "
                     "Antivol, kit anti-crevaison, pompe et éclairage sont inclus et le vélo est réglé à votre taille. Conseillé pour {routes}. Retrait au 19 rue Jean Jaurès à Nantes ou livraison à votre hébergement (10 €).",
                     bikes=PLURAL[b['id']] if LANG == 'fr' else low(b['name']), brand=b['brand'].split(' (')[0], model=b['model'], day=b['day'], weekend=b['weekend'], week=b['week'],
                     deposit=nb(b['deposit']), routes=enum([inline(ROUTE[g]['name']) if LANG == 'fr' else ROUTE[g]['name'] for g in b['good']])))


def fleet():
    cards = ''.join(f'''<article class="bike"><img src="/assets/img/{b['img']}" alt="{esc(b['alt'])}" width="{b['iw']}" height="{b['ih']}" loading="lazy" decoding="async">
<h3><a href="{b['url']}">{esc(b['name'])}</a></h3><p>{esc(b['brand'])} · {esc(b['model'])}</p><p class="price">{T("Dès {day} € / jour · {week} € la semaine", day=b['day'], week=b['week'])}</p></article>''' for b in BIKES)
    acc = ''.join(f'<tr><th scope="row">{esc(n)}</th><td>{T("{price} € / jour", price=p)}</td></tr>' for n, p in ACCESSORIES)
    body = f'''
{phero('Nos vélos', 'Nos vélos de location à Nantes', "Des vélos récents et entretenus après chaque location : vélos de voyage Velo de Ville, vélos électriques et gravels Sunn fabriqués en Loire-Atlantique, vélos enfant et cargo. Tous réglés à votre taille avant le départ.", 'v2-flotte-boutique.webp', 1400, 933, 'Les vélos de voyage Bike\'N Tour devant la boutique à Nantes', f'<div class="hero-actions">{BOOK_BTN}<a class="btn btn-ghost" href="/fr/nos-tarifs-reservation">Tarifs détaillés</a></div>')}
<section class="section"><div class="wrap"><h2>La flotte</h2><div class="bikes bikes-5">{cards}</div></div></section>
<section class="section section-tint"><div class="wrap two-col">
  <div class="prose">
    <h2>Accessoires en option</h2><div class="table-wrap"><table class="data"><tbody>{acc}</tbody></table></div>
    <h2 id="livraison">Livraison à votre hébergement</h2><p>Nous livrons et récupérons les vélos dans la métropole nantaise : hôtel, gîte, Airbnb ou gare de Nantes. <strong>10 € par livraison</strong>, jusqu'à 4 vélos. On convient ensemble de l'heure et du lieu.</p>
    <h2 id="aller-simple">Aller simple (One Way)</h2><p>Vous partez de Nantes et terminez votre voyage ailleurs ? Nous organisons la récupération des vélos à l'arrivée, sur la Loire à Vélo, la Vélodyssée, la Régalante ou en Bretagne, avec nos partenaires. <strong>Tarif sur devis</strong> selon les dates et le lieu de dépôt : contactez-nous à l'avance.</p>
    <h2>Protection casse et vol</h2><p>En option : {grouped('protect', lambda v: f'<strong>{v} € par jour</strong>')}. La casse est prise en charge à 100 % (hors usage abusif) et, en cas de vol, seuls 10 % de la valeur neuve restent à votre charge.</p>
  </div>
  <aside class="side"><div class="side-card side-body"><p class="eyebrow">Inclus avec chaque vélo</p><ul class="ticks">{''.join(f'<li>{esc(i)}</li>' for i in INCLUDED)}</ul>{BOOK_BTN}</div></aside>
</div></section>
{cta_band()}'''
    offers = {"@type": "OfferCatalog", "name": "Location de vélos à Nantes", "itemListElement": [{"@type": "Offer", "itemOffered": {"@id": SITE + b['url'] + '#product'}, "price": str(b['day']), "priceCurrency": "EUR"} for b in BIKES]}
    page('/fr/nos-velos-location', 'Location de vélos à Nantes : voyage, électrique | Bike\'N Tour',
         T("Location de vélos à Nantes : vélo de voyage dès {voyage} €/jour, électrique dès {electrique} €, gravel dès {gravel} €, enfant dès {enfant} €, cargo. Livraison 10 €, aller simple sur devis.", **{k: DAY(k) for k in BIKE}),
         [CRUMB_HOME, ('Nos vélos', None)], body, [offers], img='v2-flotte-boutique.webp', priority='0.9', kind='CollectionPage', brief=fleet_brief())


def pricing():
    rows = ''.join(f'<tr><th scope="row"><a href="{b["url"]}">{esc(b["name"])}</a></th><td>{b["day"]} €</td><td>{b["weekend"]} €</td><td>{b["week"]} €</td><td>{T("{price} € / jour", price=b["protect"]) if b["protect"] else T("Nous consulter")}</td><td>{nb(b["deposit"])} €</td></tr>' for b in BIKES)
    grids = ''.join(f'<h3>{esc(b["name"])}</h3>{price_table(b)}' for b in BIKES if b['grid'])
    acc = ''.join(f'<tr><th scope="row">{esc(n)}</th><td>{T("{price} € / jour", price=p)}</td></tr>' for n, p in ACCESSORIES)
    qas = [('Faut-il payer à la réservation ?', 'Le paiement se fait en ligne ou en boutique, par carte bancaire ou chèque.'),
           ('Peut-on annuler ?', 'Oui, gratuitement jusqu\'à 48 h avant le départ.'),
           (T('Y a-t-il des réductions pour les groupes ?'), T('Oui : 10 % de remise dès 10 personnes, et des tarifs dédiés pour les entreprises ({price}).', price=offer_price('location')))]
    body = f'''
{phero('Tarifs 2026', 'Tarifs de location de vélos à Nantes', "Des tarifs simples et dégressifs, cadenas, kit anti-crevaison et éclairage compris. Réservez en ligne en quelques minutes, annulation gratuite jusqu'à 48 h avant le départ.", 'v2-depart-boutique.webp', 1400, 933, 'Départ à vélo depuis la boutique à Nantes', f'<div class="hero-actions">{BOOK_BTN}</div>{REASSURE}')}
<section class="section"><div class="wrap">
  <h2>Location de vélos</h2>
  <div class="table-wrap"><table class="data"><thead><tr><th scope="col">Vélo</th><th scope="col">1 jour</th><th scope="col">Week-end</th><th scope="col">Semaine</th><th scope="col">Protection casse et vol</th><th scope="col">Caution</th></tr></thead><tbody>{rows}</tbody></table></div>
  <h2>Tarifs dégressifs, jour par jour</h2>{grids}
  <p class="small muted">Location à la journée : de 9 h 30 à 18 h 30. Caution plafonnée à 2 000 € pour plusieurs vélos.</p>
</div></section>
<section class="section section-tint"><div class="wrap two-col">
  <div class="prose"><h2>Accessoires et services</h2><div class="table-wrap"><table class="data"><tbody>{acc}
  <tr><th scope="row"><a href="/fr/nos-velos-location#livraison">Livraison dans la métropole nantaise</a></th><td>10 € (jusqu'à 4 vélos)</td></tr>
  <tr><th scope="row"><a href="/fr/nos-velos-location#aller-simple">Aller simple / récupération des vélos</a></th><td>Sur devis</td></tr></tbody></table></div>
  {faq_block(qas)}</div>
  <aside class="side"><div class="side-card side-body"><p class="eyebrow">Visites guidées</p><p>{T("Nantes à vélo électrique avec un guide, <strong>dès {price} € par personne</strong>.", price=TOUR_MIN)}</p><a class="btn btn-ghost" href="/fr/visites-guidees-nantes">Voir les visites</a></div></aside>
</div></section>
{cta_band()}'''
    page('/fr/nos-tarifs-reservation', T("Tarifs location vélo Nantes {year} : dès {price} €/jour | Bike'N Tour", year=datetime.date.today().year, price=MIN_DAY),
         T("Tarifs de location de vélos à Nantes : voyage {voyage} €/jour, électrique {electrique} €, gravel {gravel} €, enfant {enfant} €, cargo {cargo} €. Semaine, accessoires, livraison.", **{k: DAY(k) for k in BIKE}),
         [CRUMB_HOME, ('Tarifs', None)], body, [faq_ld(qas)] + [product_ld(b) for b in BIKES], img='v2-depart-boutique.webp', priority='0.9', brief=fleet_brief())


# =================================================================== visites et groupes
def tour_ld(t):
    return {"@type": "TouristTrip", "@id": SITE + t['url'] + '#tour', "name": t['name'], "description": t['lead'], "provider": {"@id": BIZ},
            "touristType": ["Visite guidée", "Vélo électrique"], "inLanguage": t['langs'],
            "itinerary": {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": {"@type": "Place", "name": n}} for i, (n, _) in enumerate(t['stops'])]},
            "offers": {"@type": "Offer", "price": str(t['price']), "priceCurrency": "EUR", "url": BOOK, "availability": "https://schema.org/InStock", "seller": {"@id": BIZ}}}


def tours():
    for t in TOURS:
        stops = ''.join(f'<li><span class="st-num">{i + 1}</span><div><h3>{esc(n)}</h3><p>{esc(d)}</p></div></li>' for i, (n, d) in enumerate(t['stops']))
        qas = [('Faut-il savoir faire du vélo électrique ?', 'Non : la prise en main se fait au départ avec votre guide, et le parcours est 100 % sur pistes cyclables.'),
               ('Peut-on annuler ?', 'Oui, la visite est annulable et remboursable jusqu\'à 48 h à l\'avance. Pour décaler l\'horaire, contactez-nous : on trouve toujours une solution.'),
               ('Combien de personnes par groupe ?', '12 personnes maximum par guide. Pour un groupe constitué (famille, amis, collègues), nous organisons des visites privées à l\'horaire de votre choix.')]
        body = f'''
{phero('Visite guidée à vélo électrique', esc(t['name']), esc(t['lead']), t['img'], t['iw'], t['ih'], t['alt'], f'<ul class="facts"><li><span>{T("Prix")}</span><strong>{T("{price} € / personne", price=t["price"])}</strong></li><li><span>{T("Durée")}</span><strong>{t["duration"]}</strong></li><li><span>{T("Départs")}</span><strong>{esc(t["when"])}</strong></li><li><span>{T("Langues")}</span><strong>{esc(t["langs"])}</strong></li></ul><div class="hero-actions"><a class="btn btn-primary" href="{BOOK}">Réserver la visite</a></div><ul class="reassure"><li>Annulation gratuite jusqu\'à 48 h</li><li>12 personnes maximum</li><li>100 % pistes cyclables</li></ul>')}
<section class="section"><div class="wrap two-col">
  <div class="prose"><h2>Le parcours</h2><ol class="stages">{stops}</ol>{faq_block(qas)}</div>
  <aside class="side"><div class="side-card side-body"><p class="eyebrow">Inclus</p><ul class="ticks">{''.join(f'<li>{esc(i)}</li>' for i in t['included'])}</ul>
  <p class="small"><strong>Rendez-vous :</strong> {esc(t['meet'])}. Venez 10 minutes avant le départ.</p><a class="btn btn-primary" href="{BOOK}">Réserver</a></div></aside>
</div></section>
<section class="section section-tint"><div class="wrap"><h2>Nos autres visites</h2><div class="cards cards-3">{''.join(tour_tile(o) for o in TOURS if o['id'] != t['id'])}</div></div></section>
{blog.blog_block('tour', 'panorama', 'Les lieux de la visite, sur notre blog', extra=BLOG_EXTRA.get(t['id'], ()))}
{cta_band(T('Un groupe, un séminaire ?'), T('Visites privées {price}.', price=offer_price('visites')))}'''
        page(t['url'], t['title'], t['meta'], [CRUMB_HOME, ('Visites guidées', '/fr/visites-guidees-nantes'), (t['name'], None)], body,
             [tour_ld(t), faq_ld(qas)], img=t['img'], priority='0.8',
             brief=T("{name} : visite guidée de Nantes à vélo électrique proposée par Bike'N Tour. Durée {duration}, {price} € par personne ({included}). Départs {when}, en {langs}, 12 personnes maximum par guide, 100 % sur pistes cyclables. Rendez-vous : {meet}.",
                     name=t['name'], duration=t['duration'], price=t['price'], included=', '.join((i[0].lower() + i[1:]) if LANG == 'fr' else i for i in t['included']),
                     when=(t['when'][0].lower() + t['when'][1:]) if LANG == 'fr' else t['when'], langs=langs(t['langs']), meet=t['meet']))


def tour_tile(t):
    return f'''<a class="tile" href="{t['url']}"><img src="/assets/img/{t['img']}" alt="" width="{t['iw']}" height="{t['ih']}" loading="lazy" decoding="async">
<span class="tile-body"><span class="tile-meta"><span class="tag">{esc(t['short'])}</span><span>{t['duration']} · {t['price']} €</span></span><strong>{esc(t['name'])}</strong><span class="small">{esc(t['when'])}</span></span></a>'''


def visits():
    qas = [(T('Combien coûte une visite guidée de Nantes à vélo ?'), T('De {min} € à {max} € par personne selon la visite, vélo électrique, casque et guide compris.', min=TOUR_MIN, max=TOUR_MAX)),
           ('Les visites sont-elles adaptées aux familles ?', 'Oui : le parcours est 100 % sur pistes cyclables et les vélos électriques effacent les écarts de niveau.')]
    body = f'''
{phero('Visites guidées', 'Visites guidées de Nantes à vélo électrique', "Façonnée par son port, Nantes a mille histoires à raconter. Nos guides locaux vous les font découvrir à vélo électrique, en petit groupe et 100 % sur pistes cyclables : en famille, entre amis ou entre collègues.", 'v2-visite-carrousel.webp', 1200, 900, 'Groupe en visite guidée devant le Carrousel des Mondes Marins à Nantes', f'<div class="hero-actions"><a class="btn btn-primary" href="{BOOK}">Réserver une visite</a><a class="btn btn-ghost" href="/fr/offre-groupes-seminaires#visites">Visite privée</a></div>')}
<section class="section"><div class="wrap"><h2>Choisissez votre visite</h2><div class="cards cards-3">{''.join(tour_tile(t) for t in TOURS)}</div>
<ul class="ticks ticks-row"><li>12 personnes maximum par guide</li><li>100 % sur pistes cyclables</li><li>Vélos électriques Sunn à moteur Bosch</li><li>Annulation gratuite jusqu'à 48 h</li></ul></div></section>
<section class="section"><div class="wrap two-col"><div class="prose">
  <h2>Pourquoi visiter Nantes à vélo électrique ?</h2>
  <p>Le vélo est la meilleure façon de découvrir Nantes : le centre historique, l'île de Nantes et les bords de Loire sont reliés par des pistes cyclables, et l'on voit en deux heures ce qu'une journée à pied ne suffirait pas à couvrir.</p>
  <p>Avec l'assistance électrique, personne ne force : les grands enfants, les grands-parents et les sportifs avancent au même rythme. Le guide règle votre vélo au départ et vous montre comment l'utiliser avant de partir.</p>
  <p>Nos guides vivent à Nantes. Ils racontent l'histoire de la ville, des ducs de Bretagne aux Machines de l'île, et partagent leurs adresses préférées pour prolonger la visite.</p>
</div><aside class="side"><div class="side-card side-body"><p class="eyebrow">Une visite privée ?</p><p>Famille, amis, collègues : nous organisons votre visite à l'horaire de votre choix.</p><a class="btn btn-ghost" href="/fr/offre-groupes-seminaires#visites">Demander une visite privée</a></div></aside></div></section>
<section class="section section-tint"><div class="wrap narrow">{faq_block(qas)}</div></section>
{blog.blog_block('tour', 'panorama', 'Nantes à vélo, sur notre blog', extra=('les-titans', 'trentemoult', 'la-butte-saint-anne'))}
{cta_band('Envie de voir Nantes autrement ?', 'Départ au pied de la Tour de Bretagne.')}'''
    page('/fr/visites-guidees-nantes', T("Visite guidée de Nantes à vélo électrique dès {price} € | Bike'N Tour", price=TOUR_MIN),
         T('Visites guidées de Nantes à vélo électrique avec un guide local : {list}. 12 personnes max.', list=', '.join(f"{T(TOUR_LABEL[t['id']]) if t['id'] in TOUR_LABEL else t['name']} ({t['price']} €)" for t in TOURS)),
         [CRUMB_HOME, ('Visites guidées', None)], body, [{"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": {"@id": SITE + t['url'] + '#tour'}} for i, t in enumerate(TOURS)]}, faq_ld(qas)] + [tour_ld(t) for t in TOURS],
         img='v2-visite-carrousel.webp', priority='0.9', kind='CollectionPage',
         brief=T("Bike'N Tour propose trois visites guidées de Nantes à vélo électrique, avec un guide local et 12 personnes maximum : {list}. Vélo électrique et casque compris, parcours 100 % sur pistes cyclables, annulation gratuite jusqu'à 48 h.",
                 list=SEMI.join(T("{name} ({duration}, {price} € par personne)", name=t['name'], duration=t['duration'], price=t['price']) for t in TOURS)))


def groups():
    offers = ''.join(f'''<article class="offer" id="{o['id']}"><h3>{esc(o['name'])}</h3><p class="offer-price">{esc(o['price'])}</p><ul class="ticks">{''.join(f'<li>{esc(i)}</li>' for i in o['items'])}</ul></article>''' for o in GROUP_OFFERS)
    qas = [('Quelle réduction pour un groupe ?', '10 % de remise dès 10 personnes, sur la location comme sur les visites.'),
           ('Livrez-vous les vélos sur le lieu du séminaire ?', 'Oui, dans la métropole nantaise et au-delà sur devis.'),
           ('Que faut-il préciser dans la demande de devis ?', 'Le nombre et le type de vélos, les accessoires, le lieu et l\'horaire de livraison, et si vous souhaitez une visite guidée ou une animation.')]
    svc = [{"@type": "Service", "name": o['name'], "provider": {"@id": BIZ}, "areaServed": "Nantes", "description": '; '.join(o['items'])} for o in GROUP_OFFERS]
    body = f'''
{phero('Groupes et entreprises', 'Sorties à vélo pour groupes et séminaires à Nantes', "Team building, séminaire, sortie d'équipe ou visite entre amis : grâce à l'assistance électrique, tout le monde roule ensemble. Dix ans d'expérience, et une réponse rapide à chaque demande.", 'v2-seminaire-groupe.webp', 1400, 933, 'Groupe d\'entreprise à vélo pendant un séminaire à Nantes', f'<div class="hero-actions"><a class="btn btn-primary" href="mailto:{EMAIL}?subject=Demande%20de%20devis%20groupe">Demander un devis</a><a class="btn btn-ghost" href="tel:{PHONE}">{PHONE_TXT}</a></div>')}
<section class="section"><div class="wrap"><h2>Nos formules</h2><div class="offers">{offers}</div>
<p class="small muted">10 % de réduction dès 10 personnes. Vélos récents fabriqués en Europe, cadenas et kit anti-crevaison pour chaque vélo, protection casse et vol en option.</p></div></section>
<section class="section section-tint"><div class="wrap two-col"><div class="prose">{faq_block(qas)}</div>
<aside class="side"><div class="side-card side-body"><p class="eyebrow">Votre demande</p><p>Indiquez le nombre de participants, la date, le lieu et le type de sortie : nous revenons vers vous rapidement avec une proposition.</p>
<a class="btn btn-primary" href="mailto:{EMAIL}?subject=Demande%20de%20devis%20groupe">{EMAIL}</a></div></aside></div></section>
{cta_band('Un projet de sortie ?', 'On le construit avec vous.')}'''
    page('/fr/offre-groupes-seminaires', 'Team building et séminaire à vélo à Nantes | Bike\'N Tour',
         T("Sorties à vélo pour groupes et entreprises à Nantes : location {location}, visites privées {visits}, team building.", location=offer_price('location'), visits=offer_price('visites')),
         [CRUMB_HOME, ('Groupes et entreprises', None)], body, svc + [faq_ld(qas)], img='v2-seminaire-groupe.webp', priority='0.8',
         brief=T("Bike'N Tour organise à Nantes des sorties à vélo pour les groupes et les entreprises : {list}. 10 % de remise dès 10 personnes, vélos électriques pour que tout le monde roule ensemble, livraison sur le lieu du séminaire.",
                 list=enum([f"{low(o['name'])} {(o['price'][0].lower() + o['price'][1:]) if LANG != 'de' else o['price']}" for o in GROUP_OFFERS], SEMI)))


# =================================================================== à propos, FAQ
def about():
    body = f'''
{phero('Qui sommes-nous', 'Bike\'N Tour, loueur de vélos de voyage à Nantes', "Depuis 10 ans, Antoine et l'équipe de Bike'N Tour préparent les vélos de celles et ceux qui partent à l'aventure au départ de Nantes, et font découvrir la ville à vélo électrique.", 'v2-flotte-boutique.webp', 1400, 933, 'La flotte Bike\'N Tour devant la boutique')}
<section class="section"><div class="wrap two-col">
  <div class="prose" id="histoire">
    <h2>Notre histoire</h2>
    <p>Bike'N Tour est né d'une idée simple : à Nantes, au carrefour de la Loire à Vélo, de la Vélodyssée et des véloroutes bretonnes, il manquait un loueur pensé pour le voyage à vélo. Dix ans plus tard, la boutique de la rue Jean Jaurès prépare chaque saison des centaines de voyageurs, venus de toute la France, des Pays-Bas, d'Allemagne ou d'ailleurs.</p>
    <p>Nous choisissons nos vélos pour l'itinérance, dont plusieurs fabriqués à quelques kilomètres de Nantes par Sunn, nous les contrôlons après chaque location, et nous prenons le temps de vous montrer la route. Nos guides font aussi découvrir Nantes à vélo électrique, en petit groupe.</p>
    <p><strong>[À compléter avec Antoine : date de création, parcours, anecdote.]</strong></p>
    <h2 id="contact">Nous trouver</h2>
    <address class="addr"><strong>Bike'N Tour</strong><br>19 rue Jean Jaurès, 44000 Nantes<br>Dans l'hôtel Ibis Nantes Centre Tour Bretagne<br>Tram T3, arrêt Jean Jaurès · Parking Bretagne<br><a href="tel:{PHONE}">{PHONE_TXT}</a> · <a href="mailto:{EMAIL}">{EMAIL}</a></address>
    <p><a class="arrow-link" href="https://www.google.com/maps/search/?api=1&amp;query=Bike%27N+Tour+19+rue+Jean+Jaur%C3%A8s+Nantes">Ouvrir dans Google Maps</a></p>
  </div>
  <aside class="side"><div class="side-card side-body"><p class="eyebrow">Horaires</p><p>D'avril à octobre, du mardi au dimanche<br>Tous les jours en juillet et août<br><strong>9 h 30 – 12 h · 14 h – 18 h 30</strong></p>
  <p class="small">Retrait en boutique ou livraison dans le centre de Nantes. Paiement en ligne ou en boutique, carte bancaire et chèque.</p>{BOOK_BTN}</div></aside>
</div></section>
{cta_band()}'''
    page('/fr/qui-sommes-nous-nous-contacter', 'Qui sommes-nous et contact | Bike\'N Tour Nantes',
         'Bike\'N Tour, loueur de vélos de voyage et organisateur de visites guidées à Nantes depuis 10 ans : notre histoire, adresse, horaires, accès et contact.',
         [CRUMB_HOME, ('Qui sommes-nous', None)], body, [], img='v2-flotte-boutique.webp', priority='0.6', kind='AboutPage',
         brief=T("Bike'N Tour est un loueur de vélos de voyage, électriques et gravel installé depuis 10 ans au 19 rue Jean Jaurès, 44000 Nantes (dans l'hôtel Ibis Nantes Centre Tour Bretagne, tram T3 arrêt Jean Jaurès). Ouvert d'avril à octobre du mardi au dimanche, tous les jours en juillet et août, de 9 h 30 à 12 h et de 14 h à 18 h 30. Contact : {phone}, {email}.", phone=PHONE_TXT, email=EMAIL))


def faq_page():
    blocks = ''.join(faq_block(qs, title, 'h2') for title, qs in FAQ_FULL)
    allq = [qa for _, qs in FAQ_FULL for qa in qs]
    body = f'''
<section class="phero phero-slim"><div class="wrap"><p class="eyebrow">Questions fréquentes</p><h1>Louer un vélo à Nantes : toutes vos questions</h1>
<p class="lead">Location, réservation, caution, livraison, accès à la boutique : les réponses aux questions qu'on nous pose le plus souvent. Une autre question ? Appelez-nous au <a href="tel:{PHONE}">{PHONE_TXT}</a>. Pour tout comprendre en une page : <a href="/fr/guide-location-velo-nantes">le guide de la location de vélo à Nantes</a>.</p></div></section>
<section class="section"><div class="wrap narrow">{blocks}</div></section>
{cta_band()}'''
    page('/fr/faq-locationdeveloanantes', 'FAQ location de vélo à Nantes | Bike\'N Tour',
         'Location de vélo à Nantes : tarifs, caution, assurance, livraison, aller simple, annulation, horaires et accès à la boutique Bike\'N Tour. Toutes les réponses.',
         [CRUMB_HOME, ('FAQ', None)], body, [faq_ld(allq)], priority='0.7', kind='FAQPage')


# =================================================================== sitemap et fichiers IA
def save_pages():
    """Liste des pages générées dans cette langue (relue par write_seo_files pour le sitemap)."""
    home = i18n.url('/')
    json.dump([(home, '1.0', '/')] + PAGES, open(os.path.join(os.path.dirname(__file__), f'.pages-{LANG}.json'), 'w'))


def write_seo_files():
    save_pages()
    allp = []
    for l in i18n.LANGS:
        p = os.path.join(os.path.dirname(__file__), f'.pages-{l}.json')
        if os.path.exists(p):
            allp += [tuple(x) for x in json.load(open(p))]
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for u, pr, fr in allp:
        xml.append(f'  <url>\n    <loc>{SITE}{u}</loc>\n    <lastmod>{TODAY}</lastmod>\n    <priority>{pr}</priority>')
        alts = i18n.alternates(fr)
        if len(alts) > 1:
            for l, h in alts.items():
                xml.append(f'    <xhtml:link rel="alternate" hreflang="{l}" href="{SITE}{h}"/>')
            xml.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}{fr}"/>')
        xml.append('  </url>')
    xml.append('</urlset>')
    open(os.path.join(ROOT, 'sitemap.xml'), 'w').write('\n'.join(xml) + '\n')

    bots = ['*', 'GPTBot', 'OAI-SearchBot', 'ChatGPT-User', 'ClaudeBot', 'Claude-SearchBot', 'Claude-User', 'PerplexityBot', 'Perplexity-User',
            'Google-Extended', 'Applebot-Extended', 'Amazonbot', 'meta-externalagent', 'DuckAssistBot', 'MistralAI-User']
    open(os.path.join(ROOT, 'robots.txt'), 'w').write(
        '# Moteurs de recherche et assistants IA : bienvenue (mêmes règles pour tous)\n'
        + ''.join(f'User-agent: {b}\n' for b in bots)
        + 'Allow: /\nDisallow: /tools/\nDisallow: /admin/\nDisallow: /cms/\n\n'
        + f'Sitemap: {SITE}/sitemap.xml\n')

    L = [f"# Bike'N Tour", '',
         "> Loueur de vélos de voyage, électriques et gravel installé dans le centre de Nantes (19 rue Jean Jaurès, 44000 Nantes, dans l'hôtel Ibis) depuis 10 ans. Départ de six véloroutes : Loire à Vélo, Vélodyssée, Régalante, Traversée bretonne, Canal de Nantes à Brest, Vignoble nantais. Visites guidées de Nantes à vélo électrique et sorties pour groupes. Noté 5,0/5 sur Google (161 avis) et plus de 200 avis 5 étoiles sur Tripadvisor.",
         '', '## En bref',
         "- Horaires : d'avril à octobre, du mardi au dimanche (tous les jours en juillet et août), 9h30–12h et 14h–18h30",
         f"- Contact : {PHONE_TXT} · {EMAIL} · réservation en ligne : {BOOK}",
         "- Inclus : antivol, kit anti-crevaison, pompe, porte-bagages, éclairage, chargeur (électrique)",
         "- Livraison dans la métropole nantaise : 10 € (jusqu'à 4 vélos) · aller simple : sur devis · annulation gratuite jusqu'à 48 h",
         '', '## Tarifs de location']
    L += [f"- [{b['name']}]({SITE}{b['url']}) ({b['brand']}, {b['model']}) : {b['day']} €/jour, {b['weekend']} € le week-end, {b['week']} € la semaine ; caution {nb(b['deposit'])} €" for b in BIKES]
    L += ['', '## Itinéraires au départ de Nantes']
    L += [f"- [{r['name']}]({SITE}{r['url']}) : {r['dist']}, {r['days']}, niveau {r['level'].lower()}, étapes {' → '.join(r['steps'])}" for r in ROUTES]
    L += [f"- [Idées de balades à la journée]({SITE}/fr/idees-de-balades)", '', '## Visites guidées']
    L += [f"- [{t['name']}]({SITE}{t['url']}) : {t['price']} €/personne, {t['duration']}, {t['when'].lower()}" for t in TOURS]
    L += ['', '## Groupes et entreprises'] + [f"- {o['name']} : {o['price']}" for o in GROUP_OFFERS]
    L += ['', '## Blog : balades et lieux à vélo autour de Nantes', f"- [Tous les articles]({SITE}/fr/blog)"]
    L += [f"- [{p['h1']}]({SITE}{p['url']})" for p in blog.all_posts() if p['cat'] == 'balades'][:12]
    L += ['', '## Other languages / Andere talen / Andere Sprachen',
          f"- English: [{SITE}/en]({SITE}/en) · [bike rental prices]({SITE}{i18n.url('/fr/nos-tarifs-reservation', 'en')}) · [cycle routes from Nantes]({SITE}{i18n.url('/fr/itineraires-velo-depart-nantes', 'en')})",
          f"- Nederlands: [{SITE}/nl]({SITE}/nl) · [prijzen fietsverhuur]({SITE}{i18n.url('/fr/nos-tarifs-reservation', 'nl')}) · [fietsroutes vanuit Nantes]({SITE}{i18n.url('/fr/itineraires-velo-depart-nantes', 'nl')})",
          f"- Deutsch: [{SITE}/de]({SITE}/de) · [Preise Fahrradverleih]({SITE}{i18n.url('/fr/nos-tarifs-reservation', 'de')}) · [Radrouten ab Nantes]({SITE}{i18n.url('/fr/itineraires-velo-depart-nantes', 'de')})"]
    L += ['', '## Pages utiles', f"- [Tarifs]({SITE}/fr/nos-tarifs-reservation)", f"- [FAQ]({SITE}/fr/faq-locationdeveloanantes)", f"- [Guide : louer un vélo à Nantes]({SITE}{GUIDE})", f"- [Contact et accès]({SITE}/fr/qui-sommes-nous-nous-contacter)", f"- [Version détaillée pour les IA]({SITE}/llms-full.txt)",
          '', "Chaque page du site existe aussi en Markdown : ajouter `.md` à l'adresse (ex. " + SITE + "/fr/nos-tarifs-reservation.md, " + SITE + "/index.md pour l'accueil)."]
    open(os.path.join(ROOT, 'llms.txt'), 'w').write('\n'.join(L) + '\n')

    F = ['\n'.join(L), '', '## Faits clés', f"- {fleet_brief()}"]
    F += [f"- {route_brief(r, [b for b in BIKES if r['id'] in b['good']])}" for r in ROUTES]
    F += ['', '## FAQ complète']
    for title, qs in FAQ_FULL:
        F.append(f'\n### {title}')
        F += [f'**{q}**\n{re.sub(r"<[^>]+>", "", a)}\n' for q, a in qs]
    F.append('\n## Détail des itinéraires')
    for r in ROUTES:
        x = ROUTE_EXTRA[r['id']]
        F.append(f"\n### {r['name']}\n{x['intro']}\nÉtapes conseillées : " + SEMI.join(f'{a} ({t})' for a, t in x['stages']) + f"\nRetour : {x['back']}")
    F.append('\n## Balades à la journée')
    F += [f"- {b['name']} : {b['km']}, {b['time'].lower()}, niveau {b['level'].lower()}. {b['text']} {b['back']}." for b in BALADES]
    F.append('\n## Articles du blog')
    for k, name, _ in blog.CATS:
        F.append(f'\n### {name}')
        F += [f"- [{p['h1']}]({SITE}{p['url']}) : {p['meta']}" for p in blog.all_posts() if p['cat'] == k]
    open(os.path.join(ROOT, 'llms-full.txt'), 'w').write('\n'.join(F) + '\n')




# =================================================================== guide pilier (GEO)
GUIDE = '/fr/guide-location-velo-nantes'


def guide():
    A = {q: a for _, qs in FAQ_FULL for q, a in qs}
    bikes_rows = ''.join(f'<tr><th scope="row"><a href="{b["url"]}">{esc(b["name"])}</a></th><td>{esc(b["brand"].split(" (")[0])} {esc(b["model"])}</td><td>{b["day"]} €</td><td>{b["weekend"]} €</td><td>{b["week"]} €</td><td>{nb(b["deposit"])} €</td></tr>' for b in BIKES)
    use_rows = ''.join(f'<tr><th scope="row"><a href="{b["url"]}">{esc(b["name"])}</a></th><td>{esc(b["why"])}</td></tr>' for b in BIKES)
    route_rows = ''.join(f'<tr><th scope="row"><a href="{r["url"]}">{esc(r["name"])}</a></th><td>{esc(r["km"])}</td><td>{esc(r["days"])}</td><td>{lvl(r["level"])}</td><td>{esc(" → ".join(r["steps"]))}</td></tr>' for r in ROUTES)
    tours_txt = enum([T('{name} ({duration}, {price} € par personne)', name=f'<a href="{t["url"]}">{esc(t["name"])}</a>', duration=t["duration"], price=t["price"]) for t in TOURS], SEMI)
    acc = enum([T('{name} ({price} € par jour)', name=n[0].lower() + n[1:], price=p) for n, p in ACCESSORIES])
    acc = acc[0].upper() + acc[1:]
    qa = [
        ('Où louer un vélo à Nantes pour partir en voyage ?',
         f"Chez Bike'N Tour, au 19 rue Jean Jaurès, 44000 Nantes, dans l'hôtel Ibis Nantes Centre Tour Bretagne : la boutique est en plein centre-ville, desservie par le tram T3 (arrêt Jean Jaurès) et proche du parking Bretagne. Elle est ouverte d'avril à octobre, du mardi au dimanche (tous les jours en juillet et août), de 9 h 30 à 12 h et de 14 h à 18 h 30. Six grandes véloroutes partent de là : la Loire à Vélo, la Vélodyssée, la Régalante, la Traversée bretonne, le Canal de Nantes à Brest et le Vignoble nantais.",
         ''),
        ('Combien coûte la location d\'un vélo à Nantes ?',
         T("Chez Bike'N Tour, la location à la journée coûte {list}. Les tarifs sont dégressifs : un vélo de voyage coûte {week} € la semaine, un vélo électrique {eweek} €.",
           list=enum([T("{price} € pour un vélo {kind}", price=b['day'], kind=kind(b) if LANG == 'fr' else low(b['name'])) for b in sorted(BIKES, key=lambda b: b['day'])]),
           week=BIKE['voyage']['week'], eweek=BIKE['electrique']['week']),
         f'<div class="table-wrap"><table class="data"><thead><tr><th scope="col">Vélo</th><th scope="col">Modèle</th><th scope="col">1 jour</th><th scope="col">Week-end</th><th scope="col">Semaine</th><th scope="col">Caution</th></tr></thead><tbody>{bikes_rows}</tbody></table></div><p class="small muted">Tous les tarifs jour par jour : <a href="/fr/nos-tarifs-reservation">page Tarifs</a>.</p>'),
        ('Quel vélo choisir pour son voyage ?',
         "Le vélo de voyage suffit pour les itinéraires plats comme la Loire à Vélo ou la Vélodyssée ; le vélo électrique est conseillé pour les longues étapes, les itinéraires vallonnés comme la Traversée bretonne et les couples aux niveaux différents ; le gravel convient aux chemins en stabilisé du Vignoble nantais et du Canal de Nantes à Brest.",
         f'<div class="table-wrap"><table class="data"><thead><tr><th scope="col">Vélo</th><th scope="col">Pour quels voyages ?</th></tr></thead><tbody>{use_rows}</tbody></table></div>'),
        ('Quels itinéraires à vélo partent de Nantes ?',
         "Six véloroutes partent du centre de Nantes, de 80 km (le Vignoble nantais, en boucle) à 485 km (la Traversée bretonne jusqu'au Mont-Saint-Michel). La Loire à Vélo jusqu'à Saumur (165 km, 3 à 4 jours) est la plus simple pour un premier voyage.",
         f'<div class="table-wrap"><table class="data"><thead><tr><th scope="col">Itinéraire</th><th scope="col">Distance</th><th scope="col">Durée conseillée</th><th scope="col">Niveau</th><th scope="col">Étapes</th></tr></thead><tbody>{route_rows}</tbody></table></div><p class="small muted">Distances calculées sur les tracés officiels France Vélo Tourisme depuis la boutique. Pour une seule journée : <a href="/fr/idees-de-balades">{len(BALADES)} idées de balades</a>.</p>'),
        ('Que comprend la location ?',
         T("Chaque vélo est loué avec {list}. À la demande, Bike'N Tour envoie aussi par email la fiche de l'itinéraire et la trace GPX.", list=enum([i[0].lower() + i[1:] for i in INCLUDED])),
         '<p>' + T('Accessoires en option : {list}.', list=acc) + '</p>'),
        ('Peut-on rendre le vélo dans une autre ville (aller simple) ?',
         "Oui : Bike'N Tour organise la récupération des vélos à l'arrivée, sur la Loire à Vélo, la Vélodyssée, la Régalante ou en Bretagne, avec ses partenaires. Le tarif est établi sur devis selon les dates et le lieu de dépôt ; il vaut mieux le demander à l'avance.",
         '<p><a class="arrow-link" href="/fr/nos-velos-location#aller-simple">L\'option aller simple en détail</a></p>'),
        ('Peut-on se faire livrer les vélos à l\'hôtel ou à la gare ?',
         "Oui, Bike'N Tour livre et récupère les vélos dans la métropole nantaise (hôtel, gîte, location ou gare de Nantes) pour 10 € par livraison, jusqu'à 4 vélos.", ''),
        ('Quelle caution et quelle assurance ?',
         T("La caution est de {deposits}, plafonnée à {cap} € pour plusieurs vélos. Une protection casse et vol est proposée en option : {protections}.",
           deposits=grouped('deposit', lambda v: f'{nb(v)} €'), cap=nb(2000), protections=grouped('protect', lambda v: T('{price} € par jour', price=v))), ''),
        ('Comment réserver et peut-on annuler ?',
         f"La réservation se fait en ligne sur <a href=\"{BOOK}\">bike-n-tour.lokki.rent</a>, par téléphone au {PHONE_TXT} ou en boutique. L'annulation est gratuite jusqu'à 48 h avant le départ. Le paiement se fait en ligne ou en boutique, par carte bancaire ou chèque.", ''),
        ('Peut-on visiter Nantes à vélo avec un guide ?',
         T("Oui : Bike'N Tour propose trois visites guidées à vélo électrique, en petit groupe de 12 personnes maximum et 100 % sur pistes cyclables : {list}.", list=tours_txt),
         '<p><a class="arrow-link" href="/fr/visites-guidees-nantes">Toutes les visites guidées</a></p>'),
        ('Et pour un groupe ou une entreprise ?',
         T("Bike'N Tour organise des sorties pour les groupes et les séminaires : location {location}, visites guidées privées {visits}, team building {events}, et 10 % de remise dès 10 personnes.",
           location=offer_price('location'), visits=offer_price('visites'), events=offer_price('animations')),
         '<p><a class="arrow-link" href="/fr/offre-groupes-seminaires">Offre groupes et entreprises</a></p>'),
    ]
    toc = ''.join(f'<li><a href="#q{i + 1}">{esc(q)}</a></li>' for i, (q, _, _) in enumerate(qa))
    secs = ''.join(f'<section class="guide-q" id="q{i + 1}"><h2>{esc(q)}</h2><p class="answer">{a}</p>{more}</section>' for i, (q, a, more) in enumerate(qa))
    body = f"""
<section class="phero phero-slim"><div class="wrap"><p class="eyebrow">Le guide</p><h1>Louer un vélo à Nantes&nbsp;: le guide complet</h1>
<p class="lead">Prix, choix du vélo, itinéraires au départ de Nantes, aller simple, livraison, caution : tout ce qu'il faut savoir avant de louer un vélo pour une balade ou un voyage, par l'équipe de Bike'N Tour.</p></div></section>
<section class="section"><div class="wrap two-col">
  <div class="prose guide">{secs}</div>
  <aside class="side"><nav class="side-card side-body" aria-label="Sommaire du guide"><p class="eyebrow">Sommaire</p><ol class="toc">{toc}</ol>{BOOK_BTN}</nav></aside>
</div></section>
{cta_band()}"""
    page(GUIDE, "Louer un vélo à Nantes : prix et conseils | Bike'N Tour",
         T('Guide pour louer un vélo à Nantes : prix de {min} à {max} € la journée, quel vélo choisir, 6 itinéraires au départ de Nantes, aller simple, livraison, caution.', min=MIN_DAY, max=MAX_DAY),
         [CRUMB_HOME, ('Guide de la location', None)], body,
         [faq_ld([(q, a) for q, a, _ in qa])], img='v2-depart-boutique.webp', priority='0.9',
         brief=T("Pour louer un vélo à Nantes et partir en voyage, Bike'N Tour (19 rue Jean Jaurès, centre-ville) loue {list} la journée, avec livraison à 10 €, aller simple sur devis et annulation gratuite jusqu'à 48 h. Six véloroutes partent de la boutique, dont la Loire à Vélo (165 km jusqu'à Saumur).",
                 list=enum([T("des {bikes} dès {price} €", bikes=PLURAL[b['id']] if LANG == 'fr' else low(b['name']), price=b['day']) for b in BIKES])))


# =================================================================== cookies
def cookies():
    rows = [("bnt_consent", "Bike'N Tour", "Mémorise votre choix sur les cookies (accepté ou refusé).", "6 mois", "Nécessaire")]
    if SITE_CFG.get('analytics_ga4'):
        rows += [("_ga, _ga_*", "Google Analytics", "Mesure d'audience : pages vues, durée de visite, provenance. Adresse IP anonymisée.", "13 mois", "Avec votre accord")]
    if SITE_CFG.get('matomo_url') and SITE_CFG.get('matomo_id'):
        rows += [("_pk_id, _pk_ses", "Matomo", "Mesure d'audience : pages vues, durée de visite, provenance.", "13 mois", "Avec votre accord")]
    trs = ''.join(f'<tr><th scope="row">{esc(a)}</th><td>{esc(b)}</td><td>{esc(c)}</td><td>{esc(d)}</td><td>{esc(e)}</td></tr>' for a, b, c, d, e in rows)
    body = f"""
<section class="phero phero-slim"><div class="wrap"><p class="eyebrow">Vie privée</p><h1>Cookies et mesure d'audience</h1>
<p class="lead">Nous déposons le moins de cookies possible : aucun cookie publicitaire, et aucun cookie de mesure d'audience sans votre accord.</p></div></section>
<section class="section"><div class="wrap narrow prose">
  <h2>Votre choix</h2>
  <p>Vous pouvez accepter ou refuser la mesure d'audience, et changer d'avis à tout moment. Votre choix est conservé 6 mois, puis nous vous le redemandons.</p>
  <p><button type="button" class="btn btn-primary" data-cc-open>Gérer mes cookies</button></p>
  <h2>Les cookies utilisés sur ce site</h2>
  <div class="table-wrap"><table class="data"><thead><tr><th scope="col">Nom</th><th scope="col">Éditeur</th><th scope="col">Finalité</th><th scope="col">Durée</th><th scope="col">Statut</th></tr></thead><tbody>{trs}</tbody></table></div>
  <h2>Réservation en ligne</h2>
  <p>Le bouton « Réserver mes vélos » ouvre le site de réservation de notre partenaire Lokki, qui applique sa propre politique de cookies.</p>
  <h2>Vos droits</h2>
  <p>Pour toute question sur vos données personnelles, écrivez-nous à <a href="mailto:{EMAIL}">{EMAIL}</a>. Vous pouvez aussi adresser une réclamation à la CNIL (cnil.fr).</p>
</div></section>"""
    page('/fr/cookies', "Cookies et mesure d'audience | Bike'N Tour",
         "Cookies utilisés sur bikentour.com : aucun cookie publicitaire, mesure d'audience uniquement avec votre accord. Gérer ou retirer votre consentement.",
         [CRUMB_HOME, ('Cookies', None)], body, [], priority='0.2')


import blog  # en fin de module : blog.py importe lui-même pages.py
