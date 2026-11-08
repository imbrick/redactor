# Redactor

Skill pour [Claude Code](https://claude.com/claude-code) consacré à l'écriture de contenu, de l'enquête à la publication.

## État actuel

La version actuelle est le skill de rédaction de [Kongopedia](https://github.com/imbrick/kongopedia), une encyclopédie francophone. Elle organise le travail d'un rédacteur-enquêteur en cinq phases :

1. cadrage du sujet ;
2. enquête (méthode historique, méthode scientifique, dossier de sources) ;
3. rédaction (pyramide inversée, attribution, neutralité) ;
4. preuve et relecture ;
5. publication.

Elle fournit aussi trois scripts Python :

- `scripts/verifier_references.py` vérifie les références bibliographiques dans Crossref, OpenAlex et Open Library ;
- `scripts/verifier_article.py` contrôle la forme d'un article et ses signaux de preuve ;
- `scripts/inventaire_sujets.py` dresse la liste des sujets à rédiger.

Les règles de publication (frontmatter, index, chemins `articles/`) sont encore celles de Kongopedia.

## Feuille de route

Redactor doit devenir un skill d'écriture généraliste, décliné par genre :

- `redactor-encyclopedia` : articles encyclopédiques ;
- `redactor-roman` : romans ;
- `redactor-nouvelle` : nouvelles ;
- `redactor-manga` : manga ;
- `redactor-journal` : presse quotidienne ;
- `redactor-magazine` : magazine.

## Installation

Clonez le dépôt dans le dossier des skills de Claude Code :

```bash
git clone https://github.com/imbrick/redactor.git ~/.claude/skills/redactor
```

## Tests

```bash
python -m unittest discover -s scripts
```

## Licence

MIT, voir [LICENSE](LICENSE).
