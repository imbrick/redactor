# Manuscrit et export

## 1. Assembler

```bash
python <dossier-du-skill>/scripts/assembler_manuscrit.py            # manuscrit Markdown
python <dossier-du-skill>/scripts/assembler_manuscrit.py --docx     # + .docx
python <dossier-du-skill>/scripts/assembler_manuscrit.py --pdf      # + PDF
```

Le script :
- prend les chapitres dans l'ordre du plan (à défaut, dans l'ordre de leur numéro) ;
- signale les chapitres prévus mais pas écrits, et ceux qui n'ont pas le dernier statut (`final`) ;
- retire les frontmatters, donne à chaque chapitre un titre selon `titre_chapitre` (par défaut « Chapitre 3 — La cabine » ; « {numero}. {titre} », « {titre} » seul… sont possibles) ;
- uniformise les sauts de scène en `* * *` ;
- écrit `<dossier_manuscrit>/<slug du titre>.md` avec un en-tête (titre, auteur, langue).

## 2. Exporter

L'export passe par [pandoc](https://pandoc.org/installing.html), à installer une fois :
- **.docx** : pandoc seul. C'est le format que demandent la plupart des éditeurs et des bêta-lecteurs, et il s'ouvre dans tout traitement de texte pour la mise en forme finale.
- **PDF** : pandoc et un moteur LaTeX (MiKTeX ou TeX Live). À défaut, exporter en .docx puis en PDF depuis le traitement de texte.

Sans pandoc, le manuscrit Markdown est produit et le script l'indique (code de sortie 2) : on peut l'ouvrir et l'exporter à la main.

Pour une mise en page précise (police, marges, interligne), pandoc accepte un document de référence : `pandoc manuscrit.md -o manuscrit.docx --reference-doc=modele.docx`, où `modele.docx` porte les styles voulus.

## 3. Normes de présentation d'un manuscrit

Les usages varient selon les éditeurs ; les consignes de l'éditeur visé priment. Repères courants pour un envoi :
- police lisible à empattement ou non, 12 points ;
- interligne 1,5 ou double, marges généreuses, texte aligné à gauche ou justifié ;
- pages numérotées ; chaque chapitre commence sur une nouvelle page ;
- première page : titre, nom d'auteur, coordonnées, genre et longueur.

## 4. Repères de longueur

La longueur se mesure en mots (le script) ou en signes, espaces comprises (les éditeurs français) : compter environ 6 signes par mot en français. Ordres de grandeur courants, très variables selon les collections :

| Genre | Mots |
|---|---|
| Roman de littérature générale | 50 000 à 100 000 |
| Polar, thriller | 60 000 à 110 000 |
| Fantasy, science-fiction | 80 000 à 150 000 et plus |
| Roman historique | 80 000 à 150 000 |
| Roman jeunesse et ado | 25 000 à 80 000 |

Ces chiffres sont des repères : la collection visée et l'histoire décident. L'objectif se fixe dans `objectif_mots` et le vérificateur affiche où en est le roman.
