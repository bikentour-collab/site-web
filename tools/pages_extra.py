"""Pages reprises du site actuel (mentions, CGL, recrutement, presse)."""
from pages import *


def text_page(key, url, crumb=None):
    """Page de texte (mentions, CGL, recrutement) : content/pages/<key>.md, modifiable dans l'admin."""
    import blog
    fm, text = blog.read_md(os.path.join(ROOT, 'content', 'pages', key + '.md'))
    h1 = fm.get('titre', crumb)
    body = (f'<section class="phero phero-slim"><div class="wrap"><h1>{esc(h1)}</h1></div></section>\n'
            f'<section class="section"><div class="wrap narrow prose legal">{blog.md_html(text)}</div></section>')
    page(url, fm.get('title', h1), fm.get('description', ''), [CRUMB_HOME, (crumb or h1, None)], body, [], priority='0.3')


def legal():
    text_page('mentions-legales', '/fr/mentions-legales')
    text_page('conditions-generales-de-vente', '/fr/conditions-generales-de-vente')
    text_page('nous-rejoindre', '/fr/nous-rejoindre')


from content import PRESS, REFS


def press():
    def tiles(lst, cta):
        return ''.join(f'<a class="tile press" href="{u}" rel="noopener"><span class="tile-body"><span class="tag">{esc(m)}</span>'
                       f'<strong>{esc(t)}</strong><span class="small">{cta} →</span></span></a>' for m, t, u in lst)
    refs = (f'<h2 class="press-radio">Ils nous recommandent</h2><p>Offices de tourisme et guides vélo qui présentent Bike\'N Tour.</p>'
            f'<div class="cards cards-3">{tiles(REFS, "Voir la fiche")}</div>') if REFS else ''
    body = (f'<section class="phero phero-slim"><div class="wrap"><p class="eyebrow">Presse</p><h1>Ils parlent de nous</h1>'
            f'<p class="lead">Presse, radio, blogs et offices de tourisme. Pour un article, une interview ou des photos, écrivez-nous à <a href="mailto:{EMAIL}">{EMAIL}</a>.</p></div></section>'
            f'<section class="section"><div class="wrap"><h2 class="press-radio">Dans la presse</h2><div class="cards cards-3">{tiles(PRESS, "Lire l\'article")}</div>'
            f'{refs}<h2 class="press-radio">À la radio</h2><p>Bike\'N Tour a été invité sur RTL2, NRJ et Fun Radio.</p></div></section>'
            f'<section class="section section-tint"><div class="wrap prose"><h2>Bike\'N Tour en quelques mots</h2>'
            f'<p>Bike\'N Tour est un loueur de vélos installé au 19 rue Jean Jaurès, en plein centre de Nantes, dans l\'hôtel Ibis Nantes Centre Tour Bretagne (tram T3, arrêt Jean Jaurès). '
            f'La boutique est ouverte d\'avril à octobre et porte le label Accueil Vélo.</p>'
            f'<ul><li><strong>{len(BIKES)} types de vélos à louer :</strong> {esc(", ".join(low(b["name"]) for b in BIKES))}, avec antivol, kit anti-crevaison et éclairage.</li>'
            f'<li><strong>6 grandes véloroutes au départ de la boutique :</strong> {esc(", ".join(r["name"] for r in ROUTES))}.</li>'
            f'<li><strong>{len(TOURS)} visites guidées de Nantes à vélo électrique</strong>, et des sorties sur mesure pour les groupes et les entreprises.</li>'
            f'<li><strong>Note Google :</strong> {esc(str(HOME["google_note"]))}/5 sur {esc(str(HOME["google_avis"]))} avis.</li></ul>'
            f'<h3>Pour les journalistes</h3><p>Photos en haute définition, interview, essai d\'un vélo ou participation à une visite guidée : écrivez-nous à <a href="mailto:{EMAIL}">{EMAIL}</a> '
            f'ou appelez le <a href="tel:{PHONE}">{PHONE_TXT}</a>. Pour présenter l\'activité, vous pouvez aussi vous appuyer sur <a href="/fr/qui-sommes-nous-nous-contacter">notre page « Qui sommes-nous »</a> '
            f'et sur <a href="/fr/guide-location-velo-nantes">notre guide de la location de vélo à Nantes</a>.</p></div></section>')
    biz = {"@id": f"{SITE}/#business"}
    items = ([{"@type": "NewsArticle", "headline": t, "url": u, "publisher": {"@type": "Organization", "name": m}, "about": biz} for m, t, u in PRESS]
             + [{"@type": "WebPage", "name": t, "url": u, "publisher": {"@type": "Organization", "name": m}, "about": biz} for m, t, u in REFS])
    lst = {"@type": "ItemList", "name": "Articles et sites qui parlent de Bike'N Tour",
           "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": it} for i, it in enumerate(items)]}
    names = ' et '.join(m for m, _, _ in PRESS[:2]) + (' ; recommandé par ' + ' et '.join(m for m, _, _ in REFS[:2]) if REFS else '')
    page('/fr/ils-parlent-de-nous-tv-radio-presse-blogs', "Ils parlent de nous : presse, radio, blogs | Bike'N Tour",
         f"Bike'N Tour dans la presse ({names}) et à la radio sur RTL2, NRJ et Fun Radio.",
         [CRUMB_HOME, ('Ils parlent de nous', None)], body, [lst], priority='0.5', kind='CollectionPage')
