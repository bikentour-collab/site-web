"""Vérifie une traduction : python3 i18n_check.py en
- toutes les phrases du catalogue et tous les modèles T() sont traduits
- mêmes balises HTML, mêmes liens (href) et mêmes variables {x} que le français
- fichiers content/<langue>/*.json : même structure que le français, aucun champ non traduisible
- titres Google <= 62 caractères, descriptions <= 160"""
import json, os, re, sys, collections

lang = sys.argv[1]
T = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(T)
cat = json.load(open(os.path.join(T, 'i18n', 'catalog.json')))
tr = json.load(open(os.path.join(T, 'i18n', f'{lang}.json')))
errors = []

tags = lambda s: collections.Counter(re.findall(r'</?([a-zA-Z][a-zA-Z0-9]*)', s))
hrefs = lambda s: sorted(re.findall(r'href="([^"]*)"', s))
vars_ = lambda s: sorted(set(re.findall(r'\{(\w+)\}', s)))
toks = lambda s: sorted(re.findall(r'\{\{\w+\}\}', s))

for k in cat['html']:
    v = tr.get('html', {}).get(k)
    if not v:
        errors.append(f'html manquant : {k[:80]}')
        continue
    if tags(k) != tags(v):
        errors.append(f'balises différentes : {k[:60]} -> {v[:60]}')
    if hrefs(k) != hrefs(v):
        errors.append(f'liens différents : {k[:60]}')
    if toks(k) != toks(v):
        errors.append(f'jetons {{{{x}}}} différents : {k[:60]}')
for k in cat['t']:
    v = tr.get('t', {}).get(k)
    if not v:
        errors.append(f't manquant : {k[:80]}')
        continue
    if vars_(k) != vars_(v):
        errors.append(f'variables différentes : {k[:60]} -> {v[:60]}')
    if tags(k) != tags(v):
        errors.append(f'balises différentes (t) : {k[:60]}')

KEEP = {'id', 'url', 'img', 'hero_image', 'color', 'dur', 'iso', 'good', 'level', 'grid', 'oneway', 'day', 'weekend', 'week',
        'extra', 'protect', 'deposit', 'prix', 'google_note', 'google_avis', 'tripadvisor_avis'}


def compare(fr, t, path):
    if isinstance(fr, dict):
        if not isinstance(t, dict):
            errors.append(f'{path} : objet attendu'); return
        for k in t:
            if k in KEEP:
                errors.append(f'{path}.{k} : champ non traduisible à retirer')
            elif k not in fr:
                errors.append(f'{path}.{k} : champ inconnu')
            else:
                compare(fr[k], t[k], f'{path}.{k}')
    elif isinstance(fr, list):
        if not isinstance(t, list):
            errors.append(f'{path} : liste attendue'); return
        if fr and not isinstance(fr[0], str) and len(fr) != len(t):
            errors.append(f'{path} : {len(t)} éléments au lieu de {len(fr)}')
        for i, (a, b) in enumerate(zip(fr, t)):
            compare(a, b, f'{path}[{i}]')
    elif isinstance(fr, str) and not isinstance(t, str):
        errors.append(f'{path} : texte attendu')


for f in sorted(os.listdir(os.path.join(ROOT, 'content', 'fr'))):
    p = os.path.join(ROOT, 'content', lang, f)
    if f in ('site.json', 'presse.json'):
        continue
    if not os.path.exists(p):
        errors.append(f'content/{lang}/{f} manquant'); continue
    compare(json.load(open(os.path.join(ROOT, 'content', 'fr', f))), json.load(open(p)), f)
    data = json.load(open(p))
    def walk(o, key=''):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == 'title' and isinstance(v, str) and len(v) > 62: errors.append(f'{f} title trop long ({len(v)}) : {v}')
                if k == 'meta' and isinstance(v, str) and len(v) > 160: errors.append(f'{f} meta trop longue ({len(v)}) : {v[:50]}')
                walk(v, k)
        elif isinstance(o, list):
            for v in o: walk(v, key)
    walk(data)

print(f'{lang} : {len(errors)} problème(s)')
for e in errors[:60]:
    print(' -', e)
sys.exit(1 if errors else 0)
