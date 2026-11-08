# Le recueil

Un recueil n'est pas une pile de nouvelles : c'est un livre, avec une ouverture, un parcours et une fin. Les textes se répondent, se relancent, se contrastent.

## 1. Choisir

- Partir de toutes les nouvelles disponibles et chercher ce qui les relie : un lieu, un thème, un personnage récurrent, une forme, une époque, une saison.
- Écarter les textes qui ne parlent pas avec les autres, même bons : ils trouveront un autre livre.
- Viser un ensemble cohérent en longueur ; un recueil courant compte de 8 à 20 nouvelles, entre 30 000 et 60 000 mots, selon l'éditeur.

## 2. Ordonner

- **L'ouverture** : une nouvelle qui donne le ton et la promesse du livre, souvent parmi les plus fortes.
- **La clôture** : celle qui laisse l'impression finale ; elle répond à l'ouverture.
- **Le milieu** : alterner les longueurs, les tons, les points de vue ; éviter deux chutes du même type à la suite.
- **Les échos** : un objet, un nom, une phrase qui revient d'un texte à l'autre et tisse le fil rouge.

## 3. Le fichier `recueil.md`

Section `## Nouvelles` avec un tableau ; colonnes lues par le script : `#`, `Titre`, `Fichier`. Les autres (effet, rôle dans le recueil, longueur) sont libres et servent à penser l'ordre.

```markdown
# Recueil — Marées

> Fil rouge : ce que la mer laisse à ceux qui restent sur la côte.

## Nouvelles

| # | Titre | Fichier | Effet | Rôle dans le recueil |
|---|---|---|---|---|
| 1 | Le Phare | le-phare.md | tendresse révélée par un geste | ouverture : la transmission |
| 2 | La Digue | la-digue.md | inquiétude retournée en apaisement | clôture : ce qui tient |
```

## 4. Vérifier et assembler

```bash
python <dossier-du-skill>/scripts/verifier_nouvelle.py --recueil
python <dossier-du-skill>/scripts/assembler_nouvelle.py --recueil [--docx] [--pdf]
```

Le vérificateur contrôle chaque nouvelle, signale celles qui manquent ou qui ne sont pas dans le recueil, et donne les mots et les signes de chaque texte et du total. L'assembleur produit le manuscrit du recueil, `recueil-<slug du titre>.md` (il n'écrase donc jamais une nouvelle du même titre), titré `titre_recueil`, chaque nouvelle sous son titre ; `--anonyme` le produit sans nom d'auteur.

## 5. Le dossier d'éditeur

Pour un recueil, le pitch présente le fil rouge plutôt qu'une intrigue ; le résumé décrit le parcours du livre et quelques nouvelles marquantes. Le reste suit `../roman/references/dossier-editeur.md`.
