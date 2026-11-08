# Le script et le découpage

Le script est le plan de construction des pages : le dessinateur doit pouvoir dessiner chaque case sans deviner, le lettreur placer chaque bulle sans hésiter. `verifier_manga.py` et `assembler_script.py` le lisent : garder le format ci-dessous.

## 1. Le format

```markdown
---
numero: 1
titre: "La lumière"
statut: script            # plan, script, name, final (configurable)
pages: 20                 # cible du chapitre (sinon pages_par_chapitre)
cliffhanger: "Un navire fantôme répond au phare"   # série : la fin du chapitre
---

## Page 1

### Case 1
Plan d'ensemble, vue plongeante. Un car descend vers le village, au bord d'une mer grise.
NARRATION : Le premier jour des vacances, la mer avait la couleur de l'ennui.

### Case 2
Intérieur du car. Aki, front collé à la vitre.
AKI (pensée) : Deux mois chez grand-mère. Sans réseau.

## Pages 2-3 (double page)

### Case 1
…

## Page 4 (révélation)
```

| Élément | Écriture |
|---|---|
| Page | `## Page N` ; double page : `## Pages N-M` ; webtoon : `## Séquence N` |
| Étiquettes de page | entre parenthèses après le titre : `(révélation)`, `(double page)`, `(cliffhanger)` |
| Case | `### Case N`, numérotée à partir de 1 dans chaque page |
| Description | toute ligne qui n'est pas une réplique (ou `Description : …`) |
| Réplique | `NOM : texte`, le nom en majuscules ; précision entre parenthèses : `(pensée)`, `(off)`, `(murmure)`, `(cri)` |
| Récitatif | `NARRATION : texte` (ou `RÉCITATIF`, `CARTOUCHE`) |
| Onomatopée | `SFX : BOUM` (non comptée comme bulle) |
| Voix sans personnage | `VOIX`, `TOUS`, `FOULE`, `RADIO`, `TÉLÉPHONE`, `INCONNU` : admises sans fiche dans la bible |

Les locuteurs sont comparés à la bible (nom, alias ou un des mots du nom : `AKI` pour « Aki Moreau »).

Règles de lecture à connaître :
- **Étiquettes** : plusieurs dans une parenthèse ou dans plusieurs, `(révélation, cliffhanger)` comme `(révélation) (cliffhanger)` ; une étiquette inconnue est signalée.
- **Plusieurs voix** : `AKI, ROSE : Ensemble !` ou `AKI & ROSE : …` ; voix inconnue : `??? : Qui est là ?`. Le gras (`**AKI** :`) et une puce (`- AKI :`) sont admis.
- **Réplique longue** : on peut la couper sur plusieurs lignes ; la ligne suivante la prolonge tant que la bulle ne finit pas par une ponctuation finale, ou si elle commence par une minuscule. Une description qui suit une réplique se place après une ligne vide, ou commence par `Description :`.
- **Majuscules en tête de ligne** : une ligne qui commence par des majuscules suivies de « : » est lue comme une réplique (`SNCF : …`). Pour une description de ce genre, commencer par une minuscule ou par `Description :`.
- **Double page** : exactement deux pages qui se suivent, `## Pages 2-3` (tiret, demi-cadratin, cadratin ou « à »).
- Les blocs de code (```) sont ignorés ; une case sans numéro (`### Case`) prend le numéro suivant.

## 2. Décrire une case

Une case, **un instant**. La description dit ce qu'on voit, dans l'ordre où le dessinateur en a besoin :

1. **Le cadrage** : plan d'ensemble, plan moyen, plan rapproché, gros plan, très gros plan ; plongée, contre-plongée.
2. **Le lieu et le moment**, s'ils changent.
3. **Les personnages** présents, leur position, leur action, leur expression.
4. **Le détail qui compte** pour l'histoire (un objet, un indice) — et seulement lui.

Pour un **dessinateur**, être précis sur ce qui sert l'histoire et laisser le reste à son talent. Pour l'**auteur complet** (name textuel), quelques mots suffisent : « PR Aki, surprise ».

À éviter : deux actions successives dans une case (« elle ouvre la porte et descend l'escalier ») ; ce qui ne se dessine pas (« elle pense à son père ») — le montrer par un geste, un objet, ou le dire en bulle de pensée ; une description de style graphique d'un artiste existant.

## 3. Les dialogues

- **Court** : une bulle se lit d'un regard. Repères par défaut : 3 bulles par case, 25 mots par bulle (configurables) ; au-delà, couper, répartir sur deux cases, ou laisser l'image parler.
- **Ordre de lecture** : les bulles se lisent dans le sens de lecture (de droite à gauche en `rtl`) ; l'ordre des répliques dans le script est l'ordre de lecture.
- **La case muette** est un outil : une émotion, une pause, une révélation passent mieux sans texte.
- **Ce que l'image montre, la bulle ne le répète pas** (« Oh, il pleut ! » sous une averse).
- Chaque personnage a sa façon de parler (bible) ; les onomatopées font partie du dessin et du rythme.

## 4. Du découpage à la page

Avant d'écrire les cases d'un chapitre, répartir les scènes sur les pages (`mise-en-page-et-rythme.md`) : combien de pages pour chaque scène, où tombent les temps forts. On écrit ensuite les cases page par page.
