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
MAP = open('map.inc').read()  # généré par geo2.py

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
              <p class="rc-bike"><strong>Vélo conseillé :</strong> {r['bike']}</p>
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
        n['geo'] = {"@type": "GeoCoordinates", "latitude": 47.2178, "longitude": -1.5603}
        n['areaServed'] = [{"@type": "City", "name": "Nantes"}, {"@type": "AdministrativeArea", "name": "Loire-Atlantique"}]
    if n['@type'] == 'WebSite':
        n['inLanguage'] = 'fr'  # EN/NL/DE à rajouter à la mise en ligne des traductions
    if n['@type'] == 'WebPage':
        n['dateModified'] = __import__('datetime').date.today().isoformat()
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
for _k in ('reservation', 'telephone', 'telephone_affiche', 'analytics_ga4', 'matomo_url', 'matomo_id'):
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
page = replace_lang_switch(page, '/', FLAGS, CHEV).replace('<!--ALT-->', head_links('/'))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w').write(page)
print('ok', len(page))
