# Mise en page et rythme

Le lecteur de manga lit vite. Le rythme naît du nombre de cases par page, de leur taille, et surtout de ce qu'il découvre en **tournant la page**.

## 1. La tourne

Un livre ouvert montre deux pages à la fois. Le lecteur voit toute la double page d'un coup d'œil ; il ne découvre une image par surprise qu'**en tournant**.

- Quand la page 1 est une belle page (recto), les doubles pages ouvertes associent une page paire et une page impaire (2-3, 4-5…), **quel que soit le sens de lecture**. La page découverte en tournant est la **paire**. Le sens de lecture change l'ordre des cases et laquelle des deux pages se lit en premier, pas la parité.
- **Révélation** : sur une page paire, si possible dans une grande case en haut de page. Étiquette `(révélation)` ; le script avertit si elle tombe sur une page impaire (vue avant de tourner).
- **Suspense** : la dernière case de la page impaire pose la question ; la page paire suivante y répond.
- Si les chapitres commencent sur une fausse page (verso), tout s'inverse : régler `page_revelation: "impaire"` dans `redactor.json`.

## 2. La double page

- Une image qui s'étend sur deux pages en vis-à-vis : décor grandiose, moment clé. Étiquette `(double page)`, titre `## Pages N-M`.
- Les deux pages doivent se faire face : la première porte la parité de la tourne (2-3, 4-5 avec la page 1 en recto). Le script avertit sinon.
- Rare et justifiée : une ou deux par volume, pas par chapitre.

## 3. Les cases par page

| Cases par page | Effet |
|---|---|
| 1 à 2 | pleine page, impact, révélation, pause |
| 3 à 5 | rythme courant de la narration |
| 6 à 7 | dialogue serré, action décomposée |
| plus de 7 | page dense, difficile à lire (le script avertit au-delà de `cases_max_par_page`) |

Varier : une suite de pages au même nombre de cases endort le lecteur. Une grande case après plusieurs petites crée un choc.

## 4. Répartir un chapitre

1. Lister les scènes du chapitre et ce que chacune doit accomplir.
2. Placer d'abord les temps forts sur leurs pages : la révélation (page paire), le cliffhanger (dernière page), une éventuelle double page.
3. Répartir le reste ; une scène de dialogue prend souvent 2 à 4 pages, une poursuite davantage, une émotion une page entière.
4. Vérifier que chaque page a un enjeu et que la dernière case de chaque page impaire donne envie de tourner.

## 5. Le sens de lecture

- `rtl` (droite à gauche) : lecture japonaise ; cases et bulles de droite à gauche, de haut en bas ; le livre s'ouvre « à l'envers » pour un lecteur occidental.
- `ltr` (gauche à droite) : lecture occidentale.
- Le script textuel est le même ; le dessinateur compose la page selon le sens déclaré, que le script assemblé rappelle.

## 6. Le webtoon

- Défilement vertical sur téléphone : pas de pages, pas de tourne, pas de double page. Le script se découpe en `## Séquence N`.
- **L'espace entre les cases fait le rythme** : un grand blanc ralentit, crée l'attente ; des cases serrées accélèrent.
- **La révélation** arrive après un défilement : la préparer par une case qui oblige à faire glisser l'écran.
- Cases souvent pleine largeur, peu de texte par case, épisodes de 40 à 80 cases selon les plateformes.
- Le script ne contrôle pas la tourne en webtoon ; il garde les contrôles de bulles et de continuité.
