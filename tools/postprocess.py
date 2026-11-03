"""Finitions appliquées à toutes les pages générées :
- images responsives (variantes 640 et 1200 px + srcset/sizes)
- lien de menu actif (aria-current)
- page 404 au gabarit du site
"""
import os, re, glob
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
IMG = os.path.join(ROOT, 'assets', 'img')
WIDTHS = (480, 800, 1200, 1600)


def variants(name):
    """Crée les variantes réduites d'une photo et renvoie la liste (fichier, largeur)."""
    src = os.path.join(IMG, name)
    if not os.path.exists(src) or not name.endswith('.webp') or '-w' in name or name.startswith(('logo', 'partenaire')):
        return []
    im = Image.open(src)
    w, h = im.size
    out = []
    for tw in WIDTHS:
        if w <= tw * 1.15:
            continue
        vname = name[:-5] + f'-w{tw}.webp'
        vpath = os.path.join(IMG, vname)
        if not os.path.exists(vpath) or os.path.getmtime(vpath) < os.path.getmtime(src):
            im.convert('RGB').resize((tw, round(h * tw / w)), Image.LANCZOS).save(vpath, 'WEBP', quality=78, method=6)
        out.append((vname, tw))
    if out:
        out.append((name, w))
    return out


SIZES = {
    'hero-img': '100vw', 'phero-media': '(max-width: 980px) 100vw, 50vw', 'tile': '(max-width: 640px) 100vw, (max-width: 980px) 50vw, 33vw',
    'post': '(max-width: 980px) 100vw, 33vw', 'side-card': '(max-width: 980px) 100vw, 360px', 'rc-media': '(max-width: 980px) 100vw, 400px', 'class="post"': '(max-width: 980px) 100vw, 33vw', 'article-cover': '(max-width: 1200px) 100vw, 1100px', 'post-fig': '(max-width: 980px) 100vw, 680px',
}


def responsive(html):
    def fix(m):
        tag = m.group(0)
        if 'srcset=' in tag:
            return tag
        src = re.search(r'src="/assets/img/([^"]+)"', tag)
        if not src:
            return tag
        vs = variants(src.group(1))
        if not vs:
            return tag
        ctx = html[max(0, m.start() - 400):m.start()]
        sizes = '(max-width: 980px) 100vw, 50vw'
        for key, val in SIZES.items():
            if key in tag or ctx.rfind(key) > ctx.rfind('<section'):
                sizes = val
                if key in tag:
                    break
        srcset = ', '.join(f'/assets/img/{n} {w}w' for n, w in vs)
        return tag.replace('<img ', f'<img srcset="{srcset}" sizes="{sizes}" ', 1)
    return re.sub(r'<img\b[^>]*>', fix, html)


NAV = [('/fr/nos-velos-location', ('/fr/nos-velos-location', '/fr/location-', '/fr/nos-tarifs')),
       ('/fr/itineraires-velo-depart-nantes', ('/fr/itineraires-velo-depart-nantes', '/fr/idees-de-balades')),
       ('/fr/offre-groupes-seminaires', ('/fr/offre-groupes-seminaires', '/fr/visites-guidees-nantes', '/fr/tour/')),
       ('/fr/nos-tarifs-reservation', ('/fr/nos-tarifs-reservation',))]
# le blog n'est pas dans le menu principal


_U = __import__('json').load(open(os.path.join(os.path.dirname(__file__), 'i18n', 'urls.json')))['urls']
FR_OF = {lu: fr for fr, langs in _U.items() for lu in langs.values()}


def nav_current(html, url):
    fr_url = FR_OF.get(url, url)
    url = fr_url
    for href, prefixes in NAV:
        if any(url.startswith(p) for p in prefixes):
            for h in [href] + list(_U.get(href, {}).values()):
                html = html.replace(f'<a class="nav-link" href="{h}">', f'<a class="nav-link" href="{h}" aria-current="page">', 1)
            break
    return html


def page_404():
    tpl = open(os.path.join(ROOT, 'fr', 'faq-locationdeveloanantes.html')).read()
    head = tpl[:tpl.index('<body')]
    head = re.sub(r'<title>.*?</title>', "<title>Page introuvable | Bike'N Tour</title>", head)
    head = re.sub(r'<meta name="robots"[^>]*>', '<meta name="robots" content="noindex">', head)
    head = re.sub(r'<link rel="(canonical|alternate)"[^>]*>\n?', '', head)
    head = re.sub(r'<script type="application/ld\+json">.*?</script>\n?', '', head, flags=re.S)
    header = re.search(r'<header class="hd".*?</header>', tpl, re.S).group(0)
    footer = re.search(r'<footer class="ft">.*?</footer>', tpl, re.S).group(0)
    body = f'''<body class="inner">
{header}
<main id="contenu">
<section class="section"><div class="wrap narrow notfound">
  <p class="eyebrow">Erreur 404</p>
  <h1>Oups, cette route n'existe pas</h1>
  <p class="lead">La page que vous cherchez a peut-être changé d'adresse avec notre nouveau site.</p>
  <div class="hero-actions"><a class="btn btn-primary" href="/fr/itineraires-velo-depart-nantes">Voir les itinéraires</a><a class="btn btn-ghost" href="/fr/nos-velos-location">Nos vélos</a><a class="btn btn-ghost" href="/">Accueil</a></div>
</div></section>
</main>
{footer}
</body>
</html>
'''
    open(os.path.join(ROOT, '404.html'), 'w').write(head + body)


def assets_and_fonts(html):
    """Police auto-hébergée (plus de Google Fonts) et versionnage des CSS/JS pour un cache long."""
    import hashlib
    html = re.sub(r'<link rel="preconnect" href="https://fonts\.(googleapis|gstatic)\.com"[^>]*>\n?', '', html)
    html = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>\n?', '', html)
    if 'montserrat-latin-wght-normal.woff2" as="font"' not in html:
        html = html.replace('<link rel="stylesheet" href="/assets/css/style.css', '<link rel="preload" href="/assets/fonts/montserrat-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>\n<link rel="stylesheet" href="/assets/css/style.css', 1)
    for asset in ('css/style.css', 'js/main.js'):
        h = hashlib.md5(open(os.path.join(ROOT, 'assets', asset), 'rb').read()).hexdigest()[:8]
        html = re.sub(r'/assets/' + re.escape(asset) + r'(\?v=\w+)?"', f'/assets/{asset}?v={h}"', html)
    return html


SITE = 'https://www.bikentour.com'


def markdown_twin(path, html):
    """Version Markdown de la page (contenu principal seul), lue facilement par les assistants IA."""
    from markdownify import markdownify
    title = re.search(r'<title>(.*?)</title>', html).group(1)
    canon = re.search(r'<link rel="canonical" href="([^"]+)"', html).group(1)
    desc = re.search(r'<meta name="description" content="([^"]*)"', html).group(1)
    main = re.search(r'<main[^>]*>(.*?)</main>', html, re.S).group(1)
    for pat in (r'<svg.*?</svg>', r'<script.*?</script>', r'<form.*?</form>', r'<nav class="crumbs.*?</nav>',
                r'<div class="map-ctrl.*?</div>', r'<p class="map-credit">.*?</p>', r'<section class="cta-band">.*?</section>', r'<figure class="rc-profile.*?</figure>'):
        main = re.sub(pat, '', main, flags=re.S)
    main = re.sub(r'\s(srcset|sizes)="[^"]*"', '', main)
    main = re.sub(r'(href|src)="/(?!/)', r'\1="' + SITE + '/', main)
    md = markdownify(main, heading_style='ATX', bullets='-', strip=['span'])
    md = re.sub(r'\n{3,}', '\n\n', md).strip()
    head = f"# {title}\n\n> {desc}\n\nPage : {canon} · Bike'N Tour, 19 rue Jean Jaurès, 44000 Nantes · 06 52 62 94 64 · contact@bikentour.com\n\n"
    import html as h
    open(path[:-5] + '.md', 'w').write(h.unescape(head + md) + '\n')


def run():
    files = [os.path.join(ROOT, 'index.html')] + glob.glob(os.path.join(ROOT, 'fr', '**', '*.html'), recursive=True) + glob.glob(os.path.join(ROOT, 'post', '*.html')) + [f for l in ('en', 'nl', 'de') for f in glob.glob(os.path.join(ROOT, l, '**', '*.html'), recursive=True)]
    for f in files:
        url = '/' + os.path.relpath(f, ROOT)[:-5]
        s = open(f).read()
        s = assets_and_fonts(responsive(s))
        # prix insécables : « 22 € », « € 22 » ne se coupent jamais en fin de ligne
        s = re.sub(r'(\d) €', '\\1\u00a0€', s)
        s = re.sub(r'€ (\d)', '€\u00a0\\1', s)
        if not url.endswith('/index'):
            s = nav_current(s, url)
        md_url = '/' + os.path.relpath(f, ROOT)[:-5] + '.md'
        s = re.sub(r'<link rel="alternate" type="text/markdown" href="[^"]*"[^>]*>',
                   f'<link rel="alternate" type="text/markdown" href="{md_url}" title="Version Markdown de cette page">', s)
        open(f, 'w').write(s)
        markdown_twin(f, s)
    page_404()
    p404 = os.path.join(ROOT, '404.html')
    fixed = assets_and_fonts(open(p404).read())
    open(p404, 'w').write(fixed)
    print(len(files), 'pages finalisées')


if __name__ == '__main__':
    run()
