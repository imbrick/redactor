# Liens internes et articles à venir

L'encyclopédie relie ses articles entre eux dès leur rédaction, y compris vers des sujets qui n'ont pas encore d'article. Le lien est posé une fois pour toutes : il devient actif le jour où l'article cible est publié, sans retoucher l'article qui le cite.

## 1. Format

```md
[Libellé](<prefixe_liens><slug>)
```

`prefixe_liens` vient de `redactor.json` (`/article/` par défaut, utilisé dans les exemples ci-dessous).

- Toujours la route du site `<prefixe_liens><slug>`, jamais un chemin de fichier (`../../lac-edouard.md`) : le site ne sait pas suivre un chemin de fichier, et un fichier déplacé casse le lien.
- Vers un article **existant** : son slug réel, tel qu'il figure dans son frontmatter (certains articles anciens ont un slug long, hérité d'un autre système, par exemple `hydrographie-de-la-republique-democratique-du-congo`).
- Vers un article **à venir** : le slug conventionnel, déduit de son futur titre court (`champ_titre_court`, à défaut `title`).

## 2. Slug conventionnel d'un article à venir

Le slug se déduit du titre court (nom direct, sans sous-titre) par la fonction `slugifier()` de `verifier_article.py` :

1. retirer l'article initial (le, la, les, l') et les parenthèses ;
2. retirer les accents et passer en minuscules ;
3. supprimer les apostrophes (« d'Ishango » → `dishango`) ;
4. remplacer tout autre caractère par un tiret.

| Titre simple | Slug |
|---|---|
| Os d'Ishango | `os-dishango` |
| Lac Édouard | `lac-edouard` |
| Le fleuve Congo | `fleuve-congo` |
| Mouvement du 23 mars (M23) | `mouvement-du-23-mars` |
| Barrage d'Inga | `barrage-dinga` |

Le libellé du lien peut garder une précision (« Mouvement du 23 mars (M23) ») ; le slug, lui, suit la règle. Un même sujet doit avoir **un seul slug** dans tout le corpus : avant d'en créer un, vérifier la liste des liens en attente (`inventaire_sujets.py`).

## 3. Section « Voir aussi »

Chaque entrée est un lien, existant ou à venir, éventuellement suivi d'une précision :

```md
## Voir aussi

- [Lac Édouard](/article/lac-edouard)
- [Kisangani](/article/kisangani) — carrefour fluvial, ville de l'entre-deux
- [Barrage d'Inga](/article/barrage-dinga)
```

Les sujets cités en « Voir aussi » et qui n'ont pas d'article doivent aussi figurer dans la fiche de sujets dérivés, si le projet en tient (`sujets-derives.md`).

## 4. Affichage sur le site

Comportement recommandé pour le site du projet : il rend un lien vers un slug publié comme un lien normal ; vers un slug non publié, comme un texte souligné en pointillé, non cliquable, avec l'info-bulle « Article à venir » (pas de page 404). Dès qu'un article portant ce slug est publié, tous les liens qui l'attendaient deviennent actifs à la compilation suivante.

## 5. Contrôles

`verifier_article.py` signale :

| Code | Problème |
|---|---|
| `LIEN_CHEMIN_MD` | lien vers un fichier `.md` au lieu de `/article/<slug>` (le message propose le bon lien) |
| `LIEN_SLUG_INVALIDE` | slug hors format (majuscules, espaces, soulignés) |
| `LIEN_SLUG_CONVENTION` | lien vers un article à venir dont le slug ne correspond pas au libellé selon la convention |
| `VOIR_AUSSI_SANS_LIEN` | entrée de « Voir aussi » écrite en texte simple |
| `LIENS_EN_ATTENTE` | à la publication : des articles pointent déjà vers le slug conventionnel de ce sujet, mais l'article en a pris un autre |

`inventaire_sujets.py` liste les liens en attente d'article (slug et nombre d'articles qui le citent) et fait remonter dans le plan éditorial les sujets déjà cités.

## 6. À la publication d'un article

Donner à l'article le slug conventionnel de son titre court. Si des liens l'attendent sous ce slug (`LIENS_EN_ATTENTE`), ne pas en choisir un autre : sinon il faudrait corriger tous les articles qui le citent.
