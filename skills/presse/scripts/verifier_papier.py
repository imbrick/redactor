#!/usr/bin/env python3
"""Vérificateur de papiers de presse avant livraison au CMS.

Usage :
    python verifier_papier.py <papiers/slug.md> [--root RACINE] [--verification DOSSIER.md]

Contrôle le papier (frontmatter de titraille, SEO et réseaux ; corps) et son dossier de
vérification (<dossier_verification>/<slug>.md), qui n'est jamais publié :
  - BLOQUANT : champ obligatoire absent, format ou statut inconnu, date sans guillemets,
    slug mal formé, rubrique hors liste, H1 dans le corps, exergue absente du texte,
    dossier absent (hors brouillon), citation absente du dossier, citation « off » publiée,
    fait en P0 non retiré, fait sensible à source unique non attribué, mis en cause non sollicité ;
  - avertissement : longueurs (corps, chapô, titre, SEO, message X), réseau manquant,
    dates relatives, paragraphe trop long pour l'écran, long papier sans intertitre,
    image sans crédit, source anonyme non documentée, tribune sans présentation de l'auteur.

Codes de sortie : 0 aucun bloquant ; 1 au moins un bloquant ; 2 vérification impossible.
Dépendance : PyYAML. Réutilise la lecture du frontmatter du skill encyclopedia.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

import config_presse as cp
from config_presse import ConfigPresse

# Lecture du frontmatter, résultats et affichage : communs avec le skill encyclopedia,
# présent dans le même plugin (skills/encyclopedia/scripts).
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "encyclopedia" / "scripts"))
from verifier_article import (  # noqa: E402
    Resultat, afficher, avertissement, bloquant, charger_frontmatter, separer_frontmatter, yaml)

# Utilitaires de texte communs aux skills (commun/texte.py à la racine du plugin).
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "commun"))
from texte import mots, normaliser, paragraphes, premier_mot, sections_markdown, table, vide  # noqa: E402,F401

STATUTS = ("brouillon", "relecture", "valide")
CHAMPS_OBLIGATOIRES = ("format", "titre", "chapo", "slug", "signature", "date", "statut",
                       "seo_titre", "seo_description")
FORMATS_SANS_CHAPO = frozenset({"breve"})
FORMATS_SANS_INTERTITRE = cp.FORMATS_OPINION | {"breve"}

TITRE_MAX = 90
SEO_TITRE_MAX = 60
SEO_DESCRIPTION_MIN, SEO_DESCRIPTION_MAX = 70, 160
CHAPO_MIN_MOTS, CHAPO_MAX_MOTS = 15, 60
X_MAX = 280
PARAGRAPHE_MAX_MOTS = 120
INTERTITRE_DES_MOTS = 900
CITATION_MIN_MOTS = 5

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
# Citations entre guillemets français, anglais ou droits.
CITATION_RE = re.compile(r"«\s*(.+?)\s*»|“\s*(.+?)\s*”|\"([^\"\n]+)\"", re.DOTALL)
COUPURE_RE = re.compile(r"\[[^\]]*\]|…|\.\.\.")   # « […] », « [le port] », points de suspension
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
CREDIT_RE = re.compile(r"(?i:(?:photos?|cr[ée]dits?|illustration|infographie|image)\s*:)|©|\bDR\b|"
                       r"(?i:photo d['’]archives)")
DATE_RELATIVE_RE = re.compile(
    r"\b(?:aujourd['’]hui|hier|avant-hier|demain|ce matin|ce soir|cette semaine|la semaine (?:derni[èe]re|prochaine)|"
    r"le mois (?:dernier|prochain)|l['’]an dernier)\b", re.IGNORECASE)
SOURCE_ANONYME_RE = re.compile(
    r"\b(?:source[s]? proche[s]?|selon une source|selon des sources|sous couvert d['’]anonymat|"
    r"selon nos informations|de source s[ûu]re|ayant requis l['’]anonymat)\b", re.IGNORECASE)
# Sections du dossier de vérification et colonnes lues par le script (titres normalisés).
STRUCTURE_DOSSIER = {
    "faits": ("#", "affirmation", "source 2", "sensible", "niveau", "traitement"),
    "citations": ("citation", "statut"),
    "anonymat des sources": ("designation dans le texte",),
    "contradictoire": ("sollicitee le",),
}



def format_du(fm: dict) -> str | None:
    fmt = fm.get("format")
    return fmt if isinstance(fmt, str) else None


# ── Frontmatter ────────────────────────────────────────────────────────────

def verifier_champs(fm: dict, cfg: ConfigPresse) -> list[Resultat]:
    res = []
    fmt = format_du(fm)
    for champ in CHAMPS_OBLIGATOIRES:
        if champ == "chapo" and fmt in FORMATS_SANS_CHAPO:
            continue
        if vide(fm.get(champ)):
            res.append(bloquant("CHAMP_MANQUANT", f"Champ obligatoire absent ou vide : {champ}."))
    if fm.get("format") is not None and fmt not in cp.FORMATS:
        res.append(bloquant("FORMAT_INCONNU", f"Format « {fm.get('format')} » inconnu (formats : {', '.join(cp.FORMATS)})."))
    statut = fm.get("statut")
    if statut is not None and (not isinstance(statut, str) or statut not in STATUTS):
        res.append(bloquant("STATUT_INCONNU", f"Statut « {statut} » inconnu (statuts : {', '.join(STATUTS)})."))
    if isinstance(fm.get("date"), date):
        res.append(bloquant("DATE_FORMAT", 'La date doit être entre guillemets : date: "AAAA-MM-JJ".'))
    elif fm.get("date") is not None and not (isinstance(fm["date"], str)
                                             and re.fullmatch(r"\d{4}-\d{2}-\d{2}", fm["date"])):
        res.append(bloquant("DATE_FORMAT", 'Date attendue au format "AAAA-MM-JJ".'))
    slug = fm.get("slug")
    if slug is not None and not (isinstance(slug, str) and SLUG_RE.match(slug)):
        res.append(bloquant("SLUG_FORMAT", f"Slug « {slug} » : minuscules, chiffres et tirets seulement."))
    if cfg.rubriques and fm.get("rubrique") not in cfg.rubriques:
        res.append(bloquant("RUBRIQUE_INCONNUE",
                            f"Rubrique « {fm.get('rubrique')} » hors liste ({', '.join(cfg.rubriques)})."))
    if fmt == "tribune" and vide(fm.get("presentation_auteur")):
        res.append(avertissement("TRIBUNE_AUTEUR",
                                 "Tribune sans « presentation_auteur » : qui est l'auteur, à quel titre il parle, "
                                 "ses liens d'intérêts."))
    return res


def verifier_titraille(fm: dict, corps: str) -> list[Resultat]:
    res = []
    titre, seo_titre, seo_desc, chapo = (str(fm.get(c) or "") for c in ("titre", "seo_titre", "seo_description", "chapo"))
    if len(titre) > TITRE_MAX:
        res.append(avertissement("TITRE_LONG", f"Titre de {len(titre)} signes (repère : {TITRE_MAX} au plus)."))
    if len(seo_titre) > SEO_TITRE_MAX:
        res.append(avertissement("SEO_TITRE_LONG",
                                 f"Titre SEO de {len(seo_titre)} signes : les moteurs le coupent au-delà de {SEO_TITRE_MAX}."))
    if seo_desc and len(seo_desc) < SEO_DESCRIPTION_MIN:
        res.append(avertissement("SEO_DESCRIPTION_COURTE",
                                 f"Méta-description de {len(seo_desc)} signes (repère : {SEO_DESCRIPTION_MIN} à {SEO_DESCRIPTION_MAX})."))
    if len(seo_desc) > SEO_DESCRIPTION_MAX:
        res.append(avertissement("SEO_DESCRIPTION_LONGUE",
                                 f"Méta-description de {len(seo_desc)} signes, coupée au-delà de {SEO_DESCRIPTION_MAX}."))
    if chapo and not CHAPO_MIN_MOTS <= mots(chapo) <= CHAPO_MAX_MOTS:
        res.append(avertissement("CHAPO_LONGUEUR",
                                 f"Chapô de {mots(chapo)} mots (repère : {CHAPO_MIN_MOTS} à {CHAPO_MAX_MOTS})."))
    exergues = fm.get("exergues") or []
    if isinstance(exergues, str):
        exergues = [exergues]
    if not isinstance(exergues, list):
        return res + [bloquant("EXERGUES_FORMAT", "« exergues » doit être une liste de phrases.")]
    corps_norm = normaliser(corps)
    for exergue in exergues:
        if normaliser(str(exergue)) not in corps_norm:
            res.append(bloquant("EXERGUE_ABSENTE",
                                f"Exergue absente du texte, mot pour mot : « {str(exergue)[:60]} »."))
    return res


def verifier_reseaux(fm: dict, cfg: ConfigPresse) -> list[Resultat]:
    reseaux = fm.get("reseaux") or {}
    if not isinstance(reseaux, dict):
        return [bloquant("RESEAUX_FORMAT", "« reseaux » doit être un dictionnaire { réseau: message }.")]
    res = [avertissement("RESEAU_MANQUANT", f"Pas de message pour le réseau « {r} ».")
           for r in cfg.reseaux if vide(reseaux.get(r))]
    message_x = str(reseaux.get("x") or "")
    if len(message_x) > X_MAX:
        res.append(avertissement("RESEAU_X_LONG", f"Message X de {len(message_x)} signes (limite : {X_MAX})."))
    return res


# ── Corps ──────────────────────────────────────────────────────────────────

def verifier_corps(fm: dict, corps: str, cfg: ConfigPresse) -> list[Resultat]:
    res = []
    if re.search(r"^# ", corps, re.MULTILINE):
        res.append(bloquant("H1_DANS_CORPS", "Le titre vient du frontmatter : pas de titre « # » dans le corps."))
    fmt = format_du(fm)
    total = mots(re.sub(r"!\[[^\]]*\]\([^)]*\)", "", corps))
    if fmt in cfg.longueurs:
        mini, maxi = cfg.longueurs[fmt]
        if not mini <= total <= maxi:
            res.append(avertissement("LONGUEUR_FORMAT",
                                     f"Corps de {total} mots ; repère pour « {fmt} » : {mini} à {maxi}."))
    if (fmt not in FORMATS_SANS_INTERTITRE and total > INTERTITRE_DES_MOTS
            and not re.search(r"^## ", corps, re.MULTILINE)):
        res.append(avertissement("SANS_INTERTITRE", f"{total} mots sans intertitre « ## »."))
    for i, p in enumerate(paragraphes(corps), 1):
        if mots(p) > PARAGRAPHE_MAX_MOTS:
            res.append(avertissement("PARAGRAPHE_LONG",
                                     f"Paragraphe {i} : {mots(p)} mots, à couper pour l'écran (repère : {PARAGRAPHE_MAX_MOTS})."))
    relatives = sorted({m.group(0).lower() for m in DATE_RELATIVE_RE.finditer(corps)})
    if relatives:
        res.append(avertissement("DATE_RELATIVE",
                                 f"Dates relatives ({', '.join(relatives)}) : donner le jour et la date, "
                                 "le papier reste en ligne."))
    for legende in IMAGE_RE.findall(corps):
        if not CREDIT_RE.search(legende):
            res.append(avertissement("IMAGE_CREDIT", f"Image sans crédit dans la légende : « {legende[:60]} »."))
    return res


# ── Dossier de vérification ────────────────────────────────────────────────

def citations(corps: str) -> list[str]:
    trouvees = ("".join(groupes) for groupes in CITATION_RE.findall(corps))
    return [c for c in trouvees if mots(c) >= CITATION_MIN_MOTS]


def morceaux(citation: str) -> list[str]:
    """Morceaux normalisés d'une citation coupée par « […] », « [précision] » ou « … »."""
    return [m for m in (normaliser(p) for p in COUPURE_RE.split(citation)) if m]


def dans(citation: str, texte_dossier: str) -> bool:
    parts = morceaux(citation)
    return bool(parts) and all(p in texte_dossier for p in parts)


def verifier_citations(corps: str, lignes: list[dict[str, str]]) -> list[Resultat]:
    res = []
    au_dossier = [(normaliser(l.get("citation", "")), premier_mot(l.get("statut"))) for l in lignes]
    off = [texte for texte, statut in au_dossier if statut == "off" and texte]
    trouvees = citations(corps)
    for c in trouvees:
        if any(dans(c, texte) for texte in off):
            res.append(bloquant("CITATION_OFF", f"Propos recueilli en off cité dans le texte : « {c[:60]} »."))
        elif not any(dans(c, texte) for texte, _ in au_dossier):
            res.append(bloquant("CITATION_HORS_DOSSIER",
                                f"Citation absente du dossier de vérification : « {c[:60]} »."))
    corps_norm = normaliser(corps)
    for texte in off:
        if texte in corps_norm and not any(dans(c, texte) for c in trouvees):
            res.append(bloquant("CITATION_OFF", f"Propos recueilli en off repris dans le texte : « {texte[:60]} »."))
    return res


def verifier_faits(lignes: list[dict[str, str]]) -> list[Resultat]:
    res = []
    for l in lignes:
        nom = l.get("#") or l.get("affirmation", "")[:40] or "?"
        traitement = premier_mot(l.get("traitement"))
        if premier_mot(l.get("niveau")) == "p0" and traitement != "retire":
            res.append(bloquant("FAIT_P0", f"Fait {nom} en P0 (non vérifié) : le vérifier ou le retirer."))
        if (premier_mot(l.get("sensible")) == "oui" and vide(l.get("source 2"))
                and traitement not in {"attribue", "retire"}):
            res.append(bloquant("FAIT_SENSIBLE_SOURCE_UNIQUE",
                                f"Fait sensible {nom} à source unique : le confirmer par une source indépendante, "
                                "l'attribuer explicitement ou le retirer."))
    return res


def verifier_dossier(fm: dict, corps: str, dossier: Path | None) -> list[Resultat]:
    if dossier is None or not dossier.is_file():
        if fm.get("statut") == "brouillon":
            return []
        return [bloquant("DOSSIER_ABSENT", f"Dossier de vérification introuvable ({dossier}).")]
    secs = sections_markdown(dossier.read_text(encoding="utf-8-sig", errors="replace"))
    tables: dict[str, list[dict[str, str]]] = {}
    res: list[Resultat] = []
    for section, colonnes in STRUCTURE_DOSSIER.items():
        if section not in secs:
            res.append(bloquant("DOSSIER_SECTION", f"Section « ## {section} » absente du dossier : "
                                "titre exact attendu (modèle dans references/dossier-verification.md)."))
            continue
        entetes, lignes = table(secs[section])
        manquantes = [c for c in colonnes if c not in entetes]
        if manquantes:
            res.append(bloquant("DOSSIER_COLONNE", f"Section « {section} » : colonne(s) absente(s) "
                                f"{', '.join(manquantes)} (en-têtes exacts du modèle)."))
            continue
        tables[section] = lignes
    res += verifier_faits(tables.get("faits", []))
    res += verifier_citations(corps, tables.get("citations", []))
    for l in tables.get("contradictoire", []):
        if vide(l.get("sollicitee le")):
            qui = next(iter(l.values()), "?")
            res.append(bloquant("CONTRADICTOIRE", f"« {qui} » est mis en cause sans avoir été sollicité."))
    if SOURCE_ANONYME_RE.search(corps) and not tables.get("anonymat des sources"):
        res.append(avertissement("SOURCE_ANONYME",
                                 "Source anonyme dans le texte, non documentée dans « Anonymat des sources » du dossier."))
    return res


# ── Assemblage ─────────────────────────────────────────────────────────────

def chemin_dossier(papier: Path, racine: Path, fm: dict, cfg: ConfigPresse) -> Path:
    slug = fm.get("slug") if isinstance(fm.get("slug"), str) else papier.stem
    return racine / cfg.dossier_verification / f"{slug}.md"


def verifier_papier(papier: Path, racine: Path, dossier: Path | None = None) -> list[Resultat]:
    cfg = cp.charger(racine)
    brut, corps = separer_frontmatter(papier.read_text(encoding="utf-8", errors="replace"))
    if brut is None:
        return [bloquant("FRONTMATTER_ABSENT", "Pas de frontmatter YAML entre deux lignes « --- ».")]
    fm, erreur = charger_frontmatter(brut)
    if fm is None:
        return [bloquant("FRONTMATTER_YAML", erreur)]
    dossier = dossier or chemin_dossier(papier, racine, fm, cfg)
    return (verifier_champs(fm, cfg) + verifier_titraille(fm, corps) + verifier_reseaux(fm, cfg)
            + verifier_corps(fm, corps, cfg) + verifier_dossier(fm, corps, dossier))


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Vérifie un papier de presse avant livraison au CMS.")
    ap.add_argument("papier", help="chemin du fichier .md")
    ap.add_argument("--root", help="racine du projet, là où se trouve redactor.json (détectée sinon)")
    ap.add_argument("--verification", help="fichier du dossier de vérification (par défaut <dossier_verification>/<slug>.md)")
    try:
        args = ap.parse_args(argv)
    except SystemExit as sortie:
        return 2 if sortie.code else 0
    if yaml is None:
        print("PyYAML absent : installer avec « pip install pyyaml ».", file=sys.stderr)
        return 2
    papier = Path(args.papier).resolve()
    racine = Path(args.root).resolve() if args.root else cp.trouver_racine(papier.parent, Path.cwd().resolve())
    if racine is None:
        print("Racine du projet introuvable (ni redactor.json ni dossier papiers/) : préciser --root.", file=sys.stderr)
        return 2
    try:
        resultats = verifier_papier(papier, racine, Path(args.verification).resolve() if args.verification else None)
    except cp.ConfigInvalide as err:
        print(f"Configuration invalide : {err}", file=sys.stderr)
        return 2
    except OSError as err:
        print(f"Lecture impossible : {err}", file=sys.stderr)
        return 2
    afficher(papier.name, resultats)
    return 1 if any(r.bloquant for r in resultats) else 0


if __name__ == "__main__":
    sys.exit(main())
