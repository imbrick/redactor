# Les formats

Les longueurs ci-dessous sont des ordres de grandeur courants ; le magazine, l'éditeur, la plateforme ou le concours visé décident. Les consignes de l'éditeur priment toujours.

## 1. One-shot (`oneshot`)

- Une histoire complète en un chapitre, souvent 15 à 60 pages ; format des concours de jeunes auteurs, des magazines et des portfolios.
- Un seul conflit, peu de personnages, une fin qui conclut. La construction de la nouvelle s'y applique bien (`../nouvelle/references/construction.md` : effet, chute).
- Doit montrer en peu de pages un personnage fort et un univers donnant envie d'en voir plus : c'est souvent le pilote d'une série.

## 2. Série en chapitres (`serie`)

| Rythme | Pages par chapitre (repère) |
|---|---|
| Hebdomadaire | 18 à 20 |
| Mensuel | 30 à 45 |
| Bimestriel ou trimestriel | 40 à 60 |

- Chaque chapitre a sa propre courbe (accroche, développement, temps fort) et finit sur un **cliffhanger** qui donne envie de lire la suite : étiquette `(cliffhanger)` sur la dernière page ou champ `cliffhanger` du frontmatter (le script avertit s'il manque).
- Le **premier chapitre** porte souvent plus de pages : il installe le monde, le protagoniste et la promesse de la série.
- Un **volume relié** réunit d'ordinaire 8 à 10 chapitres hebdomadaires (180 à 200 pages) ; penser l'arc du premier volume avec une fin satisfaisante.
- Fixer la cible dans `pages_par_chapitre` ; un chapitre particulier la précise dans son champ `pages`.

## 3. Webtoon (`webtoon`)

- Épisodes à défilement vertical, publiés en ligne, souvent chaque semaine ; 40 à 80 cases par épisode selon les plateformes.
- Le découpage suit `mise-en-page-et-rythme.md`, section 6.
- L'accroche des premières cases et le cliffhanger de fin comptent encore plus qu'en papier : le lecteur décide en quelques secondes.

## 4. Passer d'un format à l'autre

Adapter une série papier en webtoon (ou l'inverse) garde les scènes et les dialogues, mais refait le découpage : les doubles pages deviennent de longues séquences verticales, les révélations à la tourne deviennent des révélations après défilement. Créer un nouveau fichier par chapitre adapté et régler `format` en conséquence.
