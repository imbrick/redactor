# Révision et enrichissement après fact-check

Comment transformer un rapport de vérification en article corrigé, plus riche et mieux écrit. Cette fiche s'applique au mode « Révision » et à tout article qui sort d'un fact-check. Elle complète `redaction-journalistique.md` (clarté) et la charte anti-IA du skill éditorial (`assets/style-anti-ia.md`), qui garde le dernier mot sur le style.

## 1. L'ordre des opérations

On ne polit pas une erreur. Quatre passes, dans cet ordre :

1. **Corriger** les erreurs démontrées par le fact-check (dates, attributions, chiffres, contresens).
2. **Retirer** les affirmations restées en P0 (aucune source trouvée) et les références introuvables ou inventées. Une affirmation retirée faute de preuve est signalée dans la note éditoriale, jamais reformulée au conditionnel pour la sauver.
3. **Restructurer** : supprimer les digressions qui ne portent pas sur le sujet (effet *coatrack*), regrouper ce qui est dispersé, rétablir la pyramide inversée.
4. **Enrichir et réécrire** les passages vérifiés, selon les sections 2 à 5 de cette fiche.

Chaque modification entre dans le **journal des modifications**, livré avec l'article (hors du fichier) :

```md
| Passage | Problème (rapport) | Action | Source |
|---|---|---|---|
| Encadré de synthèse, « Matériau » | « péroné de babouin » non établi | corrigé : « os de mammifère, espèce non identifiable » | IRSNB 2024 |
| § Fouilles ultérieures | second os attribué à Brooks et Yellen | corrigé et enrichi | IRSNB ; Pletser et Huylebrouck 2016 |
| Bibliographie n° 11 | référence introuvable | retiré | — |
```

Actions possibles : corrigé, retiré, reformulé, enrichi, déplacé, conservé (avec justification).

## 2. Où trouver la matière de l'enrichissement

Enrichir, c'est ajouter des **faits sourcés, des mécanismes et du contexte**, pas des mots. La meilleure matière vient du fact-check lui-même : en vérifiant, on lit des sources que le premier rédacteur n'avait pas lues. Sur l'os d'Ishango, la vérification a fait apparaître la découverte du site par Hubert Damas en 1935, la seconde campagne de 1959 et son deuxième os encoché, le fait que chaque colonne totalise un multiple de 12, et la critique d'Olivier Keller. Chacun de ces faits nourrit un paragraphe.

Pour chaque section, poser ces questions et chercher les réponses dans les sources :

| Question | Ce qu'elle ajoute |
|---|---|
| Comment le sait-on ? | la méthode : fouille, datation, archive, recensement |
| Qui l'a établi, quand, dans quelle publication ? | l'attribution et la chronologie de la connaissance |
| Qu'est-ce qui a changé depuis ? | les révisions (une datation revue, une identification abandonnée) |
| Qui le conteste, avec quels arguments ? | le débat, sous la forme Position A / Position B |
| Quelle conséquence, quel lien avec le reste du sujet ? | la portée, sans superlatif |
| Que disent la tradition orale et la recherche locale ? | le point de vue des sociétés concernées, selon la charte |

Une réponse introuvable n'est pas comblée par une généralité : la section reste courte et la lacune va dans la note éditoriale.

## 3. Le paragraphe élaboré

Un paragraphe élaboré développe **une idée** avec ce qu'il faut pour la comprendre et la croire. Il puise dans cinq composants, sans les prendre tous à chaque fois :

1. **l'affirmation**, en tête (pyramide inversée) ;
2. **l'explication** : le comment ou le pourquoi ;
3. **la preuve et son attribution** : qui l'établit, par quelle méthode, avec l'appel `[^n]` ;
4. **la nuance** : la limite, la révision ou l'objection, nommée précisément ;
5. **la portée** : le lien avec le reste du sujet.

Ce n'est pas un gabarit. Un fait net peut tenir en une phrase seule ; une question débattue peut demander dix lignes. La charte anti-IA interdit les paragraphes tous de même longueur bâtis sur le schéma « thème, développement, synthèse » : varier délibérément, et ne jamais terminer un paragraphe par une phrase qui résume ce qu'il vient de dire.

## 4. La phrase élaborée

- **Subordonner plutôt que juxtaposer.** Trois phrases courtes qui se suivent sans lien (« Il fouille en 1950. Il trouve l'os. Il le rapporte en Belgique. ») deviennent une phrase qui hiérarchise : principale pour l'essentiel, subordonnée pour le reste.
- **Choisir le connecteur exact** : cause (*parce que*, *faute de*), conséquence (*si bien que*, *d'où*), concession (*bien que*, *même si*), opposition (*alors que*, *en revanche*), chronologie (*dès*, *jusqu'à*, *depuis*). Un connecteur faux est pire qu'aucun.
- **Identifier par l'apposition** : « Jean de Heinzelin, géologue à l'Institut royal des Sciences naturelles de Belgique, … » situe l'acteur sans phrase supplémentaire.
- **Préférer le verbe précis** au couple verbe faible + nom : *dater* plutôt que *procéder à la datation*.
- **Varier les débuts de phrase** : sujet, complément de temps, subordonnée, participe.
- **Garder la lisibilité** : une idée principale par phrase, idées secondaires rattachées ; couper au-delà de trois lignes (`redaction-journalistique.md`, section 1).

## 5. Des listes à la prose

Garder une liste ou un tableau pour ce qui est réellement énumératif : données chiffrées, inventaire, chronologie (sous forme de tableau). Convertir en prose ce qui relève du raisonnement : arguments, causes, interprétations, étapes d'un débat. Une liste à puces d'arguments cache les liens logiques que la prose oblige à écrire.

## 6. Avant / après

**Une liste d'arguments devient un raisonnement attribué.**

> Avant : « La colonne centrale présente huit groupes d'encoches : 3, 6, 4, 8, 10, 5, 5, 7. La somme totale est de 48. Les quatre premiers forment une progression où chaque nombre est le double du précédent. »

> Après : « La colonne centrale aligne huit groupes de 3, 6, 4, 8, 10, 5, 5 et 7 entailles. Jean de Heinzelin y lisait, dans sa monographie de 1957, des paires formées d'un nombre et de son double (3 et 6, 4 et 8, puis 10 et 5), les deux derniers groupes restant sans explication[^4]. Le total de la colonne, 48, est comme celui des deux autres (60 chacune) un multiple de 12 : c'est sur cette régularité que les mathématiciens Vladimir Pletser et Dirk Huylebrouck ont fondé l'hypothèse d'un comptage en bases 3 et 4[^5]. Ces lectures reposent toutefois sur un postulat que de Heinzelin posait d'emblée, celui que chaque groupe de traits note un nombre ; Olivier Keller y voit le risque de projeter nos catégories sur des signes dont la fonction reste inconnue[^6]. »

Ce qui a changé : l'erreur corrigée (des paires, pas une progression), une régularité ajoutée (multiple de 12), chaque lecture attribuée et datée, la limite nommée.

**Une phrase factuelle devient une histoire de la connaissance.**

> Avant : « Découvert en 1950 par le géologue belge Jean de Heinzelin de Braucourt lors d'une campagne archéologique dans la vallée de la Semliki. »

> Après : « Le gisement d'Ishango est signalé dès 1935 par le zoologiste liégeois Hubert Damas, qui y remarque des ossements sans pouvoir les fouiller. Jean de Heinzelin, géologue à l'Institut royal des Sciences naturelles de Belgique, y conduit deux campagnes, en 1950 puis en 1959 : la première livre le bâton gravé, la seconde un deuxième os encoché, présenté pour la première fois en 2007[^2]. »

## 7. Ce qu'enrichir n'est pas

- allonger par paraphrase, répétition ou synonymes accumulés ;
- ajouter des superlatifs, des modalisateurs en série ou du conditionnel partout ;
- plaquer des analogies avec d'autres cultures (charte anti-IA, section 5) ;
- greffer des développements généraux qui ne portent pas sur le sujet (l'histoire des tablettes mésopotamiennes dans un article sur un os gravé du Kivu) : une phrase de comparaison sourcée suffit, ou un lien vers l'article concerné ;
- combler une lacune par une généralité plausible.

Couper fait aussi partie de l'enrichissement : un article plus court mais entièrement vérifié vaut mieux qu'un long article fragile.

## 8. Contrôles

`verifier_article.py` signale les symptômes que le fact-check d'Ishango a révélés :

| Code | Symptôme | Réponse |
|---|---|---|
| `PREUVE_CHIFFRE_SANS_NOTE` | paragraphe contenant un chiffre ou une date sans appel `[^n]` | sourcer, ou retirer le chiffre |
| `STYLE_AFFIRMATION_FORTE` | « démontre que », « prouve que », « preuve tangible »… | attribuer l'interprétation à son auteur |
| `DATATION_MIXTE` | « av. J.-C. » et « BP / avant le présent » dans le même article | choisir un repère, ou convertir explicitement |
| `BIBLIO_SUSPECTE` | « publication interne », « document interne » en bibliographie | vérifier l'existence, sinon retirer |
| `PROSE_LISTES` | section où les puces dominent la prose | convertir en raisonnement (section 5) |
| `PROSE_FRAGMENTEE` | trop de paragraphes très courts | regrouper et relier (sections 3 et 4) |

Avant de livrer, relire aussi :
- [ ] chaque ligne du rapport de fact-check a une action dans le journal ;
- [ ] aucun enrichissement ne repose sur une source non consultée ;
- [ ] l'encadré de synthèse, le corps et la chronologie donnent les mêmes dates et les mêmes chiffres ;
- [ ] les longueurs de paragraphes varient, et aucun ne se termine par un résumé de lui-même.
