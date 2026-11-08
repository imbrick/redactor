#!/usr/bin/env python3
"""Vérificateur d'un script de manga : mise en page, bulles, rythme, continuité.

Usage :
    python verifier_manga.py [--root RACINE] [--chapitre N]

Format d'un chapitre (<dossier_chapitres>/*.md, frontmatter numero, titre, statut, pages, cliffhanger) :

    ## Page 3 (révélation)          ## Pages 4-5 (double page)        ## Séquence 1 (webtoon)
    ### Case 1
    Description de la case (toute ligne qui n'est pas une réplique).
    AKI : Réplique.                  AKI (pensée) : …                  NARRATION : Récitatif.
    SFX : BOUM

  - Avancement (rapport) : pages, cases et bulles par chapitre ; chapitres du plan à écrire.
  - BLOQUANT : frontmatter illisible, statut inconnu.
  - avertissement : nombre de pages différent de la cible, numérotation non continue, page sans
    case, trop de cases par page, case sans description, trop de bulles par case, bulle trop longue,
    révélation hors de la page de tourne, double page mal placée, série sans cliffhanger, locuteur
    absent de la bible, variante d'un nom ou nom récurrent hors bible (skill roman), plan.

Codes de sortie : 0 aucun bloquant ; 1 au moins un bloquant ; 2 vérification impossible.
Dépendance : PyYAML.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import config_manga as cm
from config_manga import ConfigManga

# Bible, plan et contrôle des noms : skill roman du même plugin.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "roman" / "scripts"))
import verifier_roman as vr  # noqa: E402
from verifier_roman import (  # noqa: E402
    Resultat, afficher, avertissement, bloquant, charger_frontmatter, separer_frontmatter, yaml)
from texte import mots, normaliser, vide  # noqa: E402  (commun/, via verifier_roman)

PAGE_RE = re.compile(r"^##\s+(?:pages?|s[ée]quence)\s+(\d+)(?:\s*[-–—à]\s*(\d+))?(.*)$", re.IGNORECASE)
CASE_RE = re.compile(r"^###\s+case\b\s*(\d+)?(.*)$", re.IGNORECASE)
# Locuteur borné à 60 caractères, sans quantificateurs imbriqués : pas d'emballement sur une ligne d'espaces.
REPLIQUE_RE = re.compile(r"^([^:()]{1,60})(?:\(([^()]*)\))?[ \t]*:[ \t]*(.*)$")
LOCUTEUR_RE = re.compile(r"^(?:[A-ZÀ-ÖØ-Þ0-9][A-ZÀ-ÖØ-Þ0-9 '’.,&-]*|\?+)$")
DESCRIPTION_RE = re.compile(r"^description\s*:\s*(.*)$", re.IGNORECASE)
ETIQUETTE_RE = re.compile(r"\(([^)]*)\)")
CLOTURE_RE = re.compile(r"[.!?…»\"”)]$")
ETIQUETTES = {"revelation": "revelation", "double page": "double page", "double": "double page",
              "cliffhanger": "cliffhanger"}

NARRATION = frozenset(normaliser(m) for m in ("NARRATION", "RÉCITATIF", "ENCADRÉ", "CARTOUCHE"))
ONOMATOPEES = frozenset(normaliser(m) for m in ("SFX", "ONOMATOPÉE", "ONO", "BRUIT"))
LOCUTEURS_GENERIQUES = frozenset(normaliser(m) for m in (
    "VOIX", "VOIX OFF", "TOUS", "FOULE", "RADIO", "TÉLÉ", "TÉLÉPHONE", "HAUT-PARLEUR", "INCONNU"))


@dataclass
class Bulle:
    locuteur: str
    texte: str
    nature: str            # dialogue ou narration
    precision: str = ""    # pensée, off, murmure…


@dataclass
class Case:
    numero: int
    description: list[str] = field(default_factory=list)
    bulles: list[Bulle] = field(default_factory=list)
    sfx: list[str] = field(default_factory=list)


@dataclass
class Page:
    numeros: tuple[int, ...]
    etiquettes: set[str]
    cases: list[Case] = field(default_factory=list)
    inconnues: list[str] = field(default_factory=list)   # étiquettes non reconnues

    @property
    def nom(self) -> str:
        return f"p. {'-'.join(map(str, self.numeros))}"


@dataclass
class InfoChapitre:
    chemin: Path
    numero: int | None
    titre: str
    statut: str | None
    pages: int
    cases: int
    bulles: int


@dataclass
class Rapport:
    resultats: list[Resultat] = field(default_factory=list)
    chapitres: list[InfoChapitre] = field(default_factory=list)
    manquants: list = field(default_factory=list)


# ── Lecture du script ──────────────────────────────────────────────────────

def replique(ligne: str) -> tuple[str, str, str] | None:
    """(locuteur, précision, texte) si la ligne est une réplique « NOM (précision) : texte ».
    Admet le gras Markdown (« **AKI** : »), une puce (« - AKI : »), plusieurs voix (« AKI, ROSE : »)."""
    propre = re.sub(r"\*\*|__", "", re.sub(r"^[-*+]\s+", "", ligne))
    r = REPLIQUE_RE.match(propre)
    if not r:
        return None
    locuteur = r.group(1).strip()
    if not locuteur or not LOCUTEUR_RE.match(locuteur) or locuteur != locuteur.upper():
        return None
    return locuteur, (r.group(2) or "").strip(), r.group(3).strip()


def lire_ligne(ligne: str, case: Case, suite_possible: bool) -> bool:
    """Range la ligne dans la case ; renvoie True si elle ouvre (ou prolonge) une bulle."""
    d = DESCRIPTION_RE.match(ligne)
    if d:
        if d.group(1).strip():
            case.description.append(d.group(1).strip())
        return False
    r = replique(ligne)
    if r:
        locuteur, precision, texte = r
        n = normaliser(locuteur)
        if n in ONOMATOPEES:
            case.sfx.append(texte)
            return False
        case.bulles.append(Bulle(locuteur, texte, "narration" if n in NARRATION else "dialogue", precision))
        return True
    # Réplique coupée sur plusieurs lignes : la ligne suivante la prolonge si la bulle ne se termine
    # pas par une ponctuation finale, ou si elle commence par une minuscule.
    if suite_possible and case.bulles and (not CLOTURE_RE.search(case.bulles[-1].texte) or ligne[:1].islower()):
        case.bulles[-1].texte = f"{case.bulles[-1].texte} {ligne}".strip()
        return True
    case.description.append(ligne)
    return False


def lire_etiquettes(texte: str) -> tuple[set[str], list[str]]:
    connues, inconnues = set(), []
    for groupe in ETIQUETTE_RE.findall(texte):
        for morceau in re.split(r"[,;/]", groupe):
            n = normaliser(morceau)
            if not n:
                continue
            if n in ETIQUETTES:
                connues.add(ETIQUETTES[n])
            else:
                inconnues.append(morceau.strip())
    return connues, inconnues


def lire_script(corps: str) -> list[Page]:
    pages: list[Page] = []
    case: Case | None = None
    dans_code = False
    suite = False
    for brute in corps.splitlines():
        ligne = brute.strip()
        if ligne.startswith(("```", "~~~")):
            dans_code = not dans_code
            continue
        if dans_code or not ligne:
            suite = False
            continue
        p = PAGE_RE.match(ligne)
        if p:
            debut = int(p.group(1))
            numeros = (debut, int(p.group(2))) if p.group(2) else (debut,)
            etiquettes, inconnues = lire_etiquettes(p.group(3))
            pages.append(Page(numeros, etiquettes, inconnues=inconnues))
            case, suite = None, False
            continue
        c = CASE_RE.match(ligne)
        if c and pages:
            case = Case(int(c.group(1)) if c.group(1) else len(pages[-1].cases) + 1)
            pages[-1].cases.append(case)
            suite = False
            continue
        if case is not None and not ligne.startswith("#"):
            suite = lire_ligne(ligne, case, suite)
    return pages


# ── Contrôles ──────────────────────────────────────────────────────────────

def lieux(liste: list[str], maxi: int = 8) -> str:
    return ", ".join(liste[:maxi]) + (f" (et {len(liste) - maxi} autres)" if len(liste) > maxi else "")


def parite_ok(numero: int, cfg: ConfigManga) -> bool:
    return (numero % 2 == 0) == (cfg.page_revelation == "paire")


def cible_de_pages(fm: dict, cfg: ConfigManga) -> int | None:
    pages = fm.get("pages")
    if isinstance(pages, str) and pages.strip().isdigit():
        pages = int(pages)
    if isinstance(pages, int) and not isinstance(pages, bool) and pages > 0:
        return pages
    return cfg.pages_par_chapitre


def verifier_mise_en_page(nom: str, pages: list[Page], fm: dict, cfg: ConfigManga) -> list[Resultat]:
    res = []
    attendu, ecarts = 1, []
    for p in pages:                       # sans dérouler les plages : une coquille « 1-99999999 » reste légère
        debut, fin = p.numeros[0], p.numeros[-1]
        if debut != attendu or fin < debut or fin - debut > 1:
            ecarts.append(p.nom)
        attendu = max(fin, debut) + 1
    if ecarts:
        res.append(avertissement("NUMEROTATION", f"{nom} : numérotation des "
                                 f"{'séquences' if cfg.format == 'webtoon' else 'pages'} à revoir à partir de "
                                 f"{lieux(ecarts)} (attendu : 1, 2, 3… ; double page « N-(N+1) »)."))
    inconnues = sorted({e for p in pages for e in p.inconnues})
    if inconnues:
        res.append(avertissement("ETIQUETTE_INCONNUE", f"{nom} : étiquette(s) inconnue(s) {', '.join(inconnues)} "
                                 "(connues : révélation, double page, cliffhanger)."))
    vides = [p.nom for p in pages if not p.cases]
    if vides:
        res.append(avertissement("PAGE_VIDE", f"{nom} : sans case : {lieux(vides)}."))
    if cfg.format == "webtoon":
        return res
    cible = cible_de_pages(fm, cfg)
    total = pages[-1].numeros[-1] if pages else 0
    if cible and total != cible:
        res.append(avertissement("PAGES_CIBLE", f"{nom} : {total} pages pour une cible de {cible}."))
    chargees = [f"{p.nom} ({len(p.cases)})" for p in pages if len(p.cases) > cfg.cases_max_par_page * len(p.numeros)]
    if chargees:
        res.append(avertissement("CASES_PAR_PAGE", f"{nom} : plus de {cfg.cases_max_par_page} cases par page : "
                                 f"{lieux(chargees)}."))
    return res


def verifier_cases(nom: str, pages: list[Page], cfg: ConfigManga) -> list[Resultat]:
    sans_description, bavardes, longues = [], [], []
    for p in pages:
        for c in p.cases:
            ou = f"{p.nom} c. {c.numero}"
            if not c.description:
                sans_description.append(ou)
            if len(c.bulles) > cfg.bulles_max_par_case:
                bavardes.append(f"{ou} ({len(c.bulles)})")
            longues += [f"{ou} {b.locuteur} ({mots(b.texte)} mots)" for b in c.bulles
                        if mots(b.texte) > cfg.mots_max_par_bulle]
    res = []
    if sans_description:
        res.append(avertissement("CASE_SANS_DESCRIPTION", f"{nom} : cases sans description pour le dessin : "
                                 f"{lieux(sans_description)}."))
    if bavardes:
        res.append(avertissement("BULLES_PAR_CASE", f"{nom} : plus de {cfg.bulles_max_par_case} bulles : {lieux(bavardes)}."))
    if longues:
        res.append(avertissement("MOTS_PAR_BULLE", f"{nom} : bulles de plus de {cfg.mots_max_par_bulle} mots : "
                                 f"{lieux(longues)} — couper ou répartir sur deux bulles ou deux cases."))
    return res


def verifier_rythme(nom: str, pages: list[Page], fm: dict, cfg: ConfigManga) -> list[Resultat]:
    res = []
    if cfg.format != "webtoon":
        tourne = "paires" if cfg.page_revelation == "paire" else "impaires"
        mal = [p.nom for p in pages if "revelation" in p.etiquettes and not parite_ok(p.numeros[0], cfg)]
        if mal:
            res.append(avertissement("REVELATION_TOURNE", f"{nom} : révélation sur une page vue avant la tourne "
                                     f"({lieux(mal)}) : la placer sur une page {tourne[:-1]}, découverte en tournant."))
        for p in pages:
            if len(p.numeros) == 2 or "double page" in p.etiquettes:
                a, b = p.numeros[0], p.numeros[-1]
                if b != a + 1 or not parite_ok(a, cfg):
                    res.append(avertissement("DOUBLE_PAGE", f"{nom} : double page {p.nom} : deux pages qui se font face, "
                                             f"la première {tourne[:-1]} (par exemple {'2-3' if tourne == 'paires' else '3-4'})."))
    annonce = fm.get("cliffhanger")
    a_un_cliffhanger = annonce is True or (isinstance(annonce, str) and not vide(annonce)
                                           and normaliser(annonce) not in {"non", "false", "aucun"})
    if cfg.format == "serie" and not a_un_cliffhanger and not any("cliffhanger" in p.etiquettes for p in pages):
        res.append(avertissement("CLIFFHANGER", f"{nom} : pas de cliffhanger (étiquette « (cliffhanger) » sur une page "
                                 "ou champ « cliffhanger » du frontmatter)."))
    return res


def verifier_locuteurs(nom: str, pages: list[Page], entrees: list[vr.Entree]) -> list[Resultat]:
    if not entrees:
        return []
    def connu(voix: str) -> bool:
        voix = voix.strip()
        return (not voix or set(voix) <= {"?"} or normaliser(voix) in LOCUTEURS_GENERIQUES
                or any(e.designe(voix) for e in entrees))

    inconnus = sorted({b.locuteur for p in pages for c in p.cases for b in c.bulles
                       if b.nature == "dialogue" and not all(connu(v) for v in re.split(r"[,&]| ET ", b.locuteur))})
    return [avertissement("LOCUTEUR_INCONNU", f"{nom} : locuteur(s) absent(s) de la bible : {', '.join(inconnus)}.")] \
        if inconnus else []


# ── Assemblage du rapport ──────────────────────────────────────────────────

def lire_chapitre(chemin: Path) -> tuple[dict | None, str, list[Resultat]]:
    brut, corps = separer_frontmatter(chemin.read_text(encoding="utf-8-sig", errors="replace"))
    if brut is None:
        return {}, corps, []
    fm, erreur = charger_frontmatter(brut)
    if fm is None:
        return None, corps, [bloquant("FRONTMATTER_YAML", f"{chemin.name} : {erreur}")]
    return fm, corps, []


def analyser(racine: Path, seulement: int | None = None) -> Rapport:
    cfg = cm.charger(racine)
    rapport = Rapport()
    entrees = vr.lire_bible(racine / cfg.dossier_bible)
    connus = vr.noms_connus(entrees)
    ignores = frozenset(normaliser(n) for n in cfg.noms_ignores)
    pour_plan = []
    for chemin in vr.lister_chapitres(racine / cfg.dossier_chapitres):
        fm, corps, res = lire_chapitre(chemin)
        rapport.resultats += res
        if fm is None:
            continue
        pages = lire_script(corps)
        numero = vr.nombre(fm.get("numero"))
        statut = fm.get("statut") if isinstance(fm.get("statut"), str) else None
        cases = [c for p in pages for c in p.cases]
        info = InfoChapitre(chemin, numero, str(fm.get("titre") or ""), statut,
                            pages[-1].numeros[-1] if pages else 0, len(cases), sum(len(c.bulles) for c in cases))
        rapport.chapitres.append(info)
        pour_plan.append(vr.Chapitre(chemin, numero, info.titre, statut, None, None, corps, 0))
        if seulement is not None and numero != seulement:
            continue
        nom = chemin.name
        if fm.get("statut") is not None and fm.get("statut") not in cfg.statuts:
            rapport.resultats.append(bloquant("STATUT_INCONNU", f"{nom} : statut « {fm.get('statut')} » inconnu "
                                              f"({', '.join(cfg.statuts)})."))
        rapport.resultats += verifier_mise_en_page(nom, pages, fm, cfg) + verifier_cases(nom, pages, cfg)
        rapport.resultats += verifier_rythme(nom, pages, fm, cfg) + verifier_locuteurs(nom, pages, entrees)
        texte = "\n\n".join(" ".join(c.description + [b.texte for b in c.bulles]) for c in cases)
        rapport.resultats += vr.verifier_noms(vr.Chapitre(chemin, numero, info.titre, statut, None, None, texte, 0),
                                              connus, ignores)
    rapport.chapitres.sort(key=lambda c: (c.numero is None, c.numero or 0, c.chemin.name))
    plan_rapport = vr.Rapport()
    vr.verifier_plan(vr.lire_plan(racine / cfg.plan), pour_plan, entrees, cfg, plan_rapport)
    rapport.resultats += plan_rapport.resultats
    rapport.manquants = plan_rapport.manquants
    return rapport


def afficher_avancement(rapport: Rapport, cfg: ConfigManga) -> None:
    unite = "séq." if cfg.format == "webtoon" else "pages"
    print("\n== Avancement")
    for c in rapport.chapitres:
        print(f"  {str(c.numero or '?'):>3}  {c.titre[:36]:<36} {c.statut or '—':<8} {c.pages:>4} {unite} "
              f"{c.cases:>4} cases {c.bulles:>4} bulles")
    for l in rapport.manquants:
        print(f"  {str(l.numero or '?'):>3}  {l.titre[:36]:<36} {'à écrire':<8}")
    print(f"  Total : {sum(c.pages for c in rapport.chapitres)} {unite}")


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Vérifie un script de manga : mise en page, bulles, rythme, continuité.")
    ap.add_argument("--root", help="racine du projet, là où se trouve redactor.json (détectée sinon)")
    ap.add_argument("--chapitre", type=int, help="limiter les contrôles de chapitre à ce numéro")
    try:
        args = ap.parse_args(argv)
    except SystemExit as sortie:
        return 2 if sortie.code else 0
    if yaml is None:
        print("PyYAML absent : installer avec « pip install pyyaml ».", file=sys.stderr)
        return 2
    racine = Path(args.root).resolve() if args.root else cm.trouver_racine(Path.cwd().resolve())
    if racine is None:
        print("Racine du projet introuvable (ni redactor.json, ni chapitres/, ni plan.md) : préciser --root.",
              file=sys.stderr)
        return 2
    try:
        cfg = cm.charger(racine)
        rapport = analyser(racine, args.chapitre)
    except cm.ConfigInvalide as err:
        print(f"Configuration invalide : {err}", file=sys.stderr)
        return 2
    except OSError as err:
        print(f"Lecture impossible : {err}", file=sys.stderr)
        return 2
    afficher_avancement(rapport, cfg)
    afficher("Contrôles", rapport.resultats)
    return 1 if any(r.bloquant for r in rapport.resultats) else 0


if __name__ == "__main__":
    sys.exit(main())
