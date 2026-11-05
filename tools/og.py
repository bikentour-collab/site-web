"""Images de partage (Open Graph) 1200 × 630 générées automatiquement pour chaque page.

Style « proposition 1 » : photo de la page en fond, logo blanc à gauche, titre de la page à droite.
Pour une photo produit sur fond blanc (fiches vélos) : fond bleu marine, vélo entier à droite.
Le nom du fichier contient une empreinte du texte et de la photo : une page modifiée
reçoit une nouvelle image, et les réseaux sociaux ne gardent pas l'ancienne en cache.
"""
import glob
import hashlib
import html as _html
import os
import re

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IMG = os.path.join(ROOT, 'assets', 'img')
OUT = os.path.join(IMG, 'og')
W, H = 1200, 630
NAVY = (48, 51, 110)
SUB = {'fr': 'Location de vélos à Nantes', 'en': 'Bike hire in Nantes', 'nl': 'Fietsverhuur in Nantes', 'de': 'Fahrradverleih in Nantes'}
SKIP = ('/index', '/en/index', '/nl/index', '/de/index')  # l'accueil a sa propre image (og-accueil*.jpg)


def _fonts(size, weight):
    base = os.path.join(HERE, 'og', f'Montserrat-{weight}')
    return ImageFont.truetype(base + '.ttf', size), ImageFont.truetype(base + '-ext.ttf', size)


_CMAP = None


def _has(font, ch):
    """Le caractère existe-t-il dans la police « latin » (la première) ?"""
    global _CMAP
    if _CMAP is None:
        try:
            from fontTools.ttLib import TTFont
            _CMAP = set(TTFont(os.path.join(HERE, 'og', 'Montserrat-ExtraBold.ttf')).getBestCmap())
        except Exception:  # fontTools absent : on suppose le latin de base
            _CMAP = set(range(32, 256))
    return ord(ch) in _CMAP


def _width(text, fonts):
    return sum(fonts[0 if _has(fonts[0], c) else 1].getlength(c) for c in text)


def _draw(d, xy, text, fonts, fill):
    x, y = xy
    for c in text:  # repli sur la police « latin-ext » pour œ, ł, etc.
        f = fonts[0] if _has(fonts[0], c) else fonts[1]
        d.text((x, y), c, font=f, fill=fill)
        x += f.getlength(c)


def _wrap(text, fonts, maxw):
    lines, cur = [], ''
    for w in text.split():
        t = (cur + ' ' + w).strip()
        if _width(t, fonts) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def _fit_title(text, maxw, maxlines=3):
    for size in (50, 46, 42, 38, 34, 31):
        f = _fonts(size, 'ExtraBold')
        lines = _wrap(text, f, maxw)
        if len(lines) <= maxlines:
            return f, size, lines
    f = _fonts(31, 'ExtraBold')
    lines = _wrap(text, f, maxw)[:maxlines]
    lines[-1] = lines[-1].rstrip(' ,;:') + '…'
    return f, 31, lines


def _cover(im, w, h, fy=0.4):
    r = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    x = (im.width - w) // 2
    y = int((im.height - h) * fy)
    return im.crop((x, y, x + w, y + h))


def _is_product(im):
    """Photo produit détourée sur fond blanc ?"""
    s = im.convert('RGB').resize((60, 40))
    px = [s.getpixel(p) for p in ((1, 1), (58, 1), (1, 38), (58, 38), (30, 1))]
    return sum(min(p) > 235 for p in px) >= 4


def render(title, sub, photo, dest):
    src = Image.open(photo).convert('RGB')
    logo = Image.open(os.path.join(HERE, 'og', 'logo-blanc.png')).convert('RGBA')
    if _is_product(src):
        canvas = Image.new('RGB', (W, H), NAVY)
        prod = src.copy()
        prod.thumbnail((560, 520), Image.LANCZOS)
        card = Image.new('RGB', (600, H), (255, 255, 255))
        card.paste(prod, ((600 - prod.width) // 2, (H - prod.height) // 2))
        canvas.paste(card, (W - 600, 0))
        textw, x0 = 520, 56
    else:
        canvas = _cover(src, W, H)
        # voile sombre en haut pour la lisibilité (dégradé bleu marine)
        grad = Image.new('L', (1, H))
        for y in range(H):
            grad.putpixel((0, y), int(max(0, 175 * (1 - y / (H * 0.62)))))
        veil = Image.new('RGB', (W, H), (22, 26, 70))
        canvas = Image.composite(veil, canvas, grad.resize((W, H)))
        textw, x0 = 660, 0
    d = ImageDraw.Draw(canvas)
    # logo
    lh = 96
    lg = logo.resize((round(logo.width * lh / logo.height), lh), Image.LANCZOS)
    shadow = Image.new('RGBA', lg.size, (0, 0, 0, 0))
    shadow.putalpha(lg.split()[3].point(lambda a: a * .35))
    lx, ly = 56, 48
    canvas.paste((10, 20, 50), (lx + 2, ly + 3), shadow.filter(ImageFilter.GaussianBlur(6)))
    canvas.paste(lg, (lx, ly), lg)
    # texte
    if x0:  # fiche produit : texte sous le logo
        tx, ty = x0, ly + lh + 48
    else:
        sep_x = lx + lg.width + 30
        d.line([(sep_x, ly + 4), (sep_x, ly + lh - 4)], fill=(255, 255, 255), width=2)
        tx, ty = sep_x + 30, ly - 2
        textw = W - tx - 50
    f, size, lines = _fit_title(title, textw)
    lead = round(size * 1.08)
    for i, line in enumerate(lines):
        _draw(d, (tx + 1, ty + i * lead + 2), line, f, (15, 20, 55))  # ombre légère
        _draw(d, (tx, ty + i * lead), line, f, (255, 255, 255))
    fs = _fonts(21, 'SemiBold')
    sy = ty + len(lines) * lead + 10
    _draw(d, (tx, sy), sub, fs, (215, 236, 213) if not x0 else (144, 199, 142))
    os.makedirs(OUT, exist_ok=True)
    canvas.save(dest, 'JPEG', quality=72, optimize=True, progressive=True, subsampling=2)


def clean_title(t):
    t = _html.unescape(t)
    t = re.sub(r"\s*[|–-]\s*Bike'N Tour.*$", '', t)
    return t.strip()


def apply(s, url):
    """Remplace l'image de partage d'une page par sa carte 1200 × 630 (créée si besoin)."""
    if url in SKIP or url.endswith('/404'):
        return s, None
    mt = re.search(r'<meta property="og:title" content="([^"]*)"', s)
    mi = re.search(r'<meta property="og:image" content="https://www\.bikentour\.com/assets/img/([^"]+)">', s)
    if not mt or not mi or mi.group(1).startswith(('og/', 'og-')):
        return s, None
    lang = (re.search(r'<html lang="(\w+)"', s) or [None, 'fr'])[1]
    photo = os.path.join(IMG, mi.group(1))
    if not os.path.exists(photo):
        return s, None
    title = clean_title(mt.group(1))
    sub = SUB.get(lang, SUB['fr'])
    key = hashlib.sha1(f'{title}|{sub}|{mi.group(1)}|{os.path.getsize(photo)}|v2'.encode()).hexdigest()[:10]
    slug = re.sub(r'[^a-z0-9]+', '-', url.lower()).strip('-')[:60] or 'page'
    name = f'{slug}-{key}.jpg'
    dest = os.path.join(OUT, name)
    if not os.path.exists(dest):
        for old in glob.glob(os.path.join(OUT, f'{slug}-??????????.jpg')):
            os.remove(old)
        render(title, sub, photo, dest)
    alt = re.search(r'<meta property="og:image:alt" content="[^"]*">', s)
    meta = (f'<meta property="og:image" content="https://www.bikentour.com/assets/img/og/{name}">\n'
            '<meta property="og:image:type" content="image/jpeg">\n<meta property="og:image:width" content="1200">\n'
            '<meta property="og:image:height" content="630">'
            + ('' if alt else f'\n<meta property="og:image:alt" content="{_html.escape(title)}">'))
    return s.replace(mi.group(0), meta, 1), name
