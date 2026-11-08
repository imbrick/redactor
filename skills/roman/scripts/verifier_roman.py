#!/usr/bin/env python3
"""Vérificateur d'un roman : avancement, continuité, style et, pour le polar, indices.

Usage :
    python verifier_roman.py [--root RACINE] [--chapitre N]

Lit le plan (<plan>, tableau « ## Chapitres »), la bible (<dossier_bible>/*.md : une entrée
« ## Nom » par personnage, lieu ou terme, avec des lignes « - clé : valeur ») et les chapitres
(<dossier_chapitres>/*.md, frontmatter numero, titre, pdv, date_recit, statut).

  - Avancement (rapport) : mots par chapitre, total et objectif, chapitres prévus non écrits.
  - BLOQUANT : frontmatter illisible, statut inconnu, date_recit mal formée, indice exploité avant
    d'être posé, révélation préparée par un indice posé trop tard.
  - avertissement : plan absent, chapitre hors plan ou numéroté autrement que dans le plan,
    personnage du plan ou point de vue absent de la bible, variante d'un nom de la bible, nom récurrent absent de
    la bible, point de vue d'un personnage pas encore né ou déjà mort, répétitions proches,
    adverbes en -ment, tics déclarés, dialogue au trait d'union, indice non exploité, révélation
    non préparée, indice ou chapitre inconnu, polar sans fichier d'indices.

Codes de sortie : 0 aucun bloquant ; 1 au moins un bloquant ; 2 vérification impossible.
Dépendance : PyYAML.
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import config_roman as cr
from config_roman import ConfigRoman

# Lecture du frontmatter, résultats et affichage : skill encyclopedia du même plugin.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "encyclopedia" / "scripts"))
from verifier_article import (  # noqa: E402
    Resultat, afficher, avertissement, bloquant, charger_frontmatter, separer_frontmatter, yaml)

# Utilitaires de texte communs aux skills (commun/texte.py à la racine du plugin).
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "commun"))
from texte import mots, normaliser, sections_markdown, table, vide  # noqa: E402

FICHIER_INDICES = "indices.md"
DATE_RECIT_RE = re.compile(r"^\d{4}(?:-\d{2}(?:-\d{2})?)?$")
ANNEE_RE = re.compile(r"\b(\d{4})\b")
ATTRIBUT_RE = re.compile(r"^\s*[-*]\s*([^:]+?)\s*:\s*(.*)$")
MOT_RE = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*")
# Mot à majuscule ; il peut suivre une élision (« d'Élodie »).
MAJUSCULE_RE = re.compile(r"(?<![\w-])([A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ]+(?:-[A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ]+)?)")
OUVRANTS = " \t\u00a0\u202f«“\"([*_"          # ponctuation ou balisage qui peut ouvrir une phrase
FERMANTS = ")»”\"' \u00a0\u202f"
FINS_DE_PHRASE = ".!?…:—–»\n"
REGARD_ARRIERE = 16                              # caractères examinés avant un mot
TIRET_DIALOGUE_RE = re.compile(r"^\s*-(?!-)\s*\S", re.MULTILINE)
SAUT_SCENE_RE = re.compile(r"^\s*(?:\*\s*){3,}$|^\s*(?:-\s*){3,}$", re.MULTILINE)

FENETRE_REPETITION = 25        # mots
REPETITION_MIN_LONGUEUR = 5
REPETITION_MIN_PROCHES = 2     # au moins deux reprises rapprochées pour signaler un mot
REPETITIONS_AFFICHEES = 5
ADVERBES_POUR_CENT_MOTS = 1.5
ADVERBES_MIN = 3
TIC_MIN = 2
NOM_HORS_BIBLE_MIN = 3
NOM_MIN_LONGUEUR = 4
SEUIL_VARIANTE = 0.8

MOTS_VIDES = frozenset(normaliser(m) for m in """
    alors aucun aussi autre autres avant avoir avait avaient avec beaucoup cela celle celles celui
    cette ceux chaque chez comme comment contre dans depuis donc elle elles encore entre était étaient
    être faire fait leur leurs lorsque mais même mêmes moins notre nous parce pendant peut plus
    pour pourquoi quand quelle quelles quelque quels sans selon sera sont sous tous tout toute
    toutes très votre vous était""".split())
# Mots en -ment qui sont des noms, pas des adverbes.
NOMS_EN_MENT = frozenset(normaliser(m) for m in """
    moment gouvernement document comportement mouvement bâtiment changement appartement sentiment
    vêtement élément événement instrument argument monument traitement département jugement
    logement enseignement développement fonctionnement régiment testament médicament aliment
    ciment serment tourment segment fragment parlement paiement équipement établissement
    commencement avertissement rassemblement raisonnement encouragement comment firmament
    froment gisement glissement agrandissement licenciement règlement""".split())
# Mots usuels écrits avec une majuscule qui ne sont pas des noms à mettre dans la bible.
MAJUSCULES_USUELLES = frozenset(normaliser(m) for m in """
    lundi mardi mercredi jeudi vendredi samedi dimanche janvier février mars avril mai juin juillet
    août septembre octobre novembre décembre monsieur madame mademoiselle messieurs mesdames maître
    docteur professeur dieu seigneur sainte saint noël pâques chapitre commissaire inspecteur
    inspectrice capitaine lieutenant colonel général sergent brigadier juge maire président
    présidente directeur directrice maman papa oncle tante grand-mère grand-père""".split())


@dataclass(frozen=True)
class Entree:
    nom: str
    alias: tuple[str, ...]
    attributs: dict

    @property
    def designations(self) -> set[str]:
        return {normaliser(n) for n in (self.nom, *self.alias) if n.strip()}

    @property
    def mots_du_nom(self) -> set[str]:
        """Mots à majuscule du nom et des alias : « Marc Lefèvre » → marc, lefevre."""
        return {normaliser(m) for n in (self.nom, *self.alias) for m in MOT_RE.findall(n) if m[:1].isupper()}

    def designe(self, texte: str) -> bool:
        n = normaliser(texte)
        return n in self.designations or n in self.mots_du_nom


@dataclass(frozen=True)
class LignePlan:
    numero: int | None
    titre: str
    fichier: str
    personnages: tuple[str, ...]


@dataclass(frozen=True)
class Chapitre:
    chemin: Path
    numero: int | None
    titre: str
    statut: str | None
    pdv: str | None
    date_recit: str | None
    corps: str
    mots: int


@dataclass
class Rapport:
    resultats: list[Resultat] = field(default_factory=list)
    chapitres: list[Chapitre] = field(default_factory=list)
    manquants: list[LignePlan] = field(default_factory=list)
    objectif: int | None = None

    @property
    def total(self) -> int:
        return sum(c.mots for c in self.chapitres)


# ── Lecture du projet ──────────────────────────────────────────────────────

def nombre(texte) -> int | None:
    m = re.search(r"\d+", str(texte or ""))
    return int(m.group(0)) if m else None


def lire_bible(dossier: Path) -> list[Entree]:
    entrees = []
    if not dossier.is_dir():
        return entrees
    for fichier in sorted(dossier.glob("*.md")):
        if fichier.name == FICHIER_INDICES:
            continue
        morceaux = re.split(r"^## +(.+?)\s*$", fichier.read_text(encoding="utf-8-sig", errors="replace"),
                            flags=re.MULTILINE)
        for i in range(1, len(morceaux) - 1, 2):
            attributs = {}
            for ligne in morceaux[i + 1].splitlines():
                m = ATTRIBUT_RE.match(ligne)
                if m:
                    attributs[normaliser(m.group(1))] = m.group(2).strip()
            alias = tuple(a.strip() for a in attributs.get("alias", "").split(",") if not vide(a.strip()))
            entrees.append(Entree(morceaux[i].strip(), alias, attributs))
    return entrees


def lire_plan(chemin: Path) -> list[LignePlan] | None:
    if not chemin.is_file():
        return None
    texte = chemin.read_text(encoding="utf-8-sig", errors="replace")
    _, lignes = table(sections_markdown(texte).get("chapitres", ""))
    return [LignePlan(nombre(l.get("#")), l.get("titre", ""), Path(l.get("fichier", "").strip()).name,
                      tuple(p.strip() for p in l.get("personnages", "").split(",") if not vide(p.strip())))
            for l in lignes]


def lire_chapitre(chemin: Path) -> tuple[Chapitre | None, list[Resultat]]:
    brut, corps = separer_frontmatter(chemin.read_text(encoding="utf-8-sig", errors="replace"))
    fm: dict = {}
    if brut is not None:
        fm, erreur = charger_frontmatter(brut)
        if fm is None:
            return None, [bloquant("FRONTMATTER_YAML", f"{chemin.name} : {erreur}")]
    date_recit = fm.get("date_recit")
    if isinstance(date_recit, int) and not isinstance(date_recit, bool) and 1000 <= date_recit <= 9999:
        date_recit = str(date_recit)                 # année écrite sans guillemets
    resultats = []
    if date_recit is not None and not (isinstance(date_recit, str) and DATE_RECIT_RE.match(date_recit)):
        conseil = " (entre guillemets)" if isinstance(date_recit, date) else ""
        resultats.append(bloquant("DATE_RECIT", f"{chemin.name} : date_recit attendue sous la forme "
                                  f'"AAAA", "AAAA-MM" ou "AAAA-MM-JJ"{conseil}.'))
        date_recit = None
    statut = fm.get("statut")
    return Chapitre(chemin, nombre(fm.get("numero")), str(fm.get("titre") or ""),
                    statut if isinstance(statut, str) else None,
                    fm.get("pdv") if isinstance(fm.get("pdv"), str) else None,
                    date_recit, corps, mots(corps)), resultats


# ── Contrôles du plan ──────────────────────────────────────────────────────

def verifier_plan(plan: list[LignePlan] | None, chapitres: list[Chapitre], entrees: list[Entree],
                  cfg: ConfigRoman, rapport: Rapport) -> None:
    if plan is None:
        rapport.resultats.append(avertissement("PLAN_ABSENT", f"Pas de plan ({cfg.plan}) : l'avancement est "
                                               "calculé sur les seuls chapitres écrits."))
        return
    par_fichier = {c.chemin.name: c for c in chapitres}
    prevus = {l.fichier for l in plan}
    for ligne in plan:
        chap = par_fichier.get(ligne.fichier)
        if chap is None:
            rapport.manquants.append(ligne)
        elif ligne.numero is not None and chap.numero is not None and chap.numero != ligne.numero:
            rapport.resultats.append(avertissement(
                "NUMERO_PLAN", f"{ligne.fichier} : numéro {chap.numero} dans le chapitre, {ligne.numero} dans le plan."))
    for chap in chapitres:
        if chap.chemin.name not in prevus:
            rapport.resultats.append(avertissement("CHAPITRE_HORS_PLAN", f"{chap.chemin.name} n'est pas dans le plan."))
    for ligne in plan:
        for perso in ligne.personnages:
            if not any(e.designe(perso) for e in entrees):
                rapport.resultats.append(avertissement(
                    "PERSONNAGE_INCONNU", f"Chapitre {ligne.numero} du plan : « {perso} » absent de la bible."))


# ── Contrôles de continuité ────────────────────────────────────────────────

def noms_connus(entrees: list[Entree]) -> set[str]:
    connus = set()
    for e in entrees:
        connus |= e.designations | e.mots_du_nom
    return connus


def debut_de_phrase(corps: str, position: int) -> bool:
    """Le mot qui commence à `position` ouvre-t-il une phrase, une ligne ou une réplique ?"""
    debut_ligne = corps.rfind("\n", 0, position) + 1
    if not corps[debut_ligne:position].strip(OUVRANTS + "#>—–-"):
        return True
    avant = corps[max(debut_ligne, position - REGARD_ARRIERE):position].rstrip(OUVRANTS)
    if not avant or avant[-1] in FINS_DE_PHRASE:
        return True
    sans_fermants = avant.rstrip(FERMANTS)
    return bool(sans_fermants) and sans_fermants[-1] in ".!?…"


def noms_en_majuscule(corps: str) -> list[str]:
    """Mots à majuscule qui ne commencent pas une phrase ni une réplique."""
    return [m.group(1) for m in MAJUSCULE_RE.finditer(corps) if not debut_de_phrase(corps, m.start())]


def verifier_noms(chap: Chapitre, connus: set[str], ignores: frozenset[str] = frozenset()) -> list[Resultat]:
    res = []
    inconnus = Counter()
    deja = set()
    proches: dict[str, list[str]] = {}
    connus_simples = [c for c in connus if " " not in c and len(c) >= NOM_MIN_LONGUEUR]
    for nom in noms_en_majuscule(chap.corps):
        n = normaliser(nom)
        if n in connus or n in MAJUSCULES_USUELLES or n in ignores or len(n) < NOM_MIN_LONGUEUR:
            continue
        if n not in proches:
            proches[n] = difflib.get_close_matches(n, connus_simples, n=1, cutoff=SEUIL_VARIANTE)
        proche = proches[n]
        if proche:
            if (n, proche[0]) not in deja:
                deja.add((n, proche[0]))
                modele = next((m for m in MOT_RE.findall(chap.corps) if normaliser(m) == proche[0]), proche[0])
                res.append(avertissement("NOM_VARIANTE", f"{chap.chemin.name} : « {nom} » ressemble à "
                                         f"« {modele.capitalize() if modele.islower() else modele} » (bible)."))
        else:
            inconnus[nom] += 1
    recurrents = [n for n, k in inconnus.most_common() if k >= NOM_HORS_BIBLE_MIN]
    if recurrents:
        res.append(avertissement("NOM_HORS_BIBLE", f"{chap.chemin.name} : nom(s) récurrent(s) absent(s) de la "
                                 f"bible : {', '.join(recurrents)}."))
    return res


def annee(texte) -> int | None:
    m = ANNEE_RE.search(str(texte or ""))
    return int(m.group(1)) if m else None


def verifier_pdv(chap: Chapitre, entrees: list[Entree]) -> list[Resultat]:
    if not chap.pdv or not entrees:
        return []
    entree = next((e for e in entrees if normaliser(chap.pdv) in e.designations), None) \
        or next((e for e in entrees if e.designe(chap.pdv)), None)
    if entree is None:
        return [avertissement("PDV_INCONNU", f"{chap.chemin.name} : point de vue « {chap.pdv} » absent de la bible.")]
    an = annee(chap.date_recit)
    if an is None:
        return []
    naissance, mort = annee(entree.attributs.get("naissance")), annee(entree.attributs.get("mort"))
    if naissance and an < naissance:
        return [avertissement("PDV_CHRONOLOGIE", f"{chap.chemin.name} : point de vue de {entree.nom} en {an}, "
                              f"avant sa naissance ({naissance}).")]
    if mort and an > mort:
        return [avertissement("PDV_CHRONOLOGIE", f"{chap.chemin.name} : point de vue de {entree.nom} en {an}, "
                              f"après sa mort ({mort}).")]
    return []


# ── Contrôles de style ─────────────────────────────────────────────────────

def verifier_style(chap: Chapitre, connus: set[str], cfg: ConfigRoman) -> list[Resultat]:
    res = []
    # « qu'il », « c'était » : seul le mot après l'élision compte.
    jetons = [normaliser(m).split("'")[-1] for m in MOT_RE.findall(chap.corps)]
    positions: dict[str, list[int]] = {}
    for i, j in enumerate(jetons):
        if len(j) >= REPETITION_MIN_LONGUEUR and j not in MOTS_VIDES and j not in connus:
            positions.setdefault(j, []).append(i)
    proches = Counter({m: sum(1 for a, b in zip(p, p[1:]) if b - a <= FENETRE_REPETITION)
                       for m, p in positions.items()})
    signales = [f"{m} ({k + 1}×)" for m, k in proches.most_common(REPETITIONS_AFFICHEES) if k >= REPETITION_MIN_PROCHES]
    if signales:
        res.append(avertissement("REPETITION_PROCHE", f"{chap.chemin.name} : répétitions rapprochées : "
                                 f"{', '.join(signales)}."))
    adverbes = [j for j in jetons if j.endswith("ment") and len(j) >= 7 and j not in NOMS_EN_MENT]
    if jetons and len(adverbes) >= ADVERBES_MIN and 100 * len(adverbes) / len(jetons) > ADVERBES_POUR_CENT_MOTS:
        res.append(avertissement("ADVERBES_MENT", f"{chap.chemin.name} : {len(adverbes)} adverbes en -ment "
                                 f"pour {len(jetons)} mots ({', '.join(sorted(set(adverbes))[:6])})."))
    texte = " " + " ".join(jetons) + " "
    for tic in cfg.tics:
        n = texte.count(f" {normaliser(tic)} ")
        if n >= TIC_MIN:
            res.append(avertissement("TIC", f"{chap.chemin.name} : « {tic} » {n} fois."))
    tirets = len(TIRET_DIALOGUE_RE.findall(SAUT_SCENE_RE.sub("", chap.corps)))
    if tirets:
        res.append(avertissement("DIALOGUE_TIRET", f"{chap.chemin.name} : {tirets} réplique(s) au trait d'union "
                                 "« - » : utiliser le tiret cadratin « — » (ou demi-cadratin « – »)."))
    return res


# ── Indices et révélations (polar) ─────────────────────────────────────────

def verifier_indices(chemin: Path, numeros: set[int], cfg: ConfigRoman) -> list[Resultat]:
    if not chemin.is_file():
        if cfg.genre == "polar":
            return [avertissement("INDICES_ABSENTS", f"Polar sans {chemin.name} : tenir le registre des indices "
                                  "et des révélations (references/genres.md).")]
        return []
    secs = sections_markdown(chemin.read_text(encoding="utf-8-sig", errors="replace"))
    _, indices = table(secs.get("indices", ""))
    _, revelations = table(secs.get("revelations", ""))
    res, poses = [], {}
    for l in indices:
        ident = l.get("#", "?")
        pose, exploite = nombre(l.get("pose")), nombre(l.get("exploite"))
        poses[normaliser(ident)] = pose
        for n in (pose, exploite):
            if n is not None and numeros and n not in numeros:
                res.append(avertissement("INDICE_CHAPITRE", f"Indice {ident} : chapitre {n} inconnu du plan."))
        if exploite is None:
            res.append(avertissement("INDICE_NON_EXPLOITE", f"Indice {ident} ({l.get('indice', '')}) posé "
                                     f"au chapitre {pose}, jamais exploité."))
        elif pose is not None and exploite < pose:
            res.append(bloquant("INDICE_ORDRE", f"Indice {ident} exploité au chapitre {exploite}, "
                                f"avant d'être posé (chapitre {pose})."))
    for l in revelations:
        ident, chap = l.get("#", "?"), nombre(l.get("chapitre"))
        prepare = [p.strip() for p in re.split(r"[,;]", l.get("preparee par", "")) if not vide(p.strip())]
        if not prepare:
            res.append(avertissement("REVELATION_NON_PREPAREE", f"Révélation {ident} ({l.get('revelation', '')}) "
                                     "sans indice qui la prépare."))
        for p in prepare:
            if normaliser(p) not in poses:
                res.append(avertissement("INDICE_INCONNU", f"Révélation {ident} : indice « {p} » absent du tableau."))
            elif chap is not None and poses[normaliser(p)] is not None and poses[normaliser(p)] >= chap:
                res.append(bloquant("REVELATION_TROP_TOT", f"Révélation {ident} au chapitre {chap}, préparée par "
                                    f"{p} posé au chapitre {poses[normaliser(p)]} : le lecteur ne peut pas l'avoir vu."))
    return res


# ── Assemblage du rapport ──────────────────────────────────────────────────

def lister_chapitres(dossier: Path) -> list[Path]:
    return sorted(dossier.glob("*.md")) if dossier.is_dir() else []


def analyser(racine: Path, seulement: int | None = None) -> Rapport:
    cfg = cr.charger(racine)
    rapport = Rapport(objectif=cfg.objectif_mots)
    entrees = lire_bible(racine / cfg.dossier_bible)
    for chemin in lister_chapitres(racine / cfg.dossier_chapitres):
        chap, res = lire_chapitre(chemin)
        rapport.resultats += res
        if chap is not None:
            rapport.chapitres.append(chap)
    rapport.chapitres.sort(key=lambda c: (c.numero is None, c.numero or 0, c.chemin.name))
    plan = lire_plan(racine / cfg.plan)
    verifier_plan(plan, rapport.chapitres, entrees, cfg, rapport)

    connus = noms_connus(entrees)
    for chap in rapport.chapitres:
        if seulement is not None and chap.numero != seulement:
            continue
        if chap.statut is not None and chap.statut not in cfg.statuts:
            rapport.resultats.append(bloquant("STATUT_INCONNU", f"{chap.chemin.name} : statut « {chap.statut} » "
                                              f"inconnu ({', '.join(cfg.statuts)})."))
        ignores = frozenset(normaliser(n) for n in cfg.noms_ignores)
        rapport.resultats += verifier_noms(chap, connus, ignores) + verifier_pdv(chap, entrees)
        rapport.resultats += verifier_style(chap, connus, cfg)

    numeros = {l.numero for l in plan if l.numero is not None} if plan else {c.numero for c in rapport.chapitres if c.numero}
    rapport.resultats += verifier_indices(racine / cfg.dossier_bible / FICHIER_INDICES, numeros, cfg)
    return rapport


def afficher_avancement(rapport: Rapport) -> None:
    print("\n== Avancement")
    for c in rapport.chapitres:
        print(f"  {str(c.numero or '?'):>3}  {c.titre[:40]:<40} {c.statut or '—':<10} {c.mots:>7} mots")
    for l in rapport.manquants:
        print(f"  {str(l.numero or '?'):>3}  {l.titre[:40]:<40} {'à écrire':<10} {0:>7} mots")
    ligne = f"  Total : {rapport.total} mots"
    if rapport.objectif:
        ligne += f" sur {rapport.objectif} ({100 * rapport.total // rapport.objectif} %)"
    print(ligne)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Vérifie un roman : avancement, continuité, style, indices.")
    ap.add_argument("--root", help="racine du projet, là où se trouve redactor.json (détectée sinon)")
    ap.add_argument("--chapitre", type=int, help="limiter les contrôles de chapitre à ce numéro")
    try:
        args = ap.parse_args(argv)
    except SystemExit as sortie:
        return 2 if sortie.code else 0
    if yaml is None:
        print("PyYAML absent : installer avec « pip install pyyaml ».", file=sys.stderr)
        return 2
    racine = Path(args.root).resolve() if args.root else cr.trouver_racine(Path.cwd().resolve())
    if racine is None:
        print("Racine du roman introuvable (ni redactor.json, ni chapitres/, ni plan.md) : préciser --root.",
              file=sys.stderr)
        return 2
    try:
        rapport = analyser(racine, args.chapitre)
    except cr.ConfigInvalide as err:
        print(f"Configuration invalide : {err}", file=sys.stderr)
        return 2
    except OSError as err:
        print(f"Lecture impossible : {err}", file=sys.stderr)
        return 2
    afficher_avancement(rapport)
    afficher("Contrôles", rapport.resultats)
    return 1 if any(r.bloquant for r in rapport.resultats) else 0


if __name__ == "__main__":
    sys.exit(main())
