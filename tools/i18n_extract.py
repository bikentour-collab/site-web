"""Construit tools/i18n/catalog.json : phrases françaises à traduire (gabarit + pages traduites) et modèles T().
Usage : cd tools && python3 i18n_extract.py   (relance la génération française en mode enregistrement)"""
import os, json, re, subprocess, sys
import i18n

REC = os.path.join(i18n.TOOLS, '.i18n-record.json')
subprocess.run([sys.executable, '-c', 'import runpy; runpy.run_path("build.py"); import pages, generate'], check=False,
               env={**os.environ, 'I18N_RECORD': REC, 'SITE_LANG': 'fr', 'SKIP_LANGS': '1', 'NO_BLOG': '1'})
rec = json.load(open(REC))
outputs = [o for o in rec['outputs'] if len(o) > 12]

# textes déjà traduits via content/<langue>/*.json
content_vals = set()
def walk(o):
    if isinstance(o, dict):
        for v in o.values(): walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
    elif isinstance(o, str):
        content_vals.add(i18n.norm(o))
for f in os.listdir(os.path.join(i18n.ROOT, 'content', 'fr')):
    walk(json.load(open(os.path.join(i18n.ROOT, 'content', 'fr', f))))

keys = []
sources = [open('page.tpl.html').read(), open('../index.html').read()]
sources += [open(os.path.join(i18n.ROOT, u.strip('/') + '.html')).read() for u in i18n.PAGE_KEYS.values() if u != '/']
for src in sources:
    keys += i18n.extract(src)
seen, out = set(), []
for k in keys:
    if k in seen or k in content_vals or not i18n.LETTER.search(re.sub(r'<[^>]+>|\{\{\w+\}\}', '', k)):
        continue
    if any(o in k for o in outputs):
        continue
    # phrase entièrement composée de textes du contenu (déjà traduits dans content/<langue>/)
    rest = re.sub(r'<[^>]+>', ' ', k)
    for v in sorted(content_vals, key=len, reverse=True):
        if len(v) > 2 and v in rest:
            rest = rest.replace(v, ' ')
    if not i18n.LETTER.search(rest):
        continue
    seen.add(k); out.append(k)
json.dump({'html': out, 't': rec['t']}, open(os.path.join(i18n.TOOLS, 'i18n', 'catalog.json'), 'w'), ensure_ascii=False, indent=1)
print(len(out), 'phrases,', len(rec['t']), 'modèles T(),', sum(len(k) for k in out) + sum(len(k) for k in rec['t']), 'caractères')
# remet le site français complet (avec les blocs du blog)
subprocess.run([sys.executable, 'generate.py'], check=True, stdout=subprocess.DEVNULL)
