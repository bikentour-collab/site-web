"""Construit index.html de la proposition 3 (carte interactive)."""
import json, re, html

import os
from i18n import LANG as _LANG
OUT = '../index.html' if _LANG == 'fr' else f'../{_LANG}/index.html'
STATS = json.load(open('routes_stats.json'))
ICONS = json.load(open('route_icons.json'))


LEVELS = {'Facile': 1, 'Modéré': 2, 'Difficile': 3}


def lvl(level, cls='lvl'):
    n = LEVELS[level]
    bars = ''.join(f'<rect x="{1 + k * 5}" y="{10 - (k + 1) * 3}" width="3.4" height="{(k + 1) * 3}" rx="1"{" class=\"on\"" if k < n else ""}/>' for k in range(3))
    return f'<span class="{cls} lvl-{n}"><svg viewBox="0 0 16 11" aria-hidden="true">{bars}</svg>{T(level)}</span>'


def ico(rid, cls='trace-ico'):
    i = ICONS[rid]
    return (f'<svg class="{cls} ti-{rid}" viewBox="0 0 32 32" aria-hidden="true"><path d="{i["d"]}"/>'
            f'<circle class="ti-start" cx="{i["start"][0]}" cy="{i["start"][1]}" r="2.6"/>'
            + ('' if rid == 'vignoble' else f'<circle class="ti-end" cx="{i["end"][0]}" cy="{i["end"][1]}" r="2.2"/>') + '</svg>')
from content_routes import map_svg
from i18n import LANG as _L
MAP = map_svg(_L)  # tracés générés par geo2.py + points de vue (content/fr/itineraires.json)

from content_routes import ROUTES

def route_btn(r, i):
    return f'''          <li data-duration="{r['dur']}"><button type="button" class="route-btn" data-route="{r['id']}" aria-controls="r-{r['id']}" aria-pressed="{'true' if i == 0 else 'false'}"><span class="rb-text"><strong>{r['name']}</strong><span>{r['short']}</span></span>{lvl(r['level'])}<span class="rb-meta"><strong>{r['km']}</strong><span>{r['days']}</span></span></button></li>'''


def sparkline(rid):
    p = STATS[rid]['profile']
    lo, hi = min(p), max(p)
    span = max(hi - lo, 40)
    w, h = 300, 54
    pts = ' '.join(f'{k * w / (len(p) - 1):.1f},{h - 4 - (v - lo) / span * (h - 10):.1f}' for k, v in enumerate(p))
    return (f'<figure class="rc-profile"><svg viewBox="0 0 {w} {h}" preserveAspectRatio="none" aria-hidden="true">'
            f'<polygon points="0,{h} {pts} {w},{h}"/><polyline points="{pts}"/></svg>'
            f'<figcaption>Profil · altitude de {lo} à {hi} m</figcaption></figure>')


def _post_img(slug):
    """Photo de couverture d'un article du blog (variante 480 px si elle existe)."""
    import yaml
    f = os.path.join('..', 'content', 'blog', slug + '.md')
    if not os.path.exists(f):
        return None
    m = re.match(r'^---\s*\n(.*?)\n---', open(f, encoding='utf-8').read(), re.S)
    src = m and (yaml.safe_load(m.group(1)) or {}).get('image')
    if not src:
        return None
    name = src.split('/assets/img/', 1)[-1]
    small = name[:-5] + '-w480.webp'
    return small if os.path.exists(os.path.join('..', 'assets', 'img', small)) else name


def poi_strip(r):
    """Points de vue de l'itinéraire, en photos (tirées des articles du blog)."""
    items = []
    for p in (r.get('points') or []):
        img = _post_img(p['article']) if p.get('article') else None
        if img:
            items.append(f'<li><a href="/post/{p["article"]}"><img src="/assets/img/{img}" alt="" width="480" height="320" loading="lazy" decoding="async"><span>{html.escape(p["nom"])}</span></a></li>')
    if not items:
        return ''
    return f'<div class="rc-pois"><p class="rc-pois-title">À voir en chemin</p><ul>{"".join(items[:3])}</ul></div>'


def route_card(r, i):
    steps = '<span aria-hidden="true">→</span>'.join(f'<li>{html.escape(s)}</li>' for s in r['steps'])
    steps = ''.join(f'<li>{html.escape(s)}</li>' for s in r['steps'])
    hidden = '' if i == 0 else ' hidden'
    one = 'Oui, sur demande' if r['oneway'] else 'Boucle, retour à Nantes'
    return f'''          <article class="route-card" id="r-{r['id']}" data-card="{r['id']}"{hidden}>
            <div class="rc-media"><img src="/assets/img/{r['img']}" alt="{html.escape(r['alt'])}" width="{r['iw']}" height="{r['ih']}" loading="lazy" decoding="async"><span class="rc-chip">{lvl(r['level'], 'lvl lvl-chip')}<span>{r['km']} · {r['days']}</span></span></div>
            <div class="rc-body">
              <p class="rc-tag sw-{r['color']}-text">Au départ de la boutique</p>
              <h3>{r['name']}</h3>
              <p class="rc-desc">{r['desc']}</p>
              <dl class="rc-stats">
                <div><dt>Distance</dt><dd>{r['dist']}</dd></div>
                <div><dt>Durée conseillée</dt><dd>{r['days']}</dd></div>
                <div><dt>Niveau</dt><dd>{lvl(r['level'])}</dd></div>
                <div><dt>Aller simple</dt><dd>{one}</dd></div>
              </dl>
              {sparkline(r['id'])}
              <ol class="rc-steps" aria-label="Principales étapes">{steps}</ol>
              {poi_strip(r)}
              <div class="rc-actions">
                <a class="btn btn-primary" href="https://bike-n-tour.lokki.rent">Réserver mes vélos</a>
                <a class="btn btn-ghost" href="{r['url']}">L'itinéraire détaillé</a>
              </div>
            </div>
          </article>'''

from i18n import FLAGS, CHEV, LANG, T, localize_html, replace_lang_switch, head_links

from content import FAQ_HOME as FAQ, HOME

faq_html = '\n'.join(f'''          <details{' open' if i == 0 else ''}>
            <summary><h3>{q}</h3></summary>
            <p>{a}</p>
          </details>''' for i, (q, a) in enumerate(FAQ))

# --- JSON-LD (reprend la base des propositions précédentes, adaptée)
src = open('../index.html').read()
data = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', src, re.S).group(1))
for n in data['@graph']:
    if n['@type'] == 'FAQPage':
        n['mainEntity'] = [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]
    if n['@type'] == 'BikeStore':
        n['aggregateRating']['ratingValue'] = str(HOME['google_note']).replace(',', '.')
        n['aggregateRating']['reviewCount'] = n['aggregateRating']['ratingCount'] = str(HOME['google_avis'])
        n['geo'] = {"@type": "GeoCoordinates", "latitude": 47.2238, "longitude": -1.5548}
        n['address'] = {"@type": "PostalAddress", "streetAddress": "27 quai de Versailles", "postalCode": "44000", "addressLocality": "Nantes", "addressRegion": "Pays de la Loire", "addressCountry": "FR"}
        from content import PRESS, REFS
        n['subjectOf'] = ([{"@type": "NewsArticle", "headline": t, "url": u, "publisher": {"@type": "Organization", "name": m}} for m, t, u in PRESS]
                          + [{"@type": "WebPage", "name": t, "url": u, "publisher": {"@type": "Organization", "name": m}} for m, t, u in REFS])
        from content import SITE_CFG as _SC
        _same = ["https://www.instagram.com/bikentour_nantes/", "https://www.facebook.com/BikentourNantes", "https://www.linkedin.com/company/bike'n-tour/",
                 "https://www.francevelotourisme.com/pratique/loueurs-reparateurs-de-velo/bike-n-tour-nantes"]
        _same += [u for u in (_SC.get('lien_tripadvisor'), _SC.get('lien_fiche_google')) if u]
        n['sameAs'] = _same
        n['areaServed'] = [{"@type": "City", "name": "Nantes"}, {"@type": "AdministrativeArea", "name": "Loire-Atlantique"}]
        n['description'] = "Loueur de vélos de voyage, électriques et gravel à Nantes, au départ de la Loire à Vélo, de la Vélodyssée, de la Régalante, de la Traversée bretonne et du Canal de Nantes à Brest. Location en aller simple (One Way), accessoires (sacoches Ortlieb, casque), visites guidées et animations à vélo pour les groupes."
        import datetime as _dt
        _y = _dt.date.today().year + (1 if _dt.date.today() > _dt.date(_dt.date.today().year, 10, 31) else 0)
        for _o in n.get('openingHoursSpecification') or []:  # boutique ouverte d'avril à octobre
            _o['validFrom'], _o['validThrough'] = f'{_y}-04-01', f'{_y}-10-31'
        n['hasMap'] = 'https://www.google.com/maps/search/?api=1&query=Bike%27N+Tour+27+quai+de+Versailles+Nantes'
        _wa = _SC.get('whatsapp')
        n['contactPoint'] = [{"@type": "ContactPoint", "telephone": _SC.get('telephone') or '+33652629464', "email": _SC.get('email'), "contactType": "customer service",
                              "availableLanguage": ["French", "English"]}] + ([{"@type": "ContactPoint", "contactType": "customer service", "name": "WhatsApp",
                              "url": f"https://wa.me/{_wa}", "availableLanguage": ["French", "English"]}] if _wa else [])
        from content import BIKES as _BK, ACCESSORIES as _AC
        n['hasOfferCatalog'] = {"@type": "OfferCatalog", "name": "Location de vélos et accessoires à Nantes", "itemListElement": [
            {"@type": "Offer", "name": b['name'], "url": 'https://www.bikentour.com' + b['url'], "price": str(b['day']), "priceCurrency": "EUR",
             "priceSpecification": {"@type": "UnitPriceSpecification", "price": str(b['day']), "priceCurrency": "EUR", "unitCode": "DAY"}} for b in _BK]
            + [{"@type": "Offer", "name": a, "price": str(p), "priceCurrency": "EUR",
                "priceSpecification": {"@type": "UnitPriceSpecification", "price": str(p), "priceCurrency": "EUR", "unitCode": "DAY"}} for a, p in _AC]}
    if n['@type'] == 'WebSite':
        n['inLanguage'] = 'fr'  # EN/NL/DE à rajouter à la mise en ligne des traductions
    if n['@type'] == 'WebPage':
        n['dateModified'] = '{{LASTMOD_ISO}}'  # vraie date de dernière modification, posée par postprocess.py
        n['primaryImageOfPage'] = 'https://www.bikentour.com/assets/img/v2-bord-de-loire.webp'
    if n['@type'] == 'ItemList':
        n['itemListElement'] = [{"@type": "ListItem", "position": i + 1, "item": {"@type": "TouristTrip", "name": r['name'], "description": r['desc'],
            "url": 'https://www.bikentour.com' + r['url'], "provider": {"@id": "https://www.bikentour.com/#business"},
            "itinerary": {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": j + 1, "item": {"@type": "Place", "name": s}} for j, s in enumerate(r['steps'])]}}}
            for i, r in enumerate(ROUTES)]
jsonld = json.dumps(data, ensure_ascii=False, indent=2)

tpl = open('page.tpl.html').read()
if LANG != 'fr':
    tpl = localize_html(tpl)  # phrases fixes du gabarit, avant l'insertion des données
page = (tpl.replace('<!--JSONLD-->', f'<script type="application/ld+json">\n{jsonld}\n</script>')
           .replace('<!--MAP-->', MAP)
           .replace('<!--ROUTE_BTNS-->', '\n'.join(route_btn(r, i) for i, r in enumerate(ROUTES)))
           .replace('<!--ROUTE_CARDS-->', '\n'.join(route_card(r, i) for i, r in enumerate(ROUTES)))
           .replace('<!--FAQ-->', faq_html)
           .replace('{{FLAG_FR}}', FLAGS['fr']).replace('{{FLAG_EN}}', FLAGS['en']).replace('{{FLAG_NL}}', FLAGS['nl']).replace('{{FLAG_DE}}', FLAGS['de'])
           .replace('{{CHEV}}', CHEV))
# textes de l'accueil modifiables dans l'admin (content/accueil.json)
for k in ('hero_surtitre', 'hero_titre_ligne1', 'hero_titre_ligne2', 'hero_titre_accent', 'hero_texte', 'hero_image_alt', 'google_note', 'google_avis', 'tripadvisor_avis'):
    page = page.replace('{{' + k + '}}', html.escape(str(HOME[k]), quote=True))
# coordonnées, réservation et mesure d'audience (content/site.json)
from content import SITE_CFG
_TRIPA = SITE_CFG.get('lien_tripadvisor') or 'https://www.tripadvisor.fr/Search?q=Bike%27N%20Tour%20Nantes'
_GOOG = SITE_CFG.get('lien_google_avis') or 'https://www.google.com/search?q=bike%27n+tour+nantes+avis'
page = page.replace('{{lien_tripadvisor}}', html.escape(_TRIPA, quote=True)).replace('{{lien_google_avis}}', html.escape(_GOOG, quote=True))
for _k in ('reservation', 'telephone', 'telephone_affiche', 'whatsapp', 'analytics_ga4', 'matomo_url', 'matomo_id'):
    page = page.replace('{{' + _k + '}}', html.escape(str(SITE_CFG.get(_k) or ''), quote=True))
# prix affichés sur l'accueil (content/velos.json, visites.json, groupes.json)
from content import BIKES, TOURS, GROUP_OFFERS
_bk = {x['id']: x for x in BIKES}
for _k in ('electrique', 'voyage', 'gravel', 'enfant'):
    page = page.replace('{{prix_' + _k + '}}', str(_bk[_k]['day']))
_loc = next((o['price'] for o in GROUP_OFFERS if o['id'] == 'location'), 'Sur devis')
page = (page.replace('{{protection_min}}', str(min(x['protect'] for x in BIKES if x.get('protect'))))
            .replace('{{visite_min}}', str(min(x['price'] for x in TOURS)))
            .replace('{{groupe_location}}', html.escape('Dès ' + _m.group(1) if (_m := re.search(r'([\d,.]+\s*€(?:\s*HT)?)', _loc)) else _loc)))
page = (page.replace('{{hero_image}}', '/assets/img/' + HOME['hero_image'])
            .replace('{{hero_iw}}', str(HOME['iw'])).replace('{{hero_ih}}', str(HOME['ih'])))
for rid in ICONS:
    page = page.replace('<span class="swatch sw-' + {'loire':'loire','velodyssee':'velodyssee','regalante':'regalante','traversee':'traversee','canal':'canal','vignoble':'vignoble'}[rid] + '" aria-hidden="true"></span>', '')
if LANG != 'fr':
    page = localize_html(page)  # phrases insérées avec les données (cartes, FAQ…)
# titres des articles mis en avant : toujours ceux du blog (et de leur traduction)
def _post_title(m):
    import yaml
    base = os.path.join('..', 'content', 'blog')
    for f in ([os.path.join(base, LANG, m.group(1) + '.md')] if LANG != 'fr' else []) + [os.path.join(base, m.group(1) + '.md')]:
        if os.path.exists(f):
            fm = re.match(r'^---\s*\n(.*?)\n---', open(f, encoding='utf-8').read(), re.S)
            if fm and (yaml.safe_load(fm.group(1)) or {}).get('titre'):
                return html.escape(str(yaml.safe_load(fm.group(1))['titre']))
    return m.group(1)
# accessoires en location (content/fr/velos.json)
from content import ACCESSORIES
_acc = [a for a in ACCESSORIES if not any(k in a[0].lower() for k in ('siège', 'remorque'))]
page = page.replace('<!--ACCESSOIRES-->', '<ul class="acc-list">' + ''.join(f'<li>{html.escape(n)} <b>{T("{price} € / jour", price=p)}</b></li>' for n, p in _acc) + '</ul>')
_QM = {'fr': ('« ', ' »'), 'en': ('“', '”'), 'nl': ('“', '”'), 'de': ('„', '“'), 'es': ('«', '»')}.get(_L, ('« ', ' »'))
_RN = {r['id']: r['name'] for r in ROUTES}
def _avis(x):
    who = html.escape(x.get('auteur') or '')
    tag = (f' · <button type="button" data-goto="{html.escape(x["itineraire"])}">{html.escape(_RN[x["itineraire"]])}</button>'
           if x.get('itineraire') in _RN else ' · Google')
    return f'<blockquote><p>{_QM[0]}{html.escape(x.get("texte") or "")}{_QM[1]}</p><footer>{who}{tag}</footer></blockquote>'
page = page.replace('<!--AVIS-->', ''.join(_avis(x) for x in (HOME.get('avis') or [])[:3]))
page = re.sub(r'\{\{post_titre:([a-z0-9-]+)\}\}', _post_title, page)
page = replace_lang_switch(page, '/', FLAGS, CHEV).replace('<!--ALT-->', head_links('/'))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w').write(page)
print('ok', len(page))
