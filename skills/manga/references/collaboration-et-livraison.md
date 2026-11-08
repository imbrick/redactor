# Collaboration et livraison

## 1. Scénariste et dessinateur

- **Le script donne l'intention, le dessinateur la mise en scène** : le scénariste dit ce qui doit être compris et ressenti ; le dessinateur choisit les angles et la composition, et propose des changements.
- **Le dessinateur fait le name** (le storyboard dessiné) à partir du script ; le scénariste le relit pour vérifier que l'histoire se lit, pas pour imposer ses cadrages.
- **Les notes pour le dessinateur** décrivent l'effet voulu (« on doit sentir qu'elle est minuscule face au phare »), jamais le style d'un artiste existant à imiter.
- **Les changements** décidés sur le name sont reportés dans le script, pour que le lettrage et les chapitres suivants restent justes.

## 2. L'auteur complet

Le script textuel sert de **name écrit** : il fixe le découpage, les dialogues et le rythme avant de dessiner. Descriptions brèves ; l'essentiel est la répartition en pages et en cases, et la place des temps forts. Le script passe au statut `name` quand le storyboard dessiné est fait, `final` quand les pages le sont.

## 3. Assembler le script

```bash
python <dossier-du-skill>/scripts/assembler_script.py            # script complet
python <dossier-du-skill>/scripts/assembler_script.py --lettrage # + feuille de lettrage
python <dossier-du-skill>/scripts/assembler_script.py --docx     # + export .docx (pandoc)
```

- **Script** : `<dossier_manuscrit>/<slug>-script.md`, chapitres dans l'ordre du plan, crédits (scénariste, dessinateur) en tête. Les chapitres prévus mais pas écrits, et ceux qui ne sont pas dans le plan, sont signalés.
- **Feuille de lettrage** : `<slug>-lettrage.md`, un tableau par chapitre avec page, case, locuteur, nature (dialogue, pensée, off, narration, onomatopée) et texte de chaque bulle. Le lettreur y copie les textes sans les ressaisir.

## 4. Le dossier de présentation

Pour un éditeur, un magazine ou un concours :
- **pitch** et **synopsis** de la série ou du one-shot (`../roman/references/dossier-editeur.md`) ;
- **fiches des personnages principaux**, avec leurs dessins de recherche si l'auteur les a ;
- **les premières pages** : script et, si possible, pages dessinées ou name ;
- pour une série, le plan du premier volume.

Les consignes de l'éditeur ou du concours priment (nombre de pages, format des fichiers, sens de lecture). L'envoi est fait par l'auteur.
