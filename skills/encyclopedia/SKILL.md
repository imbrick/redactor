---
name: encyclopedia
description: Chaîne complète de production d'un article encyclopédique, de l'enquête à la publication. Réunit la méthode historique (critique des sources, traditions orales, datation), la méthode scientifique (hiérarchie des preuves, mesures, hypothèses), le métier journalistique (attaque, pyramide inversée, attribution, vérification, équité) et la neutralité encyclopédique, puis contrôle l'article avec un script avant publication. Les conventions du projet (dossiers, frontmatter, index, liens internes, charte) viennent de son fichier redactor.json. Use when the user asks to research, write, revise, fact-check or publish an encyclopedia or wiki article — « rédige un article sur… », « écris l'article encyclopédique », « fais la recherche pour l'article », « vérifie / fact-check cet article », « révise l'article », « publie l'article », « contrôle le corpus », « quel article écrire ensuite ? », « liste les sujets à rédiger ».
---

# Redactor — Article encyclopédique, de l'enquête à la publication

Ce skill organise le travail d'un rédacteur-enquêteur : **comment enquêter, comment écrire avec la clarté d'un journaliste, comment prouver, comment publier**.

## Avant tout : la configuration du projet

Chercher `redactor.json` à la racine du projet et le lire. Il fixe les conventions que ce skill ne connaît pas :

| Clé | Rôle | Défaut |
|---|---|---|
| `projet` | nom du projet | `projet` |
| `charte` | skill ou fichier de la charte éditoriale (structure, ton, format des notes, hiérarchie des sources, périmètre) | aucune |
| `dossier_articles` | dossier des articles publiés | `articles` |
| `fichiers_index` | index à tenir à jour, relatifs au dossier des articles | aucun |
| `dossier_brainstorm`, `suffixe_brainstorm` | fiches de sujets dérivés | aucune, `-articles-derives.md` |
| `dossier_fact_checks` | archive des rapports de fact-check | aucune |
| `journal` | journal des publications | aucun |
| `gabarit_article` | modèle de frontmatter et de structure | aucun |
| `categories` | taxonomie des branches | aucune |
| `champs_obligatoires`, `champs_recommandes` | champs du frontmatter (`a|b` : l'un des deux suffit) | `title`, `slug` ; aucun |
| `champ_titre_court` | titre d'index, source du slug des liens à venir | `title` |
| `champ_statut`, `statuts` | statut de publication et valeurs admises | `publication_status` ; `draft`, `review`, `published` |
| `prefixe_liens` | route des liens internes | `/article/` |

Si une charte est déclarée, la charger avec ce skill : elle prime sur lui pour la forme (structure, encadré de synthèse, notes, ton, point de vue). Sans `redactor.json`, appliquer les valeurs par défaut et demander à l'utilisateur où publier. Une étape qui dépend d'une clé absente (index, fiches, journal, fact-checks) est simplement sautée.

Dans la suite, `<articles>` désigne `dossier_articles`, `<brainstorm>` désigne `dossier_brainstorm`, et ainsi de suite.

| Fiche | À charger quand |
|---|---|
| `references/methode-historique.md` | le sujet a une dimension historique (presque toujours) |
| `references/methode-scientifique.md` | sciences, géologie, médecine, datation, démographie |
| `references/redaction-journalistique.md` | à la rédaction et à la révision |
| `references/preuves-et-attribution.md` | dès la recherche (dossier de sources) et avant publication |
| `references/enquete-avancee.md` | pour monter d'un niveau de preuve (P0 à P4) : sources primaires, texte intégral, page bloquée, contradictions ; toujours en révision |
| `references/revision-enrichissement.md` | après un fact-check, et dès qu'il faut corriger, enrichir ou réécrire un article existant |
| `references/liens-internes.md` | à la rédaction (« Voir aussi », liens dans le texte) et à la publication : format `<prefixe_liens><slug>`, slug des articles à venir |
| `references/rapport-fact-check.md` | à chaque fact-check : modèle du rapport, archivage, statuts et suivi |
| `references/sujets-derives.md` | pendant l'enquête et la rédaction pour repérer les sujets dérivés ; à la publication pour la fiche de sujets ; pour choisir le prochain article |

| Script | Rôle |
|---|---|
| `scripts/verifier_references.py` | vérifie dans Crossref, OpenAlex et Open Library que chaque référence existe, contrôle les prépublications arXiv et, en dernier recours, la page de l'URL indiquée ; propose les DOI manquants et les textes intégraux en accès libre. Un lien injoignable donne « À CONFIRMER », jamais « INTROUVABLE » |
| `scripts/inventaire_sujets.py` | agrège toutes les fiches de sujets dérivés, fusionne les doublons, signale les sujets déjà rédigés mais non cochés et classe ceux qui restent à rédiger |
| `scripts/verifier_article.py` | contrôle la forme et la publication (frontmatter, notes, index), ainsi que les signaux de preuve et de rédaction (chiffres sans note, affirmations trop fortes, datations mélangées, listes ou paragraphes fragmentés) et les liens internes (format, « Voir aussi » sans lien, liens en attente) |

Les scripts lisent `redactor.json` eux-mêmes (`--root` pour indiquer la racine du projet). Dépendance : PyYAML.

## Les cinq phases

Chaque phase se termine par une **porte** : ne pas passer à la suivante tant qu'elle n'est pas franchie.

### Phase 1 — Cadrage

1. Identifier le type d'article (lieu, peuple, événement, biographie, concept, institution, document primaire, sujet scientifique).
2. Formuler la question encyclopédique : que doit savoir un lecteur qui ne connaît rien au sujet ?
3. Vérifier que l'article n'existe pas déjà : chercher le sujet et ses variantes de nom dans `<articles>` et, si le projet en a, dans les fiches `<brainstorm>/*<suffixe_brainstorm>` (l'article peut y être prévu, avec une priorité).
4. Vérifier que le sujet entre dans le périmètre fixé par la charte.
5. Choisir le dossier de catégorie existant dans `<articles>` (ne créer un dossier que si aucun ne convient) et le slug.

**Porte** : type, périmètre, dossier et slug arrêtés ; pas de doublon.

### Phase 2 — Enquête

1. Les documents fournis par l'utilisateur sont un point de départ, jamais un plafond. Chercher activement des sources de niveau 1 à 4 (WebSearch, WebFetch, portails cités dans les fiches de méthode).
2. Appliquer la méthode historique et, si le sujet l'exige, la méthode scientifique.
3. Tenir le **dossier de sources** et la **table des affirmations** (`preuves-et-attribution.md`), avec le niveau de preuve atteint pour chaque affirmation.
4. Noter les divergences entre sources et leur nature (erreur, tradition différente, datation variable).
5. Pousser la preuve avec `enquete-avancee.md` : remonter aux sources primaires, passer du résumé au texte intégral, contourner légalement les pages bloquées, chercher en amont et en aval des citations, résoudre les contradictions.
6. Noter au fil de l'eau les sujets dérivés rencontrés dans les sources (`sujets-derives.md`, sections 1 à 3).
7. Dès qu'une bibliographie existe (en révision : immédiatement), lancer `verifier_references.py` et traiter chaque entrée DIVERGENT ou INTROUVABLE.

Si l'accès au web est indisponible, le dire et travailler seulement avec les sources fournies, en signalant chaque section insuffisamment sourcée.

**Porte** : chaque fait clé a au moins deux sources indépendantes, dont une de niveau 1 à 4, ou il est marqué « à vérifier » ; les chiffres clés visent le niveau P3 (ou P2 confirmé) ; les lacunes sont listées.

### Phase 3 — Rédaction

1. Suivre la structure fixée par la charte pour ce type d'article ; à défaut : introduction, sections thématiques, chronologie si utile, bibliographie, notes.
2. Écrire l'attaque et le paragraphe d'enjeu selon `redaction-journalistique.md` ; appliquer la pyramide inversée à l'introduction et à chaque section.
3. Expliquer (comment, pourquoi) plutôt qu'énumérer ; attribuer chaque estimation et interprétation. Écrire des paragraphes et des phrases élaborés, nourris de faits et de mécanismes, jamais de remplissage (`revision-enrichissement.md`, sections 3 à 5).
4. Présenter les débats avec la structure Position A / Position B / État du débat, à poids proportionné.
5. Frontmatter : celui de `gabarit_article` s'il existe, avec au moins les `champs_obligatoires`.
6. Liens internes et « Voir aussi » : chaque renvoi est un lien `[Titre](<prefixe_liens><slug>)`, y compris vers un article qui n'existe pas encore, avec le slug conventionnel de son futur titre court (`liens-internes.md`).

**Porte** : brouillon complet, sans section creuse ni remplissage.

### Phase 4 — Preuve et relecture

1. Repasser la table des affirmations : aucune affirmation « à vérifier » ni en P0 ne reste dans le texte ; celles restées sous leur objectif de preuve le disent dans leur note (« résumé consulté »).
2. Placer les appels `[^n]` selon `preuves-et-attribution.md` (section 4).
3. Faire la relecture adversariale (`preuves-et-attribution.md`, section 7) et la relecture du rédacteur (`redaction-journalistique.md`, section 4).
4. Vérifier la cohérence entre l'encadré de synthèse s'il y en a un, le corps et la chronologie.

**Porte** : chaque affirmation sensible est sourcée ; les sections faibles sont listées pour la note éditoriale.

### Phase 5 — Publication

1. Écrire le fichier `<articles>/<categorie>/<slug>.md`. Un fichier sans `champ_statut` est considéré comme **publié**. Le slug est le slug conventionnel du titre court : des liens l'attendent peut-être déjà (`LIENS_EN_ATTENTE`, `liens-internes.md`).
2. Lancer le vérificateur (chemin relatif à ce skill) :
   ```bash
   python <dossier-du-skill>/scripts/verifier_article.py <articles>/<categorie>/<slug>.md
   ```
   Corriger tous les **BLOQUANT**, puis traiter les avertissements ou justifier ceux qu'on garde.
3. Mettre à jour chaque fichier de `fichiers_index` (compteur, ligne de branche, ordre alphabétique selon l'index).
4. Si le projet a des fiches de sujets : créer `<brainstorm>/<slug><suffixe_brainstorm>` (modèle dans `gabarit_article` ou dans la charte) avec les sujets repérés, évalués et priorisés selon `sujets-derives.md` ; s'il s'agit d'un article dérivé, cocher `#` dans la colonne « Rédigé » de toutes les fiches qui le proposent (`inventaire_sujets.py` les retrouve).
5. Ajouter une ligne au `journal` s'il existe.
6. Relancer `verifier_article.py` jusqu'à zéro bloquant, et `verifier_references.py` jusqu'à zéro DIVERGENT ou INTROUVABLE. Ne pas faire de commit git sans demande explicite.

Contrôles faits par le script : champs obligatoires présents ; slug en minuscules et tirets, unique dans `<articles>` ; `date: "AAAA-MM-JJ"` **entre guillemets** (sinon les lecteurs YAML la convertissent en objet Date) ; statut parmi `statuts` ; une seule H1 ; notes `[^n]` cohérentes et section `## Notes` en dernier.

## Modes de travail

| Demande | Phases | Livrable |
|---|---|---|
| Article complet | 1 → 5 | article publié + note éditoriale |
| Recherche seule | 1 → 2 | dossier de sources + table des affirmations + plan proposé |
| Vérification / fact-check | 4 + `verifier_references.py` + `verifier_article.py`, sans réécrire | rapport (`rapport-fact-check.md`), archivé dans `<dossier_fact_checks>/<slug>-AAAA-MM-JJ.md` et inscrit à son registre si le projet en a un + résumé à l'utilisateur |
| Révision (après fact-check ou sur demande) | fact-check s'il n'existe pas, puis `revision-enrichissement.md` : corriger → retirer → restructurer → enrichir, puis 4 et 5 | article révisé et enrichi + journal des modifications + note éditoriale + section « Suivi » du rapport mise à jour (statut `révisé`) |
| Contrôle du corpus | `verifier_article.py --corpus` | état des index, doublons, articles non conformes |
| Plan éditorial (« quoi écrire ensuite ? ») | `inventaire_sujets.py` + `sujets-derives.md` | sujets prioritaires avec leurs articles-mères, incohérences des fiches, documentation disponible pour les trois premiers |

## Livraison

Chaque fact-check donne lieu à un rapport écrit (`rapport-fact-check.md`). Chaque problème y porte un identifiant, sa localisation (passage, ligne), sa qualification (erreur démontrée, P0, référence douteuse, neutralité, forme) et sa source, afin qu'il devienne une ligne du journal des modifications. À la révision, le rapport n'est pas réécrit : sa section « Suivi » et le registre reçoivent le nouveau statut.

Terminer chaque article par une **note éditoriale** courte destinée à l'utilisateur (hors du fichier) : sections faiblement sourcées, affirmations retirées faute de preuve, débats non tranchés, résultat du vérificateur.

## Jamais

- Inventer une date, un chiffre, une citation, un auteur, un numéro de page ou une cote d'archive.
- Citer une source non consultée, ni recopier la bibliographie d'un autre article.
- Présenter une hypothèse ou une tradition comme un fait établi.
- Importer les réflexes de presse : accroche, suspense, « aujourd'hui » sans date, superlatifs.
- Corriger ou déplacer des articles du corpus qui ne font pas partie de la demande : signaler les problèmes trouvés par le script, ne les corriger que si l'utilisateur le demande.

## Pour aller plus loin (optionnel)

Si ces skills sont installés, ils peuvent approfondir une phase : `deep-research` (mode fact-check) pour l'enquête, `scholarly-citation` pour l'attribution fine, `journalism-writing` et `encyclopedia-writing` pour la structure argumentative. Ce skill et la charte du projet priment en cas de conflit.
