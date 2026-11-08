#!/usr/bin/env python3
"""Assemble les chapitres d'un roman en un manuscrit, et l'exporte en .docx ou en PDF.

Usage :
    python assembler_manuscrit.py [--root RACINE] [--docx] [--pdf]

Ordre : celui du plan (tableau « ## Chapitres » de <plan>), à défaut le numéro des chapitres.
Sortie : <dossier_manuscrit>/<slug du titre>.md, avec un en-tête (titre, auteur, langue) lu par
pandoc. Les frontmatters sont retirés, chaque chapitre reçoit un titre « # » selon
`titre_chapitre`, et les sauts de scène (« *** », « * * * », « --- ») deviennent « * * * ».
L'export .docx et PDF passe par pandoc (https://pandoc.org) ; le PDF demande en plus un moteur
LaTeX. Sans pandoc, le manuscrit Markdown est produit et l'export est signalé impossible.

Codes de sortie : 0 manuscrit produit (et exporté si demandé) ; 2 échec.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

import config_roman as cr
import verifier_roman as vr

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "encyclopedia" / "scripts"))
from verifier_article import separer_frontmatter, slugifier  # noqa: E402

SAUT_SCENE = "* * *"


class ExportImpossible(RuntimeError):
    """pandoc absent ou en échec."""


def corps_propre(texte: str) -> str:
    _, corps = separer_frontmatter(texte)
    corps = re.sub(r"\A\s*# .*\n", "", corps.lstrip("\n"))        # titre déjà donné par le manuscrit
    corps = vr.SAUT_SCENE_RE.sub(SAUT_SCENE, corps)
    corps = re.sub(rf"\n*^{re.escape(SAUT_SCENE)}$\n*", f"\n\n{SAUT_SCENE}\n\n", corps, flags=re.MULTILINE)
    return corps.strip()


def titre_de_chapitre(modele: str, numero: int | None, titre: str) -> str:
    """Titre d'un chapitre selon `titre_chapitre` ; un chapitre sans numéro (prologue) garde son titre."""
    if numero is None:
        return titre.strip()
    try:
        rendu = modele.format(numero=numero, titre=titre)
    except (KeyError, ValueError, IndexError) as err:
        raise cr.ConfigInvalide(f"« titre_chapitre » invalide ({modele}) : seuls {{numero}} et {{titre}} "
                                f"sont admis ({err}).") from err
    return re.sub(r"[\s—–:-]+$", "", rendu).strip()


def ordre(racine: Path, cfg: cr.ConfigRoman, signaler: Callable[[str], None]) -> list[tuple[int | None, str, Path]]:
    dossier = racine / cfg.dossier_chapitres
    plan = vr.lire_plan(racine / cfg.plan)
    if plan is None:
        chapitres = [vr.lire_chapitre(p)[0] for p in vr.lister_chapitres(dossier)]
        chapitres = sorted((c for c in chapitres if c), key=lambda c: (c.numero is None, c.numero or 0, c.chemin.name))
        return [(c.numero, c.titre, c.chemin) for c in chapitres]
    sequence = []
    prevus = {ligne.fichier for ligne in plan}
    for chemin in vr.lister_chapitres(dossier):
        if chemin.name not in prevus:
            signaler(f"{chemin.name} n'est pas dans le plan : absent du manuscrit (l'ajouter au plan pour l'inclure).")
    for ligne in plan:
        chemin = dossier / ligne.fichier
        if chemin.is_file():
            sequence.append((ligne.numero, ligne.titre, chemin))
        else:
            signaler(f"Chapitre {ligne.numero} ({ligne.titre}) prévu au plan mais pas écrit : absent du manuscrit.")
    return sequence


def assembler(racine: Path, signaler: Callable[[str], None] = print) -> Path:
    cfg = cr.charger(racine)
    titre = cfg.titre or cfg.projet
    # json.dumps produit une chaîne entre guillemets valable en YAML, même avec « " » ou « \ ».
    entete = ["---", f"title: {json.dumps(titre, ensure_ascii=False)}"]
    if cfg.auteur:
        entete.append(f"author: {json.dumps(cfg.auteur, ensure_ascii=False)}")
    entete += ["lang: fr", "---", ""]
    parties = ["\n".join(entete)]
    for numero, titre_chap, chemin in ordre(racine, cfg, signaler):
        chap, _ = vr.lire_chapitre(chemin)
        if chap and chap.statut and chap.statut != cfg.statuts[-1]:
            signaler(f"Chapitre {numero} au statut « {chap.statut} », pas encore « {cfg.statuts[-1]} ».")
        titre_final = titre_chap or (chap.titre if chap else "")
        parties.append(f"# {titre_de_chapitre(cfg.titre_chapitre, numero, titre_final)}\n\n"
                       f"{corps_propre(chemin.read_text(encoding='utf-8-sig', errors='replace'))}\n")
    sortie = racine / cfg.dossier_manuscrit / f"{slugifier(titre) or 'manuscrit'}.md"
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text("\n".join(parties), encoding="utf-8")
    return sortie


def exporter(manuscrit: Path, format_sortie: str, executer: Callable[[list[str]], int] = subprocess.call,
             trouver: Callable[[str], str | None] = shutil.which) -> Path:
    pandoc = trouver("pandoc")
    if pandoc is None:
        raise ExportImpossible("pandoc introuvable : l'installer (https://pandoc.org/installing.html), ou ouvrir "
                               f"{manuscrit.name} dans un traitement de texte pour l'exporter.")
    cible = manuscrit.with_suffix(f".{format_sortie}")
    code = executer([pandoc, str(manuscrit), "-o", str(cible)])
    if code != 0:
        conseil = " Le PDF demande un moteur LaTeX (MiKTeX, TeX Live) ; à défaut, exporter en .docx." \
            if format_sortie == "pdf" else ""
        raise ExportImpossible(f"pandoc a échoué (code {code}).{conseil}")
    return cible


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Assemble le manuscrit d'un roman et l'exporte.")
    ap.add_argument("--root", help="racine du projet, là où se trouve redactor.json (détectée sinon)")
    ap.add_argument("--docx", action="store_true", help="exporter aussi en .docx (pandoc)")
    ap.add_argument("--pdf", action="store_true", help="exporter aussi en PDF (pandoc et LaTeX)")
    try:
        args = ap.parse_args(argv)
    except SystemExit as sortie:
        return 2 if sortie.code else 0
    racine = Path(args.root).resolve() if args.root else cr.trouver_racine(Path.cwd().resolve())
    if racine is None:
        print("Racine du roman introuvable : préciser --root.", file=sys.stderr)
        return 2
    try:
        manuscrit = assembler(racine, signaler=lambda m: print(f"  avertissement : {m}"))
        print(f"Manuscrit : {manuscrit}")
        for fmt in [f for f, voulu in (("docx", args.docx), ("pdf", args.pdf)) if voulu]:
            print(f"Export : {exporter(manuscrit, fmt)}")
    except (cr.ConfigInvalide, ExportImpossible, OSError) as err:
        print(f"Échec : {err}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
