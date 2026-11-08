#!/usr/bin/env python3
"""Vérificateur de nouvelles : une nouvelle, sa conformité à un règlement de concours, ou un recueil.

Usage :
    python verifier_nouvelle.py <nouvelles/fichier.md> [--root RACINE]
    python verifier_nouvelle.py --recueil [--root RACINE]

Une nouvelle est un fichier Markdown avec un frontmatter : titre, statut, effet (l'effet visé,
en une phrase), personnages (facultatif), concours (identifiant d'une fiche de règlement
<dossier_concours>/<id>.md, facultatif).

  - Mots et signes (espaces comprises, hors balisage Markdown et sauts de paragraphe).
  - BLOQUANT : frontmatter illisible, statut inconnu ; pour un concours : règlement introuvable ou
    mal formé, signes ou mots hors limites, phrase imposée absente ou mal placée, mot imposé absent,
    nom de l'auteur dans le texte si l'anonymat est exigé, titre absent si exigé.
  - avertissement : titre absent, effet visé non noté, date limite dépassée ; contrôles de style
    du skill roman (répétitions, adverbes en -ment, tics, dialogues au trait d'union) ;
    pour un recueil : nouvelle prévue absente, nouvelle hors recueil, recueil absent.

Codes de sortie : 0 aucun bloquant ; 1 au moins un bloquant ; 2 vérification impossible.
Dépendance : PyYAML.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import config_nouvelle as cn
from config_nouvelle import ConfigNouvelle

# Contrôles de style et lecture des chapitres : skill roman du même plugin.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "roman" / "scripts"))
import verifier_roman as vr  # noqa: E402
from verifier_roman import (  # noqa: E402
    Resultat, afficher, avertissement, bloquant, charger_frontmatter, separer_frontmatter, yaml)
from texte import normaliser, sections_markdown, table, vide  # noqa: E402  (commun/, via verifier_roman)

CLES_REGLEMENT = {"nom", "signes_max", "signes_min", "mots_max", "mots_min", "theme", "phrase_imposee",
                  "phrase_position", "mots_imposes", "anonymat", "titre_obligatoire", "date_limite"}
POSITIONS = ("libre", "debut", "fin")
PLURIELS = ("s", "x")                            # « marche » admis pour « marches »
BOOLEENS_REGLEMENT = ("anonymat", "titre_obligatoire")
CHAINES_REGLEMENT = ("nom", "theme", "phrase_imposee")


@dataclass
class RapportNouvelle:
    chemin: Path
    titre: str = ""
    mots: int = 0
    signes: int = 0
    resultats: list[Resultat] = field(default_factory=list)


@dataclass
class RapportRecueil:
    nouvelles: list[RapportNouvelle] = field(default_factory=list)
    resultats: list[Resultat] = field(default_factory=list)


# ── Mesures ────────────────────────────────────────────────────────────────

MARQUE_LIGNE_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+\.\s+|>\s?)")


def texte_brut(corps: str) -> list[str]:
    """Paragraphes du texte tel qu'un lecteur le voit : sans titre en tête, commentaires,
    sauts de scène, marques de liste ou de citation, emphase ni adresses de liens."""
    corps = re.sub(r"<!--.*?-->", "", corps, flags=re.DOTALL)
    corps = re.sub(r"\A\s*#\s.*(?:\n|\Z)", "", corps)            # titre repris en tête du corps
    corps = vr.SAUT_SCENE_RE.sub("", corps)
    corps = re.sub(r"^#+\s*", "", corps, flags=re.MULTILINE)
    paragraphes = []
    for bloc in re.split(r"\n\s*\n", corps):
        p = " ".join(MARQUE_LIGNE_RE.sub("", l).strip() for l in bloc.splitlines() if l.strip())
        p = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", p)
        p = re.sub(r"(\*{1,3})(\S(?:.*?\S)?)\1", r"\2", p)
        p = re.sub(r"(?<!\w)(_{1,3})(\S(?:.*?\S)?)\1(?!\w)", r"\2", p)
        p = re.sub(r"[ \t]{2,}", " ", p).strip()
        if p:
            paragraphes.append(p)
    return paragraphes


def compter_signes(corps: str) -> int:
    """Signes espaces comprises, sans les marques de paragraphe (comme un traitement de texte)."""
    return sum(len(p) for p in texte_brut(corps))


def compter_mots(corps: str) -> int:
    """Mots séparés par des espaces, comme un traitement de texte (« grand-mère » : un mot)."""
    return sum(len(p.split()) for p in texte_brut(corps))


def present(expression: str, texte: str) -> bool:
    """L'expression normalisée figure-t-elle dans le texte normalisé, en mots entiers ?"""
    return bool(expression) and re.search(rf"(?<!\w){re.escape(expression)}(?!\w)", texte) is not None


def chemin_reglement(racine: Path, cfg: ConfigNouvelle, identifiant) -> Path | None:
    """Fiche de règlement d'un identifiant simple ; None si l'identifiant contient un chemin."""
    if not isinstance(identifiant, str) or re.search(r"[\\/]|\.\.", identifiant) or not identifiant.strip():
        return None
    return racine / cfg.dossier_concours / f"{identifiant.strip()}.md"


# ── Règlement de concours ──────────────────────────────────────────────────

def lire_reglement(chemin: Path) -> tuple[dict | None, str | None]:
    if not chemin.is_file():
        return None, f"règlement introuvable ({chemin})"
    brut, _ = separer_frontmatter(chemin.read_text(encoding="utf-8-sig", errors="replace"))
    if brut is None:
        return None, f"{chemin.name} : pas de frontmatter"
    regl, erreur = charger_frontmatter(brut)
    if regl is None:
        return None, f"{chemin.name} : {erreur}"
    inconnues = sorted(set(regl) - CLES_REGLEMENT)
    if inconnues:
        return None, f"{chemin.name} : clé(s) inconnue(s) {', '.join(inconnues)}"
    for cle in ("signes_max", "signes_min", "mots_max", "mots_min"):
        v = regl.get(cle)
        if v is not None and (isinstance(v, bool) or not isinstance(v, int) or v < 0):
            return None, f"{chemin.name} : « {cle} » doit être un entier positif"
    for cle in BOOLEENS_REGLEMENT:
        if cle in regl and not isinstance(regl[cle], bool):
            return None, f"{chemin.name} : « {cle} » vaut true ou false"
    for cle in CHAINES_REGLEMENT:
        if regl.get(cle) is not None and not isinstance(regl[cle], str):
            return None, f"{chemin.name} : « {cle} » doit être un texte"
    for cle in ("signes", "mots"):
        mini, maxi = regl.get(f"{cle}_min"), regl.get(f"{cle}_max")
        if mini is not None and maxi is not None and mini > maxi:
            return None, f"{chemin.name} : « {cle}_min » supérieur à « {cle}_max »"
    if regl.get("phrase_position", "libre") not in POSITIONS:
        return None, f"{chemin.name} : « phrase_position » parmi {', '.join(POSITIONS)}"
    imposes = regl.get("mots_imposes") or []
    if not isinstance(imposes, list) or not all(isinstance(m, str) for m in imposes):
        return None, f"{chemin.name} : « mots_imposes » doit être une liste de mots"
    limite = regl.get("date_limite")
    if isinstance(limite, datetime):
        regl["date_limite"] = limite = limite.date()
    if isinstance(limite, str):
        try:
            regl["date_limite"] = date.fromisoformat(limite)
        except ValueError:
            return None, f"{chemin.name} : « date_limite » au format AAAA-MM-JJ"
    elif limite is not None and not isinstance(limite, date):
        return None, f"{chemin.name} : « date_limite » au format AAAA-MM-JJ"
    return regl, None


def mot_present(mot: str, texte: str) -> bool:
    """Mot imposé présent, au singulier ou au pluriel, y compris après une élision (« l'eau »).
    Une expression de plusieurs mots (« mer vide », « grand-mère ») se cherche telle quelle."""
    m = normaliser(mot)
    if " " in m:
        return present(m, texte)
    jetons = set()
    for t in texte.split():
        jetons |= {t, t.split("'")[-1]}
    formes = {m} | {m + s for s in PLURIELS} | ({m[:-1]} if m[-1:] in PLURIELS else set())
    return bool(formes & jetons)


def noms_a_taire(auteur: str) -> list[str]:
    """Nom complet, puis nom de famille (dernier mot de quatre lettres ou plus) : ce que l'anonymat interdit."""
    complet = normaliser(auteur)
    parties = complet.split()
    noms = [complet]
    if len(parties) > 1 and len(parties[-1]) >= 4:
        noms.append(parties[-1])
    return noms


def verifier_reglement(regl: dict, fm: dict, corps: str, cfg: ConfigNouvelle, rapport: RapportNouvelle,
                       aujourd_hui: date) -> list[Resultat]:
    res = []
    nom = regl.get("nom") or "le concours"
    for cle, mesure, unite in (("signes", rapport.signes, "signes"), ("mots", rapport.mots, "mots")):
        maxi, mini = regl.get(f"{cle}_max"), regl.get(f"{cle}_min")
        if maxi is not None and mesure > maxi:
            res.append(bloquant(f"{cle.upper()}_MAX", f"{mesure} {unite} pour {maxi} au plus ({nom}) : "
                                f"retirer {mesure - maxi} {unite}."))
        if mini is not None and mesure < mini:
            res.append(bloquant(f"{cle.upper()}_MIN", f"{mesure} {unite} pour {mini} au moins ({nom})."))
    texte = normaliser(" ".join(texte_brut(corps)))
    phrase = regl.get("phrase_imposee")
    if phrase:
        p = normaliser(str(phrase))
        position = regl.get("phrase_position", "libre")
        if not present(p, texte):
            res.append(bloquant("PHRASE_IMPOSEE", f"Phrase imposée absente : « {phrase} »."))
        elif position == "debut" and not texte.startswith(p):
            res.append(bloquant("PHRASE_POSITION", f"La phrase imposée doit ouvrir le texte : « {phrase} »."))
        elif position == "fin" and not texte.endswith(p):
            res.append(bloquant("PHRASE_POSITION", f"La phrase imposée doit clore le texte : « {phrase} »."))
    for mot in regl.get("mots_imposes") or []:
        if not mot_present(mot, texte):
            res.append(bloquant("MOT_IMPOSE", f"Mot imposé absent : « {mot} »."))
    if regl.get("anonymat"):
        auteur = fm.get("auteur") if isinstance(fm.get("auteur"), str) else cfg.auteur
        trouves = [n for n in noms_a_taire(auteur) if present(n, texte)] if auteur else []
        if trouves:
            res.append(bloquant("ANONYMAT", f"Anonymat exigé : « {trouves[0]} » (nom de l'auteur) figure dans le texte."))
    limite = regl.get("date_limite")
    if isinstance(limite, date) and aujourd_hui > limite:
        res.append(avertissement("DATE_LIMITE", f"Date limite de {nom} dépassée ({limite.isoformat()})."))
    return res


# ── Une nouvelle ───────────────────────────────────────────────────────────

def verifier_nouvelle(chemin: Path, racine: Path, aujourd_hui: date | None = None) -> RapportNouvelle:
    cfg = cn.charger(racine)
    rapport = RapportNouvelle(chemin)
    brut, corps = separer_frontmatter(chemin.read_text(encoding="utf-8-sig", errors="replace"))
    fm: dict = {}
    if brut is not None:
        fm, erreur = charger_frontmatter(brut)
        if fm is None:
            rapport.resultats.append(bloquant("FRONTMATTER_YAML", f"{chemin.name} : {erreur}"))
            return rapport
    rapport.titre = str(fm.get("titre") or "").strip()
    rapport.mots = compter_mots(corps)
    rapport.signes = compter_signes(corps)
    statut = fm.get("statut")
    if statut is not None and statut not in cfg.statuts:
        rapport.resultats.append(bloquant("STATUT_INCONNU", f"{chemin.name} : statut « {statut} » inconnu "
                                          f"({', '.join(cfg.statuts)})."))
    if vide(fm.get("effet")):
        rapport.resultats.append(avertissement("EFFET_ABSENT", f"{chemin.name} : noter l'effet visé (« effet » "
                                               "du frontmatter) : c'est lui qui guide le resserrement."))

    regl = None
    if not vide(fm.get("concours")):
        chemin_regl = chemin_reglement(racine, cfg, fm["concours"])
        if chemin_regl is None:
            regl, erreur = None, f"identifiant de concours « {fm['concours']} » introuvable (un nom simple, sans chemin)"
        else:
            regl, erreur = lire_reglement(chemin_regl)
        if regl is None:
            code = "CONCOURS_INCONNU" if "introuvable" in erreur else "REGLEMENT_INVALIDE"
            rapport.resultats.append(bloquant(code, f"{chemin.name} : {erreur}."))
    if not rapport.titre:
        exige = bool(regl and regl.get("titre_obligatoire"))
        rapport.resultats.append((bloquant if exige else avertissement)(
            "TITRE_ABSENT", f"{chemin.name} : pas de titre{' (exigé par le règlement)' if exige else ''}."))
    if regl:
        rapport.resultats += verifier_reglement(regl, fm, corps, cfg, rapport, aujourd_hui or date.today())

    personnages = fm.get("personnages") if isinstance(fm.get("personnages"), list) else []
    connus = {normaliser(m) for p in personnages for m in vr.MOT_RE.findall(str(p))}
    chap = vr.Chapitre(chemin, None, rapport.titre, statut if isinstance(statut, str) else None,
                       None, None, corps, rapport.mots)
    rapport.resultats += vr.verifier_style(chap, connus, cfg)
    return rapport


# ── Un recueil ─────────────────────────────────────────────────────────────

def lire_recueil(chemin: Path) -> list[dict] | None:
    if not chemin.is_file():
        return None
    _, lignes = table(sections_markdown(chemin.read_text(encoding="utf-8-sig", errors="replace")).get("nouvelles", ""))
    return lignes


def verifier_recueil(racine: Path, aujourd_hui: date | None = None) -> RapportRecueil:
    cfg = cn.charger(racine)
    rapport = RapportRecueil()
    dossier = racine / cfg.dossier_nouvelles
    fichiers = sorted(dossier.glob("*.md")) if dossier.is_dir() else []
    lignes = lire_recueil(racine / cfg.recueil)
    if lignes is None:
        rapport.resultats.append(avertissement("RECUEIL_ABSENT", f"Pas de {cfg.recueil} : toutes les nouvelles du "
                                               "dossier sont vérifiées, sans ordre."))
        ordre = fichiers
    else:
        ordre = []
        for l in lignes:
            chemin = dossier / Path(l.get("fichier", "").strip()).name
            if chemin.is_file():
                ordre.append(chemin)
            else:
                rapport.resultats.append(avertissement("NOUVELLE_MANQUANTE", f"Nouvelle prévue au recueil mais "
                                                       f"absente : {l.get('titre', '')} ({chemin.name})."))
        prevus = {c.name for c in ordre} | {Path(l.get("fichier", "").strip()).name for l in lignes}
        rapport.resultats += [avertissement("HORS_RECUEIL", f"{f.name} n'est pas dans {cfg.recueil}.")
                              for f in fichiers if f.name not in prevus]
    for chemin in ordre:
        r = verifier_nouvelle(chemin, racine, aujourd_hui)
        rapport.nouvelles.append(r)
        rapport.resultats += r.resultats
    return rapport


# ── Ligne de commande ──────────────────────────────────────────────────────

def afficher_mesures(nouvelles: list[RapportNouvelle]) -> None:
    print("\n== Mesures")
    for n in nouvelles:
        print(f"  {n.titre[:45] or n.chemin.name:<45} {n.mots:>7} mots {n.signes:>8} signes")
    if len(nouvelles) > 1:
        print(f"  {'Total':<45} {sum(n.mots for n in nouvelles):>7} mots {sum(n.signes for n in nouvelles):>8} signes")


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Vérifie une nouvelle, sa conformité à un concours, ou un recueil.")
    ap.add_argument("nouvelle", nargs="?", help="chemin du fichier .md")
    ap.add_argument("--recueil", action="store_true", help="vérifier toutes les nouvelles du recueil")
    ap.add_argument("--root", help="racine du projet, là où se trouve redactor.json (détectée sinon)")
    try:
        args = ap.parse_args(argv)
        if not args.nouvelle and not args.recueil:
            ap.error("indiquer une nouvelle ou --recueil")
    except SystemExit as sortie:
        return 2 if sortie.code else 0
    if yaml is None:
        print("PyYAML absent : installer avec « pip install pyyaml ».", file=sys.stderr)
        return 2
    departs = [Path(args.nouvelle).resolve().parent] if args.nouvelle else []
    racine = Path(args.root).resolve() if args.root else cn.trouver_racine(*departs, Path.cwd().resolve())
    if racine is None:
        print("Racine du projet introuvable (ni redactor.json ni nouvelles/) : préciser --root.", file=sys.stderr)
        return 2
    try:
        if args.recueil:
            rapport = verifier_recueil(racine)
            nouvelles, resultats = rapport.nouvelles, rapport.resultats
        else:
            r = verifier_nouvelle(Path(args.nouvelle).resolve(), racine)
            nouvelles, resultats = [r], r.resultats
    except cn.ConfigInvalide as err:
        print(f"Configuration invalide : {err}", file=sys.stderr)
        return 2
    except OSError as err:
        print(f"Lecture impossible : {err}", file=sys.stderr)
        return 2
    afficher_mesures(nouvelles)
    afficher("Contrôles", resultats)
    return 1 if any(r.bloquant for r in resultats) else 0


if __name__ == "__main__":
    sys.exit(main())
