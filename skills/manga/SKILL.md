---
name: manga
description: "Écriture de manga de la prémisse au script : one-shot, série en chapitres, webtoon vertical. Prémisse et personnages, plan des chapitres, découpage en pages et en cases, script pour un dessinateur ou name textuel pour l'auteur complet, dialogues et bulles, rythme de lecture (tourne, double page, cliffhanger), bible et fiches de personnages, script assemblé et feuille de lettrage. Un script contrôle la mise en page, la lisibilité des bulles, le rythme et la continuité. Conventions dans la section « manga » de redactor.json. Use when the user asks to plan, script, break down, check or package a manga, a comic or a webtoon — « écris le script du chapitre 1 », « découpe cette scène en cases », « fais le one-shot », « vérifie le rythme de mes pages », « adapte en webtoon », « prépare le script pour le dessinateur », « sors la feuille de lettrage »."
---

# Redactor — Manga, de la prémisse au script

Ce skill écrit le manga **avant le dessin** : l'histoire, le découpage en pages et en cases, les dialogues, le rythme de lecture. Il sert le **scénariste** qui livre un script à un dessinateur, comme l'**auteur complet** qui veut un découpage textuel (un « name » écrit) avant de crayonner. Le format est le même ; seul le détail des descriptions change. Le skill ne dessine pas et ne génère pas d'images.

## Avant tout : la configuration

Chercher `redactor.json` à la racine du projet et lire sa section `manga` (la clé commune `charte` se lit à la racine) :

| Clé | Rôle | Défaut |
|---|---|---|
| `charte` | charte de série, de magazine ou de collection | aucune |
| `titre`, `auteur`, `dessinateur` | titre et crédits | nom du projet ; aucun |
| `format` | `oneshot`, `serie` ou `webtoon` | `serie` |
| `sens` | `rtl` (droite à gauche, japonais) ou `ltr` (gauche à droite) | `rtl` |
| `pages_par_chapitre` | cible ; un chapitre peut la préciser (champ `pages`) | aucune |
| `page_revelation` | parité de la page découverte en tournant | `paire` |
| `cases_max_par_page`, `bulles_max_par_case`, `mots_max_par_bulle` | seuils de lisibilité | 7, 3, 25 |
| `dossier_chapitres`, `plan`, `dossier_bible`, `dossier_manuscrit` | organisation du projet | `chapitres`, `plan.md`, `bible`, `manuscrit` |
| `noms_ignores` | mots à majuscule à ne pas signaler hors bible | aucun |
| `statuts` | étapes d'un chapitre ; la dernière vaut « fini » | `plan`, `script`, `name`, `final` |

Sans `redactor.json`, appliquer les défauts et proposer de créer le fichier. Exemple complet (premier chapitre d'une série fictive) : `exemples/manga/` à la racine du plugin.

| Fiche | À charger quand |
|---|---|
| `../roman/references/premisse-et-personnages.md` | phase 1 |
| `references/personnages-et-univers.md` | phases 1 et 2 : fiches visuelles, bible |
| `references/formats.md` | phase 1 : one-shot, série, webtoon ; longueurs |
| `../roman/references/structure-et-jalons.md` | phase 3 : jalons, plan |
| `references/script-et-decoupage.md` | phase 4 : format du script, cases, dialogues |
| `references/mise-en-page-et-rythme.md` | phases 3 et 4 : tourne, double page, cases par page, webtoon |
| `../roman/references/genres.md` | énigme, imaginaire, historique |
| `references/collaboration-et-livraison.md` | phase 6 : script pour le dessinateur, lettrage, dossier |

| Script | Rôle |
|---|---|
| `scripts/verifier_manga.py` | avancement (pages, cases, bulles) ; mise en page (pages par rapport à la cible, numérotation, page sans case, cases par page) ; bulles (case sans description, trop de bulles, bulle trop longue) ; rythme (révélation à la tourne, double page, cliffhanger d'une série) ; continuité (locuteurs et noms contre la bible, plan) |
| `scripts/assembler_script.py` | script complet dans l'ordre du plan, feuille de lettrage (`--lettrage`), export .docx ou PDF par pandoc |

Dépendance : PyYAML. Export : pandoc.

## Les six phases

Quatre portes demandent l'accord de l'utilisateur : ne pas continuer sans lui.

### Phase 1 — Prémisse, personnages, format *(validation de l'utilisateur)*

1. Partir de ce que l'auteur apporte ; formuler la prémisse, le thème, le public visé (`../roman/references/premisse-et-personnages.md`).
2. Choisir le format et la longueur (`formats.md`) ; pour une série, le rythme de publication et la longueur des chapitres.
3. Concevoir les personnages principaux avec ce qui compte pour le dessin : silhouette reconnaissable, tenue, expression type (`personnages-et-univers.md`).

**Porte** : présenter prémisse, format, personnages ; **attendre l'accord**.

### Phase 2 — Bible et univers

Créer la bible (`personnages-et-univers.md`) : fiches de personnages (lues par le script : nom, alias, naissance), lieux avec les détails dont le dessinateur aura besoin, règles du monde pour l'imaginaire. Elle se complète au fil des chapitres.

### Phase 3 — Plan *(validation de l'utilisateur)*

1. Jalons de l'histoire (`../roman/references/structure-et-jalons.md`) ; pour une série, l'arc du premier volume et la fin de chaque chapitre.
2. `plan.md` : un chapitre par ligne (numéro, titre, fichier, personnages, résumé) ; pour chaque chapitre, les temps forts et leur page visée (révélation, double page, cliffhanger) (`mise-en-page-et-rythme.md`).

**Porte** : présenter le plan ; **attendre l'accord**.

### Phase 4 — Script, chapitre par chapitre *(validation à chaque chapitre)*

Demander le mode s'il n'est pas fixé :
- **Claude écrit le script** : relire la bible et le chapitre précédent ; répartir les scènes en pages (`mise-en-page-et-rythme.md`), puis en cases (`script-et-decoupage.md`) ; écrire `<dossier_chapitres>/<NN>-<slug>.md`, statut `script`.
- **L'auteur écrit, Claude relit** : relecture du découpage et des dialogues, sans réécrire ; propositions ponctuelles.

Puis lancer `python <dossier-du-skill>/scripts/verifier_manga.py --chapitre <N>`, traiter les avertissements qui comptent et mettre la bible à jour.

**Porte** : présenter le chapitre (ou la relecture) ; **attendre le retour** avant le suivant.

### Phase 5 — Révision *(validation de l'utilisateur)*

Vérifier tout le projet avec le script ; relire en passes (structure, personnages, rythme des pages, dialogues, continuité) comme pour le roman (`../roman/references/revision.md`) ; rapport de révision ; corrections retenues.

**Porte** : présenter le rapport et l'état final ; **attendre l'accord**.

### Phase 6 — Livraison

`python <dossier-du-skill>/scripts/assembler_script.py [--lettrage] [--docx] [--pdf]` : script complet pour le dessinateur, feuille de lettrage pour le lettreur (`collaboration-et-livraison.md`). Dossier de présentation pour un éditeur ou un concours : pitch, synopsis, fiches de personnages, premières pages (`../roman/references/dossier-editeur.md`). Ne pas faire de commit git sans demande explicite.

## Modes de travail

| Demande | Phases | Livrable |
|---|---|---|
| Créer un manga de zéro | 1 → 6 | script complet, lettrage, dossier |
| Écrire un one-shot | 1, 3, 4, 6 (bible minimale) | script du one-shot |
| Découper une scène ou un chapitre | 4 | pages et cases |
| Relire un script ou un découpage | 4 (mode relecture) | relecture et propositions |
| Adapter en webtoon (ou l'inverse) | 1 (format) → 4 | nouveau découpage, mêmes scènes |
| Vérifier le rythme et la lisibilité | `verifier_manga.py` | rapport commenté |
| Préparer le travail du dessinateur et du lettreur | 6 | script assemblé, feuille de lettrage |

## Jamais

- Reprendre les personnages, l'univers, l'intrigue ou les dialogues d'un manga, d'un anime ou d'une bande dessinée existants, ou en écrire une imitation présentée comme originale. S'inspirer d'un genre ou d'une technique de découpage, oui ; recopier, non.
- Décrire le style graphique d'un dessinateur existant à imiter dans les notes pour le dessinateur ; décrire plutôt l'effet voulu (cadrage, ambiance, expression).
- Imposer l'histoire ou réécrire le script de l'auteur sans qu'il le demande.
- Mettre dans une case plus que ce qu'une image peut montrer : une case, un instant.
- Introduire un personnage ou un lieu sans l'inscrire dans la bible.
- Passer au chapitre suivant sans le retour de l'auteur.
