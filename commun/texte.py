"""Utilitaires de texte communs aux skills du plugin Redactor.

Normalisation pour comparer des textes, décompte de mots, paragraphes de prose,
sections et tableaux Markdown. Bibliothèque standard seulement.
"""

from __future__ import annotations

import re
import unicodedata

VIDE = {"", "—", "–", "-", "?"}

LIGATURES = str.maketrans({"œ": "oe", "Œ": "Oe", "æ": "ae", "Æ": "Ae", "’": "'"})


def normaliser(texte: str) -> str:
    """Minuscules, sans accents ni ligatures, apostrophes et espaces unifiés : pour comparer des textes."""
    texte = unicodedata.normalize("NFKD", texte.translate(LIGATURES))
    texte = "".join(c for c in texte if not unicodedata.combining(c)).lower()
    texte = re.sub(r"[^\w']+", " ", texte)
    return " ".join(texte.split())


def mots(texte: str) -> int:
    """Nombre de mots, sans les adresses des liens et des images."""
    texte = re.sub(r"\]\([^)]*\)", "]", texte)
    texte = re.sub(r"https?://\S+", "", texte)
    return len(re.findall(r"\w+(?:['’]\w+)*", texte))


HORS_PROSE_RE = re.compile(r"^(?:\||!\[|>|[-*+] |\d+\. )")


def paragraphes(corps: str) -> list[str]:
    """Paragraphes de prose : sans intertitres, tableaux, images, citations en bloc ni listes."""
    sans_titres = re.sub(r"^#.*$", "", corps, flags=re.MULTILINE)
    blocs = [b.strip() for b in re.split(r"\n\s*\n", sans_titres)]
    return [b for b in blocs if b and not HORS_PROSE_RE.match(b)]


def sections_markdown(texte: str) -> dict[str, str]:
    """{titre de section ## normalisé : contenu}."""
    morceaux = re.split(r"^## +(.+?)\s*$", texte, flags=re.MULTILINE)
    return {normaliser(morceaux[i]): morceaux[i + 1] for i in range(1, len(morceaux) - 1, 2)}


def _cellules(ligne: str) -> list[str]:
    interieur = re.sub(r"^\||(?<!\\)\|$", "", ligne.strip())
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", interieur)]


def table(contenu: str) -> tuple[list[str], list[dict[str, str]]]:
    """Premier tableau Markdown du contenu : (en-têtes normalisés, lignes non vides).
    L'en-tête « # » garde sa clé « # »."""
    lignes: list[str] = []
    for ligne in contenu.splitlines():
        if ligne.strip().startswith("|"):
            lignes.append(ligne)
        elif lignes:
            break
    if len(lignes) < 2:
        return [], []
    entetes = [c if c == "#" else normaliser(c) for c in _cellules(lignes[0])]
    rangs = [dict(zip(entetes, _cellules(l))) for l in lignes[2:]]
    return entetes, [r for r in rangs if not all(vide(v) for v in r.values())]


def premier_mot(cellule: str | None) -> str:
    """Premier mot normalisé d'une cellule : « Oui (accusation) » → « oui »."""
    decoupe = normaliser(cellule or "").split()
    return decoupe[0] if decoupe else ""


def vide(valeur) -> bool:
    if isinstance(valeur, (list, dict)):
        return not valeur
    return valeur is None or (isinstance(valeur, str) and valeur.strip() in VIDE)
