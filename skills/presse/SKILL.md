---
name: presse
description: "Production d'un papier de presse, quotidien ou magazine, de l'angle à la livraison au CMS : actualité, enquête, reportage, portrait, entretien, analyse, opinion (éditorial, tribune, chronique). Angle, entretiens (on, off, relecture), terrain, règle des deux sources et niveaux de preuve, contradictoire, déontologie (charte de Munich et charte du titre), titraille, SEO, réseaux et dossier de vérification contrôlés par script. Conventions du titre dans la section « presse » de redactor.json. Use when the user asks to pitch, report, write, edit, fact-check or package a news or magazine piece — « écris un papier sur… », « trouve un angle », « prépare l'interview de… », « fais le portrait de… », « rédige l'édito », « tire une brève de cette dépêche », « vérifie ce papier », « prépare la titraille / le SEO / les réseaux »."
---

# Redactor — Papier de presse, de l'angle à la livraison

Ce skill organise le travail d'un journaliste : **trouver l'angle, aller chercher l'information, la prouver, l'écrire pour être lu, la livrer prête à publier**. Il couvre le quotidien (actualité, délai court) et le magazine (temps long, écriture plus libre) : la méthode est la même, le format change.

## Avant tout : la configuration du titre

Chercher `redactor.json` à la racine du projet et lire sa section `presse` (les clés communes `projet` et `charte` se lisent à la racine) :

| Clé | Rôle | Défaut |
|---|---|---|
| `charte` | charte de la rédaction : ligne, ton, règles maison ; prime sur ce skill pour la forme | charte commune, sinon aucune |
| `dossier_papiers` | où écrire les papiers | `papiers` |
| `dossier_verification` | où écrire les dossiers de vérification (jamais publiés) | `verification` |
| `rubriques` | rubriques admises | libre |
| `reseaux` | messages à produire | `x`, `facebook`, `linkedin`, `newsletter` |
| `signature` | signature par défaut | aucune |
| `longueurs` | fourchettes de mots par format, `{ "format": [min, max] }` | `references/formats.md` |

Sans `redactor.json`, appliquer les défauts et demander où écrire. Si une charte est déclarée, la charger : elle complète la déontologie de ce skill et prime pour la forme. Exemple complet : `exemples/presse/` à la racine du plugin.

| Fiche | À charger quand |
|---|---|
| `references/angle-et-cadrage.md` | toujours, à la phase 1 |
| `references/formats.md` | au choix du format (phase 1) et au plan (phase 3) |
| `references/sourcing-et-verification.md` | dès l'enquête, et à la vérification |
| `references/entretiens-et-citations.md` | dès qu'il y a un entretien, et pour chaque citation |
| `references/terrain-et-reportage.md` | reportage, portrait, enquête : notes de terrain, scènes |
| `references/opinion-et-analyse.md` | analyse, éditorial, tribune, chronique |
| `references/titraille-seo-reseaux.md` | à la rédaction (titraille) et à la livraison (SEO, réseaux) |
| `references/deontologie.md` | à l'angle (sujet sensible), à la vérification, avant livraison |
| `references/dossier-verification.md` | dès la phase 2 : modèle du dossier, lu par le script |

Fiches du skill `encyclopedia` réutilisées telles quelles (chemins relatifs à ce skill) : `../encyclopedia/references/enquete-avancee.md` (échelle P0 à P4, remonter à la source primaire, contradictions) et `../encyclopedia/references/preuves-et-attribution.md` (hiérarchie des sources, relecture adversariale).

| Script | Rôle |
|---|---|
| `scripts/verifier_papier.py` | contrôle le papier et son dossier de vérification : titraille, SEO, réseaux, longueur, dates relatives, crédits photo ; chaque citation du texte présente au dossier, aucun propos « off » publié, aucun fait en P0, aucun fait sensible à source unique non attribué, aucun mis en cause non sollicité |
| `../encyclopedia/scripts/verifier_references.py` | vérifie dans Crossref, OpenAlex et Open Library les rapports et études listés sous « ## Sources » du dossier |

Dépendance : PyYAML.

## Les six phases

Chaque phase se termine par une **porte**. Trois portes demandent l'accord de l'utilisateur : ne pas continuer sans lui.

### Phase 1 — Angle *(validation de l'utilisateur)*

1. Distinguer le sujet de l'angle (`angle-et-cadrage.md`) : l'angle est la question précise à laquelle le papier répond, en une phrase.
2. Choisir le format et la longueur (`formats.md`), la rubrique, le registre (quotidien ou magazine), la date de publication visée.
3. Lister ce qu'il faut savoir et où le chercher : documents, personnes à interroger, terrain.
4. Repérer les risques (`deontologie.md`) : personnes mises en cause, mineurs, victimes, procédure judiciaire en cours, conflit d'intérêts.

**Porte** : présenter la proposition d'angle (modèle dans `angle-et-cadrage.md`) et **attendre l'accord de l'utilisateur**.

### Phase 2 — Enquête

1. Documents et web : remonter chaque information à sa source primaire (`../encyclopedia/references/enquete-avancee.md`). Une dépêche ou un article de confrère est un point de départ, pas une source finale.
2. Entretiens : préparer, conduire, consigner (`entretiens-et-citations.md`). Fixer le statut de chaque propos (on, off, contexte) **au moment où il est recueilli**. Les entretiens sont menés par l'utilisateur : Claude prépare les questions et exploite les notes ou transcriptions qu'on lui donne, il n'invente jamais un échange.
3. Terrain : exploiter les notes de l'utilisateur (`terrain-et-reportage.md`) en séparant le vu, l'entendu et le rapporté.
4. Tenir le **dossier de vérification** au fil de l'eau (`dossier-verification.md`) : chaque fait, avec ses sources, sa sensibilité et son niveau ; chaque citation, avec son statut ; chaque source anonyme ; chaque mis en cause, avec la date à laquelle il a été sollicité.
5. Appliquer la règle des deux sources aux faits sensibles (`sourcing-et-verification.md`).

Sans accès au web, le dire et travailler seulement avec la matière fournie, en signalant les trous.

**Porte** : les faits sensibles ont deux sources indépendantes ou sont attribués ; chaque mis en cause a été sollicité ou va l'être avant publication ; les lacunes sont listées.

### Phase 3 — Plan *(validation de l'utilisateur)*

1. Choisir la structure du format (`formats.md`) : pyramide inversée, récit en scènes, portrait à fil rouge, questions-réponses, démonstration.
2. Écrire **l'attaque** (deux versions si le choix n'est pas évident) et le paragraphe d'enjeu.
3. Proposer le plan en intertitres, avec pour chaque partie les faits et citations du dossier qu'elle utilise, et la chute.

**Porte** : présenter attaque et plan, et **attendre l'accord de l'utilisateur**.

### Phase 4 — Rédaction

1. Écrire le corps selon le format, dans la langue du lecteur : phrases courtes, verbes d'action, chiffres arrondis et comparés, sigles développés.
2. Attribuer chaque information qui n'est pas de notoriété publique ; verbes d'attribution neutres (`sourcing-et-verification.md`).
3. Séparer les faits et l'opinion : aucun jugement de la rédaction hors des formats d'opinion (`opinion-et-analyse.md`).
4. Écrire la titraille complète (`titraille-seo-reseaux.md`) : surtitre, titre, chapô, intertitres, exergues tirées mot pour mot du texte, légendes avec crédit.
5. Écrire le fichier `<dossier_papiers>/<slug>.md` avec `statut: brouillon` (frontmatter dans `titraille-seo-reseaux.md`).

**Porte** : papier complet à la longueur du format ; chaque citation et chaque fait du texte figure au dossier.

### Phase 5 — Vérification

1. Relecture adversariale : lire le papier comme la personne mise en cause, puis comme son avocat (`../encyclopedia/references/preuves-et-attribution.md`, section 7). Chaque phrase qui fâche doit tenir sur pièce.
2. Vérifier titre, chapô et messages réseaux contre le corps : rien n'y promet plus que ce que le texte prouve.
3. Passer `statut: relecture` et lancer le vérificateur (chemin relatif à ce skill) :
   ```bash
   python <dossier-du-skill>/scripts/verifier_papier.py <dossier_papiers>/<slug>.md
   ```
   Corriger tous les **BLOQUANT** ; traiter les avertissements ou dire pourquoi on les garde.
4. Si le dossier liste des rapports ou des études sous « ## Sources » : `python <dossier-du-skill>/../encyclopedia/scripts/verifier_references.py <dossier_verification>/<slug>.md`, puis traiter chaque DIVERGENT ou INTROUVABLE.
5. Écrire les champs SEO et les messages réseaux (`titraille-seo-reseaux.md`).

**Porte** : zéro bloquant ; relecture adversariale faite.

### Phase 6 — Livraison *(validation de l'utilisateur)*

1. Présenter à l'utilisateur : le papier, le dossier de vérification et la **note de livraison** (ci-dessous).
2. **Attendre son accord** avant de passer `statut: valide`. Ne jamais publier soi-même dans le CMS.
3. Fournir le texte prêt à coller : titraille, corps, légendes, champs SEO, messages réseaux, chacun dans un bloc séparé.
4. Ne pas faire de commit git sans demande explicite.

**Note de livraison** (hors du fichier) : angle tenu ou ajusté, faits attribués faute de seconde source, citations non relues, mis en cause sans réponse, avertissements du script conservés, points à surveiller après publication (droit de réponse attendu, chiffre à actualiser).

## Modes de travail

| Demande | Phases | Livrable |
|---|---|---|
| Papier complet | 1 → 6 | papier + dossier de vérification + note de livraison |
| Proposition d'angle | 1 | proposition d'angle, plan d'enquête |
| Préparation d'entretien | 1 + `entretiens-et-citations.md` | grille de questions, points à vérifier, documents à avoir sous la main |
| Dépêche ou communiqué → brève ou article | 1 (court) → 6 | papier, sources primaires vérifiées, ce qui reste à confirmer |
| Vérification d'un papier existant | 5, sans réécrire | rapport : bloquants, avertissements, faits non sourcés, citations à vérifier, relecture adversariale |
| Titraille, SEO, réseaux seuls | `titraille-seo-reseaux.md` + script | titraille et champs, cohérents avec le corps |
| Changement de format (actualité → analyse, article → brève) | 1 → 6 sur la matière existante | nouveau papier ; les faits ne changent pas, seule la construction change |

## Jamais

- Inventer un fait, un chiffre, une citation, un interlocuteur, une scène, un détail d'ambiance, un lieu ou une date. Pas de personnage composite, pas de scène reconstituée présentée comme vue.
- Publier un propos recueilli en off, ou identifier une source à qui l'anonymat a été promis.
- Retoucher une citation au point d'en changer le sens, ou présenter comme citation ce qui est une paraphrase.
- Mettre quelqu'un en cause sans l'avoir sollicité, ou présenter un suspect comme coupable.
- Faire promettre au titre, au chapô ou aux réseaux plus que le texte ne prouve.
- Glisser l'opinion de la rédaction dans un papier d'information.
- Copier le texte d'un confrère ou d'une dépêche sans le citer.
- Passer un papier au statut `valide` sans l'accord de l'utilisateur.

## Pour aller plus loin (optionnel)

Si ces skills sont installés, ils peuvent aider à une phase : `deep-research` pour l'enquête documentaire, `journalism-writing` pour la structure, `copy-editing` pour la relecture de style. Ce skill et la charte du titre priment en cas de conflit.
