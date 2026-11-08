---
name: kongopedia-redaction
description: Chaîne complète de production d'un article Kongopedia, de l'enquête à la publication. Réunit la méthode historique (critique des sources, traditions orales, datation), la méthode scientifique (hiérarchie des preuves, mesures, hypothèses), le métier journalistique (attaque, pyramide inversée, attribution, vérification, équité) et la neutralité encyclopédique, puis contrôle l'article avec un script avant de le publier dans articles/. Use when the user asks to research, write, revise, fact-check or publish a Kongopedia article — « rédige un article Kongopedia sur… », « écris l'article », « fais la recherche pour Kongopedia », « vérifie / fact-check cet article », « révise l'article », « publie l'article », « contrôle le corpus », « quel article écrire ensuite ? », « liste les sujets à rédiger ». Complète kongopedia-editorial-skill (charte maison), qu'il faut charger avec lui.
---

# Kongopedia — Rédaction, de l'enquête à la publication

Ce skill organise le travail d'un rédacteur-enquêteur. Il ne répète pas la charte maison : structure, infobulle `[!INFO]`, notes `[^n]`, hiérarchie des sources (niveaux 1 à 8), protocole anti-IA, point de vue africain et article de référence Wagénia sont dans **`kongopedia-editorial-skill`**. Charger les deux.

Ce que ce skill ajoute : **comment enquêter, comment écrire avec la clarté d'un journaliste, comment prouver, comment publier**.

| Fiche | À charger quand |
|---|---|
| `references/methode-historique.md` | le sujet a une dimension historique (presque toujours) |
| `references/methode-scientifique.md` | sciences, géologie, médecine, datation, démographie |
| `references/redaction-journalistique.md` | à la rédaction et à la révision |
| `references/preuves-et-attribution.md` | dès la recherche (dossier de sources) et avant publication |
| `references/enquete-avancee.md` | pour monter d'un niveau de preuve (P0 à P4) : sources primaires, texte intégral, page bloquée, contradictions ; toujours en révision |
| `references/revision-enrichissement.md` | après un fact-check, et dès qu'il faut corriger, enrichir ou réécrire un article existant |
| `references/liens-internes.md` | à la rédaction (« Voir aussi », liens dans le texte) et à la publication : format `/article/<slug>`, slug des articles à venir |
| `references/rapport-fact-check.md` | à chaque fact-check : modèle du rapport, archivage dans `ressources/fact-checks/`, statuts et suivi |
| `references/sujets-derives.md` | pendant l'enquête et la rédaction pour repérer les sujets dérivés ; à la publication pour la fiche brainstorm ; pour choisir le prochain article |

| Script | Rôle |
|---|---|
| `scripts/verifier_references.py` | vérifie dans Crossref, OpenAlex et Open Library que chaque référence existe, contrôle les prépublications arXiv et, en dernier recours, la page de l'URL indiquée ; propose les DOI manquants et les textes intégraux en accès libre. Un lien injoignable donne « À CONFIRMER », jamais « INTROUVABLE » |
| `scripts/inventaire_sujets.py` | agrège toutes les fiches brainstorm, fusionne les doublons, signale les sujets déjà rédigés mais non cochés et classe ceux qui restent à rédiger |
| `scripts/verifier_article.py` | contrôle la forme et la publication (frontmatter lu par le site, notes, index), ainsi que les signaux de preuve et de rédaction (chiffres sans note, affirmations trop fortes, datations mélangées, listes ou paragraphes fragmentés) et les liens internes (format `/article/<slug>`, « Voir aussi » sans lien, liens en attente) |

## Les cinq phases

Chaque phase se termine par une **porte** : ne pas passer à la suivante tant qu'elle n'est pas franchie.

### Phase 1 — Cadrage

1. Identifier le type d'article (lieu, peuple, événement, biographie, concept, institution, document primaire, sujet scientifique).
2. Formuler la question encyclopédique : que doit savoir un lecteur qui ne connaît rien au sujet ?
3. Vérifier que l'article n'existe pas déjà : chercher le sujet et ses variantes de nom dans `articles/` et dans les fiches `ressources/brainstorm/*-articles-derives.md` (l'article peut y être prévu, avec une priorité).
4. Choisir le dossier de catégorie existant dans `articles/` (ne créer un dossier que si aucun ne convient) et le slug.

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

1. Suivre le blueprint du skill éditorial adapté au type d'article.
2. Écrire l'attaque et le paragraphe d'enjeu selon `redaction-journalistique.md` ; appliquer la pyramide inversée à l'introduction et à chaque section.
3. Expliquer (comment, pourquoi) plutôt qu'énumérer ; attribuer chaque estimation et interprétation. Écrire des paragraphes et des phrases élaborés, nourris de faits et de mécanismes, jamais de remplissage (`revision-enrichissement.md`, sections 3 à 5).
4. Présenter les débats avec la structure Position A / Position B / État du débat, à poids proportionné.
5. Frontmatter : celui de `ressources/PROMPT-REDACTION-ARTICLE.md`, avec en plus les contraintes du site décrites en phase 5.
6. Liens internes et « Voir aussi » : chaque renvoi est un lien `[Titre](/article/<slug>)`, y compris vers un article qui n'existe pas encore, avec le slug conventionnel de son futur `titre_simple` (`liens-internes.md`).

**Porte** : brouillon complet, sans section creuse ni remplissage.

### Phase 4 — Preuve et relecture

1. Repasser la table des affirmations : aucune affirmation « à vérifier » ni en P0 ne reste dans le texte ; celles restées sous leur objectif de preuve le disent dans leur note (« résumé consulté »).
2. Placer les appels `[^n]` selon `preuves-et-attribution.md` (section 4).
3. Faire la relecture adversariale (`preuves-et-attribution.md`, section 7) et la relecture du rédacteur (`redaction-journalistique.md`, section 4).
4. Vérifier la cohérence entre l'infobulle, le corps et la chronologie.

**Porte** : chaque affirmation sensible est sourcée ; les sections faibles sont listées pour la note éditoriale.

### Phase 5 — Publication

1. Écrire le fichier `articles/<categorie>/<slug>.md`. Le site Next.js lit tout `articles/` ; un fichier sans `publication_status` y est **publié**. Le slug est le slug conventionnel du `titre_simple` : des liens l'attendent peut-être déjà (`LIENS_EN_ATTENTE`, `liens-internes.md`).
2. Lancer le vérificateur (chemin relatif à ce skill) :
   ```bash
   python <dossier-du-skill>/scripts/verifier_article.py articles/<categorie>/<slug>.md
   ```
   Corriger tous les **BLOQUANT**, puis traiter les avertissements ou justifier ceux qu'on garde.
3. Mettre à jour `articles/INDEX.md` (compteur et ligne de branche) et `articles/INDEX-ALPHABETIQUE.md` (ordre alphabétique strict), avec les chemins actuels `articles/…`, plus jamais `ressources/articles/…`.
4. Créer `ressources/brainstorm/<slug>-articles-derives.md` (modèle dans `ressources/PROMPT-REDACTION-ARTICLE.md`) avec les sujets repérés, évalués et priorisés selon `sujets-derives.md` ; s'il s'agit d'un article dérivé, cocher `#` dans la colonne « Rédigé » de toutes les fiches qui le proposent (`inventaire_sujets.py` les retrouve).
5. Ajouter une ligne à `ressources/log.md`.
6. Relancer `verifier_article.py` jusqu'à zéro bloquant, et `verifier_references.py` jusqu'à zéro DIVERGENT ou INTROUVABLE. Ne pas faire de commit git sans demande explicite.

Contraintes du site que le script contrôle : `title`, `titre_simple` et `slug` présents ; slug en minuscules et tirets, unique dans `articles/` ; `date: "AAAA-MM-JJ"` **entre guillemets** (sinon gray-matter la convertit en objet Date) ; `publication_status` parmi `draft`, `review`, `published` ; une seule H1 ; notes `[^n]` cohérentes et section `## Notes` en dernier.

## Modes de travail

| Demande | Phases | Livrable |
|---|---|---|
| Article complet | 1 → 5 | article publié + note éditoriale |
| Recherche seule | 1 → 2 | dossier de sources + table des affirmations + plan proposé |
| Vérification / fact-check | 4 + `verifier_references.py` + `verifier_article.py`, sans réécrire | rapport archivé `ressources/fact-checks/<slug>-AAAA-MM-JJ.md` (`rapport-fact-check.md`) + ligne au registre + résumé à l'utilisateur |
| Révision (après fact-check ou sur demande) | fact-check s'il n'existe pas, puis `revision-enrichissement.md` : corriger → retirer → restructurer → enrichir, puis 4 et 5 | article révisé et enrichi + journal des modifications + note éditoriale + section « Suivi » du rapport et registre mis à jour (statut `révisé`) |
| Contrôle du corpus | `verifier_article.py --corpus` | état des index, doublons, articles non conformes |
| Plan éditorial (« quoi écrire ensuite ? ») | `inventaire_sujets.py` + `sujets-derives.md` | sujets prioritaires avec leurs articles-mères, incohérences des fiches, documentation disponible pour les trois premiers |

## Livraison

Chaque fact-check donne lieu à un rapport écrit et archivé (`rapport-fact-check.md`) : `ressources/fact-checks/<slug>-AAAA-MM-JJ.md`, inscrit au registre `ressources/fact-checks/README.md`. Chaque problème y porte un identifiant, sa localisation (passage, ligne), sa qualification (erreur démontrée, P0, référence douteuse, neutralité, forme) et sa source, afin qu'il devienne une ligne du journal des modifications. À la révision, le rapport n'est pas réécrit : sa section « Suivi » et le registre reçoivent le nouveau statut.

Terminer chaque article par une **note éditoriale** courte destinée à l'utilisateur (hors du fichier) : sections faiblement sourcées, affirmations retirées faute de preuve, débats non tranchés, résultat du vérificateur.

## Jamais

- Inventer une date, un chiffre, une citation, un auteur, un numéro de page ou une cote d'archive.
- Citer une source non consultée, ni recopier la bibliographie d'un autre article.
- Présenter une hypothèse ou une tradition comme un fait établi.
- Importer les réflexes de presse : accroche, suspense, « aujourd'hui » sans date, superlatifs.
- Corriger ou déplacer des articles du corpus qui ne font pas partie de la demande : signaler les problèmes trouvés par le script, ne les corriger que si l'utilisateur le demande.

## Pour aller plus loin (optionnel)

Si ces skills globaux sont installés, ils peuvent approfondir une phase : `deep-research` (mode fact-check) pour l'enquête, `scholarly-citation` pour l'attribution fine, `journalism-writing` et `encyclopedia-writing` pour la structure argumentative. Ils sont en anglais et conçus pour un autre projet : ce skill et la charte Kongopedia priment en cas de conflit.
