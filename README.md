# Redactor

Plugin [Claude Code](https://claude.com/claude-code) d'écriture de contenu, de l'enquête à la publication.

| Skill | Genre | État |
|---|---|---|
| `redactor:encyclopedia` | articles encyclopédiques et wikis | disponible |
| `redactor:roman` | romans | prévu |
| `redactor:nouvelle` | nouvelles | prévu |
| `redactor:manga` | manga | prévu |
| `redactor:journal` | presse quotidienne | prévu |
| `redactor:magazine` | magazine | prévu |

## Installation

Dans Claude Code :

```
/plugin install redactor --marketplace imbrick/redactor
```

Sur une version plus ancienne de Claude Code, en deux commandes :

```
/plugin marketplace add imbrick/redactor
/plugin install redactor@redactor
```

Les scripts de vérification demandent Python 3.10 ou plus et PyYAML (`pip install pyyaml`).

## `redactor:encyclopedia`

Le skill organise le travail d'un rédacteur-enquêteur en cinq phases, chacune fermée par une porte à franchir avant la suivante :

1. cadrage du sujet ;
2. enquête (méthode historique, méthode scientifique, dossier de sources, niveau de preuve de chaque affirmation) ;
3. rédaction (pyramide inversée, attribution, neutralité, débats présentés position par position) ;
4. preuve et relecture ;
5. publication.

Il sait aussi faire un fact-check sans réécrire, réviser un article après fact-check, contrôler tout un corpus et proposer le prochain article à écrire.

Trois scripts Python l'accompagnent :

- `verifier_references.py` vérifie que chaque référence bibliographique existe, dans Crossref, OpenAlex et Open Library ;
- `verifier_article.py` contrôle le frontmatter, les notes, les index, les liens internes et des signaux de preuve (chiffres sans note, affirmations trop fortes, datations mélangées) ;
- `inventaire_sujets.py` agrège les fiches de sujets dérivés et classe ceux qui restent à rédiger.

On l'appelle en langage naturel (« rédige un article sur le lac Kivu », « fais le fact-check de cet article ») ou directement avec `/redactor:encyclopedia`.

### Configurer un projet : `redactor.json`

Le skill ne connaît aucun projet en particulier. Chaque projet décrit ses conventions dans un fichier `redactor.json` placé à sa racine. Toutes les clés sont facultatives ; sans fichier, les valeurs par défaut s'appliquent.

| Clé | Rôle | Défaut |
|---|---|---|
| `projet` | nom du projet | `projet` |
| `charte` | skill ou fichier de la charte éditoriale, qui prime pour la forme | aucune |
| `dossier_articles` | dossier des articles publiés | `articles` |
| `fichiers_index` | index à tenir à jour, relatifs au dossier des articles | aucun |
| `dossier_brainstorm` | fiches de sujets dérivés | aucun |
| `suffixe_brainstorm` | suffixe des fiches | `-articles-derives.md` |
| `dossier_fact_checks` | archive des rapports de fact-check | aucun |
| `journal` | journal des publications | aucun |
| `gabarit_article` | modèle de frontmatter et de structure | aucun |
| `categories` | taxonomie des branches | aucune |
| `champs_obligatoires` | champs exigés dans le frontmatter | `["title", "slug"]` |
| `champs_recommandes` | champs conseillés ; `"a\|b"` : l'un des deux suffit | aucun |
| `champ_titre_court` | titre d'index, d'où se déduit le slug des articles à venir | `title` |
| `champ_statut`, `statuts` | statut de publication et valeurs admises | `publication_status`, `["draft", "review", "published"]` |
| `prefixe_liens` | route des liens internes | `/article/` |

Exemple complet : [`exemples/redactor.json`](exemples/redactor.json). [Kongopedia](https://github.com/imbrick/kongopedia), l'encyclopédie francophone pour laquelle le skill a été écrit, en a un à la racine de son dépôt.

## Développement

Tester le plugin en local sans le publier :

```
/plugin marketplace add C:/chemin/vers/redactor
/plugin install redactor@redactor
```

Lancer les tests :

```bash
cd skills/encyclopedia/scripts
python -m unittest discover
```

## Licence

MIT, voir [LICENSE](LICENSE).
