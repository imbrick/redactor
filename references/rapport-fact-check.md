# Rapport de fact-check : rédaction, archivage et suivi

Tout fact-check produit un rapport écrit, archivé dans le dépôt. Il sert trois usages : décider de la suite (corrections ciblées ou révision complète), alimenter le journal des modifications de la révision (`revision-enrichissement.md`), et garder la trace de ce qui a été vérifié, avec quelles sources, à quelle date.

## 1. Où et comment archiver

- Fichier : `ressources/fact-checks/<slug>-AAAA-MM-JJ.md` (date du fact-check). Un nouveau fact-check du même article crée un nouveau fichier, il n'écrase pas l'ancien.
- Registre : une ligne par rapport dans `ressources/fact-checks/README.md`, mise à jour à chaque changement de statut.
- Le dossier `ressources/` est ignoré par git : un nouveau rapport s'ajoute avec `git add -f` (seulement quand l'utilisateur demande un commit).

## 2. Statuts

| Statut | Sens |
|---|---|
| `ouvert` | rapport livré, aucune correction appliquée |
| `révision en cours` | corrections commencées |
| `révisé` | révision publiée ; indiquer la date et le commit |
| `clos` | rien à corriger, ou corrections refusées par l'utilisateur (motif noté) |

Quand l'article est révisé, on ne réécrit pas le rapport : on complète sa section « Suivi » et on marque chaque constat (`corrigé`, `retiré`, `maintenu`, `non traité`).

## 3. Modèle

````markdown
---
article: "articles/<chemin>/<slug>.md"
slug: "<slug>"
titre: "<titre_simple>"
date_verification: "AAAA-MM-JJ"
methode: "skill kongopedia-redaction, mode Fact-check"
statut: "ouvert"
verdict: "révision complète | corrections ciblées | conforme"
bilan:
  erreurs_demontrees: 0
  affirmations_p0: 0
  references: "N trouvées · N à confirmer · N introuvables"
  avertissements_verificateur: 0
---

# Fact-check — <titre> (AAAA-MM-JJ)

## 1. Synthèse
Trois à cinq phrases : état général, gravité, verdict et raison du verdict.

## 2. Contrôles automatiques
Résultat de `verifier_article.py` (codes) et de `verifier_references.py` (bilan), avec les faux positifs identifiés.

## 3. Erreurs démontrées
| ID | Passage (ligne) | Problème | Correction proposée | Source |
|---|---|---|---|---|
| E1 | … | … | … | lien ou référence |

## 4. Affirmations non prouvées (P0) ou surdimensionnées
| ID | Passage | Problème | Action proposée |
|---|---|---|---|
| P1 | … | … | sourcer / nuancer / retirer |

## 5. Bibliographie
Références douteuses (R1…), références sans affirmation rattachée, sources centrales manquantes.

## 6. Neutralité et charte
Point de vue, jugements non attribués, débats présentés à sens unique (N1…).

## 7. Forme
Notes, structure, coquilles, liens cassés, frontmatter (F1…).

## 8. Sujets dérivés repérés
Liste à reporter dans la fiche brainstorm.

## 9. Sources consultées pour la vérification
Liste des sources effectivement lues.

## 10. Suivi
| Date | Action | Constats traités | Commit |
|---|---|---|---|
| AAAA-MM-JJ | Fact-check | — | — |
````

## 4. Règles de rédaction

- Chaque constat porte un **identifiant** (E, P, R, N, F suivi d'un numéro) et sa **localisation** (ligne ou section) : il doit pouvoir devenir une ligne du journal des modifications sans relecture de l'article.
- « Erreur démontrée » exige une source consultée qui contredit le texte. Sans elle, le constat va en P0 (« non retrouvé », « à confirmer »), jamais en erreur.
- Distinguer les faux positifs des scripts des vrais problèmes, et les signaler pour améliorer les scripts.
- Un rapport reconstitué après coup (fact-check antérieur à l'archivage) le dit dans sa synthèse.
