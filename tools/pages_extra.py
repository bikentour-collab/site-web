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


from content import PRESS


def press():
    items = ''.join(f'<a class="tile press" href="{u}" rel="noopener"><span class="tile-body"><span class="tag">{esc(m)}</span>'
                    f'<strong>{esc(t)}</strong><span class="small">Lire l\'article →</span></span></a>' for m, t, u in PRESS)
    body = (f'<section class="phero phero-slim"><div class="wrap"><p class="eyebrow">Presse</p><h1>Ils parlent de nous</h1>'
            f'<p class="lead">Presse, radio et blogs. Pour un article, une interview ou des photos, écrivez-nous à <a href="mailto:{EMAIL}">{EMAIL}</a>.</p></div></section>'
            f'<section class="section"><div class="wrap"><div class="cards cards-3">{items}</div>'
            f'<h2 class="press-radio">À la radio</h2><p>RTL2, NRJ et Fun Radio. <span class="muted">[Liens des interventions à fournir]</span></p></div></section>')
    page('/fr/ils-parlent-de-nous-tv-radio-presse-blogs', "Ils parlent de nous : presse, radio, blogs | Bike'N Tour",
         "Bike'N Tour dans la presse : Ouest-France, Le Bonbon Nantes, Tourisme Loire-Atlantique, et à la radio sur RTL2, NRJ et Fun Radio.",
         [CRUMB_HOME, ('Ils parlent de nous', None)], body, [], priority='0.4')
