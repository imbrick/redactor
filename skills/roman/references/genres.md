# Les genres

Le genre est un contrat avec le lecteur : il annonce ce qu'il trouvera. On peut jouer avec le contrat, pas l'ignorer. La valeur de la clé `genre` de `redactor.json` est entre parenthèses.

## 1. Littérature générale (`litterature`)

- **Ce que le lecteur attend** : des personnages complexes, une voix, une vérité sur l'expérience humaine ; l'intrigue peut être ténue, le changement intérieur ne l'est pas.
- **Ce qui porte le livre** : la voix (`voix-et-style.md`), le sous-texte, le détail juste, le thème qui se révèle sans être énoncé.
- **Pièges** : l'introspection qui tourne en rond, faute de scènes où le personnage agit ; le style qui se regarde écrire ; la fin qui refuse de conclure par principe plutôt que par nécessité.

## 2. Polar et thriller (`polar`)

**Ce que le lecteur attend** : une énigme ou une menace, une tension constante, une résolution loyale.

| | Polar (énigme) | Thriller (menace) |
|---|---|---|
| Question | qui, comment, pourquoi ? | va-t-il s'en sortir ? |
| Le lecteur sait | moins que l'enquêteur, ou autant | souvent plus que le héros |
| Moteur | les indices et les déductions | le compte à rebours et le danger |

**Le contrat de loyauté** : le lecteur doit avoir vu, avant la révélation, tout ce qui permet de la comprendre. Les indices sont posés, parfois cachés au milieu d'autres détails, jamais retenus.

**Le registre des indices** (`bible/indices.md`), lu par le script :

```markdown
## Indices

| # | Indice | Posé | Exploité |
|---|---|---|---|
| I1 | Le casque fendu près du corps | 1 | 3 |

## Révélations

| # | Révélation | Chapitre | Préparée par |
|---|---|---|---|
| R1 | Morel était dans la cabine | 3 | I1, I2, I3 |
```

Les colonnes « Posé », « Exploité » et « Chapitre » portent des numéros de chapitre ; « Préparée par » liste des numéros d'indices.

| Code | Signal |
|---|---|
| `INDICE_NON_EXPLOITE` | un indice posé n'est jamais exploité (fusil de Tchekhov) |
| `INDICE_ORDRE` (bloquant) | un indice est exploité avant d'être posé |
| `REVELATION_NON_PREPAREE` | une révélation qu'aucun indice ne prépare |
| `REVELATION_TROP_TOT` (bloquant) | une révélation préparée par un indice posé au même chapitre ou après |
| `INDICE_INCONNU`, `INDICE_CHAPITRE` | renvoi à un indice ou un chapitre qui n'existe pas |
| `INDICES_ABSENTS` | polar sans registre |

**Autres outils** : les fausses pistes (crédibles, et expliquées à la fin) ; la ligne de temps du crime, établie avant d'écrire, séparée de l'ordre de la narration ; l'alibi de chaque suspect.

**Pièges** : le coupable qu'on n'a jamais vu ; la résolution par aveu ou par hasard ; l'enquêteur qui trouve tout sans effort ; la procédure (police, justice) invraisemblable — la vérifier quand le roman se veut réaliste.

## 3. Imaginaire (`imaginaire`)

- **Ce que le lecteur attend** : un monde cohérent qui fait naître des histoires impossibles ailleurs ; la fantasy, la science-fiction et le fantastique ont chacun leurs codes.
- **La règle d'or** : les règles du monde (magie, technologie, société) sont fixées avant de servir à résoudre un problème. Une solution magique non annoncée est une triche, comme un indice caché en polar.
- **La bible du monde** (`bible/monde.md`, entrées `## `) : géographie, histoire, peuples, pouvoirs et leurs **limites** et leurs **coûts**, technologie, économie, religions. `bible/lexique.md` : chaque terme inventé, avec une graphie fixe (le script compare les noms des chapitres aux entrées de la bible et signale les variantes).
- **L'exposition** : le monde se découvre par le regard d'un personnage et par ses usages, pas par des chapitres d'encyclopédie. Le lecteur accepte de ne pas tout comprendre tout de suite.
- **Pièges** : le lexique inventé en avalanche dès la première page ; le monde riche et l'intrigue pauvre ; le héros élu qui n'a rien à décider.

## 4. Roman historique (`historique`)

- **Ce que le lecteur attend** : une époque rendue vivante et exacte, et une histoire qui n'aurait pu se passer qu'à ce moment-là.
- **Documenter** avec la méthode du skill encyclopedia : `../encyclopedia/references/methode-historique.md` (critique des sources, datation) et `../encyclopedia/references/preuves-et-attribution.md`. Noter les sources dans la bible (`bible/sources.md`, libre).
- **Séparer l'attesté de l'inventé** : dans la bible, chaque personnage et chaque événement réel porte une mention `- statut : historique` ou `- statut : fictif`. Les personnages historiques ne font pas, dans le roman, ce qui contredit ce qu'on sait d'eux sans que l'auteur l'assume (et le signale dans une note de l'auteur).
- **La langue** : éviter les anachronismes de vocabulaire et de mentalité, sans pasticher une langue ancienne illisible.
- **Pièges** : l'érudition qui écrase le récit ; les personnages qui pensent comme des contemporains ; les dates fausses. `verifier_roman.py` contrôle la cohérence des dates de naissance et de mort des personnages de point de vue ; vérifier les autres dates contre la chronologie.

## 5. Mélanger les genres

Un polar historique, une fantasy intime, un thriller de science-fiction : le genre déclaré dans `redactor.json` décide des contrôles du script (registre d'indices exigé pour `polar`) ; les exigences des autres genres se suivent quand même, avec les fiches correspondantes.
