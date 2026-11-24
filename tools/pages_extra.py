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
    jobs()


def jobs():
    """Page recrutement : texte de l'admin (content/pages/nous-rejoindre.md) et formulaire de candidature avec CV."""
    import blog
    from icons import icon
    fm, text = blog.read_md(os.path.join(ROOT, 'content', 'pages', 'nous-rejoindre.md'))
    h1 = fm.get('titre', 'Nous rejoindre')
    form = f'''<form class="form-card" data-form-api="/api/contact" data-kind="candidature" data-mailto="{EMAIL}" novalidate
  data-ok="Merci ! Votre candidature est bien partie. Antoine la lit et vous répond rapidement."
  data-err="L'envoi n'a pas fonctionné. Réessayez, ou envoyez votre CV directement à {EMAIL}."
  data-big="Votre CV dépasse 5 Mo : enregistrez-le en PDF plus léger, ou envoyez-le par email."
  data-msg="Votre messagerie s'ouvre : pensez à joindre votre CV avant d'envoyer.">
  <h2>{icon('briefcase')} Postuler</h2>
  <p class="small muted">Les champs marqués d'un * sont obligatoires.</p>
  <div class="hp" aria-hidden="true"><label>Site web <input type="text" name="site" tabindex="-1" autocomplete="off"></label></div>
  <label class="field"><span>Nom et prénom *</span><input name="nom" autocomplete="name" required></label>
  <div class="field-row">
    <label class="field"><span>Email *</span><input name="email" type="email" autocomplete="email" required></label>
    <label class="field"><span>Téléphone</span><input name="tel" type="tel" autocomplete="tel"></label>
  </div>
  <label class="field"><span>Poste</span><select name="poste">
    <option>Stage gestion de projet et relation clients</option><option>Renfort saisonnier</option><option>Guide de visites à vélo</option><option>Candidature spontanée</option>
  </select></label>
  <label class="field"><span>Vos disponibilités</span><input name="dates" placeholder="Ex. d'avril à septembre"></label>
  <label class="field"><span>Quelques mots sur vous *</span><textarea name="message" rows="5" required placeholder="Pourquoi Bike'N Tour, ce que vous aimeriez apporter à l'équipe…"></textarea></label>
  <label class="field file-field"><span>{icon('paperclip')} Votre CV (PDF, Word ou image, 5 Mo maximum)</span><input name="cv" type="file" accept=".pdf,.doc,.docx,.odt,.jpg,.jpeg,.png"></label>
  <p class="small muted">Votre candidature est transmise uniquement à Bike'N Tour, qui ne la conserve que le temps du recrutement.</p>
  <button class="btn btn-primary" type="submit">{icon('send')}<span>Envoyer ma candidature</span></button>
  <p class="form-status" role="status" aria-live="polite"></p>
</form>'''
    body = (f'<section class="phero phero-slim"><div class="wrap"><p class="eyebrow">Recrutement</p><h1>{esc(h1)}</h1>'
            f'<p class="lead">{esc(fm.get("description", ""))}</p></div></section>'
            f'<section class="section section-top0"><div class="wrap jobs-grid"><div class="prose jobs-text">{blog.md_html(text)}</div>'
            f'<div class="jobs-form" id="postuler">{form}</div></div></section>')
    ld = {"@type": "JobPosting", "title": "Stage gestion de projet et relation clients", "description": re.sub(r'<[^>]+>', ' ', blog.md_html(text))[:3000],
          "datePosted": TODAY, "employmentType": "INTERN", "hiringOrganization": {"@id": BIZ},
          "jobLocation": {"@type": "Place", "address": {"@type": "PostalAddress", "streetAddress": "27 quai de Versailles", "postalCode": "44000", "addressLocality": "Nantes", "addressCountry": "FR"}},
          "baseSalary": {"@type": "MonetaryAmount", "currency": "EUR", "value": {"@type": "QuantitativeValue", "value": 600, "unitText": "MONTH"}}}
    page('/fr/nous-rejoindre', fm.get('title', h1), fm.get('description', ''), [CRUMB_HOME, ('Nous rejoindre', None)], body, [ld], priority='0.4')


from content import PRESS, REFS


def press():
    from icons import icon
    def tiles(lst, cta):
        return ''.join(f'<a class="press-card" href="{u}" rel="noopener"><span class="press-media">{esc(m)}</span>'
                       f'<strong>{esc(t)}</strong><span class="arrow-link">{T(cta)}</span></a>' for m, t, u in lst)
    refs = (f'<h2>Ils nous recommandent</h2><p class="muted">Offices de tourisme et guides vélo qui présentent Bike\'N Tour.</p>'
            f'<div class="press-grid">{tiles(REFS, "Voir la fiche")}</div>') if REFS else ''
    stats = (f'<ul class="press-stats"><li><strong>{esc(str(HOME["google_note"]))}/5</strong><span>{T("{n} avis Google", n=HOME["google_avis"])}</span></li>'
             f'<li><strong>{esc(str(HOME["tripadvisor_avis"]))}</strong><span>{T("avis 5 étoiles sur Tripadvisor")}</span></li>'
             f'<li><strong>6</strong><span>véloroutes au départ de la boutique</span></li>'
             f'<li><strong>Accueil Vélo</strong><span>label France Vélo Tourisme</span></li></ul>')
    body = (f'<section class="phero phero-slim"><div class="wrap"><p class="eyebrow">Presse</p><h1>Ils parlent de nous</h1>'
            f'<p class="lead">Presse, radio, blogs et offices de tourisme parlent de Bike\'N Tour. Pour un article, une interview ou des photos, écrivez-nous.</p>{stats}</div></section>'
            f'<section class="section section-top0"><div class="wrap"><h2>Dans la presse</h2><div class="press-grid">{tiles(PRESS, "Lire l\'article")}</div>'
            f'{refs}<h2>À la radio</h2><p>Bike\'N Tour a été invité sur RTL2, NRJ et Fun Radio.</p></div></section>'
            f'<section class="section section-tint"><div class="wrap press-kit"><div class="prose"><h2>Bike\'N Tour en quelques mots</h2>'
            f'<p>Bike\'N Tour est un loueur de vélos installé au 27 quai de Versailles, au bord de l\'Erdre, face à l\'île de Versailles (tram ligne 2, arrêt Saint-Mihiel). '
            f'La boutique est ouverte d\'avril à octobre et porte le label Accueil Vélo.</p>'
            f'<ul><li><strong>{T("{n} types de vélos à louer :", n=len(BIKES))}</strong> {esc(", ".join(low(b["name"]) for b in BIKES))}{T(", avec antivol, kit anti-crevaison et éclairage.")}</li>'
            f'<li><strong>{T("{n} grandes véloroutes au départ de la boutique :", n=len(ROUTES))}</strong> {esc(", ".join(r["name"] for r in ROUTES))}.</li>'
            f'<li><strong>{T("{n} visites guidées de Nantes à vélo électrique", n=len(TOURS))}</strong>{T(", et des sorties sur mesure pour les groupes et les entreprises.")}</li></ul></div>'
            f'<div class="ccard press-contact"><p class="eyebrow">{icon("newspaper")} Contact presse</p>'
            f'<p>Photos en haute définition, interview, essai d\'un vélo ou participation à une visite guidée : Antoine vous répond.</p>'
            f'<a class="qbtn" href="mailto:{EMAIL}">{icon("mail")}<span>{EMAIL}</span></a><a class="qbtn" href="tel:{PHONE}">{icon("phone")}<span>{PHONE_TXT}</span></a>'
            f'<a class="qbtn" href="/assets/img/logo-texte.png" download>{icon("download")}<span>Télécharger le logo</span></a></div></div></section>')
    biz = {"@id": f"{SITE}/#business"}
    items = ([{"@type": "NewsArticle", "headline": t, "url": u, "publisher": {"@type": "Organization", "name": m}, "about": biz} for m, t, u in PRESS]
             + [{"@type": "WebPage", "name": t, "url": u, "publisher": {"@type": "Organization", "name": m}, "about": biz} for m, t, u in REFS])
    lst = {"@type": "ItemList", "name": "Articles et sites qui parlent de Bike'N Tour",
           "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": it} for i, it in enumerate(items)]}
    page('/fr/ils-parlent-de-nous-tv-radio-presse-blogs', "Presse : ils parlent de Bike'N Tour | Bike'N Tour",
         T("Bike'N Tour dans la presse (Ouest-France, Le Bonbon Nantes…), à la radio sur RTL2, NRJ et Fun Radio, et recommandé par les offices de tourisme. Contact presse."),
         [CRUMB_HOME, ('Presse', None)], body, [lst], priority='0.5', kind='CollectionPage')
