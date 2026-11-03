"""Traductions du site (EN, NL, DE).

- content/<langue>/*.json : textes modifiables dans l'admin (superposés au français par content.py)
- tools/i18n/<langue>.json : textes fixes du site, deux tables :
    "html" : phrases du gabarit et des pages (clé = phrase française, avec ses balises <a>, <strong>…)
    "t"    : modèles avec variables, utilisés par T() (ex. « Dès {day} € / jour »)
- tools/i18n/urls.json : adresse de chaque page dans chaque langue

La génération française reste la référence ; une page traduite est produite avec le même code,
puis localize_html() remplace les phrases connues et réécrit les liens internes vers la bonne langue."""
import os, re, json, html as H

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
SITE = 'https://www.bikentour.com'
LANGS = ['fr', 'en', 'nl', 'de']
LANG = os.environ.get('SITE_LANG', 'fr')
NAMES = {'fr': 'Français', 'en': 'English', 'nl': 'Nederlands', 'de': 'Deutsch'}
LOCALE = {'fr': 'fr_FR', 'en': 'en_GB', 'nl': 'nl_NL', 'de': 'de_DE'}
MONTHS = {
    'fr': ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'],
    'en': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
    'nl': ['januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli', 'augustus', 'september', 'oktober', 'november', 'december'],
    'de': ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']}
AND = {'fr': 'et', 'en': 'and', 'nl': 'en', 'de': 'und'}
OR = {'fr': 'ou', 'en': 'or', 'nl': 'of', 'de': 'oder'}

_U = json.load(open(os.path.join(TOOLS, 'i18n', 'urls.json'), encoding='utf-8'))
PAGE_KEYS = _U['pages']          # clé -> adresse française
URLS = _U['urls']                # adresse française -> {langue: adresse}


def _load_cat(lang):
    p = os.path.join(TOOLS, 'i18n', f'{lang}.json')
    return json.load(open(p, encoding='utf-8')) if lang != 'fr' and os.path.exists(p) else {'html': {}, 't': {}}


CAT = _load_cat(LANG)
RECORD = os.environ.get('I18N_RECORD')   # chemin : enregistre les modèles T() utilisés (extraction du catalogue)
_recorded = {}
_outputs = set()


def norm(s):
    s = re.sub(r'\s+', ' ', s).strip()
    return s.replace('&#x27;', "'").replace('&#39;', "'").replace('&quot;', '"')


def T(key, **kw):
    """Modèle de phrase traduit, puis variables insérées : T('Dès {day} € / jour', day=22)."""
    if RECORD is not None:
        _recorded[key] = sorted(kw)
    tpl = CAT.get('t', {}).get(key) or key
    try:
        out = tpl.format(**kw) if kw else tpl
    except (KeyError, IndexError, ValueError):
        out = key.format(**kw) if kw else key
    if RECORD is not None and kw:
        _outputs.add(norm(out))
    return out


def save_record():
    if RECORD:
        json.dump({'t': _recorded, 'outputs': sorted(_outputs)}, open(RECORD, 'w'), ensure_ascii=False, indent=1)


def url(fr_url, lang=None):
    """Adresse d'une page française dans une langue (None si la page n'est pas traduite)."""
    lang = lang or LANG
    if lang == 'fr':
        return fr_url
    return URLS.get(fr_url, {}).get(lang)


def alternates(fr_url):
    return {l: url(fr_url, l) for l in LANGS if url(fr_url, l)}


def date(d, lang=None):
    lang = lang or LANG
    m = MONTHS[lang][d.month - 1]
    return {'en': f'{m} {d.day}, {d.year}', 'de': f'{d.day}. {m} {d.year}'}.get(lang, f'{d.day} {m} {d.year}')


def number(n, lang=None):
    lang = lang or LANG
    s = f'{n:,}'
    return s if lang == 'en' else s.replace(',', '.' if lang in ('nl', 'de') else ' ')


def enum(items, word=None, sep=', '):
    word = word or AND[LANG]
    items = list(items)
    return sep.join(items[:-1]) + f' {word} ' + items[-1] if len(items) > 1 else (items[0] if items else '')


# ------------------------------------------------------------------ sélecteur de langue
def lang_switch(fr_url, flags, chev):
    """Bouton + menu des langues pour une page (liens vers la même page dans chaque langue)."""
    alts = alternates(fr_url)
    lis = ''.join(
        f'<li><a href="{alts.get(l) or url("/", l)}" hreflang="{l}" lang="{l}"{" aria-current=\"page\"" if l == LANG else ""}>{flags[l]}{NAMES[l]}</a></li>'
        for l in LANGS)
    label = {'fr': 'changer de langue', 'en': 'change language', 'nl': 'taal wijzigen', 'de': 'Sprache wechseln'}[LANG]
    return (f'<button class="drop-btn lang-btn" type="button" aria-expanded="false" aria-controls="dd-lang">{flags[LANG]}<span>{LANG.upper()}</span>'
            f'<span class="sr-only">, {label}</span>{chev}</button>\n        <ul class="dd dd-lang" id="dd-lang">{lis}</ul>')


def replace_lang_switch(page_html, fr_url, flags, chev):
    return re.sub(r'<button class="drop-btn lang-btn".*?</ul>', lambda m: lang_switch(fr_url, flags, chev), page_html, count=1, flags=re.S)


# ------------------------------------------------------------------ découpage du HTML en phrases
UNIT = {'p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'td', 'th', 'dt', 'dd', 'figcaption', 'summary', 'caption', 'label',
        'button', 'a', 'span', 'strong', 'em', 'small', 'option', 'blockquote', 'address', 'title', 'legend', 'b', 'i', 'time'}
BLOCK = {'p', 'li', 'ul', 'ol', 'div', 'section', 'article', 'aside', 'nav', 'header', 'footer', 'main', 'table', 'thead', 'tbody',
         'tr', 'td', 'th', 'dl', 'dt', 'dd', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'figure', 'figcaption', 'form', 'details', 'summary',
         'address', 'blockquote', 'fieldset', 'select', 'svg', 'img', 'button', 'input', 'textarea', 'iframe', 'picture', 'video'}
OPAQUE = {'script', 'style', 'svg', 'template', 'noscript', 'code', 'pre', 'textarea'}
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}
TOKEN = re.compile(r'<!--.*?-->|<!\w[^>]*>|<(/?)([a-zA-Z][a-zA-Z0-9-]*)((?:[^>"\']|"[^"]*"|\'[^\']*\')*)>|[^<]+', re.S)
LETTER = re.compile(r'[A-Za-zÀ-ÿ]')


def _tree(s):
    """Analyse légère : liste de nœuds {tag, start, inner_start, inner_end, children, parent}."""
    root = {'tag': '#root', 'children': [], 'parent': None, 'inner_start': 0}
    cur = root
    pos = 0
    while pos < len(s):
        m = TOKEN.match(s, pos)
        if not m:
            break
        tok = m.group(0)
        if m.group(2):
            tag = m.group(2).lower()
            if m.group(1):  # fermeture
                n = cur
                while n is not root and n['tag'] != tag:
                    n = n['parent']
                if n is not root:
                    while cur is not n:  # balises non fermées
                        cur['inner_end'] = m.start(); cur['end'] = m.start(); cur = cur['parent']
                    n['inner_end'] = m.start(); n['end'] = m.end(); cur = n['parent']
            else:
                node = {'tag': tag, 'start': m.start(), 'inner_start': m.end(), 'children': [], 'parent': cur, 'attrs': m.group(3)}
                cur['children'].append(node)
                if tag in OPAQUE and tag != 'svg' or tag == 'svg':
                    close = re.compile(rf'</{tag}\s*>', re.I).search(s, m.end())
                    end = close.start() if close else len(s)
                    node['inner_end'] = end; node['end'] = close.end() if close else len(s)
                    node['opaque'] = True
                    pos = node['end']
                    continue
                if tag not in VOID and not tok.endswith('/>'):
                    cur = node
                else:
                    node['inner_end'] = node['end'] = m.end()
        elif not tok.startswith('<'):
            cur['children'].append({'tag': '#text', 'start': m.start(), 'end': m.end(), 'parent': cur})
        pos = m.end()
    while cur is not root:
        cur['inner_end'] = cur['end'] = len(s); cur = cur['parent']
    return root


def _has_block(n):
    return any(c['tag'] in BLOCK or c['tag'] in OPAQUE or (c['tag'] not in ('#text',) and _has_block(c)) for c in n.get('children', []))


def _text(s, n):
    return H.unescape(re.sub(r'<[^>]+>', ' ', s[n['inner_start']:n['inner_end']]))


def segments(s):
    """Phrases à traduire : (début, fin, clé). Un élément de texte (p, li, h2, a…) sans bloc à l'intérieur
    forme une phrase entière, balises de mise en forme comprises ; sinon on descend dans ses enfants."""
    out = []

    def walk(n):
        for c in n.get('children', []):
            t = c['tag']
            if t == '#text':
                raw = s[c['start']:c['end']]
                if LETTER.search(H.unescape(raw)):
                    lead = len(raw) - len(raw.lstrip()); trail = len(raw) - len(raw.rstrip())
                    out.append((c['start'] + lead, c['end'] - trail, norm(raw)))
                continue
            if c.get('opaque') or t in VOID:
                continue
            if t in UNIT and not _has_block(c) and LETTER.search(_text(s, c)):
                inner = s[c['inner_start']:c['inner_end']]
                lead = len(inner) - len(inner.lstrip()); trail = len(inner) - len(inner.rstrip())
                out.append((c['inner_start'] + lead, c['inner_end'] - trail, norm(inner)))
            else:
                walk(c)

    walk(_tree(s))
    return out


ATTRS = re.compile(r'(\s(?:alt|title|aria-label|placeholder|data-subject|data-body|data-msg)=")([^"]*)(")')
META = re.compile(r'(<meta (?:name|property)="(?:description|og:title|og:description|og:image:alt|twitter:title|twitter:description)" content=")([^"]*)(")')
JSONLD = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.S)
HREF = re.compile(r'((?:href|data-href)=")((?:https://www\.bikentour\.com)?/[^"#?]*)([#?][^"]*)?(")')


def _tr_text(v, table):
    k = norm(H.unescape(v))
    t = table.get(k)
    return H.escape(t, quote=True) if t else v


def _map_url(u):
    """Adresse française (relative ou absolue) -> adresse dans la langue courante, si la page est traduite."""
    absolute = u.startswith(SITE)
    path = u[len(SITE):] if absolute else u
    path = path.rstrip('/') or '/'
    t = url(path)
    if not t:
        return u
    return (SITE + t) if absolute else t


def _walk_json(o, table):
    if isinstance(o, dict):
        return {k: (LANG if k == 'inLanguage' and v == 'fr' else _walk_json(v, table)) for k, v in o.items()}
    if isinstance(o, list):
        return [_walk_json(v, table) for v in o]
    if isinstance(o, str):
        if o.startswith(SITE + '/') or o == SITE + '/':
            base, frag = (o.split('#', 1) + [''])[:2]
            m = _map_url(base)
            return m + ('#' + frag if frag else '')
        return table.get(norm(o), o)
    return o


def localize_html(s, lang=None):
    """Traduit une page française générée : phrases, attributs, données Google, liens internes, langue."""
    lang = lang or LANG
    if lang == 'fr':
        return s
    table = CAT.get('html', {})
    # 1. phrases (de la fin vers le début pour garder les positions)
    for a, b, key in sorted(segments(s), reverse=True):
        t = table.get(key)
        if t:
            s = s[:a] + t + s[b:]
    # 2. attributs et méta-descriptions
    s = ATTRS.sub(lambda m: m.group(1) + _tr_text(m.group(2), table) + m.group(3), s)
    s = META.sub(lambda m: m.group(1) + _tr_text(m.group(2), table) + m.group(3), s)
    # 3. données structurées
    def ld(m):
        try:
            data = _walk_json(json.loads(m.group(2)), table)
        except ValueError:
            return m.group(0)
        return m.group(1) + '\n' + json.dumps(data, ensure_ascii=False, indent=1) + '\n' + m.group(3)
    s = JSONLD.sub(ld, s)
    # 4. liens internes vers les pages traduites
    s = HREF.sub(lambda m: m.group(1) + _map_url(m.group(2)) + (m.group(3) or '') + m.group(4), s)
    # 5. langue du document
    s = s.replace('<html lang="fr">', f'<html lang="{lang}">', 1)
    s = s.replace('<meta property="og:locale" content="fr_FR">', f'<meta property="og:locale" content="{LOCALE[lang]}">')
    return s


def extract(s):
    """Toutes les phrases et attributs traduisibles d'une page (pour constituer le catalogue)."""
    keys = [k for _, _, k in segments(s)]
    keys += [norm(H.unescape(m.group(2))) for m in ATTRS.finditer(s) if LETTER.search(m.group(2))]
    keys += [norm(H.unescape(m.group(2))) for m in META.finditer(s)]
    for m in JSONLD.finditer(s):
        def strings(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k not in ('@id', '@type', '@context', 'url', 'image', 'logo', 'telephone', 'email', 'target', 'sameAs', 'hasMap', 'item', 'priceCurrency', 'availability', 'inLanguage', 'datePublished', 'dateModified', 'cssSelector'):
                        yield from strings(v)
            elif isinstance(o, list):
                for v in o:
                    yield from strings(v)
            elif isinstance(o, str) and LETTER.search(o) and not o.startswith('http'):
                yield norm(o)
        try:
            keys += list(strings(json.loads(m.group(2))))
        except ValueError:
            pass
    return keys


# ------------------------------------------------------------------ drapeaux du sélecteur de langue
FLAGS = {
 'fr': '<svg class="flag" viewBox="0 0 3 2" aria-hidden="true"><rect width="1" height="2" fill="#002395"/><rect x="1" width="1" height="2" fill="#fff"/><rect x="2" width="1" height="2" fill="#ED2939"/></svg>',
 'en': '<svg class="flag" viewBox="0 0 60 40" aria-hidden="true"><rect width="60" height="40" fill="#012169"/><path d="M0 0L60 40M60 0L0 40" stroke="#fff" stroke-width="8"/><path d="M0 0L60 40M60 0L0 40" stroke="#C8102E" stroke-width="3"/><path d="M30 0V40M0 20H60" stroke="#fff" stroke-width="12"/><path d="M30 0V40M0 20H60" stroke="#C8102E" stroke-width="7"/></svg>',
 'nl': '<svg class="flag" viewBox="0 0 3 2" aria-hidden="true"><rect width="3" height="2" fill="#21468B"/><rect width="3" height="1.333" fill="#fff"/><rect width="3" height=".667" fill="#AE1C28"/></svg>',
 'de': '<svg class="flag" viewBox="0 0 5 3" aria-hidden="true"><rect width="5" height="3" fill="#FFCE00"/><rect width="5" height="2" fill="#DD0000"/><rect width="5" height="1" fill="#000"/></svg>',
}
CHEV = '<svg class="chev" viewBox="0 0 12 8" aria-hidden="true"><path d="M1.5 1.5 6 6l4.5-4.5"/></svg>'


def head_links(fr_url):
    """canonical + hreflang (+ og:url) d'une page, à insérer après la traduction."""
    own = url(fr_url) or fr_url
    canon = SITE + own
    alts = alternates(fr_url)
    out = [f'<link rel="canonical" href="{canon}">']
    out += [f'<link rel="alternate" hreflang="{l}" href="{SITE}{u}">' for l, u in alts.items()]
    out.append(f'<link rel="alternate" hreflang="x-default" href="{SITE}{fr_url}">')
    out.append(f'<meta property="og:url" content="{canon}">')
    return '\n'.join(out)
