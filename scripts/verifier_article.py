#!/usr/bin/env python3
"""Vérificateur d'articles Kongopedia — contrôles déterministes avant publication.

Usage :
    python verifier_article.py <article.md> [--root <depot>]
    python verifier_article.py --corpus [--root <depot>]

Un article est contrôlé sur trois plans :
  1. Frontmatter : ce que le frontend Next.js lit réellement (frontend/lib/content/articles.ts,
     gray-matter + js-yaml).
  2. Corps : règles maison (une H1, notes [^n] cohérentes, pas de « ex-… », anti-IA…).
  3. Publication : présence dans INDEX.md, INDEX-ALPHABETIQUE.md et fiche brainstorm.

Codes de sortie :
  0  aucun contrôle bloquant n'échoue
  1  au moins un contrôle BLOQUANT échoue
  2  impossible de vérifier (fichier illisible, racine introuvable, PyYAML absent, arguments)
Dépendance : PyYAML.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - environnement sans PyYAML
    yaml = None

INDEX_FICHIERS = ("INDEX.md", "INDEX-ALPHABETIQUE.md")
STATUTS_VALIDES = {"draft", "review", "published"}
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ANCIENNE_VERSION_RE = re.compile(r"-(?:old|backup|bak|v\d+)$", re.IGNORECASE)
CADRATINS_MAX_PAR_PARAGRAPHE = 2  # une incise « — … — » compte pour deux tirets
ARTICLE_INITIAL_RE = re.compile(r"^(?:le|la|les|un|une|des)\s|^l['’]", re.IGNORECASE)
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
APPEL_NOTE_RE = re.compile(r"\[\^([^\]\s]+)\]")
DEF_NOTE_RE = re.compile(r"^\[\^([^\]\s]+)\]:", re.MULTILINE)
H1_RE = re.compile(r"^# \S", re.MULTILINE)
H2_RE = re.compile(r"^## +(.+?)\s*$", re.MULTILINE)
CONCLUSION_RE = re.compile(r"^#{2,3} +(?:[IVXLC]+\.\s*)?(conclusion|en résumé)\b", re.IGNORECASE | re.MULTILINE)
EX_RE = re.compile(r"\(ex-|\b[Ee]x-[A-ZÉÈÀ]")
CITATION_INLINE_RE = re.compile(
    r"\((?:[Ss]ource\s*:[^)]*|[A-ZÉ][\w .&'’-]{1,40},?\s*(?:1[5-9]|20)\d{2}[a-z]?(?:,\s*p\.\s*[\d–-]+)?)\)")
MOJIBAKE_RE = re.compile("�|Ã[©¨ª«¢®´§¹ ]")
FORMULES_IA = (
    "il convient de souligner", "il convient de noter", "il est important de noter",
    "il est important de souligner", "tel que mentionné plus haut",
    "comme indiqué dans la section précédente", "comme mentionné précédemment",
    "joue un rôle crucial", "véritable joyau", "témoigne de la richesse",
)
AFFIRMATIONS_FORTES = (
    "démontre que", "démontrant que", "démontré que", "prouve que", "prouvant que", "prouvé que",
    "preuve tangible", "preuve irréfutable", "sans aucun doute", "incontestablement", "il est certain que",
)
AV_JC_RE = re.compile(r"\bav\.\s*J\.?-?C\b")
AVANT_PRESENT_RE = re.compile(r"\bBP\b|avant le présent")
BIBLIO_SUSPECTE_RE = re.compile(r"publication interne|document interne|diffusion interne", re.IGNORECASE)
NOMBRE_RE = re.compile(r"\d[\d  ]*\d")  # « 2 325 », « 20 000 » : espaces fines incluses
ANNEE_RE = re.compile(r"1\d{3}|20\d{2}")
PUCE_RE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+\S", re.MULTILINE)
TITRE_RE = re.compile(r"^(#{2,6}) +(.+?)\s*$", re.MULTILINE)
NUMERO_TITRE_RE = re.compile(r"^(?:[ivxlc]+|\d+)\.\s*")
SECTIONS_HORS_PROSE = ("notes", "bibliograph", "chronolog", "sources", "voir aussi", "références")
LIEN_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)\)")
LIEN_ARTICLE_PREFIXE = "/article/"
PARENTHESES_RE = re.compile(r"\([^)]*\)")
APOSTROPHES = "'’"
PUCES_MIN_PAR_SECTION = 3
PARAGRAPHE_COURT_MOTS = 30
PARAGRAPHES_MIN_FRAGMENTATION = 5
PART_MAX_PARAGRAPHES_COURTS = 0.4


@dataclass(frozen=True)
class Resultat:
    code: str
    bloquant: bool
    message: str


def bloquant(code: str, message: str) -> Resultat:
    return Resultat(code, True, message)


def avertissement(code: str, message: str) -> Resultat:
    return Resultat(code, False, message)


# ── YAML aligné sur js-yaml (gray-matter) ──────────────────────────────────

if yaml is not None:
    class ChargeurKongopedia(yaml.SafeLoader):
        """SafeLoader qui se comporte comme js-yaml côté site :
        seuls true/false sont des booléens (pas yes/no/on/off) et une clé dupliquée est une erreur."""

    ChargeurKongopedia.yaml_implicit_resolvers = {
        initiale: [(tag, regex) for tag, regex in resolveurs if tag != "tag:yaml.org,2002:bool"]
        for initiale, resolveurs in yaml.SafeLoader.yaml_implicit_resolvers.items()
    }
    ChargeurKongopedia.add_implicit_resolver(
        "tag:yaml.org,2002:bool", re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"), list("tTfF"))

    def _mapping_sans_doublon(chargeur, noeud, deep=False):
        chargeur.flatten_mapping(noeud)
        vues = set()
        for noeud_cle, _ in noeud.value:
            cle = chargeur.construct_object(noeud_cle, deep=deep)
            if cle in vues:
                raise yaml.constructor.ConstructorError(
                    None, None, f"clé dupliquée « {cle} » (gray-matter refuserait le fichier)", noeud_cle.start_mark)
            vues.add(cle)
        return chargeur.construct_mapping(noeud, deep=deep)

    ChargeurKongopedia.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping_sans_doublon)


# ── Lecture ────────────────────────────────────────────────────────────────

def separer_frontmatter(texte: str) -> tuple[str | None, str]:
    """Retourne (yaml_brut, corps). yaml_brut vaut None sans frontmatter."""
    texte = texte.lstrip("﻿")
    if not re.match(r"---[ \t]*\n", texte):
        return None, texte
    fin = re.search(r"^---[ \t]*$", texte[3:], re.MULTILINE)
    if not fin:
        return None, texte
    return texte[3:3 + fin.start()], texte[3 + fin.end():]


def charger_frontmatter(brut: str) -> tuple[dict | None, str | None]:
    try:
        donnees = yaml.load(brut, Loader=ChargeurKongopedia) or {}
    except yaml.YAMLError as err:
        return None, f"YAML invalide : {err}"
    if not isinstance(donnees, dict):
        return None, "Le frontmatter n'est pas un dictionnaire YAML."
    return donnees, None


def lire_texte(chemin: Path) -> str:
    return chemin.read_text(encoding="utf-8", errors="replace")


def lire_frontmatter(chemin: Path) -> dict | None:
    brut, _ = separer_frontmatter(lire_texte(chemin))
    if brut is None:
        return None
    fm, _ = charger_frontmatter(brut)
    return fm


def est_vide(valeur) -> bool:
    return valeur is None or valeur == [] or (isinstance(valeur, str) and not valeur.strip())


def est_publie(fm: dict) -> bool:
    """Même règle que articles.ts : statut absent, vide ou « published »."""
    statut = fm.get("publication_status")
    return not statut or statut == "published"


def lister_articles(racine: Path) -> list[Path]:
    dossier = racine / "articles"
    if not dossier.is_dir():
        return []
    return sorted(p for p in dossier.rglob("*") if p.is_file() and p.name.endswith(".md")
                  and p.name not in INDEX_FICHIERS)


def sans_code(corps: str) -> str:
    """Retire les blocs de code clôturés (``` ou ~~~), selon les règles CommonMark."""
    gardees, ouverture = [], None
    for ligne in corps.split("\n"):
        m = FENCE_RE.match(ligne)
        if ouverture is None:
            info = ligne[m.end():] if m else ""
            if m and not (m.group(1)[0] == "`" and "`" in info):
                ouverture = m.group(1)
            else:
                gardees.append(ligne)
        elif (m and m.group(1)[0] == ouverture[0] and len(m.group(1)) >= len(ouverture)
              and not ligne[m.end():].strip()):
            ouverture = None
    return "\n".join(gardees)


def chemin_dans_articles(chemin: Path, racine: Path) -> str | None:
    try:
        return chemin.resolve().relative_to((racine / "articles").resolve()).as_posix()
    except ValueError:
        return None


# ── Contrôles du frontmatter ───────────────────────────────────────────────

def verifier_slug(slug) -> list[Resultat]:
    if est_vide(slug):
        return [bloquant("FM_SLUG", "Champ « slug » absent : l'article n'aura pas d'URL.")]
    if not isinstance(slug, str):
        return [bloquant("FM_SLUG_FORMAT", f"Slug {slug!r} lu comme un nombre ou une liste : l'écrire entre guillemets.")]
    if not SLUG_RE.match(slug):
        return [bloquant("FM_SLUG_FORMAT", f"Slug « {slug} » invalide : minuscules, chiffres et tirets uniquement.")]
    return []


def verifier_champs(fm: dict) -> list[Resultat]:
    res = []
    if est_vide(fm.get("title")):
        res.append(bloquant("FM_TITLE", "Champ « title » absent : le site ne peut pas afficher l'article."))
    res += verifier_slug(fm.get("slug"))
    titre_simple = fm.get("titre_simple")
    if est_vide(titre_simple):
        res.append(bloquant("FM_TITRE_SIMPLE", "Champ « titre_simple » absent (sert à l'index et aux menus)."))
    elif ARTICLE_INITIAL_RE.match(str(titre_simple)):
        res.append(avertissement("FM_TITRE_SIMPLE_ARTICLE",
                                 f"« titre_simple » commence par un article : « {titre_simple} »."))
    if est_vide(fm.get("excerpt")) and est_vide(fm.get("summary")):
        res.append(avertissement("FM_RESUME", "Ni « excerpt » ni « summary » : la liste d'articles n'aura pas de résumé."))
    if est_vide(fm.get("categories")):
        res.append(avertissement("FM_CATEGORIES", "Champ « categories » vide ou absent."))
    return res


def verifier_date_et_statut(fm: dict) -> list[Resultat]:
    res = []
    date = fm.get("date")
    if date is None:
        res.append(avertissement("FM_DATE", "Champ « date » absent : tri chronologique impossible."))
    elif isinstance(date, (dt.date, dt.datetime)):
        res.append(bloquant("FM_DATE_NON_QUOTEE",
                            f"La date {date} n'est pas entre guillemets : gray-matter la convertit en objet Date "
                            "(bug corrigé au commit 228c102). Écrire date: \"AAAA-MM-JJ\"."))
    statut = fm.get("publication_status")
    if not est_vide(statut) and not (isinstance(statut, str) and statut in STATUTS_VALIDES):
        res.append(bloquant("FM_STATUT", f"publication_status « {statut} » invalide (draft, review ou published)."))
    return res


def verifier_doublons(chemin: Path, racine: Path, fm: dict) -> list[Resultat]:
    slug = fm.get("slug")
    if not isinstance(slug, str) or not slug:
        return []
    res = []
    for p in lister_articles(racine):
        if p.resolve() == chemin.resolve():
            continue
        autre = lire_frontmatter(p)
        if autre and autre.get("slug") == slug and est_publie(autre):
            message = f"Slug « {slug} » déjà utilisé par {p.relative_to(racine).as_posix()} (publié)."
            res.append(bloquant("SLUG_DUPLIQUE", message) if est_publie(fm)
                       else avertissement("SLUG_DUPLIQUE", message + " Conflit dès la publication de ce brouillon."))
    return res


def verifier_emplacement(chemin: Path, racine: Path, fm: dict) -> list[Resultat]:
    rel = chemin_dans_articles(chemin, racine)
    if rel is None:
        return [bloquant("FICHIER_EMPLACEMENT", "L'article n'est pas sous articles/ : le site ne le verra pas.")]
    res = []
    slug = fm.get("slug")
    if ANCIENNE_VERSION_RE.search(chemin.stem) and est_publie(fm):
        res.append(avertissement("FICHIER_ANCIENNE_VERSION",
                                 f"« {chemin.name} » ressemble à une ancienne version mais sera publiée en double : "
                                 "la sortir de articles/ ou lui donner publication_status: \"draft\"."))
    if isinstance(slug, str) and slug and chemin.stem != slug:
        res.append(avertissement("FICHIER_NOM", f"Nom de fichier « {chemin.name} » différent du slug (« {slug}.md » attendu)."))
    if "/" not in rel:
        res.append(avertissement("FICHIER_CATEGORIE", "Article placé à la racine de articles/, sans dossier de catégorie."))
    return res + verifier_doublons(chemin, racine, fm)


# ── Contrôles du corps ─────────────────────────────────────────────────────

def verifier_structure(corps: str) -> list[Resultat]:
    res = []
    nb_h1 = len(H1_RE.findall(corps))
    if nb_h1 != 1:
        res.append(bloquant("CORPS_H1", f"{nb_h1} titre(s) H1 trouvé(s) : il en faut exactement un."))
    if CONCLUSION_RE.search(corps):
        res.append(avertissement("CORPS_CONCLUSION", "Section « Conclusion » ou « En résumé » : interdite par la charte."))
    return res


def verifier_notes(corps: str) -> list[Resultat]:
    res = []
    definitions = set(DEF_NOTE_RE.findall(corps))
    appels = set(APPEL_NOTE_RE.findall(DEF_NOTE_RE.sub("", corps)))
    for n in sorted(appels - definitions):
        res.append(bloquant("NOTE_NON_DEFINIE", f"Appel [^{n}] sans définition dans la section Notes."))
    for n in sorted(definitions - appels):
        res.append(avertissement("NOTE_ORPHELINE", f"Note [^{n}] définie mais jamais appelée dans le texte."))
    titres = H2_RE.findall(corps)
    if definitions and (not titres or not titres[-1].lower().startswith("notes")):
        res.append(avertissement("NOTES_POSITION", "La section « ## Notes » doit être la toute dernière de l'article."))
    return res


def paragraphes_de_prose(corps: str) -> list[str]:
    blocs = re.split(r"\n\s*\n", corps)
    exclus = ("#", "|", ">", "[^")
    return [b for b in blocs if b.strip() and not b.lstrip().startswith(exclus)]


def verifier_style(corps: str) -> list[Resultat]:
    res = []
    texte_courant = DEF_NOTE_RE.split(corps)[0]
    if EX_RE.search(texte_courant):
        res.append(avertissement("STYLE_EX", "Construction « ex-… » pour un ancien nom : la remplacer par une phrase datée."))
    citations = CITATION_INLINE_RE.findall(texte_courant)
    if citations:
        exemples = ", ".join(sorted(set(citations))[:3])
        res.append(avertissement("STYLE_CITATION_INLINE",
                                 f"Possible citation entre parenthèses ({exemples}) : si c'est une source, "
                                 "la remplacer par une note [^n]."))
    bas = corps.lower()
    trouvees = [f for f in FORMULES_IA if f in bas]
    if trouvees:
        res.append(avertissement("STYLE_FORMULE_IA", "Formules mécaniques à reformuler : " + " ; ".join(trouvees)))
    trop = sum(1 for p in paragraphes_de_prose(corps) if p.count("—") > CADRATINS_MAX_PAR_PARAGRAPHE)
    if trop:
        res.append(avertissement("STYLE_CADRATIN", f"{trop} paragraphe(s) avec plus d'une incise entre tirets cadratins (—)."))
    return res


# ── Contrôles de preuve et de qualité rédactionnelle (fiche revision-enrichissement.md) ──

def sections(corps: str) -> list[tuple[int, str, str]]:
    """Découpe le corps à chaque titre de niveau 2 à 6 : [(niveau, titre, contenu)].
    Le préambule a le niveau 1 et un titre vide."""
    morceaux, niveau, titre, debut = [], 1, "", 0
    for m in TITRE_RE.finditer(corps):
        morceaux.append((niveau, titre, corps[debut:m.start()]))
        niveau, titre, debut = len(m.group(1)), m.group(2), m.end()
    morceaux.append((niveau, titre, corps[debut:]))
    return morceaux


def est_hors_prose(titre: str) -> bool:
    return NUMERO_TITRE_RE.sub("", titre.lower()).startswith(SECTIONS_HORS_PROSE)


def sections_de_prose(corps: str) -> list[tuple[str, str]]:
    """Sections rédigées [(titre, contenu)], hors Notes, Bibliographie, Chronologie et assimilées.
    Une sous-section hérite de l'exclusion de la section de niveau 2 qui la contient."""
    gardees, parent_exclu = [], False
    for niveau, titre, contenu in sections(corps):
        if niveau <= 2:
            parent_exclu = est_hors_prose(titre)
        if not parent_exclu and not est_hors_prose(titre):
            gardees.append((titre, contenu))
    return gardees


def contient_quantite(texte: str) -> bool:
    """Vrai si le texte contient un nombre d'au moins deux chiffres qui n'est pas une année seule."""
    return any(not ANNEE_RE.fullmatch(m.group()) for m in NOMBRE_RE.finditer(texte))


def verifier_preuve(corps: str) -> list[Resultat]:
    res = []
    texte_courant = DEF_NOTE_RE.split(corps)[0]
    paragraphes = [p for _, contenu in sections_de_prose(texte_courant) for p in paragraphes_de_prose(contenu)]
    sans_note = [p for p in paragraphes if contient_quantite(p) and not APPEL_NOTE_RE.search(p)]
    if sans_note:
        extrait = " ".join(sans_note[0].split())[:70]
        res.append(avertissement("PREUVE_CHIFFRE_SANS_NOTE",
                                 f"{len(sans_note)} paragraphe(s) avec un chiffre sans appel [^n] "
                                 f"(premier : « {extrait}… »)."))
    bas = texte_courant.lower()
    fortes = [f for f in AFFIRMATIONS_FORTES if f in bas]
    if fortes:
        res.append(avertissement("STYLE_AFFIRMATION_FORTE",
                                 "Interprétation présentée comme un fait, à attribuer : " + " ; ".join(fortes)))
    if AV_JC_RE.search(texte_courant) and AVANT_PRESENT_RE.search(texte_courant):
        res.append(avertissement("DATATION_MIXTE",
                                 "Dates en « av. J.-C. » et en « BP / avant le présent » : vérifier la cohérence "
                                 "(environ 2 000 ans d'écart) et convertir explicitement."))
    biblio = "".join(contenu for _, titre, contenu in sections(corps) if titre.lower().startswith("bibliograph"))
    suspectes = [l.strip()[:70] for l in biblio.splitlines() if BIBLIO_SUSPECTE_RE.search(l)]
    if suspectes:
        res.append(avertissement("BIBLIO_SUSPECTE",
                                 f"Référence à l'existence douteuse, à vérifier ou retirer : « {suspectes[0]}… »."))
    return res


def verifier_redaction(corps: str) -> list[Resultat]:
    res = []
    prose = sections_de_prose(DEF_NOTE_RE.split(corps)[0])
    listes = []
    for titre, contenu in prose:
        puces = len(PUCE_RE.findall(contenu))
        redige = sum(1 for p in paragraphes_de_prose(contenu) if not PUCE_RE.match(p))
        if puces >= PUCES_MIN_PAR_SECTION and puces > redige:
            listes.append(titre or "introduction")
    if listes:
        res.append(avertissement("PROSE_LISTES",
                                 "Puces plus nombreuses que les paragraphes rédigés dans : " + " ; ".join(listes)
                                 + ". Convertir les raisonnements en prose."))
    redigees = [p for _, contenu in prose for p in paragraphes_de_prose(contenu) if not PUCE_RE.match(p)]
    courts = [p for p in redigees if len(p.split()) < PARAGRAPHE_COURT_MOTS]
    if len(redigees) >= PARAGRAPHES_MIN_FRAGMENTATION and len(courts) / len(redigees) >= PART_MAX_PARAGRAPHES_COURTS:
        res.append(avertissement("PROSE_FRAGMENTEE",
                                 f"{len(courts)} paragraphe(s) sur {len(redigees)} font moins de "
                                 f"{PARAGRAPHE_COURT_MOTS} mots : regrouper et relier les idées."))
    return res


def verifier_encodage(texte: str) -> list[Resultat]:
    res = []
    if texte.startswith("﻿"):
        res.append(bloquant("FM_BOM", "Le fichier commence par un BOM UTF-8 : gray-matter ne verra pas le frontmatter. "
                                      "Réenregistrer en UTF-8 sans BOM."))
    if MOJIBAKE_RE.search(texte):
        res.append(avertissement("ENCODAGE", "Caractères mal encodés détectés (« Ã© », « � ») : vérifier l'encodage UTF-8."))
    return res


# ── Liens internes ─────────────────────────────────────────────────────────
# Convention : [Libellé](/article/<slug>). Le slug d'un article à venir se déduit de son
# titre_simple avec slugifier(), si bien que le lien fonctionnera dès sa publication.

def slugifier(titre: str) -> str:
    """« Os d'Ishango » → os-dishango ; « Le fleuve Congo » → fleuve-congo."""
    texte = ARTICLE_INITIAL_RE.sub("", PARENTHESES_RE.sub(" ", titre).strip())
    texte = unicodedata.normalize("NFD", texte).encode("ascii", "ignore").decode().lower()
    texte = re.sub(f"[{APOSTROPHES}]", "", texte)
    return re.sub(r"[^a-z0-9]+", "-", texte).strip("-")


def liens_internes(corps: str) -> list[tuple[str, str]]:
    """(libellé, slug) de chaque lien /article/<slug> du corps."""
    return [(lib, cible[len(LIEN_ARTICLE_PREFIXE):].strip("/")) for lib, cible in LIEN_RE.findall(corps)
            if cible.startswith(LIEN_ARTICLE_PREFIXE)]


def carte_du_corpus(racine: Path) -> tuple[dict[str, Path], dict[str, set[Path]]]:
    """Slugs publiés (slug → fichier) et liens internes (slug cible → fichiers qui le citent)."""
    slugs, liens = {}, {}
    for chemin in lister_articles(racine):
        fm = lire_frontmatter(chemin) or {}
        slugs[str(fm.get("slug") or chemin.stem)] = chemin
        for _, cible in liens_internes(separer_frontmatter(lire_texte(chemin))[1]):
            liens.setdefault(cible, set()).add(chemin)
    return slugs, liens


def verifier_liens(chemin: Path, racine: Path, corps: str) -> list[Resultat]:
    slugs = carte_du_corpus(racine)[0]
    res = []
    for libelle, cible in LIEN_RE.findall(corps):
        if cible.startswith(("http://", "https://", "#", "mailto:")):
            continue
        if cible.endswith(".md") or ".md#" in cible:
            fichier = (chemin.parent / cible.split("#")[0]).resolve()
            fm = lire_frontmatter(fichier) if fichier.exists() else None
            slug = str((fm or {}).get("slug") or slugifier(libelle))
            res.append(avertissement("LIEN_CHEMIN_MD", f"Lien « {libelle} » vers un fichier : écrire [{libelle}](/article/{slug})."))
        elif cible.startswith(LIEN_ARTICLE_PREFIXE):
            slug = cible[len(LIEN_ARTICLE_PREFIXE):].strip("/")
            if not SLUG_RE.match(slug):
                res.append(avertissement("LIEN_SLUG_INVALIDE", f"Lien « {libelle} » : slug « {slug} » hors format (minuscules, chiffres, tirets)."))
            elif slug not in slugs and slugifier(libelle) != slug:
                res.append(avertissement("LIEN_SLUG_CONVENTION",
                                         f"Lien à venir « {libelle} » → {slug} : la convention donnerait « {slugifier(libelle)} » ; "
                                         "garder un seul slug par sujet, celui du futur titre_simple."))
    voir_aussi = [c for _, t, c in sections(corps) if "voir aussi" in t.lower()]
    sans_lien = [l for c in voir_aussi for l in c.splitlines() if PUCE_RE.match(l) and not LIEN_RE.search(l)]
    if sans_lien:
        res.append(avertissement("VOIR_AUSSI_SANS_LIEN",
                                 f"{len(sans_lien)} entrée(s) de « Voir aussi » sans lien (premier : « {sans_lien[0].strip()[2:]} ») : "
                                 "écrire [Titre](/article/<slug>), même si l'article n'existe pas encore."))
    return res


def verifier_liens_en_attente(chemin: Path, racine: Path, fm: dict) -> list[Resultat]:
    """Des articles citent-ils ce sujet sous le slug conventionnel alors que l'article en a pris un autre ?"""
    slug, titre = fm.get("slug"), fm.get("titre_simple")
    if not isinstance(slug, str) or not isinstance(titre, str):
        return []
    attendu = slugifier(titre)
    citants = carte_du_corpus(racine)[1].get(attendu, set()) - {chemin.resolve(), chemin}
    if attendu == slug or not citants:
        return []
    return [avertissement("LIENS_EN_ATTENTE",
                          f"{len(citants)} article(s) pointent déjà vers /article/{attendu} : adopter ce slug "
                          f"ou corriger leurs liens ({', '.join(sorted(p.stem for p in citants))}).")]


# ── Contrôles de publication ───────────────────────────────────────────────

def est_reference(suffixe: str, texte: str) -> bool:
    return re.search(r"(?<![\w-])" + re.escape(suffixe), texte) is not None


def verifier_publication(chemin: Path, racine: Path, fm: dict) -> list[Resultat]:
    suffixe = chemin_dans_articles(chemin, racine)
    if not est_publie(fm) or suffixe is None:
        return []
    res = []
    for fichier, code in (("INDEX.md", "INDEX_ABSENT"), ("INDEX-ALPHABETIQUE.md", "INDEX_ALPHA_ABSENT")):
        index = racine / "articles" / fichier
        if not index.exists() or not est_reference(suffixe, lire_texte(index)):
            res.append(avertissement(code, f"Article absent de articles/{fichier}."))
    slug = fm.get("slug") if isinstance(fm.get("slug"), str) else chemin.stem
    if not (racine / "ressources" / "brainstorm" / f"{slug}-articles-derives.md").exists():
        res.append(avertissement("BRAINSTORM_ABSENT",
                                 f"Fiche ressources/brainstorm/{slug}-articles-derives.md absente."))
    return res


# ── Points d'entrée ────────────────────────────────────────────────────────

def verifier_article(chemin: Path, racine: Path) -> list[Resultat]:
    """Contrôle un article. Lève OSError si le fichier est illisible."""
    chemin, racine = Path(chemin), Path(racine)
    texte = chemin.read_text(encoding="utf-8", errors="replace")
    brut, corps = separer_frontmatter(texte)
    corps = sans_code(corps)
    res = (verifier_encodage(texte) + verifier_structure(corps) + verifier_notes(corps) + verifier_style(corps)
           + verifier_preuve(corps) + verifier_redaction(corps))
    if brut is None:
        return [bloquant("FM_ABSENT", "Aucun frontmatter YAML (bloc --- … --- en tête de fichier).")] + res
    fm, erreur = charger_frontmatter(brut)
    if erreur:
        return [bloquant("FM_INVALIDE", erreur)] + res
    return (verifier_champs(fm) + verifier_date_et_statut(fm) + verifier_emplacement(chemin, racine, fm)
            + res + verifier_liens(chemin, racine, corps) + verifier_liens_en_attente(chemin, racine, fm)
            + verifier_publication(chemin, racine, fm))


def compteur_annonce(texte: str) -> int | None:
    m = re.search(r"\*\*(\d+) articles? index", texte)
    return int(m.group(1)) if m else None


def verifier_index(racine: Path, fichier: str, articles: list[Path]) -> list[Resultat]:
    index = racine / "articles" / fichier
    if not index.exists():
        return [bloquant("CORPUS_INDEX_ABSENT", f"articles/{fichier} introuvable.")]
    texte = lire_texte(index)
    res = []
    annonce = compteur_annonce(texte)
    if annonce is not None and annonce != len(articles):
        res.append(avertissement("CORPUS_COMPTEUR", f"{fichier} annonce {annonce} articles, le corpus en compte {len(articles)}."))
    for p in articles:
        suffixe = p.relative_to(racine / "articles").as_posix()
        if not est_reference(suffixe, texte):
            res.append(avertissement("CORPUS_NON_INDEXE", f"{fichier} : {suffixe} n'est pas indexé."))
    sans_url = re.sub(r"https?://\S+", "", texte)
    for lien in sorted(set(re.findall(r"[\w./-]+\.md", sans_url))):
        if not ((racine / lien).exists() or (racine / "articles" / lien).exists()):
            res.append(avertissement("CORPUS_LIEN_MORT", f"{fichier} pointe vers {lien}, qui n'existe pas."))
    return res


def verifier_corpus(racine: Path) -> list[Resultat]:
    racine = Path(racine)
    articles = [p for p in lister_articles(racine) if est_publie(lire_frontmatter(p) or {})]
    res = []
    for fichier in INDEX_FICHIERS:
        res += verifier_index(racine, fichier, articles)
    return res


def trouver_racine(*departs: Path) -> Path | None:
    for depart in departs:
        for p in [depart, *depart.parents]:
            if (p / "articles").is_dir() and ((p / "frontend").is_dir() or (p / "articles" / "INDEX.md").exists()):
                return p
    return None


def afficher(titre: str, resultats: list[Resultat]) -> None:
    nb_b = sum(r.bloquant for r in resultats)
    print(f"\n== {titre} — {nb_b} bloquant(s), {len(resultats) - nb_b} avertissement(s)")
    for r in sorted(resultats, key=lambda r: not r.bloquant):
        print(f"  {'BLOQUANT     ' if r.bloquant else 'avertissement'} [{r.code}] {r.message}")


def analyser_arguments(argv: list[str] | None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Vérifie un article Kongopedia avant publication.")
    ap.add_argument("article", nargs="?", help="chemin du fichier .md")
    ap.add_argument("--corpus", action="store_true", help="contrôler les index et tout le corpus")
    ap.add_argument("--root", help="racine du dépôt Kongopedia (détectée sinon)")
    args = ap.parse_args(argv)
    if not args.article and not args.corpus:
        ap.error("indiquer un article ou --corpus")
    return args


def executer(args: argparse.Namespace, racine: Path) -> list[Resultat]:
    resultats = []
    if args.article:
        resultats = verifier_article(Path(args.article), racine)
        afficher(Path(args.article).name, resultats)
    if args.corpus:
        for p in lister_articles(racine):
            r = verifier_article(p, racine)
            resultats += r
            if any(x.bloquant for x in r):
                afficher(p.relative_to(racine).as_posix(), [x for x in r if x.bloquant])
        corpus = verifier_corpus(racine)
        resultats += corpus
        afficher("Index et corpus", corpus)
    return resultats


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        args = analyser_arguments(argv)
    except SystemExit as sortie:
        return 2 if sortie.code else 0
    if yaml is None:
        print("PyYAML absent : installer avec « pip install pyyaml ».", file=sys.stderr)
        return 2
    departs = [Path(args.article).resolve().parent] if args.article else []
    departs += [Path.cwd().resolve(), Path(__file__).resolve().parent]
    racine = Path(args.root).resolve() if args.root else trouver_racine(*departs)
    if racine is None:
        print("Racine Kongopedia introuvable : préciser --root.", file=sys.stderr)
        return 2
    try:
        resultats = executer(args, racine)
    except OSError as err:
        print(f"Lecture impossible : {err}", file=sys.stderr)
        return 2
    return 1 if any(r.bloquant for r in resultats) else 0


if __name__ == "__main__":
    sys.exit(main())
