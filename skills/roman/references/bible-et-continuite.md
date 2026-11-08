# Bible et continuité

La bible est la mémoire du roman : tout ce qui a été établi sur les personnages, les lieux, le temps et les règles du monde. Elle évite qu'un personnage change d'yeux entre deux chapitres ou qu'un mort reprenne la parole. `verifier_roman.py` lit le plan, la bible et les chapitres : garder les formats ci-dessous.

## 1. Organisation du projet

```
redactor.json          section « roman »
voix.md                fiche de voix (déclarée comme charte)
plan.md                jalons et tableau des chapitres
bible/
  personnages.md       une entrée « ## Nom » par personnage
  lieux.md             une entrée « ## Nom » par lieu
  chronologie.md       repères datés (libre)
  indices.md           polar : indices et révélations
  monde.md, lexique.md imaginaire : règles, termes inventés (libre, entrées « ## »)
chapitres/
  01-le-corps.md       un fichier par chapitre
manuscrit/             produit par assembler_manuscrit.py
```

Les noms de dossiers et de fichiers se changent dans `redactor.json`.

## 2. Les entrées de la bible

Chaque fichier de `bible/` (sauf `indices.md`) contient des entrées : un titre `## Nom`, puis des lignes `- clé : valeur`. Le script lit :

| Clé | Rôle |
|---|---|
| `alias` | autres façons de nommer l'entrée, séparées par des virgules (« Mathilde, la commissaire ») |
| `naissance` | année (ou date) de naissance |
| `mort` | année (ou date) de mort |

Toutes les autres clés sont libres (rôle, désir, apparence, voix, relations…) et servent à l'écriture.

```markdown
## Mathilde Arnaud
- alias : Mathilde, la commissaire
- naissance : 1981
- rôle : commissaire à Belcourt, protagoniste
- yeux : gris
```

Tout nom écrit avec une majuscule dans les chapitres est comparé à ces noms, à leurs alias et aux mots qui les composent.

## 3. Le plan et les chapitres

**`plan.md`** contient une section `## Chapitres` avec un tableau. Colonnes lues : `#`, `Titre`, `Fichier`, `Personnages` (séparés par des virgules). Les autres colonnes (PDV, Jalon, Résumé) sont libres. Une section `## Jalons` peut précéder le tableau.

**Chaque chapitre** commence par un frontmatter :

```yaml
---
numero: 2
titre: "L'équipe de nuit"
pdv: "Mathilde Arnaud"      # nom ou alias d'une entrée de la bible
date_recit: "2026-11-02"    # "AAAA-MM-JJ" ou "AAAA-MM" entre guillemets ; une année seule peut s'en passer
statut: brouillon           # plan, brouillon, relu, final (configurable)
---
```

Le corps est de la prose. Les scènes sont séparées par une ligne `* * *`. Pas de titre `#` dans le corps : l'assembleur le crée.

## 4. Ce que le script contrôle

| Code | Signal |
|---|---|
| `PLAN_ABSENT`, `CHAPITRE_HORS_PLAN`, `NUMERO_PLAN` | plan absent, fichier non prévu, numéro différent du plan |
| `PERSONNAGE_INCONNU`, `PDV_INCONNU` | personnage du plan ou point de vue absent de la bible (le nom complet, un alias ou un des mots du nom suffit : « Mathilde » pour « Mathilde Arnaud ») |
| `NOM_VARIANTE` | un nom proche d'un nom de la bible (« Mathide » pour « Mathilde ») |
| `NOM_HORS_BIBLE` | un nom propre qui revient au moins trois fois dans un chapitre sans être dans la bible ; les mots en début de phrase ou de réplique, les jours, les mois et les titres usuels (« Commissaire », « Maman ») ne comptent pas, et la clé `noms_ignores` de `redactor.json` en ajoute d'autres |
| `PDV_CHRONOLOGIE` | le point de vue appartient à un personnage pas encore né ou déjà mort à la date du récit |
| `STATUT_INCONNU`, `DATE_RECIT`, `FRONTMATTER_YAML` | frontmatter mal formé (bloquants) |
| style et indices | `voix-et-style.md`, section 4 ; `genres.md`, section 2 |

Le rapport d'avancement donne les mots par chapitre, le total par rapport à `objectif_mots` et les chapitres du plan qui restent à écrire.

## 5. Ce que le script ne voit pas

Les couleurs d'yeux, les liens de parenté, les distances entre lieux, le jour de la semaine d'une date, la saison, les règles du monde : c'est à la relecture de continuité (`revision.md`, passe 4) de les vérifier contre la bible. Tenir la chronologie à jour aide à repérer qu'un personnage ne peut pas être à deux endroits le même soir.

## 6. Tenir la bible à jour

Après chaque chapitre, ajouter ce qu'il a établi : un nouveau personnage (même secondaire, s'il revient), un lieu, une date, un détail physique, un indice. Une information qui contredit la bible se tranche avec l'auteur : on corrige le chapitre ou on corrige la bible, jamais aucun des deux.
