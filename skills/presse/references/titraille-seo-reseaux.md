# Titraille, SEO et réseaux

La titraille fait lire, le SEO fait trouver, les réseaux font venir. Les trois obéissent à la même règle : **ne rien promettre que le texte ne tienne**.

## 1. Le frontmatter du papier

```yaml
---
format: actualite            # breve, actualite, enquete, reportage, portrait, entretien,
                             # analyse, editorial, tribune, chronique
rubrique: Économie           # dans la liste « rubriques » de redactor.json si elle existe
surtitre: "Transport maritime"
titre: "…"
chapo: "…"                   # facultatif pour une brève
slug: port-belcourt-reouverture
signature: "Jeanne Exemple"
date: "2026-11-03"           # entre guillemets
statut: brouillon            # brouillon → relecture → valide (valide : accord de l'utilisateur)
seo_titre: "…"
seo_description: "…"
mots_cles: [Belcourt, port, grève]
exergues:
  - "phrase reprise mot pour mot du corps"
reseaux:
  x: "…"
  facebook: "…"
  linkedin: "…"
  newsletter: "…"            # objet du courriel
presentation_auteur: "…"     # tribune : qui est l'auteur, à quel titre, liens d'intérêts
---
```

Le corps ne contient **pas** de titre `#`, car le CMS l'affiche à partir du frontmatter. Les intertitres sont en `##` et les images en `![légende. Photo : auteur](fichier)`.

## 2. La titraille

| Élément | Rôle | Repère |
|---|---|---|
| **Surtitre** | situe le sujet ou le genre | 2 à 5 mots : « Transport maritime », « Enquête », « Tribune » |
| **Titre** | dit l'essentiel ou donne envie de lire | 90 signes au plus ; un verbe conjugué de préférence |
| **Chapô** | résume et donne envie de lire la suite | 15 à 60 mots ; complète le titre sans le répéter |
| **Intertitres** | relancent et structurent | tous les 250 à 400 mots ; informatifs plutôt que décoratifs |
| **Exergue** | met en avant une phrase forte | reprise **mot pour mot** du corps (le script bloque sinon) |
| **Légende** | dit ce que montre l'image | qui, quoi, où, quand, crédit |

**Le titre** :
- **informatif** (« Le port de Belcourt rouvre après trois semaines de grève ») pour l'actualité ;
- **incitatif** (« À Belcourt, la nuit où les grues se sont tues ») pour le magazine, à condition que le chapô informe ;
- jamais de question à laquelle le papier répond non ;
- jamais de guillemets autour d'un propos que personne n'a tenu ;
- jamais de conditionnel pour habiller une rumeur.

**Le chapô** répond aux questions que le titre laisse ouvertes. Pour l'actualité, il dit qui, quoi, quand et où. Pour le magazine, il dit l'enjeu et ce que le papier raconte.

## 3. Le SEO

| Champ | Repère | Règle |
|---|---|---|
| `seo_titre` | 60 signes au plus | les mots que le lecteur tape, au début ; peut différer du titre éditorial |
| `seo_description` | 70 à 160 signes | une phrase complète qui résume le fait principal |
| `slug` | minuscules, chiffres, tirets | court, stable, sans date ni mots vides inutiles |
| `mots_cles` | 3 à 6 | noms propres et thèmes du papier, pas de bourrage |

Ce qui fait vraiment trouver un papier :
- un sujet traité à fond ;
- des noms propres complets ;
- des intertitres informatifs ;
- des liens vers les sources et les papiers précédents du titre.

Le SEO ne justifie jamais une promesse que le texte ne tient pas.

## 4. Les réseaux

Chaque réseau a son lecteur. Le message renvoie au papier sans le trahir.

| Réseau | Registre | Repère |
|---|---|---|
| `x` | le fait, vite | 280 signes au plus, lien compris selon la plateforme (le script avertit au-delà de 280) |
| `facebook` | le fait et ce qu'il change pour les gens | 1 à 3 phrases |
| `linkedin` | l'enjeu professionnel, économique, institutionnel | 1 à 3 phrases, ton sobre |
| `newsletter` | objet du courriel | 40 à 60 signes, le fait ou l'enjeu |

Règles :
- aucune information qui ne soit pas dans le papier ;
- aucune exagération ;
- aucune citation tronquée qui change le sens ;
- pas de « vous ne devinerez jamais » ni de suspense artificiel ;
- un papier d'opinion est présenté comme tel (« Tribune », « Édito ») ;
- un fait attribué dans le papier reste attribué dans le message.

## 5. Contrôle de cohérence

Relire dans cet ordre : titre, chapô, intertitres, exergues, légendes, `seo_titre`, `seo_description`, chaque message réseau. Chaque élément doit être **vrai d'après le corps**, au même niveau de certitude. Un « selon le syndicat » dans le texte reste un « selon le syndicat » partout.
