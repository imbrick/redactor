# Voix et style

La voix est ce qui fait qu'une page est de cet auteur et pas d'un autre. Quand Claude rédige, il écrit dans la voix de l'auteur, pas dans la sienne ; quand il relit, il protège cette voix au lieu de la lisser.

## 1. La fiche de voix

Elle se rédige à la phase 1 et se garde à la racine du projet (déclarée comme `charte` dans `redactor.json`). Elle tient en une page :

```markdown
# Fiche de voix — <titre>

- Narration : personne, focalisation, temps (passé simple, présent…)
- Phrase : longueur, rythme, ponctuation favorite
- Lexique : registre, mots aimés, mots bannis, part du dialecte ou de l'argot
- Dialogues : typographie, incises, façon de parler de chaque personnage principal
- Images : d'où viennent les comparaisons et les métaphores
- Ton : distance, humour, émotion dite ou montrée
- À éviter : tics, clichés, tournures que l'auteur ne veut pas
- Extraits de référence : deux ou trois passages de l'auteur qui sonnent juste
```

**Avec des pages de l'auteur** : les analyser (longueur moyenne des phrases, temps, dialogues, images récurrentes, ce qu'il ne fait jamais), rédiger la fiche, la faire valider. **Sans pages** : poser les choix un par un et écrire une page d'essai que l'auteur corrige.

Les tics notés dans « À éviter » vont aussi dans la clé `tics` de `redactor.json`, pour que le script les compte.

## 2. Écrire dans la voix de l'auteur

- Relire la fiche et les extraits de référence avant chaque chapitre.
- Garder ses choix même s'ils ne sont pas les plus « corrects » : une phrase longue et sinueuse, une répétition voulue, un mot régional.
- Ne pas ajouter ce que l'auteur ne fait pas : métaphores s'il n'en use pas, adjectifs en cascade, explications des émotions.
- En cas de doute, écrire deux versions courtes d'un passage et laisser l'auteur choisir.

## 3. Typographie française du dialogue

| Usage | Règle |
|---|---|
| Réplique | tiret cadratin « — » (ou demi-cadratin « – ») en début de ligne, suivi d'une espace |
| Ouverture d'un échange | guillemets « » avec espaces insécables, puis tirets pour les répliques suivantes ; ou tirets seuls — choisir et s'y tenir |
| Incise | « dit-elle », « demanda Morel », avec inversion du sujet ; pas de tiret avant l'incise |
| Pensée rapportée | italique ou discours indirect libre, selon la fiche de voix |
| Points de suspension | « … » (un seul caractère) |

Le trait d'union « - » en début de réplique est une faute de typographie fréquente : le script la signale.

## 4. Les contrôles de style du script

`verifier_roman.py` signale, chapitre par chapitre :
- les **répétitions rapprochées** : un mot de cinq lettres ou plus, hors mots outils et noms de la bible, repris plusieurs fois à moins de 25 mots d'intervalle ;
- les **adverbes en -ment** au-delà de 1,5 pour 100 mots ;
- les **tics** déclarés dans `tics`, à partir de deux occurrences ;
- les **répliques au trait d'union**.

Ce sont des signaux, pas des fautes. Une répétition peut être un effet, un adverbe peut être le mot juste. À la relecture, on regarde chaque signal et on garde ce qui est voulu.

## 5. Ce qu'on corrige toujours

- Les fautes d'orthographe, d'accord et de conjugaison (concordance des temps, passé simple).
- Les changements de point de vue involontaires dans une scène.
- Les changements de temps verbal non voulus.
- Les incohérences avec la bible (noms, âges, lieux, règles du monde).

Tout le reste — rythme, lexique, images — se propose et ne s'impose pas.
