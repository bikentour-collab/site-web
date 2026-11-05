# Consigne de rédaction : réécriture des articles du blog Bike'N Tour

Bike'N Tour loue des vélos de voyage, électriques, gravel, enfant et cargo, et propose des visites guidées de Nantes à vélo électrique. La boutique est au 19 rue Jean Jaurès, 44000 Nantes, dans l'hôtel Ibis Nantes Centre Tour Bretagne (tram T3, arrêt Jean Jaurès). Elle est ouverte d'avril à octobre.

Les articles datent de 2019 à 2021 : ils sont courts (120 à 500 mots) et parfois périmés. Le but est d'en faire des articles utiles, exacts et durables, bien classés sur Google et faciles à citer pour les assistants IA.

## Dépôt et fichiers de référence
- Dépôt : `/home/claude/bikentour`. Les articles sont dans `content/blog/<slug>.md`, et l'adresse publique est `/post/<slug>`.
- Faits et liens internes à consulter :
  - `content/fr/balades.json` : distances et niveaux validés par le client ;
  - `content/fr/itineraires.json` : itinéraires, étapes et points de vue ;
  - `content/fr/velos.json` : vélos ;
  - `content/fr/visites.json` : visites guidées.
- Modèles du rendu attendu, à lire avant d'écrire : `content/blog/balade-incontournable-lerdre-a-velo.md` (balade) et `content/blog/balade-incontournable-lile-de-nantes.md` (Nantes).

## Format (sinon le site casse)
- **En-tête YAML** entre `---` :
  - garder exactement `titre`, `date`, `resume`, `image`, `categorie`, `lien`, `brouillon` ;
  - ne pas modifier `date`, `image`, `categorie`, `lien` ni `brouillon` ;
  - ajouter ou mettre `mise_a_jour: "2026-11-05"` ;
  - valeurs texte entre guillemets doubles.
- **`titre`** : clair, mot-clé en tête, 55 caractères au plus. Le titre est coupé au premier « : » quand il est trop long ; préférer « – » ou une phrase sans deux-points si le titre dépasse 45 caractères. Le nom du fichier, donc l'adresse, ne change pas.
- **`resume`** : 2 phrases. La première fait 155 caractères au plus et sert de description Google (lieu, intérêt, distance ou accès depuis la boutique).
- **Corps** :
  - Markdown simple : `##` et `###`, paragraphes, listes `-`, liens `[texte](/chemin)` ;
  - garder TOUTES les images existantes `![alt](/assets/img/...)`, placées entre les sections, avec un texte alt utile et vrai (regarder la photo avec l'outil Read si besoin) ;
  - pas de HTML ni de tableau.
- **Fiche pratique** juste après l'introduction quand c'est pertinent (lieu ou balade) : une liste dont CHAQUE ligne commence par un libellé en gras parmi Distance, Durée, Niveau, Dénivelé, Départ, Arrivée, Retour, Boucle, Accès. Exemple : `- **Distance :** 3 km depuis la boutique`. Laisser TOUJOURS une ligne vide avant et après la liste. Au moins 2 lignes.

## Structure (600 à 900 mots de corps)
1. **Introduction** de 2-3 phrases qui répond directement : qu'est-ce que c'est, pourquoi y aller, comment y aller à vélo depuis la boutique.
2. **Fiche pratique.**
3. **Deux ou trois sections `##` adaptées au sujet**, par exemple « Un peu d'histoire », « Ce qu'il faut voir », « Le parcours », « Y aller à vélo depuis la boutique ».
4. **`## Infos pratiques`** : saison, pause, accès, sans horaires ni prix de tiers sauf s'ils sont vérifiés et durables.
5. **`## Quel vélo choisir ?`** (court) ou un paragraphe équivalent, avec des liens vers les pages pertinentes parmi `/fr/location-velo-de-voyage`, `/fr/location-velo-electrique-voyage`, `/fr/location-gravel-nantes`, `/fr/location-velo-enfant`, `/fr/location-velo-cargo`, `/fr/visites-guidees-nantes`, `/fr/tour/tour-du-panorama-nantais`, `/fr/tour/tour-a-velo-electrique-culture-urbaine-a-nantes`, `/fr/tour/tour-surprenantes` et les pages `/fr/itineraires-velo-depart-nantes/<loire-a-velo|velodyssee|regalante|traversee-bretonne|canal-nantes-brest|vignoble-nantais>`.
6. **`## Questions fréquentes`** : 3 questions en `###`, réponses courtes et concrètes.
7. **Dernière ligne** : garder le lien « À lire aussi : … » existant (il pointe vers l'article de référence du sujet) et ajouter si utile un lien vers un autre article `/post/...`.

## Éviter le doublon avec l'article de référence
Plusieurs anciens articles traitent le même sujet qu'un article déjà réécrit. Dans ce cas, prendre un ANGLE DIFFÉRENT et renvoyer vers l'article de référence pour le trajet complet. Par exemple, l'article « le lac de Grand-Lieu » parle du lac lui-même (nature, oiseaux, Maison du lac, villages) ; le trajet à vélo est dans `/post/balade-incontournable-de-nantes-au-lac-de-grand-lieu`. Les articles de référence :
- Mauves : `/post/balade-incontournable-la-loire-a-velo-de-nantes-a-mauves-sur-loire`
- Cordemais et Villa Cheminée : `/post/balade-incontournable-la-loire-a-velo-de-nantes-a-cordemais`
- Estuaire et Saint-Brevin : `/post/balade-incontournable-le-parcours-de-lestuaire-de-nantes-a-saint-brevin-les-pins`
- Sèvre et Clisson : `/post/balade-incontournable-la-sevre-nantaise`
- Grand-Lieu : `/post/balade-incontournable-de-nantes-au-lac-de-grand-lieu`
- Erdre : `/post/balade-incontournable-lerdre-a-velo`
- Île de Nantes : `/post/balade-incontournable-lile-de-nantes`
- Ligne verte et Voyage à Nantes : `/post/le-voyage-a-nantes-2021-a-deja-commence`
- Pornic : `/post/pornic-a-velo`
- Vélo électrique : `/post/pourquoi-tester-un-velo-a-assistance-electrique-vae-a-nantes`
- Premier voyage à vélo : `/post/balade-incontournable-le-voyage-a-velo`

## Exactitude : règle absolue
- Vérifier chaque fait (dates historiques, hauteurs, distances, horaires de saison, noms) avec WebSearch ou WebFetch sur des sources fiables :
  - Ville de Nantes et Nantes Métropole ;
  - nantes-tourisme.com, levoyageanantes.fr, lesmachines-nantes.fr ;
  - francevelotourisme.com ;
  - sites des communes et du Département de Loire-Atlantique ;
  - Wikipédia, en recoupant.
- Ne rien inventer : ni chiffre, ni date, ni prix de tiers, ni horaire, ni nom de commerce. Si un fait n'est pas sûr, ne pas en parler. Une entreprise privée citée dans l'article d'origine (brasserie, restaurant) n'est gardée que si sa page officielle ou une source récente confirme qu'elle est toujours ouverte ; sinon, réorienter l'article vers le quartier ou le thème.
- Pas d'information datée présentée comme actuelle.
- Les tarifs Bike'N Tour ne s'écrivent pas en chiffres : faire un lien vers `/fr/nos-tarifs-reservation`.

## Style
- Français naturel et chaleureux, vouvoiement, phrases courtes.
- Ton d'un loueur local passionné qui conseille, sans superlatif creux ni remplissage.
- Typographie française : espace avant « : », « ? » et « ! ».

## Contrôle final
- Chaque fichier commence par `---` et son YAML est valide :
  `python3 -c "import yaml,sys; print(yaml.safe_load(open(sys.argv[1]).read().split('---')[1]))" <fichier>`
- `cd /home/claude/bikentour/tools && python3 -c "import blog; print(len(blog.prepare()))"` affiche 46 sans erreur.
- Ne modifier QUE les fichiers de la liste confiée.
- Compte rendu final pour chaque article : nouveau titre, nombre de mots, 2-3 sources principales (URL), et les faits retirés faute de vérification.
