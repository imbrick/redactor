---
name: roman
description: "Écriture d'un roman de la prémisse au manuscrit : littérature générale, polar ou thriller, imaginaire, roman historique. Prémisse et personnages, jalons et plan, scènes et chapitres rédigés par Claude ou par l'auteur, voix de l'auteur, bible (personnages, lieux, chronologie, indices), révision d'ensemble, manuscrit assemblé, export .docx ou PDF et dossier d'éditeur. Un script contrôle l'avancement, la continuité, le style et, pour le polar, les indices. Conventions dans la section « roman » de redactor.json. Use when the user asks to plan, write, continue, revise or package a novel — « aide-moi à construire mon roman », « développe ce personnage », « fais le plan », « écris le chapitre 3 », « relis ce chapitre », « vérifie la continuité », « révise le manuscrit », « assemble le manuscrit », « prépare le synopsis / la quatrième de couverture »."
---

# Redactor — Roman, de la prémisse au manuscrit

Ce skill accompagne l'écriture d'un roman avec la méthode de l'**entre-deux** : quelques jalons fixés (le début, les grands tournants, la fin visée), le reste découvert en écrivant et repris en révision. L'auteur décide ; Claude construit avec lui, rédige quand on le lui demande, relit toujours.

## Avant tout : la configuration du roman

Chercher `redactor.json` à la racine du projet et lire sa section `roman` (la clé commune `charte` se lit à la racine) :

| Clé | Rôle | Défaut |
|---|---|---|
| `charte` | fiche de voix ou de style de l'auteur, ou charte de collection ; prime pour la forme | aucune |
| `titre`, `auteur` | titre du roman, nom d'auteur (manuscrit) | nom du projet ; aucun |
| `genre` | `litterature`, `polar`, `imaginaire`, `historique` | `litterature` |
| `dossier_chapitres` | un fichier Markdown par chapitre | `chapitres` |
| `plan` | plan du roman (jalons, tableau des chapitres) | `plan.md` |
| `dossier_bible` | bible : personnages, lieux, chronologie, indices… | `bible` |
| `dossier_manuscrit` | manuscrit assemblé et exports | `manuscrit` |
| `objectif_mots` | longueur visée | aucun |
| `tics` | mots ou tournures que l'auteur veut surveiller | aucun |
| `noms_ignores` | mots à majuscule à ne pas signaler comme absents de la bible (« Brigadier ») | aucun |
| `statuts` | étapes d'un chapitre, la dernière vaut « fini » | `plan`, `brouillon`, `relu`, `final` |
| `titre_chapitre` | titre des chapitres dans le manuscrit | `Chapitre {numero} — {titre}` |

Sans `redactor.json`, appliquer les défauts et proposer de créer le fichier. Exemple complet (polar fictif) : `exemples/roman/` à la racine du plugin.

| Fiche | À charger quand |
|---|---|
| `references/premisse-et-personnages.md` | phase 1 ; dès qu'un personnage naît ou change |
| `references/structure-et-jalons.md` | phase 3 ; à la révision de structure |
| `references/scene-et-chapitre.md` | phase 4, avant chaque chapitre |
| `references/voix-et-style.md` | dès la phase 1 (fiche de voix) ; avant de rédiger ou de relire |
| `references/bible-et-continuite.md` | phase 2 ; à chaque chapitre ; formats lus par le script |
| `references/genres.md` | dès la phase 1 : exigences propres au polar, à l'imaginaire, à l'historique |
| `references/revision.md` | phase 5, et pour toute relecture d'un chapitre |
| `references/dossier-editeur.md` | phase 6 : pitch, résumé, synopsis, quatrième de couverture |
| `references/manuscrit-et-export.md` | phase 6 : assemblage, normes de manuscrit, export |

| Script | Rôle |
|---|---|
| `scripts/verifier_roman.py` | avancement (mots par chapitre, total et objectif, chapitres à écrire) ; continuité (personnages du plan absents de la bible, variantes de noms, noms récurrents hors bible, point de vue d'un personnage pas encore né ou déjà mort) ; style (répétitions rapprochées, adverbes en -ment, tics déclarés, dialogues au trait d'union) ; polar (indice non exploité ou exploité avant d'être posé, révélation non préparée ou préparée trop tard) |
| `scripts/assembler_manuscrit.py` | assemble les chapitres dans l'ordre du plan en un manuscrit Markdown, puis l'exporte en .docx ou PDF avec pandoc s'il est installé |

Dépendance : PyYAML. Export : pandoc (et un moteur LaTeX pour le PDF).

## Les six phases

Quatre portes demandent l'accord de l'utilisateur : ne pas continuer sans lui.

### Phase 1 — Prémisse et personnages *(validation de l'utilisateur)*

1. Écouter ce que l'auteur a déjà : une image, une situation, un personnage, une fin. Ne pas imposer une histoire.
2. Formuler la prémisse en une phrase, le thème, le genre, le lectorat, la longueur visée (`premisse-et-personnages.md`).
3. Construire le protagoniste (désir, besoin, blessure, contradiction) et les personnages qui lui résistent.
4. Établir la **fiche de voix** (`voix-et-style.md`) : à partir de pages déjà écrites par l'auteur si elles existent, sinon par choix explicites (narrateur, temps, registre).
5. Repérer les exigences du genre (`genres.md`).

**Porte** : présenter prémisse, personnages principaux, fin visée et fiche de voix ; **attendre l'accord**.

### Phase 2 — Monde et bible

1. Créer la bible (`bible-et-continuite.md`) : personnages, lieux, chronologie ; pour le polar, le registre des indices ; pour l'imaginaire, les règles du monde et le lexique.
2. Roman historique : documenter l'époque avec la méthode du skill encyclopedia (`../encyclopedia/references/methode-historique.md`) et noter les sources dans la bible ; distinguer ce qui est attesté de ce qui est inventé.
3. La bible ne précède pas toute l'écriture : elle se complète au fil des chapitres.

**Porte** : bible minimale en place (personnages principaux, lieux principaux, repères de chronologie).

### Phase 3 — Jalons et plan *(validation de l'utilisateur)*

1. Fixer les jalons (`structure-et-jalons.md`) : situation initiale, incident déclencheur, premier tournant, point médian, crise, climax, dénouement — adaptés au roman, pas plaqués.
2. Découper en chapitres dans `plan.md` : numéro, titre, fichier, point de vue, personnages, jalon, résumé en une ou deux phrases. Les chapitres entre deux jalons peuvent rester esquissés : ils se découvrent en écrivant.
3. Polar : placer les indices et les révélations dans `bible/indices.md` en même temps que le plan.

**Porte** : présenter jalons et plan ; **attendre l'accord**.

### Phase 4 — Écriture, chapitre par chapitre *(validation à chaque chapitre)*

Pour chaque chapitre, demander à l'auteur le mode s'il ne l'a pas fixé :
- **Claude rédige** : relire la fiche de voix, la bible et les deux chapitres précédents ; construire les scènes (`scene-et-chapitre.md`) ; écrire le chapitre dans `<dossier_chapitres>/<NN>-<slug>.md` (frontmatter dans `bible-et-continuite.md`), statut `brouillon`.
- **L'auteur écrit, Claude relit** : lire le chapitre sans le réécrire ; rendre une relecture (`revision.md`, section 4) avec ce qui fonctionne, ce qui accroche, et des propositions ponctuelles que l'auteur accepte ou non.

Puis, dans les deux cas :
1. lancer `python <dossier-du-skill>/scripts/verifier_roman.py --chapitre <N>` et traiter les avertissements qui comptent ;
2. mettre à jour la bible avec ce que le chapitre a créé (personnage, lieu, date, indice) ;
3. noter dans le plan ce que le chapitre a changé à la suite.

**Porte** : présenter le chapitre (ou la relecture) et **attendre le retour de l'auteur** avant le chapitre suivant.

### Phase 5 — Révision d'ensemble *(validation de l'utilisateur)*

1. Lancer `verifier_roman.py` sur tout le roman.
2. Relire en passes successives (`revision.md`) : structure, personnages, scènes, continuité, style.
3. Rédiger le **rapport de révision** : problèmes classés par importance, chapitres concernés, propositions.
4. Appliquer les corrections que l'auteur retient, chapitre par chapitre ; passer les chapitres revus au dernier statut (`final`).

**Porte** : présenter le rapport de révision et l'état final ; **attendre l'accord** avant l'assemblage.

### Phase 6 — Manuscrit, export, dossier d'éditeur

1. `python <dossier-du-skill>/scripts/assembler_manuscrit.py [--docx] [--pdf]` (`manuscrit-et-export.md`).
2. Rédiger le dossier d'éditeur (`dossier-editeur.md`) : pitch, résumé d'une page, synopsis complet, quatrième de couverture, lettre d'accompagnement si l'auteur la veut.
3. Ne pas faire de commit git sans demande explicite.

## Modes de travail

| Demande | Phases | Livrable |
|---|---|---|
| Construire un roman de zéro | 1 → 6 | roman complet, chapitre par chapitre |
| Développer une idée ou un personnage | 1 (partielle) | prémisse ou fiche de personnage |
| Faire le plan d'un roman commencé | 2 → 3 sur l'existant | bible et plan tirés des chapitres écrits |
| Écrire ou continuer un chapitre | 4 | chapitre + bible à jour |
| Relire un chapitre de l'auteur | 4 (mode relecture) | relecture, sans réécriture non demandée |
| Vérifier la continuité ou l'avancement | `verifier_roman.py` | rapport commenté |
| Réviser le manuscrit | 5 | rapport de révision, puis corrections validées |
| Préparer l'envoi à un éditeur | 6 | manuscrit, export, dossier d'éditeur |

## Jamais

- Imposer une intrigue, un thème ou une fin : proposer, l'auteur choisit.
- Réécrire un chapitre de l'auteur sans qu'il le demande, ou effacer sa voix au profit d'une écriture « propre » et neutre.
- Reprendre le texte, les personnages ou l'univers d'une œuvre existante, ou en écrire une imitation présentée comme originale. S'inspirer d'un genre ou d'une technique, oui ; recopier, non.
- Présenter comme historique un fait inventé dans un roman historique sans le dire à l'auteur (la note de l'auteur peut le signaler au lecteur).
- Introduire un personnage, un lieu ou une règle du monde sans l'inscrire dans la bible.
- Résoudre une énigme de polar par un élément que le lecteur n'a pas pu voir.
- Passer au chapitre suivant sans le retour de l'auteur.

## Pour aller plus loin (optionnel)

Si ces skills sont installés, ils peuvent aider à une phase : `book-writer` pour une autre approche de la structure, `copy-editing` pour la relecture de style, `deep-research` pour documenter un roman historique. Ce skill et la fiche de voix de l'auteur priment en cas de conflit.
