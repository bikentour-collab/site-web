"""Blog : articles /post/<slug> et index /fr/blog.
Contenu : content/blog/<slug>.md (modifiable dans l'admin /admin), en-tête YAML + texte en Markdown."""
import re, os, datetime
import yaml, markdown
from PIL import Image
import pages
from pages import page, esc, cta_band, lvl, BOOK_BTN, CRUMB_HOME, ROUTE, BIZ, SITE
from i18n import T
from content import BIKES, TOURS

BLOGDIR = os.path.join(pages.ROOT, 'content', 'blog')
BIKE = {b['id']: b for b in BIKES}
TOUR = {t['id']: t for t in TOURS}
BLOG = '/fr/blog'
MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']

CATS = [('balades', 'Balades à vélo', 'Itinéraires à la journée au départ de Nantes, avec distance, durée et niveau.'),
        ('nantes', 'À voir à Nantes', 'Lieux, quartiers et monuments à découvrir à vélo, en ville et aux portes de Nantes.'),
        ('conseils', 'Conseils et voyage à vélo', 'Voyage à vélo, vélo électrique, vélo cargo, slow tourisme.')]
CATNAME = {k: n for k, n, _ in CATS}

# Choix « automatique » de la page à mettre en avant à côté d'un article (maillage interne)
CTA_RULES = [(('assistance-electrique',), 'bike', 'electrique'), (('cargo',), 'bike', 'cargo'),
             (('sevre', 'vignoble', 'goulaine'), 'route', 'vignoble'), (('erdre',), 'route', 'canal'),
             (('loire', 'mauves', 'oudon', 'indre', 'cordemais', '2-bacs', 'estuaire', 'creature', 'chassay'), 'route', 'loire'),
             (('grand-lieu', 'pornic', 'baule', 'guerande'), 'route', 'velodyssee'),
             (('voyage-a-velo', 'slow-tourisme', 'top-5', 'cyclable'), 'hub', None),
             (('little-atlantique',), 'tour', 'urbain')]


def cta_target(slug, lien='auto'):
    if lien and lien != 'auto':
        kind, _, ident = lien.partition(':')
        ok = {'route': ROUTE, 'bike': BIKE, 'tour': TOUR}
        if kind == 'hub' or ident in ok.get(kind, {}):
            return kind, ident or None
    for keys, kind, ident in CTA_RULES:
        if any(k in slug for k in keys):
            return kind, ident
    return 'tour', 'panorama'


# Textes des articles traduits (le reste de la page passe par le catalogue i18n)
L10N = {
    'en': {'cat': {'balades': 'Bike rides', 'nantes': 'Things to see in Nantes', 'conseils': 'Cycling tips'},
           'upd': 'Updated', 'pub': 'Published', 'sign': "by the Bike'N Tour team, bike hire at 19 rue Jean Jaurès in Nantes.",
           'also': 'Also on our blog', 'band': ('Fancy riding there?', 'We get your bike ready in Nantes.'), 'block': 'From our blog'},
    'nl': {'cat': {'balades': 'Fietstochten', 'nantes': 'Bezienswaardigheden in Nantes', 'conseils': 'Fietstips'},
           'upd': 'Bijgewerkt op', 'pub': 'Gepubliceerd op', 'sign': "door het team van Bike'N Tour, fietsverhuur aan de rue Jean Jaurès 19 in Nantes.",
           'also': 'Ook op onze blog', 'band': ('Zin om erheen te fietsen?', 'Wij zetten uw fiets klaar in Nantes.'), 'block': 'Van onze blog'},
    'de': {'cat': {'balades': 'Radtouren', 'nantes': 'Sehenswertes in Nantes', 'conseils': 'Tipps zum Radreisen'},
           'upd': 'Aktualisiert am', 'pub': 'Veröffentlicht am', 'sign': "vom Team von Bike'N Tour, Fahrradverleih in der Rue Jean Jaurès 19 in Nantes.",
           'also': 'Mehr aus unserem Blog', 'band': ('Lust, mit dem Rad hinzufahren?', 'Wir machen Ihr Rad in Nantes startklar.'), 'block': 'Aus unserem Blog'},
}


def lang_posts(lang=None):
    """Articles traduits dans une langue : l'article français, avec titre, résumé et texte traduits."""
    lang = lang or pages.LANG
    d = os.path.join(BLOGDIR, lang)
    if lang == 'fr' or not os.path.isdir(d):
        return []
    fr = {p['slug']: p for p in all_posts()}
    out = []
    for f in sorted(os.listdir(d)):
        if not f.endswith('.md') or f[:-3] not in fr:
            continue
        fm, text = read_md(os.path.join(d, f))
        if not fm.get('url') or not fm.get('titre'):
            continue
        body = md_html(text)
        resume = str(fm.get('resume') or '')
        p = dict(fr[f[:-3]], h1=str(fm['titre']), body_html=body, meta=trunc(resume), lead=trunc(resume, 400), lang=lang,
                 words=len(re.sub(r'<[^>]+>', ' ', body).split()), catname=L10N[lang]['cat'][fr[f[:-3]]['cat']])
        out.append(p)
    return out


def build_lang():
    """Pages des articles traduits (anglais, néerlandais, allemand)."""
    import i18n
    lp = lang_posts()
    for p in lp:
        post_page(p, lp, date_fn=lambda d: i18n.date(d, p['lang']))
    return lp


def fr_date(d):
    return f'{d.day} {MOIS[d.month - 1]} {d.year}'


def trunc(d, limit=158):
    d = re.sub(r'\s+', ' ', d).strip()
    if len(d) > limit:
        cut = d[:limit]
        end = cut.rfind('. ')
        d = cut[:end + 1] if end > 90 else cut[:cut.rfind(' ')].rstrip(',;:') + '…'
    return d


def seo_title(h1):
    h1 = h1.replace('’', "'")
    short = h1.split(' : ', 1)[1] if ' : ' in h1 else h1  # « Balade incontournable à vélo : X » -> « X »
    short = short[0].upper() + short[1:]
    generic = h1.lower().startswith(('balade incontournable', 'le blog'))  # préfixe sans valeur : on peut le couper
    cands = [f"{h1} | Bike'N Tour", f'{h1} | Blog vélo Nantes']
    cands += ([f"{short} | Bike'N Tour", f"{short} à vélo | Blog Nantes", short, h1] if generic else [h1, f"{short} | Bike'N Tour", short])
    for t in cands:
        if len(t) <= 62:
            return t
    return h1[:60].rsplit(' ', 1)[0] + '…'


def local_img(src):
    """'/assets/img/x.webp' -> 'x.webp' (chemin relatif à assets/img)."""
    return src.split('/assets/img/', 1)[-1].lstrip('/')


def size(name):
    try:
        return Image.open(os.path.join(pages.ROOT, 'assets', 'img', name)).size
    except Exception:
        return 1200, 800


def figure(tag):
    src = re.search(r'src="([^"]+)"', tag).group(1)
    alt = (re.search(r'alt="([^"]*)"', tag) or [None, ''])[1]
    if not src.startswith('/assets/img/'):
        return f'<figure class="post-fig">{tag}</figure>'
    w, h = size(local_img(src))
    return f'<figure class="post-fig"><img src="{src}" alt="{alt}" width="{w}" height="{h}" loading="lazy" decoding="async"></figure>'


FACT_LABELS = {'distance', 'durée', 'niveau', 'dénivelé', 'départ', 'arrivée', 'retour', 'boucle', 'accès',
               'duration', 'level', 'elevation', 'start', 'finish', 'return', 'loop', 'access',  # en
               'afstand', 'duur', 'hoogteverschil', 'aankomst', 'terug', 'lus', 'toegang',  # nl
               'strecke', 'dauer', 'höhenmeter', 'ziel', 'rückfahrt', 'rundtour', 'anfahrt'}  # de


def md_html(text):
    h = markdown.markdown(text, extensions=['extra', 'sane_lists'])
    h = re.sub(r'<p>\s*(<img [^>]*>)\s*</p>', lambda m: figure(m.group(1)), h)
    h = re.sub(r'<dl>(.*?)</dl>', lambda m: '<dl class="post-facts">' + ''.join(
        f'<div><dt>{dt}</dt><dd>{re.sub(r"</?p>", "", dd).strip()}</dd></div>' for dt, dd in re.findall(r'<dt>(.*?)</dt>\s*<dd>(.*?)</dd>', m.group(1), re.S)) + '</dl>', h, flags=re.S)
    # liste « **Distance :** 36 km / **Durée :** … » -> fiche structurée
    def facts(m):
        items = re.findall(r'<li>(.*?)</li>', m.group(1), re.S)
        def fact(li):
            f = re.fullmatch(r'\s*(?:<p>)?<strong>([^<]+?)\s*:?\s*</strong>\s*:?\s*(.*?)(?:</p>)?\s*', li, re.S)
            return (f.group(1).strip(), f.group(2).strip()) if f and f.group(1).strip().lower() in FACT_LABELS else None
        k = len(items)
        while k > 0 and fact(items[k - 1]):
            k -= 1
        if len(items) - k < 2:
            return m.group(0)
        fs = [fact(li) for li in items[k:]]
        rows = ' post-facts-rows' if max(len(re.sub(r'<[^>]+>', '', v)) for _, v in fs) > 28 else ''  # valeurs longues : une ligne par info
        dl = f'<dl class="post-facts{rows}">' + ''.join('<div><dt>{}</dt><dd>{}</dd></div>'.format(*f) for f in fs) + '</dl>'
        return ('<ul>' + ''.join(f'<li>{li}</li>' for li in items[:k]) + '</ul>' if k else '') + dl
    h = re.sub(r'<ul>(.*?)</ul>', facts, h, flags=re.S)
    h = re.sub(r'<a href="(https?://(?!www\.bikentour\.com)[^"]+)"', r'<a href="\1" rel="noopener"', h)
    h = re.sub(r'<p>(<a href="[^"]*google[^"]*"[^>]*>Voir le parcours sur Google Maps</a>)</p>', r'<p class="post-map">\1</p>', h)
    return h


def read_md(path):
    txt = open(path, encoding='utf-8').read()
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)$', txt, re.S)
    return (yaml.safe_load(m.group(1)) or {}, m.group(2)) if m else ({}, txt)


def prepare():
    posts = []
    for f in sorted(os.listdir(BLOGDIR)):
        if not f.endswith('.md'):
            continue
        fm, text = read_md(os.path.join(BLOGDIR, f))
        if fm.get('brouillon'):
            continue
        slug = f[:-3]
        d = fm.get('date') or datetime.date.today()
        if isinstance(d, datetime.datetime):
            d = d.date()
        elif isinstance(d, str):
            d = datetime.date.fromisoformat(d[:10])
        m = fm.get('mise_a_jour')
        if isinstance(m, datetime.datetime):
            m = m.date()
        elif isinstance(m, str) and m.strip():
            m = datetime.date.fromisoformat(m.strip()[:10])
        if not isinstance(m, datetime.date) or m <= d:
            m = None
        body = md_html(text)
        resume = str(fm.get('resume') or re.sub(r'<[^>]+>', ' ', body))
        cat = fm.get('categorie') if fm.get('categorie') in CATNAME else 'balades'
        hero = local_img(fm.get('image') or '/assets/img/v2-bord-de-loire.webp')
        posts.append(dict(slug=slug, h1=str(fm.get('titre') or slug), d=d, maj=m, body_html=body, hero=hero, cat=cat,
                          cta=cta_target(slug, fm.get('lien', 'auto')), url='/post/' + slug, meta=trunc(resume), lead=trunc(resume, 400),
                          words=len(re.sub(r'<[^>]+>', ' ', body).split())))
    posts.sort(key=lambda x: x['d'], reverse=True)
    return posts


def rss(posts):
    """Flux RSS du blog (/fr/blog.xml) : découverte des nouveaux articles par les agrégateurs et les moteurs."""
    from email.utils import format_datetime
    from xml.sax.saxutils import escape as x
    items = ''.join(
        f'<item><title>{x(p["h1"])}</title><link>{SITE}{p["url"]}</link><guid isPermaLink="true">{SITE}{p["url"]}</guid>'
        f'<pubDate>{format_datetime(datetime.datetime.combine(p["d"], datetime.time(9), datetime.timezone.utc))}</pubDate>'
        f'<category>{x(CATNAME[p["cat"]])}</category><description>{x(p["meta"])}</description>'
        f'<enclosure url="{SITE}/assets/img/{p["hero"]}" type="image/webp" length="0"/></item>' for p in posts[:50])
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>'
           f'<title>Le blog de Bike\'N Tour</title><link>{SITE}{BLOG}</link><language>fr</language>'
           f'<description>Balades à vélo, lieux à voir et conseils de voyage à vélo au départ de Nantes.</description>'
           f'<atom:link href="{SITE}/fr/blog.xml" rel="self" type="application/rss+xml"/>{items}</channel></rss>\n')
    open(os.path.join(pages.ROOT, 'fr', 'blog.xml'), 'w', encoding='utf-8').write(xml)


def build():
    posts = prepare()
    for p in posts:
        post_page(p, posts)
    index(posts)
    rss(posts)
    return posts


def card(p, heading='h3'):
    w, h = size(p['hero'])
    return (f'<a class="post" href="{p["url"]}"><img src="/assets/img/{p["hero"]}" alt="" width="{w}" height="{h}" loading="lazy" decoding="async">'
            f'<span class="post-tag">{esc(p.get("catname") or CATNAME[p["cat"]])}</span><{heading} class="post-title">{esc(p["h1"])}</{heading}>'
            f'<span class="post-meta">{esc(p["meta"][:110].rsplit(" ", 1)[0])}…</span></a>')


def cta_card(kind, ident):
    if kind == 'route':
        r = ROUTE[ident]
        return (f'<div class="side-card"><img src="/assets/img/{r["img"]}" alt="" width="{r["iw"]}" height="{r["ih"]}" loading="lazy" decoding="async">'
                f'<div class="side-body"><p class="eyebrow">Itinéraire au départ de la boutique</p><p class="side-title"><a href="{r["url"]}">{esc(r["name"])}</a></p>'
                f'<p class="small">{esc(r["km"])} · {esc(r["days"])} · {lvl(r["level"])}</p><p class="small">{esc(r["short"])}</p>'
                f'<a class="btn btn-ghost" href="{r["url"]}">Voir l\'itinéraire</a> {BOOK_BTN}</div></div>')
    if kind == 'bike':
        b = BIKE[ident]
        return (f'<div class="side-card"><img src="/assets/img/{b["img"]}" alt="" width="{b["iw"]}" height="{b["ih"]}" loading="lazy" decoding="async">'
                f'<div class="side-body"><p class="eyebrow">À louer à Nantes</p><p class="side-title"><a href="{b["url"]}">{esc(b["name"])}</a></p>'
                f'<p class="small">{T("Dès {day} € / jour, {week} € la semaine.", day=b["day"], week=b["week"])}</p><a class="btn btn-ghost" href="{b["url"]}">Voir le vélo</a> {BOOK_BTN}</div></div>')
    if kind == 'tour':
        t = TOUR[ident]
        return (f'<div class="side-card"><img src="/assets/img/{t["img"]}" alt="" width="{t["iw"]}" height="{t["ih"]}" loading="lazy" decoding="async">'
                f'<div class="side-body"><p class="eyebrow">Visite guidée à vélo électrique</p><p class="side-title"><a href="{t["url"]}">{esc(t["name"])}</a></p>'
                f'<p class="small">{t["duration"]} · {T("{price} € par personne", price=t["price"])} · {esc(t["when"])}</p><a class="btn btn-primary" href="{t["url"]}">Découvrir la visite</a></div></div>')
    return (f'<div class="side-card side-body"><p class="eyebrow">Partir à vélo depuis Nantes</p><p>Six véloroutes partent de notre boutique, en plein centre de Nantes : on vous prépare le vélo, les sacoches et la trace GPX.</p>'
            f'<a class="btn btn-ghost" href="/fr/itineraires-velo-depart-nantes">Les itinéraires</a> {BOOK_BTN}</div>')


def related(p, posts, n=3):
    def score(o):
        return (o['cta'] == p['cta']) * 3 + (o['cat'] == p['cat']) * 2 + len(set(o['slug'].split('-')) & set(p['slug'].split('-')) - {'la', 'le', 'de', 'a', 'velo', 'les', 'balade', 'incontournable', 'nantes'})
    return sorted((o for o in posts if o is not p), key=lambda o: (-score(o), -o['d'].toordinal()))[:n]


def post_page(p, posts, date_fn=None):
    w, h = size(p['hero'])
    # la couverture n'est pas répétée dans le corps de l'article
    p['body_html'] = re.sub(r'<figure class="post-fig"><img src="/assets/img/' + re.escape(p['hero']) + r'"[^>]*></figure>', '', p['body_html'], count=1)
    rel = related(p, posts)
    lang = p.get('lang', 'fr')
    L = L10N.get(lang)
    dt = date_fn or fr_date
    if L:  # article traduit
        when = (f'{L["upd"]} <time datetime="{p["maj"].isoformat()}">{dt(p["maj"])}</time>' if p['maj']
                else f'<time datetime="{p["d"].isoformat()}">{dt(p["d"])}</time>')
        eyebrow = f'{esc(p["catname"])} · {when}'
        sign = f'{L["pub"]} {dt(p["d"])} {L["sign"]}'
        more = f'<section class="section section-tint"><div class="wrap"><h2>{L["also"]}</h2><div class="posts">{"".join(card(o) for o in rel)}</div></div></section>' if rel else ''
        band = cta_band(*L['band'])
    else:
        when = (f'Mis à jour le <time datetime="{p["maj"].isoformat()}">{fr_date(p["maj"])}</time>' if p['maj']
                else f'<time datetime="{p["d"].isoformat()}">{fr_date(p["d"])}</time>')
        eyebrow = f'<a href="{BLOG}#{p["cat"]}">{esc(CATNAME[p["cat"]])}</a> · {when}'
        sign = f"Article publié le {fr_date(p['d'])}" + (f", mis à jour le {fr_date(p['maj'])}" if p['maj'] else '') + " par l'équipe Bike'N Tour, loueur de vélos de voyage au 19 rue Jean Jaurès à Nantes."
        more = f'''<section class="section section-tint"><div class="wrap">
  <h2>À lire aussi</h2>
  <div class="posts">{''.join(card(o) for o in rel)}</div>
  <p class="more"><a class="arrow-link" href="{BLOG}">Tous les articles du blog</a></p>
</div></section>'''
        band = cta_band('Envie d\'y aller à vélo ?', 'On vous prépare le vélo au départ de Nantes.')
    body = f'''
<article class="article">
  <header class="wrap article-head">
    <p class="eyebrow">{eyebrow}</p>
    <h1>{esc(p['h1'])}</h1>
    <p class="lead">{esc(p['lead'])}</p>
  </header>
  <figure class="wrap article-cover"><img src="/assets/img/{p['hero']}" alt="{esc(p['h1'])}" width="{w}" height="{h}" fetchpriority="high"></figure>
  <div class="wrap two-col">
    <div class="prose article-body">
{p['body_html']}
      <p class="article-sign small muted">{sign}</p>
    </div>
    <div class="side">{cta_card(*p['cta'])}</div>
  </div>
</article>
{more}
{band}'''
    art = {"@type": "BlogPosting", "@id": SITE + p['url'] + '#article', "headline": p['h1'], "description": p['meta'],
           "datePublished": p['d'].isoformat(), "dateModified": (p['maj'] or p['d']).isoformat(), "inLanguage": lang, "image": f"{SITE}/assets/img/{p['hero']}",
           "wordCount": p['words'], "articleSection": CATNAME[p['cat']],
           "author": {"@type": "Organization", "@id": BIZ, "name": "Bike'N Tour"}, "publisher": {"@id": BIZ},
           "mainEntityOfPage": {"@id": SITE + p['url'] + '#webpage'}}
    if L:
        import i18n
        own = i18n.url(p['url'])
        art.update({"@id": SITE + own + '#article', "mainEntityOfPage": {"@id": SITE + own + '#webpage'}, "articleSection": p['catname'],
                    "translationOfWork": {"@id": SITE + p['url'] + '#article'}})
        t = f"{p['h1']} | Bike'N Tour"
        page(p['url'], t if len(t) <= 62 else p['h1'], p['meta'], [CRUMB_HOME, (p['h1'], None)], body, [art],
             img=p['hero'], priority='0.5', og_type='article')
        return
    art["isPartOf"] = {"@id": SITE + BLOG + '#blog'}
    page(p['url'], seo_title(p['h1']), p['meta'], [CRUMB_HOME, ('Blog', BLOG), (p['h1'], None)], body, [art],
         img=p['hero'], priority='0.5', og_type='article')


def index(posts):
    sections = ''
    for k, name, intro in CATS:
        lst = [p for p in posts if p['cat'] == k]
        sections += f'''<section class="section{' section-tint' if k == 'nantes' else ''}" id="{k}" aria-labelledby="t-{k}"><div class="wrap">
  <h2 id="t-{k}">{esc(name)} <span class="muted small">({len(lst)} articles)</span></h2><p class="muted">{esc(intro)}</p>
  <div class="posts">{''.join(card(p) for p in lst)}</div></div></section>\n'''
    chips = ''.join(f'<a class="chip" href="#{k}">{esc(n)}</a>' for k, n, _ in CATS)
    top = next((p for p in posts if 'top-5' in p['slug']), posts[0])
    body = f'''
<section class="phero phero-slim"><div class="wrap"><p class="eyebrow">Le blog</p><h1>Blog vélo : balades et bons plans à Nantes</h1>
<p class="lead">{len(posts)} articles écrits par l'équipe de Bike'N Tour : balades à vélo au départ de Nantes, lieux à découvrir en ville et sur l'estuaire, conseils pour voyager à vélo. Pour commencer : <a href="{top['url']}">notre top 5 des balades incontournables</a>.</p>
<nav class="chips" aria-label="Catégories du blog">{chips}</nav></div></section>
{sections}
{cta_band('Une balade vous tente ?', 'On vous prépare le vélo.')}'''
    blog = {"@type": "Blog", "@id": SITE + BLOG + '#blog', "name": "Le blog de Bike'N Tour", "url": SITE + BLOG, "inLanguage": "fr", "publisher": {"@id": BIZ},
            "blogPost": [{"@id": SITE + p['url'] + '#article'} for p in posts]}
    lst = {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": SITE + p['url'], "name": p['h1']} for i, p in enumerate(posts)]}
    page(BLOG, 'Blog vélo Nantes : balades, lieux et conseils | Bike\'N Tour',
         f'{len(posts)} articles pour découvrir Nantes et ses environs à vélo : balades à la journée, Loire, Erdre, Sèvre, estuaire, lieux insolites et conseils de voyage à vélo.',
         [CRUMB_HOME, ('Blog', None)], body, [blog, lst], img=top['hero'], priority='0.7', kind='CollectionPage')


_CACHE = []


def all_posts():
    if not _CACHE:
        _CACHE.extend(prepare())
    return _CACHE


def by_slug(part):
    return next((p for p in all_posts() if part in p['slug']), None)


def blog_block(kind, ident=None, title='Sur le blog', n=3, tint=False, extra=()):
    """Section « Sur le blog » : articles liés à un itinéraire, un vélo ou une visite (articles en français uniquement)."""
    if os.environ.get('NO_BLOG'):
        return ''
    if pages.LANG != 'fr':
        lp = lang_posts()
        if not lp:
            return ''
        lp.sort(key=lambda p: (p['cta'] != (kind, ident), p['slug']))
        return (f'<section class="section{" section-tint" if tint else ""}"><div class="wrap"><h2>{L10N[pages.LANG]["block"]}</h2>'
                f'<div class="posts">{"".join(card(p) for p in lp[:n])}</div></div></section>')
    lst = [p for p in all_posts() if p['cta'] == (kind, ident)]
    first = [by_slug(s) for s in extra if by_slug(s)]
    lst = first + [p for p in lst if p not in first]
    lst += [p for p in all_posts() if p['cat'] == 'balades' and p not in lst]
    uniq = []
    for p in lst:
        if all(p is not q for q in uniq):
            uniq.append(p)
    lst = uniq
    return (f'<section class="section{" section-tint" if tint else ""}"><div class="wrap"><h2>{esc(title)}</h2>'
            f'<div class="posts">{"".join(card(p) for p in lst[:n])}</div>'
            f'<p class="more"><a class="arrow-link" href="{BLOG}">Tous les articles du blog</a></p></div></section>')
