# Redactor

Plugin [Claude Code](https://claude.com/claude-code) d'écriture de contenu, de l'enquête à la publication.

| Skill | Genre | État |
|---|---|---|
| `redactor:encyclopedia` | articles encyclopédiques et wikis | disponible |
| `redactor:presse` | presse quotidienne et magazine | disponible |
| `redactor:roman` | romans | disponible |
| `redactor:nouvelle` | nouvelles, concours, recueils | disponible |
| `redactor:manga` | manga | prévu |

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

Exemple complet : [`exemples/redactor.json`](exemples/redactor.json).

## `redactor:presse`

Le skill organise le travail d'un journaliste en six phases. Trois d'entre elles attendent la validation de l'utilisateur : l'angle, le plan et la livraison.

1. angle (sujet, angle, format, longueur, risques) ;
2. enquête (documents, entretiens, terrain, dossier de vérification tenu au fil de l'eau) ;
3. plan (attaque et intertitres) ;
4. rédaction (corps, titraille complète) ;
5. vérification (règle des deux sources, niveaux de preuve P0 à P4, contradictoire, relecture adversariale, script) ;
6. livraison au CMS (titraille, corps, champs SEO, messages pour X, Facebook, LinkedIn et la newsletter).

Il couvre les brèves et l'actualité, l'enquête, le reportage, le portrait, l'entretien, l'analyse et l'opinion (éditorial, tribune, chronique). Sa déontologie part de la charte de Munich, que chaque titre complète par sa propre charte.

Chaque papier a un **dossier de vérification**, un document interne jamais publié. Pour chaque fait, il donne les sources, la sensibilité et le niveau de preuve. Il note aussi le statut de chaque citation (on, off, relue), les sources anonymes et la date à laquelle chaque mis en cause a été sollicité.

`verifier_papier.py` contrôle le papier et son dossier avant livraison. Il bloque dans ces cas :
- une citation du texte absente du dossier ;
- un propos « off » publié ;
- un fait en P0 ;
- un fait sensible à source unique non attribué ;
- un mis en cause non sollicité ;
- une exergue qui n'est pas dans le texte.

Il avertit aussi sur les longueurs (corps, chapô, titre et champs SEO), les dates relatives et les crédits photo manquants. `verifier_references.py`, le script du skill encyclopedia, vérifie les rapports et études cités au dossier.

On l'appelle en langage naturel (« trouve un angle sur la grève au port », « prépare l'interview du maire », « vérifie ce papier ») ou avec `/redactor:presse`.

### Configurer un titre : section `presse` de `redactor.json`

| Clé | Rôle | Défaut |
|---|---|---|
| `charte` | charte de la rédaction (prime sur la `charte` commune) | charte commune, sinon aucune |
| `dossier_papiers` | dossier des papiers | `papiers` |
| `dossier_verification` | dossier des dossiers de vérification | `verification` |
| `rubriques` | rubriques admises | libre |
| `reseaux` | messages à produire | `["x", "facebook", "linkedin", "newsletter"]` |
| `signature` | signature par défaut | aucune |
| `longueurs` | fourchettes de mots par format, `{ "actualite": [300, 800] }` | voir `skills/presse/references/formats.md` |

Exemple complet, avec un papier fictif et son dossier de vérification : [`exemples/presse/`](exemples/presse/). Un même `redactor.json` peut porter plusieurs sections : chaque skill lit la sienne et ignore celles des autres.

## `redactor:roman`

Le skill accompagne l'écriture d'un roman avec la méthode de l'entre-deux. On fixe quelques jalons (le début, les grands tournants, la fin visée), et le reste se découvre en écrivant. Le travail suit six phases ; quatre d'entre elles attendent la validation de l'auteur :

1. prémisse, personnages et fiche de voix *(validation)* ;
2. monde et bible : personnages, lieux, chronologie, indices du polar, règles d'un monde imaginaire, sources d'un roman historique ;
3. jalons et plan *(validation)* ;
4. écriture, chapitre par chapitre *(validation à chaque chapitre)*. Pour chaque chapitre, l'auteur choisit : Claude le rédige dans sa voix, ou l'auteur l'écrit et Claude le relit ;
5. révision d'ensemble en cinq passes, avec un rapport de révision *(validation)* ;
6. manuscrit assemblé, export .docx ou PDF, dossier d'éditeur (pitch, résumé, synopsis, quatrième de couverture).

Il sert la littérature générale, le polar et le thriller, l'imaginaire et le roman historique.

Deux scripts l'accompagnent :

- `verifier_roman.py` contrôle quatre choses :
  - l'avancement : mots par chapitre, total par rapport à l'objectif, chapitres à écrire ;
  - la continuité : noms absents de la bible ou mal orthographiés, point de vue d'un personnage pas encore né ou déjà mort ;
  - le style : répétitions rapprochées, adverbes en -ment, tics déclarés, dialogues au trait d'union ;
  - pour le polar, les indices : indice jamais exploité, révélation non préparée ou préparée trop tard.
- `assembler_manuscrit.py` assemble les chapitres dans l'ordre du plan, puis les exporte en .docx ou en PDF avec [pandoc](https://pandoc.org) s'il est installé.

On l'appelle en langage naturel (« aide-moi à construire mon roman », « écris le chapitre 3 », « vérifie la continuité ») ou avec `/redactor:roman`.

### Configurer un roman : section `roman` de `redactor.json`

| Clé | Rôle | Défaut |
|---|---|---|
| `charte` | fiche de voix de l'auteur ou charte de collection | charte commune, sinon aucune |
| `titre`, `auteur` | titre et auteur du manuscrit | nom du projet ; aucun |
| `genre` | `litterature`, `polar`, `imaginaire` ou `historique` | `litterature` |
| `dossier_chapitres` | un fichier Markdown par chapitre | `chapitres` |
| `plan` | jalons et tableau des chapitres | `plan.md` |
| `dossier_bible` | personnages, lieux, chronologie, indices | `bible` |
| `dossier_manuscrit` | manuscrit assemblé et exports | `manuscrit` |
| `objectif_mots` | longueur visée | aucun |
| `tics` | mots ou tournures à surveiller | aucun |
| `noms_ignores` | mots à majuscule à ne pas signaler comme absents de la bible | aucun |
| `statuts` | étapes d'un chapitre ; la dernière vaut « fini » | `["plan", "brouillon", "relu", "final"]` |
| `titre_chapitre` | titre des chapitres dans le manuscrit | `Chapitre {numero} — {titre}` |

Exemple complet, avec un polar fictif (plan, bible, registre d'indices, deux chapitres, fiche de voix) : [`exemples/roman/`](exemples/roman/).

## `redactor:nouvelle`

Une nouvelle vise un effet, et tout dans le texte y concourt. Le skill suit cinq phases ; trois d'entre elles attendent la validation de l'auteur :

1. idée, effet visé et contraintes *(validation)* ;
2. construction, en partant de la chute ou d'une image ;
3. premier jet, rédigé par Claude ou par l'auteur *(validation)* ;
4. resserrement ;
5. version finale et mise en forme *(validation)*.

Il sert trois usages :

- la nouvelle isolée ;
- le concours ou l'appel à textes : le règlement devient une fiche dans `concours/`, que le script vérifie ;
- le recueil : ordre, fil rouge et manuscrit assemblé.

Il réutilise la fiche de voix, la méthode de la scène, les genres et les contrôles de style du skill roman.

Deux scripts l'accompagnent :

- `verifier_nouvelle.py` mesure les mots et les signes, espaces comprises. Il contrôle aussi la conformité au règlement :
  - signes et mots minimum et maximum ;
  - phrase imposée et sa place ;
  - mots imposés ;
  - anonymat, titre exigé, date limite.

  Il applique les contrôles de style du roman et, avec `--recueil`, vérifie tout le recueil.
- `assembler_nouvelle.py` met en forme une nouvelle ou assemble le recueil, puis l'exporte en .docx ou en PDF avec pandoc. Quand le concours exige l'anonymat, le texte sort sans nom d'auteur.

On l'appelle en langage naturel (« écris une nouvelle sur… », « vérifie que ma nouvelle respecte le règlement », « organise mon recueil ») ou avec `/redactor:nouvelle`.

### Configurer : section `nouvelle` de `redactor.json`

| Clé | Rôle | Défaut |
|---|---|---|
| `charte` | fiche de voix de l'auteur | charte commune, sinon aucune |
| `auteur` | nom d'auteur (manuscrit, contrôle d'anonymat) | aucun |
| `titre_recueil` | titre du recueil | nom du projet |
| `dossier_nouvelles` | un fichier Markdown par nouvelle | `nouvelles` |
| `dossier_concours` | une fiche de règlement par concours | `concours` |
| `recueil` | ordre des nouvelles du recueil | `recueil.md` |
| `dossier_manuscrit` | textes mis en forme et exports | `manuscrit` |
| `tics` | mots ou tournures à surveiller | aucun |
| `statuts` | étapes d'une nouvelle ; la dernière vaut « fini » | `["idee", "premier-jet", "revise", "final"]` |

Exemple complet, avec deux nouvelles, un recueil et le règlement d'un concours fictif : [`exemples/nouvelle/`](exemples/nouvelle/).

## Développement

Tester le plugin en local sans le publier :

```
/plugin marketplace add C:/chemin/vers/redactor
/plugin install redactor@redactor
```

Lancer les tests, skill par skill :

```bash
(cd skills/encyclopedia/scripts && python -m unittest discover)
(cd skills/presse/scripts && python -m unittest discover)
(cd skills/roman/scripts && python -m unittest discover)
(cd skills/nouvelle/scripts && python -m unittest discover)
```

## Licence

MIT, voir [LICENSE](LICENSE).
