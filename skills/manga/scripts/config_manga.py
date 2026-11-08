"""Configuration d'un manga : section « manga » du fichier redactor.json.

Toutes les clés sont facultatives. La clé commune `charte` (racine du fichier) peut
désigner une charte de série ou de collection ; `charte` dans la section prime.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

NOM_FICHIER = "redactor.json"
SECTION = "manga"
FORMATS = ("oneshot", "serie", "webtoon")
SENS = ("rtl", "ltr")                        # droite à gauche (japonais), gauche à droite
PARITES = ("paire", "impaire")
STATUTS_DEFAUT = ("plan", "script", "name", "final")


class ConfigInvalide(ValueError):
    """redactor.json illisible ou mal formé."""


@dataclass(frozen=True)
class ConfigManga:
    projet: str = "projet"
    charte: str | None = None
    titre: str | None = None
    auteur: str | None = None                # scénariste, ou auteur complet
    dessinateur: str | None = None
    format: str = "serie"
    sens: str = "rtl"
    pages_par_chapitre: int | None = None    # cible ; un chapitre peut la préciser (champ « pages »)
    page_revelation: str = "paire"           # page découverte en tournant (paire si la page 1 est un recto)
    cases_max_par_page: int = 7
    bulles_max_par_case: int = 3
    mots_max_par_bulle: int = 25
    dossier_chapitres: str = "chapitres"
    plan: str = "plan.md"
    dossier_bible: str = "bible"
    dossier_manuscrit: str = "manuscrit"
    noms_ignores: tuple[str, ...] = ()
    statuts: tuple[str, ...] = STATUTS_DEFAUT


DEFAUT = ConfigManga()
_FACULTATIVES = {"charte", "titre", "auteur", "dessinateur", "pages_par_chapitre"}
_ENTIERS = {"pages_par_chapitre", "cases_max_par_page", "bulles_max_par_case", "mots_max_par_bulle"}
_LISTES = {"noms_ignores", "statuts"}
_CHOIX = {"format": FORMATS, "sens": SENS, "page_revelation": PARITES}
_CLES = _FACULTATIVES | _ENTIERS | _LISTES | set(_CHOIX) | {"dossier_chapitres", "plan", "dossier_bible",
                                                             "dossier_manuscrit"}


def depuis_dict(donnees: dict) -> ConfigManga:
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
        if valeur is None:
            if cle not in _FACULTATIVES:
                raise ConfigInvalide(f"« {SECTION}.{cle} » ne peut pas valoir null (omettre la clé pour le défaut).")
            valeurs[cle] = None
        elif cle in _ENTIERS:
            if isinstance(valeur, bool) or not isinstance(valeur, int) or valeur <= 0:
                raise ConfigInvalide(f"« {SECTION}.{cle} » doit être un entier positif.")
            valeurs[cle] = valeur
        elif cle in _LISTES:
            if not isinstance(valeur, list) or not all(isinstance(v, str) for v in valeur):
                raise ConfigInvalide(f"« {SECTION}.{cle} » doit être une liste de chaînes.")
            valeurs[cle] = tuple(valeur)
        elif not isinstance(valeur, str):
            raise ConfigInvalide(f"« {SECTION}.{cle} » doit être une chaîne.")
        elif cle in _CHOIX and valeur not in _CHOIX[cle]:
            raise ConfigInvalide(f"« {SECTION}.{cle} » parmi {', '.join(_CHOIX[cle])} (reçu : {valeur}).")
        else:
            valeurs[cle] = valeur
    cfg = ConfigManga(**valeurs)
    if not cfg.statuts:
        raise ConfigInvalide(f"« {SECTION}.statuts » ne peut pas être vide.")
    return cfg


@lru_cache(maxsize=None)
def _charger(racine: Path) -> ConfigManga:
    fichier = racine / NOM_FICHIER
    if not fichier.exists():
        return DEFAUT
    try:
        donnees = json.loads(fichier.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as err:
        raise ConfigInvalide(f"{fichier} illisible : {err}") from err
    return depuis_dict(donnees)


def charger(racine: Path) -> ConfigManga:
    return _charger(Path(racine).resolve())


def trouver_racine(*departs: Path) -> Path | None:
    """Premier dossier qui contient redactor.json ; à défaut, un dossier chapitres/ ou un plan.md."""
    for depart in departs:
        for p in [depart, *depart.parents]:
            if (p / NOM_FICHIER).is_file():
                return p
    for depart in departs:
        for p in [depart, *depart.parents]:
            if (p / DEFAUT.dossier_chapitres).is_dir() or (p / DEFAUT.plan).is_file():
                return p
    return None
