# Le dossier de vérification

Chaque papier a son dossier de vérification. C'est un document interne, **jamais publié**. Il est écrit dans `<dossier_verification>/<slug>.md`, ouvert dès l'enquête et tenu à jour jusqu'à la livraison. Il sert à trois choses :
- vérifier le papier avant publication ;
- répondre à une contestation après publication ;
- reprendre le sujet plus tard.

`verifier_papier.py` lit ses tableaux. Il faut donc garder **les titres de section et les en-têtes de colonnes exactement** comme dans le modèle :
- une section « Faits », « Citations », « Anonymat des sources » ou « Contradictoire » absente ou renommée est un bloquant ;
- de même pour une colonne lue par le script et absente ou renommée, sinon le contrôle se désactiverait sans prévenir ;
- on peut ajouter d'autres sections et d'autres colonnes, le script les ignore ;
- une ligne entièrement vide est ignorée ;
- un `|` à l'intérieur d'une cellule s'écrit `\|`.

Dans les colonnes *Sensible*, *Niveau*, *Traitement* et *Statut*, seul **le premier mot** compte. On peut le commenter ensuite : « oui (accusation) », « P0 (non vérifié) », « attribué aux armateurs », « off, non citable ».

## 1. Modèle

```markdown
# Dossier de vérification — <titre du papier>

- Papier : `<dossier_papiers>/<slug>.md`
- Rédacteur : …
- Dernière mise à jour : AAAA-MM-JJ

## Faits

| # | Affirmation | Source 1 | Source 2 | Sensible | Niveau | Traitement |
|---|---|---|---|---|---|---|
| F1 | … | document ou personne, date | — | oui / non | P0 à P4 | publié / attribué / retiré |

## Citations

| # | Citation | Locuteur | Recueillie | Statut |
|---|---|---|---|---|
| C1 | texte exact, tel qu'il figure dans le papier | nom, fonction | date, moyen, enregistré ou non | on / contexte / off / embargo … / relue / non relue |

## Anonymat des sources

| Désignation dans le texte | Identité connue de | Raison de l'anonymat |
|---|---|---|
| un cadre de la capitainerie | rédaction en chef | risque de sanction |

## Contradictoire

| Personne ou organisation mise en cause | Sollicitée le | Réponse |
|---|---|---|
| … | AAAA-MM-JJ, moyen | réponse résumée, ou « pas de réponse au AAAA-MM-JJ » |

## Sources

- Documents, rapports, études, bases de données consultés, un par ligne (lus par `verifier_references.py`).

## Points ouverts

- Ce qui reste à confirmer, à actualiser, à surveiller après publication.
```

## 2. Remplir les colonnes

**Faits**
- *Affirmation* : le fait tel qu'il est écrit dans le papier, résumé.
- *Source 1*, *Source 2* : précises et datées. Un tiret « — » signifie qu'il n'y a pas de deuxième source.
- *Sensible* : `oui` pour une accusation, un chiffre clé, une information non publique, une intention prêtée, la vie privée, un bilan humain (`sourcing-et-verification.md`, section 1).
- *Niveau* : P0 à P4 (`sourcing-et-verification.md`, section 2).
- *Traitement* :
  - `publié` : le fait est écrit comme établi ;
  - `attribué` : il est écrit avec sa source unique (« selon… ») ;
  - `retiré` : il a été écarté. On garde la ligne pour la mémoire du dossier.

**Citations**
- *Citation* : le texte exact tel qu'il figure dans le papier, ou plus long.
  - Le script vérifie que chaque citation de cinq mots ou plus du papier se retrouve dans une ligne de cette colonne. Il compare sans tenir compte de la casse, des accents, des ligatures ni de la ponctuation.
  - Il reconnaît les guillemets « », “ ” et " ".
  - Une citation coupée par « […] », par une précision entre crochets ou par « … » est retrouvée morceau par morceau.
- *Statut* : voir `entretiens-et-citations.md`, section 3. Le script bloque une citation `off` retrouvée dans le papier, même partiellement.
- Les propos off se consignent aussi : ils rappellent ce qu'on ne peut pas publier.

**Anonymat des sources**
- On désigne la source par une périphrase, jamais par son nom. Si le dossier fuite, il ne doit identifier personne.
- Le script avertit si le papier contient une formule de source anonyme (« selon une source proche », « sous couvert d'anonymat », « selon nos informations ») alors que ce tableau est vide.

**Contradictoire**
- Une ligne par personne ou organisation mise en cause. *Sollicitée le* est obligatoire : le script bloque une ligne sans date.

## 3. Ce que le script ne vérifie pas

Le script contrôle la cohérence entre le papier et le dossier, pas la vérité du dossier. Il ne sait pas :
- si une source est indépendante ;
- si une citation est fidèle à l'enregistrement ;
- si tous les mis en cause figurent au tableau ;
- si une citation de moins de cinq mots, ou rapportée sans guillemets, est exacte.

Ces points relèvent de la relecture de vérification (`sourcing-et-verification.md`, section 7).
