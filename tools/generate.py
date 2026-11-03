"""Génère tout le site : accueil (build.py), pages intérieures, blog, sitemap, robots, llms.txt,
puis les versions anglaise, néerlandaise et allemande (même code, SITE_LANG=en|nl|de).
Usage : cd tools && python3 generate.py"""
import os, sys, runpy, subprocess

LANG = os.environ.get('SITE_LANG', 'fr')
runpy.run_path('build.py')
import pages, pages_extra, blog, i18n

I18N_PAGES = (pages.route_pages, pages.hub, pages.balades, pages.bike_pages, pages.fleet, pages.pricing, pages.tours,
              pages.visits, pages.groups, pages.about, pages.faq_page, pages.guide, pages.cookies)
if LANG == 'fr':
    for f in I18N_PAGES + (pages_extra.legal, pages_extra.press, blog.build):
        f()
    i18n.save_record()
    pages.save_pages()
    print(len(pages.PAGES) + 1, 'pages générées (fr)')
    if os.environ.get('SKIP_LANGS'):
        sys.exit(0)
    for lang in i18n.LANGS[1:]:
        subprocess.run([sys.executable, 'generate.py'], check=True, env={**os.environ, 'SITE_LANG': lang})
    pages.write_seo_files()
    import postprocess
    postprocess.run()
else:
    for f in I18N_PAGES:
        f()
    pages.save_pages()
    print(len(pages.PAGES) + 1, f'pages générées ({LANG})')
