# Concours et appels à textes

Un concours se perd souvent sur le règlement avant de se perdre sur le texte : trop long, phrase imposée oubliée, nom de l'auteur dans le fichier, envoi après la date. Ce skill transforme le règlement en fiche que le script vérifie.

## 1. Lire le règlement

Lire le règlement **en entier**, sur le site de l'organisateur, et relever :
- la longueur (en signes espaces comprises, en mots, en pages ? minimum et maximum) ;
- le thème, la phrase ou les mots imposés, et leur place (première phrase, dernière, libre) ;
- l'anonymat et la façon de transmettre l'identité (fiche séparée, enveloppe) ;
- l'exigence d'inédit (jamais publié, ni en revue, ni en ligne, ni primé ailleurs) ;
- le format du fichier (police, interligne, .docx ou PDF, nom du fichier) ;
- la date limite, les frais, les droits cédés en cas de prix ;
- les catégories (âge, langue, région).

En cas de doute, la lecture la plus stricte l'emporte, et on suggère à l'auteur d'interroger l'organisateur.

## 2. La fiche de règlement

Un fichier par concours dans `<dossier_concours>/<identifiant>.md`. Le frontmatter est lu par le script ; le corps reprend en clair le reste du règlement.

```yaml
---
nom: "Prix des Embruns 2027"
signes_max: 12000          # espaces comprises
signes_min: 1000
mots_max:                  # si le règlement compte en mots
mots_min:
theme: "le retour"         # pour mémoire, non vérifié
phrase_imposee: "Pour ceux qui reviennent"
phrase_position: libre     # libre, debut (ouvre le texte) ou fin (le clôt)
mots_imposes: [phare]
anonymat: true
titre_obligatoire: true
date_limite: "2027-03-31"
---
```

Toutes les clés sont facultatives ; une clé inconnue ou mal typée (`anonymat: "non"` au lieu de `false`, minimum supérieur au maximum) rend la fiche invalide (bloquant), pour éviter qu'une faute de frappe désactive un contrôle. L'identifiant est un nom simple, sans chemin. La nouvelle s'y rattache par `concours: <identifiant>` dans son frontmatter.

## 3. Ce que le script vérifie

| Code | Contrôle |
|---|---|
| `CONCOURS_INCONNU`, `REGLEMENT_INVALIDE` | la fiche existe et elle est bien formée |
| `SIGNES_MAX`, `SIGNES_MIN`, `MOTS_MAX`, `MOTS_MIN` | la longueur (le message dit combien couper) |
| `PHRASE_IMPOSEE`, `PHRASE_POSITION` | la phrase imposée figure, à la place exigée (comparaison sans casse, accents ni ponctuation) |
| `MOT_IMPOSE` | chaque mot imposé figure, au singulier ou au pluriel, y compris après une élision (« l'eau ») ; une expression (« mer vide », « grand-mère ») se cherche telle quelle |
| `ANONYMAT` | ni le nom complet de l'auteur ni son nom de famille ne figurent dans le texte (en mots entiers) |
| `TITRE_ABSENT` | un titre, s'il est exigé |
| `DATE_LIMITE` | avertissement si la date est passée |

**Les signes** sont comptés espaces comprises, et **les mots** séparés par des espaces (« grand-mère » compte pour un mot), sans le titre repris en tête, le balisage Markdown, les commentaires ni les marques de paragraphe, comme le font les traitements de texte. Le compte reste une estimation : vérifier dans le traitement de texte de l'organisateur quand on est à moins de 2 % de la limite.

## 4. Ce que le script ne vérifie pas

- Le respect du thème, l'inédit, le format du fichier, les pièces à joindre : à vérifier avec l'auteur avant l'envoi.
- Les indices d'identité autres que le nom : une dédicace, un lieu trop personnel, les **métadonnées du fichier** (auteur du document .docx ou PDF). Avant l'envoi, effacer l'auteur dans les propriétés du document.

## 5. Mettre en forme pour l'envoi

`assembler_nouvelle.py <fichier>` produit un texte **sans nom d'auteur** quand le règlement exige l'anonymat (`--signe` pour forcer la signature). Si la fiche de règlement est introuvable ou mal formée, il s'arrête plutôt que de signer par mégarde : corriger la fiche, ou forcer avec `--anonyme` ou `--signe`. L'export .docx ou PDF passe par pandoc (`../roman/references/manuscrit-et-export.md`). L'envoi lui-même est fait par l'auteur.

## 6. Un texte, plusieurs concours

Adapter un texte à un autre règlement crée une **nouvelle version** (un autre fichier, rattaché à l'autre fiche) ; l'original reste intact. Un texte primé ou publié n'est plus inédit : le noter dans son frontmatter (champ libre `publication`) pour ne pas le proposer à tort.
