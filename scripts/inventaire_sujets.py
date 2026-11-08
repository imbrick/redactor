#!/usr/bin/env python3
"""Inventaire des sujets dérivés Kongopedia — que reste-t-il à rédiger, et dans quel ordre ?

Usage :
    python inventaire_sujets.py [--top N] [--branche TEXTE] [--root <depot>]

Lit toutes les fiches ressources/brainstorm/*-articles-derives.md (lignes de tableau
« Titre pressenti | Branche taxonomique | Priorité | Rédigé ») et les confronte au corpus articles/ :
  - fusionne les sujets proposés par plusieurs fiches (priorité maximale retenue) ;
  - signale les sujets déjà rédigés dont la colonne « Rédigé » n'est pas cochée ;
  - signale les sujets cochés sans article correspondant ;
  - classe les sujets à rédiger : priorité, puis nombre de fiches qui les proposent.

Le rapprochement se fait sur le titre normalisé (sans article initial, accents ni parenthèses),
comparé au titre_simple, au début du title et au slug de chaque article : un titre formulé
autrement n'est pas reconnu, d'où des cas à vérifier à la main.

Codes de sortie : 0 rapport produit ; 2 vérification impossible (racine ou fiches introuvables).
Dépendance : PyYAML (via verifier_article).
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import verifier_article as va

SUFFIXE_FICHE = "-articles-derives.md"
LIGNE_RE = re.compile(r"^\|([^|]+)\|([^|]+)\|([^|]*⭐[^|]*)\|([^|]*)\|\s*$")
ARTICLE_INITIAL_RE = re.compile(r"^(?:le|la|les|un|une|des|l)\s+")
PARENTHESES_RE = re.compile(r"\([^)]*\)")
TOP_PAR_DEFAUT = 20


@dataclass(frozen=True)
class Sujet:
    titre: str
    branche: str
    priorite: int
    redige: bool
    fiche: str


@dataclass(frozen=True)
class Candidat:
    cle: str
    titre: str
    branche: str
    priorite: int
    fiches: tuple[str, ...]
    coche: bool


@dataclass(frozen=True)
class Rapport:
    candidats: list[Candidat]
    a_rediger: list[Candidat]
    redige_non_coche: list[Candidat]
    coche_sans_article: list[Candidat]


def normaliser(texte: str) -> str:
    sans_accents = unicodedata.normalize("NFD", texte).encode("ascii", "ignore").decode()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", sans_accents.lower()).split())


def cle(titre: str) -> str:
    """Forme de comparaison : sans parenthèses, accents, ponctuation ni article initial."""
    return ARTICLE_INITIAL_RE.sub("", normaliser(PARENTHESES_RE.sub(" ", titre)))


# ── Lecture ────────────────────────────────────────────────────────────────

def lire_fiche(chemin: Path) -> list[Sujet]:
    nom = chemin.name[:-len(SUFFIXE_FICHE)]
    sujets = []
    for ligne in va.lire_texte(chemin).splitlines():
        m = LIGNE_RE.match(ligne.strip())
        if m:
            titre, branche, priorite, redige = (g.strip() for g in m.groups())
            sujets.append(Sujet(titre, branche, priorite.count("⭐"), "#" in redige, nom))
    return sujets


def lire_fiches(racine: Path) -> list[Sujet]:
    dossier = Path(racine) / "ressources" / "brainstorm"
    return [s for chemin in sorted(dossier.glob(f"*{SUFFIXE_FICHE}")) for s in lire_fiche(chemin)]


def cles_du_corpus(racine: Path) -> set[str]:
    cles = set()
    for chemin in va.lister_articles(Path(racine)):
        fm = va.lire_frontmatter(chemin) or {}
        titre_long = str(fm.get("title") or "").split("—")[0]
        for valeur in (fm.get("titre_simple"), titre_long, str(fm.get("slug") or chemin.stem).replace("-", " ")):
            if valeur and cle(str(valeur)):
                cles.add(cle(str(valeur)))
    return cles


# ── Analyse ────────────────────────────────────────────────────────────────

def fusionner(sujets: list[Sujet]) -> list[Candidat]:
    groupes: dict[str, list[Sujet]] = {}
    for s in sujets:
        groupes.setdefault(cle(s.titre), []).append(s)
    candidats = []
    for k, groupe in groupes.items():
        meilleur = max(groupe, key=lambda s: s.priorite)
        fiches = tuple(sorted({s.fiche for s in groupe}))
        candidats.append(Candidat(k, meilleur.titre, meilleur.branche, meilleur.priorite, fiches,
                                  any(s.redige for s in groupe)))
    return candidats


def inventorier(racine: Path, branche: str | None = None) -> Rapport:
    candidats = fusionner(lire_fiches(racine))
    existants = cles_du_corpus(racine)
    redige_non_coche = [c for c in candidats if c.cle in existants and not c.coche]
    coche_sans_article = [c for c in candidats if c.coche and c.cle not in existants]
    a_rediger = [c for c in candidats if c.cle not in existants and not c.coche
                 and (not branche or branche.lower() in c.branche.lower())]
    a_rediger.sort(key=lambda c: (-c.priorite, -len(c.fiches), c.cle))
    return Rapport(candidats, a_rediger, redige_non_coche, coche_sans_article)


# ── Affichage ──────────────────────────────────────────────────────────────

def ligne_candidat(c: Candidat) -> str:
    sources = f" — proposé par {len(c.fiches)} fiches" if len(c.fiches) > 1 else ""
    return f"  {'⭐' * c.priorite:<3} {c.titre}  [{c.branche}]{sources}  ({', '.join(c.fiches)})"


def afficher(rapport: Rapport, top: int) -> None:
    multiples = sum(len(c.fiches) > 1 for c in rapport.candidats)
    print(f"== {len(rapport.candidats)} sujets distincts, dont {multiples} proposés par plusieurs fiches ; "
          f"{len(rapport.a_rediger)} à rédiger")
    if rapport.redige_non_coche:
        print(f"\n== Déjà rédigés mais non cochés « # » ({len(rapport.redige_non_coche)}) : cocher dans les fiches")
        for c in rapport.redige_non_coche:
            print(ligne_candidat(c))
    if rapport.coche_sans_article:
        print(f"\n== Cochés sans article retrouvé ({len(rapport.coche_sans_article)}) : titre différent ou case cochée à tort")
        for c in rapport.coche_sans_article:
            print(ligne_candidat(c))
    print(f"\n== Priorités à rédiger (top {min(top, len(rapport.a_rediger))})")
    for c in rapport.a_rediger[:top]:
        print(ligne_candidat(c))


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Inventorie les sujets dérivés des fiches brainstorm Kongopedia.")
    ap.add_argument("--top", type=int, default=TOP_PAR_DEFAUT, help="nombre de sujets prioritaires à afficher")
    ap.add_argument("--branche", help="ne garder que les sujets dont la branche contient ce texte")
    ap.add_argument("--root", help="racine du dépôt Kongopedia (détectée sinon)")
    args = ap.parse_args(argv)
    if va.yaml is None:
        print("PyYAML absent : installer avec « pip install pyyaml ».", file=sys.stderr)
        return 2
    racine = Path(args.root).resolve() if args.root else va.trouver_racine(Path.cwd(), Path(__file__).resolve().parent)
    if racine is None or not (racine / "ressources" / "brainstorm").is_dir():
        print("Dossier ressources/brainstorm introuvable : préciser --root.", file=sys.stderr)
        return 2
    afficher(inventorier(racine, args.branche), args.top)
    return 0


if __name__ == "__main__":
    sys.exit(main())
