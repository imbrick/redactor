"""Configuration d'un roman : section « roman » du fichier redactor.json.

Toutes les clés sont facultatives. La clé commune `charte` (racine du fichier) peut
désigner une fiche de voix ou de style ; `charte` dans la section prime.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

NOM_FICHIER = "redactor.json"
SECTION = "roman"
GENRES = ("litterature", "polar", "imaginaire", "historique")
STATUTS_DEFAUT = ("plan", "brouillon", "relu", "final")


class ConfigInvalide(ValueError):
    """redactor.json illisible ou mal formé."""


@dataclass(frozen=True)
class ConfigRoman:
    projet: str = "projet"
    charte: str | None = None                 # fiche de voix, de style ou de collection
    titre: str | None = None
    auteur: str | None = None
    genre: str = "litterature"
    dossier_chapitres: str = "chapitres"
    plan: str = "plan.md"
    dossier_bible: str = "bible"
    dossier_manuscrit: str = "manuscrit"
    objectif_mots: int | None = None
    tics: tuple[str, ...] = ()                # mots ou tournures à surveiller
    noms_ignores: tuple[str, ...] = ()        # mots à majuscule à ne pas signaler hors bible
    statuts: tuple[str, ...] = STATUTS_DEFAUT
    titre_chapitre: str = "Chapitre {numero} — {titre}"


DEFAUT = ConfigRoman()
_CHAINES = {"charte", "titre", "auteur", "genre", "dossier_chapitres", "plan", "dossier_bible",
            "dossier_manuscrit", "titre_chapitre"}
_LISTES = {"tics", "statuts", "noms_ignores"}
_FACULTATIVES = {"charte", "titre", "auteur", "objectif_mots"}   # seules à admettre null
_CLES = _CHAINES | _LISTES | {"objectif_mots"}


def depuis_dict(donnees: dict) -> ConfigRoman:
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
        elif cle == "objectif_mots":
            if valeur is not None and (isinstance(valeur, bool) or not isinstance(valeur, int) or valeur <= 0):
                raise ConfigInvalide(f"« {SECTION}.objectif_mots » doit être un entier positif.")
            valeurs[cle] = valeur
        elif valeur is not None and not isinstance(valeur, str):
            raise ConfigInvalide(f"« {SECTION}.{cle} » doit être une chaîne.")
        else:
            valeurs[cle] = valeur
    cfg = ConfigRoman(**valeurs)
    if cfg.genre not in GENRES:
        raise ConfigInvalide(f"Genre « {cfg.genre} » inconnu (genres : {', '.join(GENRES)}).")
    if not cfg.statuts:
        raise ConfigInvalide(f"« {SECTION}.statuts » ne peut pas être vide.")
    return cfg


@lru_cache(maxsize=None)
def _charger(racine: Path) -> ConfigRoman:
    fichier = racine / NOM_FICHIER
    if not fichier.exists():
        return DEFAUT
    try:
        donnees = json.loads(fichier.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as err:
        raise ConfigInvalide(f"{fichier} illisible : {err}") from err
    return depuis_dict(donnees)


def charger(racine: Path) -> ConfigRoman:
    """Configuration roman du projet dont racine est la racine."""
    return _charger(Path(racine).resolve())


def trouver_racine(*departs: Path) -> Path | None:
    """Premier dossier, en remontant depuis chaque départ, qui contient redactor.json ;
    à défaut, premier dossier qui contient un dossier chapitres/ ou un plan.md."""
    for depart in departs:
        for p in [depart, *depart.parents]:
            if (p / NOM_FICHIER).is_file():
                return p
    for depart in departs:
        for p in [depart, *depart.parents]:
            if (p / DEFAUT.dossier_chapitres).is_dir() or (p / DEFAUT.plan).is_file():
                return p
    return None
