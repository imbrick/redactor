"""Configuration d'un titre de presse : section « presse » du fichier redactor.json.

Les clés communes à tout le plugin (`projet`, `charte`) se lisent à la racine du fichier ;
les clés propres à la presse dans l'objet `presse`, dont la `charte` prime si elle y figure.
Toutes les clés sont facultatives.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

NOM_FICHIER = "redactor.json"
SECTION = "presse"

# Fourchettes par défaut, en mots, du corps de chaque format. Un titre les ajuste dans
# `longueurs` ; ce sont des repères de rédaction, pas des normes.
LONGUEURS_DEFAUT: Mapping[str, tuple[int, int]] = MappingProxyType({
    "breve": (40, 200),
    "actualite": (250, 900),
    "enquete": (1500, 6000),
    "reportage": (900, 4000),
    "portrait": (800, 3000),
    "entretien": (700, 3500),
    "analyse": (600, 2000),
    "editorial": (300, 800),
    "tribune": (500, 1300),
    "chronique": (350, 1000),
})
FORMATS = tuple(LONGUEURS_DEFAUT)
FORMATS_OPINION = frozenset({"editorial", "tribune", "chronique"})


class ConfigInvalide(ValueError):
    """redactor.json illisible ou mal formé."""


@dataclass(frozen=True)
class ConfigPresse:
    projet: str = "projet"
    charte: str | None = None
    dossier_papiers: str = "papiers"
    dossier_verification: str = "verification"
    rubriques: tuple[str, ...] = ()           # vide : rubrique libre
    reseaux: tuple[str, ...] = ("x", "facebook", "linkedin", "newsletter")
    signature: str | None = None              # signature par défaut
    longueurs: Mapping[str, tuple[int, int]] = field(default_factory=lambda: LONGUEURS_DEFAUT)


DEFAUT = ConfigPresse()
_CHAINES = {"charte", "dossier_papiers", "dossier_verification", "signature"}
_LISTES = {"rubriques", "reseaux"}
_CLES_SECTION = _CHAINES | _LISTES | {"longueurs"}


def _longueurs(valeur) -> Mapping[str, tuple[int, int]]:
    if not isinstance(valeur, dict):
        raise ConfigInvalide("« longueurs » doit être un objet { format: [min, max] }.")
    fusion = dict(LONGUEURS_DEFAUT)
    for fmt, bornes in valeur.items():
        if fmt not in LONGUEURS_DEFAUT:
            raise ConfigInvalide(f"Format inconnu dans « longueurs » : {fmt} (formats : {', '.join(FORMATS)}).")
        ok = (isinstance(bornes, list) and len(bornes) == 2
              and all(isinstance(b, int) and b >= 0 for b in bornes) and bornes[0] <= bornes[1])
        if not ok:
            raise ConfigInvalide(f"« longueurs.{fmt} » doit être [min, max] avec 0 ≤ min ≤ max.")
        fusion[fmt] = (bornes[0], bornes[1])
    return MappingProxyType(fusion)


def depuis_dict(donnees: dict) -> ConfigPresse:
    if not isinstance(donnees, dict):
        raise ConfigInvalide(f"{NOM_FICHIER} doit contenir un objet JSON.")
    section = donnees.get(SECTION, {})
    if not isinstance(section, dict):
        raise ConfigInvalide(f"« {SECTION} » doit être un objet.")
    inconnues = sorted(set(section) - _CLES_SECTION)
    if inconnues:
        raise ConfigInvalide(f"Clé(s) inconnue(s) dans « {SECTION} » : {', '.join(inconnues)}.")

    valeurs: dict = {}
    for cle in ("projet", "charte"):
        if isinstance(donnees.get(cle), str):
            valeurs[cle] = donnees[cle]
    for cle, valeur in section.items():
        if cle in _LISTES:
            if not isinstance(valeur, list) or not all(isinstance(v, str) for v in valeur):
                raise ConfigInvalide(f"« {SECTION}.{cle} » doit être une liste de chaînes.")
            valeurs[cle] = tuple(valeur)
        elif cle == "longueurs":
            valeurs[cle] = _longueurs(valeur)
        elif valeur is not None and not isinstance(valeur, str):
            raise ConfigInvalide(f"« {SECTION}.{cle} » doit être une chaîne.")
        else:
            valeurs[cle] = valeur
    return ConfigPresse(**valeurs)


@lru_cache(maxsize=None)
def _charger(racine: Path) -> ConfigPresse:
    fichier = racine / NOM_FICHIER
    if not fichier.exists():
        return DEFAUT
    try:
        donnees = json.loads(fichier.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as err:
        raise ConfigInvalide(f"{fichier} illisible : {err}") from err
    return depuis_dict(donnees)


def charger(racine: Path) -> ConfigPresse:
    """Configuration presse du projet dont racine est la racine."""
    return _charger(Path(racine).resolve())


def trouver_racine(*departs: Path) -> Path | None:
    """Premier dossier, en remontant depuis chaque départ, qui contient redactor.json ;
    à défaut, premier dossier qui contient un dossier papiers/."""
    for depart in departs:
        for p in [depart, *depart.parents]:
            if (p / NOM_FICHIER).is_file():
                return p
    for depart in departs:
        for p in [depart, *depart.parents]:
            if (p / DEFAUT.dossier_papiers).is_dir():
                return p
    return None

