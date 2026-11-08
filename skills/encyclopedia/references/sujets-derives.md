# Repérer les sujets dérivés et tenir le plan éditorial

Chaque article ouvre d'autres articles : un lac, un acteur, une institution, un concept qu'il mentionne sans pouvoir les développer. Cette fiche dit comment repérer ces sujets, les évaluer, les consigner dans la fiche de sujets dérivés (`<dossier_brainstorm>/<slug><suffixe_brainstorm>`, voir `redactor.json`) et exploiter l'ensemble des fiches pour choisir le prochain article. Le gabarit de la fiche peut être fixé par `gabarit_article` ou par la charte ; à défaut, un tableau par section thématique, au format de la section 5.

## 1. Quand repérer

Le repérage se fait **pendant** le travail, pas après :

- **Enquête (phase 2)** : chaque source lue mentionne des personnes, des lieux, des événements et des travaux. Noter au fil de l'eau ceux qui reviennent dans plusieurs sources : la récurrence est le meilleur indice d'un sujet autonome.
- **Rédaction (phase 3)** : toute phrase obligée de résumer en quelques mots ce qui mériterait une section signale un sujet dérivé. C'est aussi le remède à la digression : on renvoie au futur article au lieu de greffer un développement hors sujet.
- **Fact-check et révision** : les sources lues pour vérifier un article font apparaître des sujets que le premier rédacteur ignorait. Sur l'os d'Ishango, la vérification a ajouté l'os de Lebombo, Katanda, Jean de Heinzelin, le lac Édouard et la loi belge de 2022.

## 2. Où chercher dans l'article

| Gisement | Exemples tirés du corpus |
|---|---|
| Personnes nommées | Jean de Heinzelin, Joseph Kasa-Vubu, Msiri |
| Lieux et milieux | lac Édouard, chutes Boyoma, Kisangani |
| Peuples, langues, institutions | Empire luba, ICCN, Union minière du Haut-Katanga |
| Événements | sécession du Katanga, éruption de 2002 |
| Concepts et techniques | Rift est-africain, pêche aux nasses, bâton de comptage |
| Objets, œuvres, documents | os de Lebombo, discours du 30 juin 1960 |
| Débats et questions transversales | restitution des biens culturels, datation des sites |

Lire aussi l'encadré de synthèse, la chronologie et la section « Voir aussi » : chaque ligne qui n'a pas encore d'article est un candidat.

## 3. Le test d'autonomie

Un sujet entre dans la fiche s'il passe ces quatre questions :

1. **Est-ce une entrée d'encyclopédie ?** Un nom propre ou un groupe nominal qu'un lecteur chercherait tel quel (« Lac Édouard »), pas une section (« Le climat au Paléolithique »).
2. **Y a-t-il de quoi écrire ?** Au moins deux sources indépendantes probables, dont une de niveau 1 à 4. Un sujet sans sources reste une idée, notée « à documenter ».
3. **Le sujet existe-t-il déjà ?** Lancer `inventaire_sujets.py` et chercher dans le dossier des articles sous toutes ses variantes de nom.
4. **Relève-t-il du périmètre du projet ?** Celui que fixe la charte.

## 4. Fixer la priorité

| Priorité | Critère |
|---|---|
| ⭐⭐⭐ | Sujet central pour le périmètre du projet, souvent cité dans le corpus, sources disponibles ; son absence crée un trou visible (un lien « Voir aussi » sans cible, un acteur majeur sans biographie) |
| ⭐⭐ | Sujet utile qui approfondit un article existant, sources disponibles mais moins abondantes |
| ⭐ | Sujet de complément ou de niche, ou sujet aux sources encore incertaines |

Un sujet proposé par plusieurs fiches monte naturellement en tête du plan éditorial : c'est le signal que plusieurs articles en ont besoin.

## 5. Consigner dans la fiche

- Une ligne par sujet : `| Titre pressenti | Branche taxonomique | Priorité | Rédigé |`, dans la section thématique qui convient.
- Le **titre pressenti** suit les règles du titre court (`champ_titre_court`) (nom direct, sans sous-titre) ; garder la même formulation d'une fiche à l'autre pour que l'inventaire reconnaisse les doublons.
- La **branche** vient de la taxonomie du projet (`categories`).
- Mettre à jour le récapitulatif chiffré en bas de fiche et la ligne « Source » (chemin de l'article-mère).
- À chaque révision d'un article, compléter sa fiche avec les sujets découverts.
- À la publication d'un article dérivé, cocher `#` dans la colonne « Rédigé » de **toutes** les fiches qui le proposent.

## 6. Exploiter l'ensemble des fiches

```bash
python <dossier-du-skill>/scripts/inventaire_sujets.py --top 20
python <dossier-du-skill>/scripts/inventaire_sujets.py --branche "Hydrographie"
```

Le script fusionne les doublons entre fiches, classe les sujets à rédiger (priorité, puis nombre de fiches qui les proposent) et signale deux incohérences :

- **déjà rédigés mais non cochés** : cocher `#` dans les fiches concernées ;
- **cochés sans article retrouvé** : le titre de l'article diffère du titre pressenti, ou la case a été cochée à tort.

Le rapprochement se fait sur le titre normalisé : un sujet rédigé sous un autre nom (« Lualaba » pour « Le Congo supérieur ») n'est pas reconnu. Vérifier à la main avant de lancer la rédaction d'un sujet proposé par le script.

## 7. Livrable du mode « Plan éditorial »

- la liste priorisée des sujets à rédiger (ou filtrée par branche), avec pour chacun les articles-mères qui le proposent ;
- les incohérences des fiches et leur correction ;
- pour les trois premiers sujets, une estimation rapide de la documentation disponible (sources de niveau 1 à 4 repérées), afin de proposer celui qui peut être écrit le plus solidement.
