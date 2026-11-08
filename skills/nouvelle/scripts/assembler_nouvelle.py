#!/usr/bin/env python3
"""Met en forme une nouvelle, ou assemble un recueil, et l'exporte en .docx ou en PDF.

Usage :
    python assembler_nouvelle.py <nouvelles/fichier.md> [--anonyme] [--docx] [--pdf] [--root RACINE]
    python assembler_nouvelle.py --recueil [--docx] [--pdf] [--root RACINE]

Sortie : <dossier_manuscrit>/<slug du titre>.md avec un en-tête (titre, auteur, langue) lu par
pandoc ; frontmatter retiré, sauts de scène uniformisés en « * * * ». Une nouvelle liée à un
concours qui exige l'anonymat est produite sans nom d'auteur, sauf --signe. Recueil : nouvelles
dans l'ordre de <recueil>, chacune sous un titre « # ». Export : pandoc, comme le skill roman.

Codes de sortie : 0 produit (et exporté si demandé) ; 2 échec.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable

import config_nouvelle as cn
import verifier_nouvelle as vn

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "roman" / "scripts"))
import assembler_manuscrit as am  # noqa: E402
from verifier_article import charger_frontmatter, separer_frontmatter, slugifier  # noqa: E402


def frontmatter(chemin: Path) -> dict:
    brut, _ = separer_frontmatter(chemin.read_text(encoding="utf-8-sig", errors="replace"))
    fm, _ = charger_frontmatter(brut) if brut is not None else ({}, None)
    return fm or {}


def entete(titre: str, auteur: str | None) -> str:
    lignes = ["---", f"title: {json.dumps(titre, ensure_ascii=False)}"]
    if auteur:
        lignes.append(f"author: {json.dumps(auteur, ensure_ascii=False)}")
    return "\n".join(lignes + ["lang: fr", "---", ""])


def concours_anonyme(fm: dict, racine: Path, cfg: cn.ConfigNouvelle) -> bool:
    """Le concours de la nouvelle exige-t-il l'anonymat ? Un règlement illisible est une erreur :
    mieux vaut s'arrêter que signer par mégarde un texte destiné à un concours anonyme."""
    if vide_ou_absent(fm.get("concours")):
        return False
    chemin = vn.chemin_reglement(racine, cfg, fm["concours"])
    regl, erreur = vn.lire_reglement(chemin) if chemin else (None, f"identifiant « {fm['concours']} » invalide")
    if regl is None:
        raise cn.ConfigInvalide(f"règlement du concours illisible ({erreur}) : le corriger, ou forcer avec "
                                "--anonyme ou --signe.")
    return bool(regl.get("anonymat"))


def vide_ou_absent(valeur) -> bool:
    return valeur is None or (isinstance(valeur, str) and not valeur.strip())


def ecrire(racine: Path, cfg: cn.ConfigNouvelle, titre: str, contenu: str, prefixe: str = "") -> Path:
    sortie = racine / cfg.dossier_manuscrit / f"{prefixe}{slugifier(titre) or 'nouvelle'}.md"
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(contenu, encoding="utf-8")
    return sortie


def assembler_nouvelle(chemin: Path, racine: Path, anonyme: bool | None = None) -> Path:
    cfg = cn.charger(racine)
    fm = frontmatter(chemin)
    titre = str(fm.get("titre") or chemin.stem)
    if anonyme is None:
        anonyme = concours_anonyme(fm, racine, cfg)
    auteur = None if anonyme else (fm.get("auteur") if isinstance(fm.get("auteur"), str) else cfg.auteur)
    corps = am.corps_propre(chemin.read_text(encoding="utf-8-sig", errors="replace"))
    return ecrire(racine, cfg, titre, entete(titre, auteur) + "\n" + corps + "\n")


def assembler_recueil(racine: Path, signaler: Callable[[str], None] = print, anonyme: bool = False) -> Path:
    cfg = cn.charger(racine)
    rapport = vn.verifier_recueil(racine)
    for r in rapport.resultats:
        if r.code in {"NOUVELLE_MANQUANTE", "HORS_RECUEIL", "RECUEIL_ABSENT"}:
            signaler(r.message)
    titre = cfg.titre_recueil or cfg.projet
    parties = [entete(titre, None if anonyme else cfg.auteur)]
    for n in rapport.nouvelles:
        corps = am.corps_propre(n.chemin.read_text(encoding="utf-8-sig", errors="replace"))
        parties.append(f"# {n.titre or n.chemin.stem}\n\n{corps}\n")
    # Préfixe : le recueil n'écrase jamais une nouvelle qui porterait le même titre.
    return ecrire(racine, cfg, titre, "\n".join(parties), prefixe="recueil-")


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Met en forme une nouvelle ou assemble un recueil, puis l'exporte.")
    ap.add_argument("nouvelle", nargs="?", help="chemin du fichier .md")
    ap.add_argument("--recueil", action="store_true", help="assembler le recueil")
    groupe = ap.add_mutually_exclusive_group()
    groupe.add_argument("--anonyme", action="store_true", help="sans nom d'auteur")
    groupe.add_argument("--signe", action="store_true", help="avec le nom d'auteur, même pour un concours anonyme")
    ap.add_argument("--docx", action="store_true", help="exporter aussi en .docx (pandoc)")
    ap.add_argument("--pdf", action="store_true", help="exporter aussi en PDF (pandoc et LaTeX)")
    ap.add_argument("--root", help="racine du projet, là où se trouve redactor.json (détectée sinon)")
    try:
        args = ap.parse_args(argv)
        if not args.nouvelle and not args.recueil:
            ap.error("indiquer une nouvelle ou --recueil")
    except SystemExit as sortie:
        return 2 if sortie.code else 0
    departs = [Path(args.nouvelle).resolve().parent] if args.nouvelle else []
    racine = Path(args.root).resolve() if args.root else cn.trouver_racine(*departs, Path.cwd().resolve())
    if racine is None:
        print("Racine du projet introuvable : préciser --root.", file=sys.stderr)
        return 2
    try:
        if args.recueil:
            sortie = assembler_recueil(racine, signaler=lambda m: print(f"  avertissement : {m}"),
                                       anonyme=args.anonyme)
        else:
            anonyme = True if args.anonyme else (False if args.signe else None)
            sortie = assembler_nouvelle(Path(args.nouvelle).resolve(), racine, anonyme)
        print(f"Manuscrit : {sortie}")
        for fmt in [f for f, voulu in (("docx", args.docx), ("pdf", args.pdf)) if voulu]:
            print(f"Export : {am.exporter(sortie, fmt)}")
    except (cn.ConfigInvalide, am.ExportImpossible, OSError) as err:
        print(f"Échec : {err}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
