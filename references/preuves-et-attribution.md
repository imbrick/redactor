# Preuves et attribution

Comment rendre chaque affirmation d'un article Kongopedia traçable jusqu'à sa source. Le format des notes `[^n]` et de la bibliographie est fixé par `kongopedia-editorial-skill` ; cette fiche organise le travail de preuve.

## 1. Le dossier de sources (avant d'écrire)

Le constituer pendant la recherche, dans la conversation ou dans un fichier de travail (ne pas le placer dans `articles/`) :

```md
| # | Source (auteur, titre, année) | Type | Niveau (1-8) | Ce qu'elle établit | Dépend de | Consultée le |
|---|---|---|---|---|---|---|
| S1 | Ndaywel è Nziem, *Histoire générale du Congo*, 1998 | secondaire | 1 | chronologie du royaume X | — | 2026-11-07 |
| S2 | Joshua Project, fiche « … » | base | 3 | population estimée | Ethnologue (S3) | 2026-11-07 |
```

La colonne « Dépend de » empêche de compter deux fois la même source (voir `methode-historique.md`, section 4).

## 2. La table des affirmations

Décomposer le texte en affirmations atomiques. Une phrase peut en contenir plusieurs : « En 1906, l'Union minière du Haut-Katanga est fondée avec un capital de 10 millions de francs » contient une date, un acteur et un chiffre, et chacun doit être soutenu.

```md
| Affirmation | Statut | Preuve | Sources | Note |
|---|---|---|---|---|
| Fondation de l'UMHK en 1906 | établi | P4 | S1, S4 | [^2] |
| Capital initial de 10 millions de francs | à vérifier | P1 | S4 seule | — |
```

La colonne **Preuve** donne le niveau réellement atteint (P0 à P4), défini dans `enquete-avancee.md` avec les objectifs à atteindre avant publication.

Statuts :
- **établi** : sources indépendantes concordantes, dont au moins une de niveau 1 à 4 ;
- **probable** : une bonne source, aucune contradiction connue ;
- **débattu** : sources de qualité en désaccord, à présenter comme tel ;
- **à vérifier** : ne pas publier en l'état ; chercher une deuxième source ou retirer.

## 3. Trois types d'énoncés, trois formulations

| Type | Formulation | Exemple |
|---|---|---|
| Fait établi | affirmatif, sans précaution | « La ville est fondée en 1883. » |
| Estimation | chiffre + qui estime + année + méthode | « L'INS estimait la population de [ville] à [N] habitants en [année], par projection du recensement de 1984. » |
| Interprétation | attribuée à son auteur | « Pour Jan Vansina, ce royaume résulte de… » |
| Tradition orale | attribuée au recueil ou aux informateurs | « Selon la tradition recueillie auprès des notables en 2018, … » |

Ne pas mettre de précautions partout : un fait établi s'écrit simplement. La précaution signale un doute réel.

## 4. Ce qui appelle une note `[^n]`

- tout chiffre (population, superficie, bilan, date contestée) ;
- toute citation directe ;
- toute interprétation ou jugement attribué ;
- tout fait surprenant, rare ou susceptible d'être contesté ;
- toute donnée de l'infobulle qui n'est pas répétée et sourcée dans le corps.

Les faits de connaissance générale (Kinshasa est la capitale de la RDC) n'en ont pas besoin. Regrouper dans une même note les sources d'un même fait, pour rester dans la limite de 8 à 10 notes fixée par la charte.

## 5. Interdits absolus

- Citer une source qu'on n'a pas consultée, y compris en recopiant la bibliographie d'un article Wikipédia.
- Inventer ou deviner un numéro de page, une date de consultation, un DOI, une cote d'archive.
- Reformuler une citation directe en gardant les guillemets.
- Présenter comme établie une affirmation de statut « à vérifier ».

Quand une source manque, l'écrire : signaler la section faible dans la note éditoriale de fin de livraison plutôt que de combler le vide.

## 6. Liens et pérennité

- Préférer le DOI à l'URL de l'éditeur.
- Indiquer la date de consultation des pages web.
- Pour une page fragile (presse locale, site institutionnel), vérifier si une copie existe sur archive.org et la mentionner.

## 7. Relecture adversariale (avocat du diable)

Avant publication, se poser ces questions et corriger ce qu'elles révèlent :
1. Quelle est la source la plus faible de l'article, et que soutient-elle ?
2. Quel chiffre ai-je recalculé ou confronté à une deuxième source ?
3. Qui contesterait cette phrase, et avec quels arguments ? Sont-ils présentés ?
4. Une seule version d'une tradition ou d'une datation est-elle présentée comme certaine ?
5. Un nom colonial est-il donné comme référence, ou une construction « ex-… » a-t-elle survécu ?
6. L'infobulle, le corps et le tableau chronologique donnent-ils les mêmes dates et les mêmes chiffres ?
7. Chaque appel `[^n]` a-t-il sa note, et chaque note dit-elle ce que la source établit ?
