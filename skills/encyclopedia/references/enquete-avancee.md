# Enquête avancée : pousser la preuve plus loin

À charger quand une affirmation importante ne repose encore que sur un résumé, une source secondaire ou une page inaccessible, et pour tout article de révision. Cette fiche dit comment monter d'un niveau de preuve, et quand s'arrêter.

## 1. L'échelle des niveaux de preuve

Chaque ligne de la table des affirmations (`preuves-et-attribution.md`) porte un niveau de preuve atteint :

| Niveau | Ce qui a été réellement consulté |
|---|---|
| **P0** | Rien : affirmation reprise sans vérification |
| **P1** | Source secondaire, tertiaire ou résumé d'article seulement |
| **P2** | Texte intégral d'une source de niveau 1 à 4, passage repéré (page, tableau, figure) |
| **P3** | Donnée primaire : base de référence, rapport officiel, archive, mesure, texte de loi |
| **P4** | Deux sources de niveau P2 ou P3, indépendantes et concordantes |

Objectifs avant publication :
- chiffres, dates et bilans humains de l'encadré de synthèse et de l'introduction : **P3**, ou **P2** confirmé par une deuxième source ;
- affirmations débattues : **P4** pour chaque position présentée, ou présentation explicite du désaccord ;
- citations directes : **P2** au minimum, contre le texte original ;
- rien en **P0** dans le texte publié.

Le niveau atteint figure dans la note de fin quand il est inférieur à l'objectif (« résumé consulté », « chiffre rapporté par la presse »).

## 2. Remonter à la source primaire

Une information passe souvent par plusieurs mains : donnée brute, rapport, dépêche, article de presse, encyclopédie. Remonter la chaîne jusqu'au premier maillon accessible, et citer ce maillon.

| Domaine | Sources primaires à viser |
|---|---|
| Volcans, séismes | Global Volcanism Program (Smithsonian), rapports hebdomadaires GVP/USGS, bulletins de l'Observatoire volcanologique de Goma, catalogue sismique de l'USGS |
| Crises humanitaires | Rapports de situation OCHA et HCR sur ReliefWeb, communiqués datés des agences des Nations unies |
| Démographie | Institut national de la statistique (INS-RDC), recensements, UN DESA *World Population Prospects* |
| Eau, climat, agriculture | FAO AQUASTAT, Global Runoff Data Centre (GRDC), Banque mondiale |
| Biodiversité | GBIF, Liste rouge de l'UICN |
| Patrimoine | Centre du patrimoine mondial de l'UNESCO (fiches et décisions du Comité) |
| Droit | Journaux officiels nationaux (par exemple Journal officiel de la RDC, Leganet.cd, Légifrance) |
| Histoire coloniale | Archives des anciennes puissances coloniales (par exemple Archives africaines du SPF Affaires étrangères à Bruxelles, MRAC Tervuren, ANOM à Aix-en-Provence), presse ancienne numérisée (Gallica, BelgicaPress de la KBR) |
| Langues et peuples | Glottolog, Ethnologue, recueils de traditions orales publiés |
| Littérature scientifique | Crossref, OpenAlex, Persée, Cairn, HAL, AJOL |

## 3. Vérifier automatiquement les références

Lancer, dès que la bibliographie existe et à nouveau avant publication :

```bash
python <dossier-du-skill>/scripts/verifier_references.py <dossier_articles>/<categorie>/<slug>.md
```

Le script interroge Crossref, OpenAlex et Open Library. Lecture des statuts :
- **TROUVÉ** : la référence existe ; ajouter le DOI proposé s'il manquait.
- **À CONFIRMER** : résultat proche ou livre absent d'Open Library ; vérifier dans un catalogue (BnF, KBR, WorldCat).
- **DIVERGENT** : le DOI pointe vers une autre publication ; corriger le DOI ou la référence.
- **INTROUVABLE** : aucune trace ; retrouver la référence exacte à la main ou la retirer. Une référence introuvable n'est jamais conservée « en attendant ».
- **ERREUR RÉSEAU** : rien n'est conclu ; relancer plus tard.

Le script contrôle l'existence des références, pas qu'elles disent ce que l'article leur fait dire : cette vérification reste manuelle (section 4).

## 4. Du résumé au texte intégral

Un résumé suffit pour savoir qu'une étude existe, pas pour lui attribuer un chiffre précis. Pour passer de P1 à P2 :
1. Prendre le lien « Texte intégral en accès libre » donné par `verifier_references.py`, quand il existe.
2. Sinon, chercher une copie légale : dépôts institutionnels (HAL, ORBi, dépôts universitaires), prépublication (ESSOAr, EarthArXiv), page personnelle de l'auteur, toutes les versions listées par Google Scholar.
3. Lire le passage qui porte le chiffre ou l'affirmation, et noter la page, le tableau ou la figure dans la note.

Ne jamais contourner un accès payant par des sites pirates. Si aucun texte intégral n'est accessible, garder « résumé consulté » dans la note.

## 5. Quand une page est bloquée

Une erreur 403 ou une page qui ne se charge pas n'est pas une impasse. Dans l'ordre :
1. Une autre page de la même institution (rapport hebdomadaire, fiche imprimable, version PDF, API publique).
2. La copie archivée de la page sur la Wayback Machine (`web.archive.org`).
3. La même donnée reprise par une source primaire équivalente (un rapport de l'USGS à la place de la fiche du Smithsonian).
4. Signaler dans la note éditoriale que la source de référence n'a pas pu être consultée, et donner le niveau de preuve réellement atteint.

## 6. Recherche en chaîne à partir des citations

- **En amont** : lire la bibliographie d'une source clé pour trouver les études originales qu'elle résume.
- **En aval** : chercher les travaux qui citent une source clé (« Cité par » dans Google Scholar, filtre `cites:` dans OpenAlex). C'est ainsi qu'on découvre qu'un chiffre de 2005 a été révisé en 2019.

Une source ancienne sur un phénomène mesurable (population, débit, gaz, superficie) doit toujours être confrontée à ses citations récentes.

## 7. Recherche multilingue et variantes de noms

- Chercher en français, en anglais et, pour la période coloniale belge, en néerlandais ; en portugais ou en espagnol quand le sujet le demande.
- Chercher toutes les graphies : Nyiragongo et Niragongo, Nyamulagira et Nyamuragira, noms vernaculaires, anciens noms officiels. Les sources anciennes emploient souvent la graphie coloniale.
- Chercher les noms des personnes sous leurs différentes transcriptions.

## 8. Résoudre une contradiction

Quand deux sources donnent des valeurs différentes :
1. Dresser la liste : valeur, source, date, méthode, niveau de preuve.
2. Vérifier si l'écart s'explique : dates différentes, périmètres différents (ville ou agglomération), unités, mesure ou estimation.
3. Préférer la source primaire la plus récente dont la méthode est explicite.
4. Si l'écart reste inexpliqué, présenter la fourchette en attribuant chaque valeur. Ne jamais faire la moyenne de deux sources.

## 9. Fraîcheur des faits vivants

Population, statut d'un volcan, niveau d'un lac, titulaire d'une fonction, état de conservation : chercher la source datée la plus récente et écrire « en [année] ». Ce qui était vrai à la date de la source n'est pas présenté comme vrai aujourd'hui.

## 10. Budget et critère d'arrêt

- Compter en général dix à vingt recherches pour un article ; davantage pour un sujet très débattu.
- S'arrêter quand les affirmations clés ont atteint leur objectif de niveau de preuve, ou quand trois recherches successives n'apportent rien de nouveau sur un point.
- Consigner les points restés en dessous de l'objectif dans la note éditoriale, au lieu de prolonger la recherche indéfiniment.
- Pour un article long, l'enquête peut être répartie par section entre plusieurs sous-agents travaillant en parallèle, chacun rendant ses lignes de table des affirmations avec leurs sources. Ne le faire qu'avec l'accord de l'utilisateur, car le coût augmente d'autant.
