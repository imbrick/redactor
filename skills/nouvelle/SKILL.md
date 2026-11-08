---
name: nouvelle
description: "Écriture de nouvelles, de l'idée à la version finale : nouvelle isolée, concours et appels à textes, recueil. Effet visé, construction par la chute ou par une image, premier jet rédigé par Claude ou par l'auteur, resserrement, conformité au règlement d'un concours (signes, mots, phrase et mots imposés, anonymat, date limite), ordre et fil rouge d'un recueil, export .docx ou PDF. Réutilise la voix, la scène et les contrôles de style du skill roman. Conventions dans la section « nouvelle » de redactor.json. Use when the user asks to find an idea for, write, tighten, check or package a short story or a collection — « écris une nouvelle sur… », « j'ai une idée de chute », « vérifie que ma nouvelle respecte le règlement du concours », « resserre ce texte », « organise mon recueil », « prépare l'envoi au concours »."
---

# Redactor — Nouvelle, de l'idée à la version finale

Une nouvelle vise **un effet** et tout y concourt : chaque phrase, chaque détail, le titre, la dernière ligne. Ce skill aide à trouver cet effet, à construire le texte pour le produire, à l'écrire, à le resserrer, puis à le rendre conforme à un concours ou à l'intégrer dans un recueil.

## Avant tout : la configuration

Chercher `redactor.json` à la racine du projet et lire sa section `nouvelle` (la clé commune `charte` se lit à la racine) :

| Clé | Rôle | Défaut |
|---|---|---|
| `charte` | fiche de voix de l'auteur | aucune |
| `auteur` | nom d'auteur (manuscrit ; contrôle d'anonymat) | aucun |
| `titre_recueil` | titre du recueil | nom du projet |
| `dossier_nouvelles` | un fichier Markdown par nouvelle | `nouvelles` |
| `dossier_concours` | une fiche de règlement par concours ou appel à textes | `concours` |
| `recueil` | ordre des nouvelles d'un recueil | `recueil.md` |
| `dossier_manuscrit` | textes mis en forme et exports | `manuscrit` |
| `tics` | mots ou tournures à surveiller | aucun |
| `statuts` | étapes d'une nouvelle, la dernière vaut « fini » | `idee`, `premier-jet`, `revise`, `final` |

Sans `redactor.json`, appliquer les défauts et proposer de créer le fichier. Exemple complet (deux nouvelles, un recueil, un règlement fictif) : `exemples/nouvelle/` à la racine du plugin.

| Fiche | À charger quand |
|---|---|
| `references/idee-et-effet.md` | phase 1 |
| `references/construction.md` | phase 2 |
| `references/resserrement.md` | phase 4, et pour toute relecture |
| `references/concours.md` | dès qu'un concours ou un appel à textes est en jeu |
| `references/recueil.md` | pour un recueil |
| `../roman/references/voix-et-style.md` | dès la phase 1 (fiche de voix), avant de rédiger ou de relire |
| `../roman/references/scene-et-chapitre.md` | phase 3 : construire et écrire les scènes |
| `../roman/references/genres.md` | nouvelle policière, fantastique, de science-fiction ou historique |
| `../roman/references/manuscrit-et-export.md` | phase 5 : export, normes de présentation |

| Script | Rôle |
|---|---|
| `scripts/verifier_nouvelle.py` | mots et signes ; statut, titre, effet visé ; conformité au règlement (signes et mots minimum et maximum, phrase imposée et sa place, mots imposés, anonymat, titre exigé, date limite) ; contrôles de style du skill roman ; pour un recueil (`--recueil`) : nouvelles manquantes ou hors recueil |
| `scripts/assembler_nouvelle.py` | met en forme une nouvelle (anonyme d'office si le concours l'exige) ou assemble le recueil, puis exporte en .docx ou PDF avec pandoc |

Dépendance : PyYAML. Export : pandoc (et un moteur LaTeX pour le PDF).

## Le fichier d'une nouvelle

```yaml
---
titre: "Le Phare"
statut: premier-jet
effet: "la tendresse qui se révèle dans le geste de la dernière phrase"
personnages: [Rose]            # exclus du contrôle des répétitions
concours: prix-des-embruns     # facultatif : <dossier_concours>/prix-des-embruns.md
---
```

Le corps est de la prose ; les scènes sont séparées par `* * *`. Pas de titre `#` dans le corps.

## Les cinq phases

Trois portes demandent l'accord de l'utilisateur : ne pas continuer sans lui.

### Phase 1 — Idée, effet, contraintes *(validation de l'utilisateur)*

1. Partir de ce que l'auteur apporte : une chute, une image, une situation, une contrainte de concours (`idee-et-effet.md`).
2. Formuler **l'effet visé** en une phrase (ce que le lecteur doit ressentir en refermant le texte) et le noter dans `effet`.
3. Concours ou appel à textes : lire le règlement en entier, créer la fiche dans `<dossier_concours>/` (`concours.md`), signaler à l'auteur les contraintes qui pèsent sur l'idée (longueur, thème, phrase imposée, inédit).
4. Établir ou relire la fiche de voix.

**Porte** : présenter l'idée, l'effet visé, le type de nouvelle et les contraintes ; **attendre l'accord**.

### Phase 2 — Construction

1. Choisir l'entrée (`construction.md`) : **par la chute** (on fixe la fin et on remonte), ou **par l'image** (on part d'une scène et la forme se cherche en écrivant).
2. Esquisser en quelques lignes : situation, tension, bascule, fin ; le point de vue, le temps, la longueur visée.
3. Pour une nouvelle à chute : lister ce que le lecteur doit avoir vu sans le remarquer, et où le placer.

**Porte** : l'esquisse tient en une demi-page et chaque étape sert l'effet.

### Phase 3 — Premier jet *(validation de l'utilisateur)*

Demander le mode à l'auteur s'il ne l'a pas fixé :
- **Claude rédige** : relire la fiche de voix et l'esquisse ; écrire le texte d'un trait, statut `premier-jet`.
- **L'auteur écrit, Claude relit** : relecture sans réécriture (`resserrement.md`, section 4).

Puis lancer `python <dossier-du-skill>/scripts/verifier_nouvelle.py <dossier_nouvelles>/<fichier>.md`.

**Porte** : présenter le premier jet ou la relecture ; **attendre le retour de l'auteur**.

### Phase 4 — Resserrement

1. Relire contre l'effet visé (`resserrement.md`) : couper ce qui ne le sert pas, retravailler l'ouverture, la chute et le titre.
2. Concours : ramener le texte dans les limites du règlement en coupant, jamais en trichant sur la présentation.
3. Relancer le vérificateur jusqu'à zéro bloquant ; passer le statut à `revise`.

### Phase 5 — Version finale *(validation de l'utilisateur)*

1. Présenter la version resserrée, les mesures (mots, signes) et le résultat du vérificateur.
2. **Attendre l'accord** avant de passer `statut: final`.
3. Mettre en forme : `python <dossier-du-skill>/scripts/assembler_nouvelle.py <fichier> [--docx] [--pdf]` (anonyme d'office si le concours l'exige ; arrêt si le règlement est illisible ; `--signe` ou `--anonyme` pour forcer). Recueil : `--recueil` (`recueil.md`).
4. Concours : rappeler à l'auteur les pièces à joindre (fiche d'identité séparée, attestation d'inédit…) et la date limite. Ne rien envoyer soi-même. Ne pas faire de commit git sans demande explicite.

## Modes de travail

| Demande | Phases | Livrable |
|---|---|---|
| Écrire une nouvelle | 1 → 5 | nouvelle finale + mesures |
| Trouver une idée ou une chute | 1 (et 2 si demandé) | pistes, effet visé, esquisse |
| Relire une nouvelle de l'auteur | 3 (mode relecture) + 4 | relecture, propositions de coupes |
| Vérifier la conformité à un concours | fiche de règlement + vérificateur | rapport de conformité, coupes proposées si dépassement |
| Adapter un texte à un autre concours | 1 (contraintes) + 4 + 5 | version conforme ; l'original est conservé |
| Organiser un recueil | `recueil.md` + `--recueil` | ordre, fil rouge, manuscrit du recueil |

## Jamais

- Imposer l'idée, la chute ou l'effet : proposer, l'auteur choisit.
- Réécrire le texte de l'auteur sans qu'il le demande.
- Reprendre le texte ou l'intrigue d'une nouvelle existante, ou en écrire une imitation présentée comme originale.
- Envoyer à un concours un texte qui ne respecte pas le règlement, ou contourner une limite par la mise en page.
- Laisser un nom ou un indice d'identité dans un texte destiné à un concours anonyme.
- Proposer à un concours qui exige un inédit un texte déjà publié, sans le signaler à l'auteur.
- Passer au statut `final` sans l'accord de l'utilisateur.
