# Audit du site bikentour.com : 90 / 100

*Audit réalisé le 3 novembre 2026 sur la version prête à pousser (151 pages HTML en 4 langues : 76 en français, dont les 46 articles du blog, et 25 dans chacune des 3 autres langues). Contrôles automatiques : `tools/audit.py`, Lighthouse 12.2 en mode mobile, Playwright.*

| Domaine | Note | Constat |
| --- | --- | --- |
| SEO technique | **19 / 20** | 0 titre ni description en double ou trop long, 1 H1 par page, 0 image sans `alt`, canonical correct partout, `hreflang` réciproques dans les 4 langues, sitemap multilingue, 304 liens internes sans erreur. Les 140 anciennes URL Webflow répondent : 104 servies directement et 36 redirigées en 301. |
| Contenu et SEO on-page | **8 / 10** | Pages commerciales riches (guide, FAQ, itinéraires). Points faibles : les articles du blog datent de 2021 et sont courts (110 à 350 mots) ; la page « Presse » est mince. |
| GEO / AEO (moteurs de réponse IA) | **14 / 15** | Encadrés « En bref » citables sur 92 pages, FAQPage sur 80 pages, guide questions-réponses, fiche entreprise complète sur chaque page, `llms.txt`, `llms-full.txt`, une version Markdown par page, robots IA autorisés. Il manque des signaux externes : fiche Google Business, lien Tripadvisor, citations sur les sites de France Vélo Tourisme. |
| Multilingue | **9 / 10** | 25 pages par langue (EN, NL, DE), textes de vente adaptés, mots-clés locaux, 36 anciennes URL de langue conservées, admin en 4 langues. Le blog reste en français. |
| Performance | **14 / 15** | Lighthouse mobile entre 93 et 99 sur 8 pages testées dans les 4 langues. Images WebP responsives, Brotli, cache long, carte interactive chargée à l'approche de l'écran. |
| Accessibilité | **9 / 10** | Lighthouse 100 sur toutes les pages testées : contrastes, libellés, langue du document, navigation au clavier. Les tests manuels avec lecteur d'écran restent à faire. |
| UX, UI et conversion | **8 / 10** | Arguments de réassurance sous chaque bouton de réservation, barre de réservation fixe sur mobile, prix visibles partout, avis mis en avant. Limites : la réservation se fait sur le site externe Lokki, et le formulaire « trace GPX » ouvre la messagerie du visiteur. |
| Sécurité et conformité | **9 / 10** | En-têtes CSP stricte, HSTS, nosniff, frame ; admin protégée (session signée, anti-force brute), dossiers techniques inaccessibles, bannière cookies conforme CNIL (rien n'est chargé sans accord). Il manque l'adresse de l'hébergeur dans les mentions légales. |
| **Total** | **90 / 100** | |

## Améliorations faites pendant cet audit
- **Traductions EN/NL/DE fonctionnelles** : 75 pages, `hreflang`, sitemap, sélecteur de langue page par page, 36 anciennes URL de langue de nouveau en 200 au lieu de 302.
- **Prix toujours justes** : aucun prix n'est plus écrit en dur. Ils viennent de l'admin et se répercutent dans les 4 langues, les encadrés, le guide et les données Google.
- **Bannière cookies** conforme CNIL et page « Cookies ».
- **CSP** stricte et règles `robots.txt` unifiées.
- **Accueil** : chargement différé de la carte (performance de 89 à 93-94).
- **Typographie** : prix insécables, ponctuation propre à chaque langue.
- **Contenus** : titres en double corrigés (articles du blog, pages NL/DE), page des visites étoffée, menu « 12 idées voyages » corrigé.

## Pour gagner les 10 derniers points
1. **Mentions légales** : compléter l'adresse de l'hébergeur (Railway Corp.).
2. **Signaux externes** : renseigner la fiche Google Business et le lien Tripadvisor ; demander un lien depuis les fiches France Vélo Tourisme et l'office de tourisme de Nantes.
3. **Blog** : rafraîchir les 10 articles les plus visités (infos pratiques, photos, 600 mots et plus) et traduire les 3 meilleurs.
4. **Formulaire GPX** : brancher un service d'envoi (ex. Brevo) pour remettre la trace sans ouvrir la messagerie.
5. **Accessibilité** : faire un test manuel au lecteur d'écran (VoiceOver, NVDA).
6. **Notre histoire** : faire valider par Antoine la date de création et son parcours.
