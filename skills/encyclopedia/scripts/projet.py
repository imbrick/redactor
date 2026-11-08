"""Configuration d'un projet éditorial : fichier redactor.json à la racine du projet.

Le skill ne connaît aucun projet en particulier. Chaque projet décrit ses conventions
(dossiers, champs du frontmatter, index, fiches de sujets dérivés, liens internes) dans
un fichier redactor.json placé à sa racine. Toutes les clés sont facultatives : une clé
absente prend la valeur par défaut ci-dessous.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, fields
from functools import lru_cache
from pathlib import Path

NOM_FICHIER = "redactor.json"


class ConfigInvalide(ValueError):
    """redactor.json illisible ou mal formé."""


@dataclass(frozen=True)
class Config:
    projet: str = "projet"
    charte: str | None = None                 # skill ou fichier qui fixe la charte éditoriale
    dossier_articles: str = "articles"
    fichiers_index: tuple[str, ...] = ()      # index tenus à jour, relatifs à dossier_articles
    dossier_brainstorm: str | None = None     # fiches de sujets dérivés
    suffixe_brainstorm: str = "-articles-derives.md"
    dossier_fact_checks: str | None = None
    journal: str | None = None
    gabarit_article: str | None = None
    categories: str | None = None
    champs_obligatoires: tuple[str, ...] = ("title", "slug")
    champs_recommandes: tuple[str, ...] = ()  # « a|b » : l'un des deux suffit
    champ_titre_court: str | None = None      # titre d'index ; à défaut, title
    champ_statut: str = "publication_status"
    statuts: tuple[str, ...] = ("draft", "review", "published")
    prefixe_liens: str = "/article/"

    @property
    def champ_titre(self) -> str:
        return self.champ_titre_court or "title"


DEFAUT = Config()
_TUPLES = {"fichiers_index", "champs_obligatoires", "champs_recommandes", "statuts"}
# Sections propres aux autres skills du plugin (lues par leurs propres scripts).
SECTIONS_GENRES = frozenset({"presse", "roman"})


def depuis_dict(donnees: dict) -> Config:
    if not isinstance(donnees, dict):
        raise ConfigInvalide(f"{NOM_FICHIER} doit contenir un objet JSON.")
    connues = {f.name for f in fields(Config)}
    inconnues = sorted(set(donnees) - connues - {"$schema", "description"} - SECTIONS_GENRES)
    if inconnues:
        raise ConfigInvalide(f"Clé(s) inconnue(s) dans {NOM_FICHIER} : {', '.join(inconnues)}.")
    valeurs = {}
    for cle, valeur in donnees.items():
        if cle not in connues:
            continue
        if cle in _TUPLES:
            if not isinstance(valeur, list) or not all(isinstance(v, str) for v in valeur):
                raise ConfigInvalide(f"« {cle} » doit être une liste de chaînes.")
            valeur = tuple(valeur)
        elif valeur is not None and not isinstance(valeur, str):
            raise ConfigInvalide(f"« {cle} » doit être une chaîne.")
        valeurs[cle] = valeur
    return Config(**valeurs)


@lru_cache(maxsize=None)
def _charger(racine: Path) -> Config:
    fichier = racine / NOM_FICHIER
    if not fichier.exists():
        return DEFAUT
    try:
        donnees = json.loads(fichier.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as err:
        raise ConfigInvalide(f"{fichier} illisible : {err}") from err
    return depuis_dict(donnees)


def charger(racine: Path) -> Config:
    """Configuration du projet dont racine est la racine (valeurs par défaut sans redactor.json)."""
    return _charger(Path(racine).resolve())


def trouver_racine(*departs: Path) -> Path | None:
    """Premier dossier, en remontant depuis chaque départ, qui contient redactor.json ;
    à défaut, premier dossier qui contient un dossier articles/."""
    for depart in departs:
        for p in [depart, *depart.parents]:
            if (p / NOM_FICHIER).is_file():
                return p
    for depart in departs:
        for p in [depart, *depart.parents]:
            if (p / DEFAUT.dossier_articles).is_dir():
                return p
    return None
