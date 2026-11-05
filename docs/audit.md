# Audit du site bikentour.com : 96,5 / 100

*Audit refait le 5 novembre 2026 (après-midi), après le chantier « contenu + 8 actions ». Version prête à pousser : 172 pages HTML en 4 langues (76 en français, dont les 46 articles du blog, et 32 dans chacune des 3 autres langues). Contrôles : `tools/audit.py`, Lighthouse mobile sur 9 pages, axe-core (WCAG 2.1 AA et bonnes pratiques) sur 15 pages en ordinateur et en mobile, parcours au clavier, maillage interne. Précédents audits : 90 / 100 le 3 novembre, 92 / 100 le 5 novembre au matin.*

| Domaine | Note | Constat |
| --- | --- | --- |
| SEO technique | **20 / 20** | 0 erreur de titre, description, H1, canonical, `hreflang`, données structurées ; 323 liens internes testés, 0 erreur, 0 lien vers une adresse redirigée. |
| Contenu et SEO on-page | **9,5 / 10** | Les 46 articles du blog font désormais de 725 à 1 070 mots (faits vérifiés, fiches pratiques, FAQ, liens internes) ; page presse étoffée. Reste : quelques distances estimées et points signalés à faire valider par Antoine. |
| GEO / AEO | **14,5 / 15** | « En bref », FAQPage, `llms.txt`, versions Markdown, presse et recommandations reliées à la fiche entreprise, fiche France Vélo Tourisme en `sameAs`. Manque : liens Google Business et Tripadvisor à coller dans l'admin (champs prêts). |
| Multilingue | **10 / 10** | 32 pages par langue, dont 7 articles du blog traduits (top 5, premier voyage à vélo, île de Nantes, vélo électrique, Pornic, Sèvre nantaise, estuaire) avec `hreflang` vers le français ; images de partage dans la langue de la page. |
| Performance | **14,5 / 15** | Lighthouse mobile 93 à 100 sur les 9 pages testées (accueil 93, contre 89-91 avant) ; CLS 0. Affichage principal de l'accueil en 2,7 s, encore un peu au-dessus de 2,5 s. |
| Accessibilité | **9,5 / 10** | Lighthouse 100 partout ; axe-core : 0 défaut sur 30 contrôles après correction (carte, tableaux défilants, encadrés) ; parcours clavier correct. Test au lecteur d'écran à faire par une personne. |
| UX, UI et conversion | **8,5 / 10** | Image de partage soignée pour chaque page, formulaire GPX qui envoie directement (dès que la clé Brevo est ajoutée), badges d'avis reliés à l'admin. Limite : réservation sur Lokki. |
| Sécurité et conformité | **10 / 10** | Hébergeur complet dans les mentions légales ; formulaire protégé (champ piège, 5 demandes par heure et par adresse IP). |
| **Total** | **96,5 / 100** | +4,5 points depuis ce matin, +6,5 depuis le 3 novembre |

## Fait pendant ce chantier (5 novembre après-midi)
- **Contenu** : 33 articles anciens réécrits (725 à 900 mots), avec erreurs historiques corrigées (frères Crucy, château de la Droitière, levée de la Divatte 1856, Porte-Vue sur la Maine, tunnel Saint-Félix, Tour Bretagne fermée jusqu'en 2029…) ; page « Ils parlent de nous » complétée (présentation, contact presse).
- **Mentions légales** : adresse de Railway Corporation.
- **Google et Tripadvisor** : badges d'avis et chiffres pilotés par l'admin, champs pour les liens des fiches, fiche France Vélo Tourisme reliée.
- **Accueil mobile** : photo du haut chargée en priorité, fond de carte chargé à l'ouverture de la carte (performance 89-91 → 93).
- **Images de partage** : 1 200 × 630 automatiques pour toutes les pages (photo + logo + titre dans la langue), régénérées à chaque modification.
- **Formulaire GPX** : envoi direct par Brevo (`BREVO_API_KEY` dans Railway), accusé de réception dans la langue du visiteur, repli sur la messagerie sans clé.
- **Accessibilité** : rôle de la carte, tableaux défilants accessibles au clavier et nommés, encadrés non imbriqués.
- **Traductions** : 3 articles en anglais, néerlandais et allemand ; bloc « From our blog » sur les pages traduites.

## Pour aller chercher les 3,5 derniers points
1. **Antoine, dans l'admin** : coller les liens de la fiche Google Business et de Tripadvisor. *+0,5*
2. **Railway** : ajouter `BREVO_API_KEY` (compte Brevo gratuit, expéditeur `contact@bikentour.com` validé). *+0,5*
3. **Faire valider par Antoine** : distances estimées de quelques articles, distance du lac de Grand-Lieu (18 ou 21 km), durée du TER Pornic–Nantes, guinguettes de l'Erdre, rappel Babboe 2024 sur le vélo cargo. *+0,5*
4. **Test au lecteur d'écran** (VoiceOver, NVDA) par une personne. *+0,5*
5. **Accueil mobile sous 2,5 s** (aujourd'hui 2,6-2,7 s en mobile simulé, photo du haut déjà allégée de 25 %) : il faudrait une photo recadrée spécifiquement pour mobile. *+0,5*
6. ~~Traduire plus d'articles~~ : fait (7 articles en EN/NL/DE).
7. **Réservation intégrée** au site au lieu du site externe Lokki, si l'outil le permet. *+1*

## Corrigé pendant cet audit (5 novembre)
- Page « Idées de balades » (4 langues) : titres H3 sans H2 au-dessus, passés en H2 (accessibilité 98 → 100 sur la page allemande).

## Améliorations faites pendant cet audit
- **Traductions EN/NL/DE fonctionnelles** : 75 pages, `hreflang`, sitemap, sélecteur de langue page par page, 36 anciennes URL de langue de nouveau en 200 au lieu de 302.
- **Prix toujours justes** : aucun prix n'est plus écrit en dur. Ils viennent de l'admin et se répercutent dans les 4 langues, les encadrés, le guide et les données Google.
- **Bannière cookies** conforme CNIL et page « Cookies ».
- **CSP** stricte et règles `robots.txt` unifiées.
- **Accueil** : chargement différé de la carte (performance de 89 à 93-94).
- **Typographie** : prix insécables, ponctuation propre à chaque langue.
- **Contenus** : titres en double corrigés (articles du blog, pages NL/DE), page des visites étoffée, menu « 12 idées voyages » corrigé.

## Améliorations SEO / GEO du 4 novembre
- Dates de modification réelles (sitemap, pages, données Google) au lieu de la date du jour
- 25 points de vue géolocalisés (TouristAttraction) sur les 6 itinéraires, dans les 4 langues et dans `llms.txt`
- Guide : procédure « Louer un vélo en 4 étapes » (HowTo)
- Sitemap avec images (151 pages), flux RSS du blog, balises de géolocalisation

## Blog et presse (4 novembre, suite)
- 12 articles stratégiques réécrits (800 à 1 070 mots) : réponse directe, fiche pratique, parcours, à voir, infos pratiques, FAQ, liens internes ; faits vérifiés sur France Vélo Tourisme, Le Voyage à Nantes, SNCF/Aléop
- Champ « Date de mise à jour » dans l'admin : « Mis à jour le » sur l'article et `dateModified` pour Google
- Page presse : données structurées des articles, rubrique « Ils nous recommandent » (France Vélo Tourisme, Le Voyage à Nantes, En Pays de la Loire, SNCF Connect), mentions reliées à la fiche entreprise sur toutes les pages et dans `llms.txt`
- Maillage interne : 32 anciens articles renvoient vers l'article de référence de leur sujet (ancre descriptive au lieu de « Voir ici… ») ; pages itinéraires, visites, vélo enfant et guide mettent en avant les articles réécrits ; 0 lien cassé, 0 lien vers une URL redirigée
- Images : fond de carte allégé (80 Ko au lieu de 430 Ko, version HD chargée seulement au zoom), tailles adaptées pour les vignettes vélos de l'accueil ; accueil mobile 350 Ko d'images au lieu de 700 Ko
