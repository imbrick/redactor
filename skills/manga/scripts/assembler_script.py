#!/usr/bin/env python3
"""Assemble le script complet d'un manga pour le dessinateur, et la feuille de lettrage.

Usage :
    python assembler_script.py [--root RACINE] [--lettrage] [--docx] [--pdf]

Script : <dossier_manuscrit>/<slug du titre>-script.md, chapitres dans l'ordre du plan (à défaut,
de leur numéro), chaque chapitre sous « # Chapitre N — Titre », pages et cases décalées d'un
niveau (« ### Page », « #### Case »), frontmatters retirés.
Lettrage (--lettrage) : <slug>-lettrage.md, un tableau par chapitre : page, case, locuteur,
nature (dialogue, pensée, narration, onomatopée) et texte de chaque bulle, pour le lettreur.
Export .docx ou PDF par pandoc, comme le skill roman.

Codes de sortie : 0 produit (et exporté si demandé) ; 2 échec.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Callable

import config_manga as cm
import verifier_manga as vm

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "roman" / "scripts"))
import assembler_manuscrit as am  # noqa: E402
import verifier_roman as vr  # noqa: E402
from verifier_article import slugifier  # noqa: E402


def entete(cfg: cm.ConfigManga, sous_titre: str) -> str:
    titre = cfg.titre or cfg.projet
    lignes = ["---", f"title: {json.dumps(titre, ensure_ascii=False)}",
              f"subtitle: {json.dumps(sous_titre, ensure_ascii=False)}"]
    auteurs = [a for a in (cfg.auteur, cfg.dessinateur) if a]
    if auteurs:
        lignes.append(f"author: {json.dumps(auteurs, ensure_ascii=False)}")
    return "\n".join(lignes + ["lang: fr", "---", ""])


def chapitres_dans_l_ordre(racine: Path, cfg: cm.ConfigManga, signaler: Callable[[str], None]):
    """(numéro, titre, frontmatter, corps) de chaque chapitre écrit, dans l'ordre du plan."""
    dossier = racine / cfg.dossier_chapitres
    lus = {}
    for chemin in vr.lister_chapitres(dossier):
        fm, corps, _ = vm.lire_chapitre(chemin)
        if fm is not None:
            lus[chemin.name] = (vr.nombre(fm.get("numero")), str(fm.get("titre") or ""), fm, corps)
    plan = vr.lire_plan(racine / cfg.plan)
    if plan is None:
        return sorted(lus.values(), key=lambda c: (c[0] is None, c[0] or 0))
    sequence, vus = [], set()
    for ligne in plan:
        if ligne.fichier in vus:
            signaler(f"{ligne.fichier} figure deux fois dans le plan : la ligne en double est ignorée.")
            continue
        vus.add(ligne.fichier)
        if ligne.fichier in lus:
            numero, titre, fm, corps = lus.pop(ligne.fichier)
            sequence.append((ligne.numero if ligne.numero is not None else numero, ligne.titre or titre, fm, corps))
        else:
            signaler(f"Chapitre {ligne.numero} ({ligne.titre}) prévu au plan mais pas écrit.")
    for nom in sorted(lus):
        signaler(f"{nom} n'est pas dans le plan : absent du script assemblé.")
    return sequence


def ecrire(racine: Path, cfg: cm.ConfigManga, suffixe: str, contenu: str) -> Path:
    sortie = racine / cfg.dossier_manuscrit / f"{slugifier(cfg.titre or cfg.projet) or 'manga'}-{suffixe}.md"
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(contenu, encoding="utf-8")
    return sortie


def titre_chapitre(numero, titre: str) -> str:
    return f"Chapitre {numero} — {titre}" if numero is not None and titre else (titre or f"Chapitre {numero}")


def assembler_script(racine: Path, signaler: Callable[[str], None] = print) -> Path:
    cfg = cm.charger(racine)
    parties = [entete(cfg, "Script")]
    for numero, titre, fm, corps in chapitres_dans_l_ordre(racine, cfg, signaler):
        decale = re.sub(r"^(#{1,5})(\s)", r"#\1\2", corps.strip(), flags=re.MULTILINE)
        parties.append(f"# {titre_chapitre(numero, titre)}\n\n{decale}\n")
    return ecrire(racine, cfg, "script", "\n".join(parties))


def cellule(texte: str) -> str:
    return texte.replace("\\", "\\\\").replace("|", "\\|").strip()


def feuille_de_lettrage(racine: Path, signaler: Callable[[str], None] = print) -> Path:
    cfg = cm.charger(racine)
    parties = [entete(cfg, "Lettrage")]
    for numero, titre, _fm, corps in chapitres_dans_l_ordre(racine, cfg, signaler):
        lignes = [f"# {titre_chapitre(numero, titre)}", "", "| Page | Case | Locuteur | Nature | Texte |",
                  "|---|---|---|---|---|"]
        for page in vm.lire_script(corps):
            nom_page = "-".join(map(str, page.numeros))
            for case in page.cases:
                for b in case.bulles:
                    nature = b.precision or b.nature
                    lignes.append(f"| {nom_page} | {case.numero} | {cellule(b.locuteur)} | {cellule(nature)} | {cellule(b.texte)} |")
                for son in case.sfx:
                    lignes.append(f"| {nom_page} | {case.numero} | SFX | onomatopée | {cellule(son)} |")
        parties.append("\n".join(lignes) + "\n")
    return ecrire(racine, cfg, "lettrage", "\n".join(parties))


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Assemble le script d'un manga et la feuille de lettrage.")
    ap.add_argument("--root", help="racine du projet, là où se trouve redactor.json (détectée sinon)")
    ap.add_argument("--lettrage", action="store_true", help="produire aussi la feuille de lettrage")
    ap.add_argument("--docx", action="store_true", help="exporter aussi en .docx (pandoc)")
    ap.add_argument("--pdf", action="store_true", help="exporter aussi en PDF (pandoc et LaTeX)")
    try:
        args = ap.parse_args(argv)
    except SystemExit as sortie:
        return 2 if sortie.code else 0
    racine = Path(args.root).resolve() if args.root else cm.trouver_racine(Path.cwd().resolve())
    if racine is None:
        print("Racine du projet introuvable : préciser --root.", file=sys.stderr)
        return 2
    signaler = lambda m: print(f"  avertissement : {m}")  # noqa: E731
    try:
        sorties = [assembler_script(racine, signaler)]
        if args.lettrage:
            sorties.append(feuille_de_lettrage(racine, lambda m: None))
        for sortie in sorties:
            print(f"Produit : {sortie}")
            for fmt in [f for f, voulu in (("docx", args.docx), ("pdf", args.pdf)) if voulu]:
                print(f"Export : {am.exporter(sortie, fmt)}")
    except (cm.ConfigInvalide, am.ExportImpossible, OSError) as err:
        print(f"Échec : {err}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
