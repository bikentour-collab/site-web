# Bike'N Tour – bikentour.com

Site statique (HTML/CSS/JS, sans framework) en 5 langues (FR, EN, NL, DE, ES), généré par des scripts Python,
servi par un petit serveur Node sur Railway, avec une administration Sveltia CMS sur `/admin`.

```
GitHub (dépôt unique)  ──push──▶  GitHub Action « Générer le site »  ──commit──▶  Railway (npm start)
        ▲                              tools/generate.py
        └── /admin (Sveltia CMS) : Antoine modifie textes, tarifs, photos, articles
```

## Mise en ligne (une seule fois)

1. **GitHub** : créer un dépôt privé (ex. `bikentour/site`), y pousser ce dossier sur la branche `main`.
   Dans *Settings → Actions → General*, autoriser « Read and write permissions » (l'action enregistre les pages générées).
2. **Railway** : *New Project → Deploy from GitHub repo* (Node détecté, commande `npm start`, port fourni par `PORT`).
   Ajouter le domaine `www.bikentour.com` (*Settings → Networking*) puis mettre à jour le DNS ; rediriger `bikentour.com` vers `www`.
3. **Variables Railway** (*Variables*) :

| Variable | Rôle |
| --- | --- |
| `ADMIN_USER` | identifiant de connexion à `/admin` |
| `ADMIN_PASSWORD` | mot de passe de `/admin` (12 caractères minimum). **Sans lui, l'administration reste fermée.** |
| `SESSION_SECRET` | chaîne aléatoire longue (signature des sessions) – ex. `openssl rand -hex 32` |
| `GITHUB_REPO` | `compte/depot`, ex. `bikentour/site` |
| `GITHUB_TOKEN` | **mode simple** : jeton GitHub « fine-grained » limité à ce dépôt, permission *Contents : Read and write*. Antoine se connecte alors uniquement avec identifiant + mot de passe, et arrive directement dans l'administration (session préparée par le serveur). **Recommandé.** |
| `TRANSLATE_API_KEY` | clé du service de traduction automatique de l'admin (bouton « Traduire »). Par défaut **Google Gemini** : clé gratuite sur https://aistudio.google.com/app/apikey (commence par `AIza`). Déposée automatiquement dans l'admin après connexion : rien à saisir pour l'éditeur. |
| `TRANSLATE_SERVICE` | facultatif : `google-ai` (Gemini, défaut), `anthropic` (Claude), `openai`, `google` (Cloud Translation), `mistral`, `deepseek`. |
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | **mode alternatif** (sans `GITHUB_TOKEN`) : application OAuth GitHub, callback `https://www.bikentour.com/cms/callback` ; chaque éditeur se connecte avec son compte GitHub. |
| `SITE_URL` | facultatif, `https://www.bikentour.com` par défaut |
| `PROD_HOSTS` | facultatif : domaines indexables (par défaut `www.bikentour.com,bikentour.com`). Toute autre adresse, dont l'adresse de test Railway, est servie en `noindex`. |
| `RESEND_API_KEY` | clé API Resend (resend.com, gratuit jusqu'à 3 000 emails/mois). Le formulaire « Fiche PDF et trace GPX » des pages itinéraires envoie alors **immédiatement** au visiteur, dans sa langue, la fiche PDF et la trace GPX en pièces jointes, et une copie de la demande à `CONTACT_EMAIL`. Sans clé, le formulaire ouvre la messagerie du visiteur. |
| `SENDER_EMAIL` | facultatif : expéditeur, sur un domaine vérifié dans Resend (DNS de bikentour.com : enregistrements SPF/DKIM fournis par Resend). Par défaut `Bike'N Tour <contact@bikentour.com>`. |
| `CONTACT_EMAIL` | facultatif : adresse qui reçoit les demandes et les réponses des visiteurs (par défaut `contact@bikentour.com`). |
| `CONTACT_EMAIL` | facultatif : adresse qui reçoit les demandes (par défaut `contact@bikentour.com`) |

4. Vérifier : `https://www.bikentour.com/admin` → écran de connexion → « Se connecter avec GitHub » (mode simple : connexion immédiate).

## Modifier le site
- **Antoine** : `/admin` (voir `docs/mode-emploi-admin.md`). Chaque publication déclenche l'action GitHub, le site est à jour en 2 à 3 minutes.
- **Développeur** : modifier `tools/` ou `assets/`, puis `cd tools && python3 generate.py`, vérifier en local, pousser.

## Lancer en local
```bash
pip install -r tools/requirements.txt
cd tools && python3 generate.py      # génère les 4 langues, le blog, sitemap, llms.txt, versions .md
cd .. && PORT=4180 ADMIN_USER=test ADMIN_PASSWORD=test node server.js
```
L'admin fonctionne aussi en local avec « Travailler avec un dépôt local » (Chrome/Edge).

## Organisation
- `content/fr/*.json` : contenu de référence (vélos et tarifs, itinéraires, visites, groupes, balades, FAQ, accueil, coordonnées)
- `content/en|nl|de/*.json` : textes traduits (prix, photos et identifiants viennent toujours du français)
- `content/blog/*.md` : 46 articles (français), `content/pages/*.md` : mentions légales, CGL, recrutement
- `tools/generate.py` : point d'entrée ; `build.py` + `page.tpl.html` (accueil), `pages.py`, `pages_extra.py`, `blog.py`,
  `postprocess.py` (images responsives, versions Markdown, menu actif, versionnage CSS/JS), `content.py` (lecture du contenu)
- `tools/i18n.py`, `tools/i18n/*.json` : traductions des textes fixes (catalogue `catalog.json`, `i18n_extract.py` pour le régénérer,
  `i18n_check.py <langue>` pour le vérifier), `tools/i18n/urls.json` : adresse de chaque page dans chaque langue
- `tools/audit.py` : audit automatique (titres, hreflang, liens, données structurées, en-têtes, texte non traduit)
- `admin/` : Sveltia CMS 0.250.0 (hébergé avec le site) + `config.yml`
- `server.js` : pages, redirections 301 (`redirects.json`), URL propres, compression, cache, en-têtes de sécurité (CSP, HSTS),
  connexion admin (session signée, anti-force brute), service de jeton GitHub pour le CMS
- `.github/workflows/generer-le-site.yml` : régénération automatique à chaque modification du contenu (+ chaque lundi)

## Ajouter ou retraduire des textes fixes
1. Modifier le français dans `tools/` puis `python3 i18n_extract.py` (met à jour `tools/i18n/catalog.json`).
2. Compléter `tools/i18n/en.json`, `nl.json`, `de.json` (clé = phrase française) ; `python3 i18n_check.py en` doit afficher 0 problème.
3. Une phrase non traduite s'affiche en français : rien ne casse.

## SEO, GEO, performances
- Dates de modification réelles par page (`tools/lastmod.json`, mis à jour par la génération) : sitemap, « Mis à jour le », `dateModified`
- Sitemap avec images, flux RSS du blog (`/fr/blog.xml`), géolocalisation de la boutique dans l'en-tête
- Points de vue des itinéraires (carte, pages, JSON-LD TouristAttraction avec coordonnées, `llms.txt`) ; guide avec procédure HowTo
- 4 langues avec `hreflang` réciproques, sitemap multilingue, 36 anciennes URL EN/NL/DE conservées, 140 anciennes URL Webflow toutes servies (200 ou 301)
- JSON-LD complet par page (BikeStore, TouristTrip, Product, FAQPage, BlogPosting, BreadcrumbList…), encadrés « En bref » (speakable)
- `llms.txt`, `llms-full.txt`, version Markdown de chaque page (`/page.md`), `robots.txt` ouvert aux robots IA
- Images WebP responsives, police auto-hébergée, CSS/JS versionnés en cache long, Brotli
- Bannière cookies conforme CNIL : rien n'est chargé sans accord ; identifiant GA4 ou Matomo à renseigner dans l'admin

## Reste à faire / à valider avec Antoine
- Adresse de l'hébergeur Railway dans les mentions légales ; texte « Notre histoire » ; lien Tripadvisor ; droits photos
- Protection casse et vol : 2 €/j (voyage, enfant) et 3 €/j (électrique, gravel) selon la grille 2026
- Formulaire « trace GPX » : ouvre la messagerie du visiteur (brancher un service d'envoi si besoin)
- Blog : 12 articles réécrits le 4/11/2026 ; points à valider listés dans `docs/audit.md` ; 34 articles anciens restent à rafraîchir


## Fiches PDF et traces GPX des itinéraires
- `tools/gpx_export.py` écrit `assets/gpx/bikentour-<itinéraire>.gpx` (parcours au départ de Nantes, même découpage que la carte), recalculé seulement si `tools/data` change.
- `tools/fiche.py` écrit `assets/pdf/fiches/<itinéraire>-<langue>.pdf` à chaque génération (30 fiches : 6 itinéraires × 5 langues) à partir du contenu de l'admin : une étape modifiée dans l'admin est donc à jour dans la fiche.
- Envoi : `server.js` (`/api/gpx`, Resend).
