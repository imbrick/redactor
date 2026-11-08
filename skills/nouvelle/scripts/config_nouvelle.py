"""Configuration des nouvelles : section « nouvelle » du fichier redactor.json.

Toutes les clés sont facultatives. La clé commune `charte` (racine du fichier) peut
désigner la fiche de voix de l'auteur ; `charte` dans la section prime.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

NOM_FICHIER = "redactor.json"
SECTION = "nouvelle"
STATUTS_DEFAUT = ("idee", "premier-jet", "revise", "final")


class ConfigInvalide(ValueError):
    """redactor.json illisible ou mal formé."""


@dataclass(frozen=True)
class ConfigNouvelle:
    projet: str = "projet"
    charte: str | None = None                 # fiche de voix de l'auteur
    auteur: str | None = None
    titre_recueil: str | None = None
    dossier_nouvelles: str = "nouvelles"
    dossier_concours: str = "concours"        # une fiche de règlement par concours ou appel à textes
    recueil: str = "recueil.md"               # ordre des nouvelles d'un recueil
    dossier_manuscrit: str = "manuscrit"
    tics: tuple[str, ...] = ()
    statuts: tuple[str, ...] = STATUTS_DEFAUT


DEFAUT = ConfigNouvelle()
_LISTES = {"tics", "statuts"}
_FACULTATIVES = {"charte", "auteur", "titre_recueil"}
_CLES = _LISTES | _FACULTATIVES | {"dossier_nouvelles", "dossier_concours", "recueil", "dossier_manuscrit"}


def depuis_dict(donnees: dict) -> ConfigNouvelle:
    if not isinstance(donnees, dict):
        raise ConfigInvalide(f"{NOM_FICHIER} doit contenir un objet JSON.")
    section = donnees.get(SECTION, {})
    if not isinstance(section, dict):
        raise ConfigInvalide(f"« {SECTION} » doit être un objet.")
    inconnues = sorted(set(section) - _CLES)
    if inconnues:
        raise ConfigInvalide(f"Clé(s) inconnue(s) dans « {SECTION} » : {', '.join(inconnues)}.")
    valeurs: dict = {}
    for cle in ("projet", "charte"):
        if isinstance(donnees.get(cle), str):
            valeurs[cle] = donnees[cle]
    for cle, valeur in section.items():
        if valeur is None and cle not in _FACULTATIVES:
            raise ConfigInvalide(f"« {SECTION}.{cle} » ne peut pas valoir null (omettre la clé pour le défaut).")
        if cle in _LISTES:
            if not isinstance(valeur, list) or not all(isinstance(v, str) for v in valeur):
                raise ConfigInvalide(f"« {SECTION}.{cle} » doit être une liste de chaînes.")
            valeurs[cle] = tuple(valeur)
        elif valeur is not None and not isinstance(valeur, str):
            raise ConfigInvalide(f"« {SECTION}.{cle} » doit être une chaîne.")
        else:
            valeurs[cle] = valeur
    cfg = ConfigNouvelle(**valeurs)
    if not cfg.statuts:
        raise ConfigInvalide(f"« {SECTION}.statuts » ne peut pas être vide.")
    return cfg


@lru_cache(maxsize=None)
def _charger(racine: Path) -> ConfigNouvelle:
    fichier = racine / NOM_FICHIER
    if not fichier.exists():
        return DEFAUT
    try:
        donnees = json.loads(fichier.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as err:
        raise ConfigInvalide(f"{fichier} illisible : {err}") from err
    return depuis_dict(donnees)


def charger(racine: Path) -> ConfigNouvelle:
    return _charger(Path(racine).resolve())


def trouver_racine(*departs: Path) -> Path | None:
    """Premier dossier qui contient redactor.json ; à défaut, un dossier nouvelles/."""
    for depart in departs:
        for p in [depart, *depart.parents]:
            if (p / NOM_FICHIER).is_file():
                return p
    for depart in departs:
        for p in [depart, *depart.parents]:
            if (p / DEFAUT.dossier_nouvelles).is_dir():
                return p
    return None
