#!/usr/bin/env python3
"""Vérificateur de références Kongopedia — chaque entrée de la bibliographie existe-t-elle ?

Usage :
    python verifier_references.py <article.md>

Pour chaque entrée de la section « ## Bibliographie » :
  - article avec DOI : le DOI est résolu dans Crossref et le titre comparé ;
  - article sans DOI : recherche par titre dans Crossref et OpenAlex ;
  - livre (titre en italique, sans guillemets) : recherche dans Open Library ;
  - prépublication arXiv (« arXiv:AAMM.NNNNN » ou lien arxiv.org) : titre comparé via l'API arXiv ;
  - entrée avec URL que les bases ne connaissent pas : la page est consultée avant de conclure
    (titre présent : TROUVÉ ; PDF, titre absent ou lien injoignable : À CONFIRMER ; lien mort : INTROUVABLE).
Signale aussi une copie en accès libre du texte intégral quand OpenAlex en connaît une.

Statuts : TROUVÉ · À CONFIRMER · DIVERGENT (le DOI pointe vers autre chose) ·
INTROUVABLE (à retrouver à la main ou à retirer) · ERREUR RÉSEAU (rien n'est conclu).

Codes de sortie : 0 tout est trouvé ou à confirmer ; 1 au moins une entrée DIVERGENT ou
INTROUVABLE ; 2 vérification impossible (fichier illisible, aucune bibliographie).
Aucune dépendance hors bibliothèque standard. Aucune donnée personnelle n'est envoyée.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import ssl
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from html import unescape
from pathlib import Path

TROUVE, A_CONFIRMER, DIVERGENT = "TROUVÉ", "À CONFIRMER", "DIVERGENT"
INTROUVABLE, ERREUR_RESEAU = "INTROUVABLE", "ERREUR RÉSEAU"
SEUIL_TROUVE, SEUIL_PROCHE = 0.85, 0.6
USER_AGENT = "kongopedia-verifier/1.0 (verification bibliographique)"
DELAI_RESEAU_S = 20

BIBLIO_RE = re.compile(r"^## +(?:bibliographie|références bibliographiques|references)\b.*$", re.IGNORECASE | re.MULTILINE)
ENTREE_RE = re.compile(r"^\s*(?:[-*]|\d+\.)\s+(.+)$")
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s,;)»]+")
GUILLEMETS_RE = re.compile(r"«\s*(.+?)\s*»")
ITALIQUE_RE = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)|(?<![\w*])_([^_]+)_(?!\w)")
# Indices qu'un titre en italique est celui d'un article de revue, non d'un livre.
REVUE_RE = re.compile(r"\d+\s*\(\d[\d–-]*\)|vol\.|p\.\s*\d+\s*[–-]|journal|letters|review|proceedings|"
                      r"bulletin|comptes rendus|nature|science|geology|geosystems|publications", re.IGNORECASE)
ANNEE_RE = re.compile(r"\b(1[5-9]\d{2}|20\d{2})\b")
ARXIV_RE = re.compile(r"arxiv(?:\.org/abs/|:)\s*(\d{4}\.\d{4,5}(?:v\d+)?|[a-z.-]+/\d{7})", re.IGNORECASE)
URL_RE = re.compile(r"https?://[^\s<>»)\]]+")
ATOM = "{http://www.w3.org/2005/Atom}"
TAILLE_MAX_PAGE = 2_000_000
MOTS_TITRE_DANS_PAGE = 8


class NonTrouve(Exception):
    """La ressource demandée n'existe pas (HTTP 404) : ce n'est pas une panne."""


@dataclass(frozen=True)
class Reference:
    texte: str
    auteur: str
    titre: str
    annee: int | None
    doi: str | None
    est_livre: bool
    arxiv: str | None = None
    url: str | None = None


@dataclass(frozen=True)
class Verdict:
    reference: Reference
    statut: str
    detail: str
    doi: str | None = None
    acces_libre: str | None = None


# ── Extraction ─────────────────────────────────────────────────────────────

def section_bibliographie(texte: str) -> str:
    debut = BIBLIO_RE.search(texte)
    if not debut:
        return ""
    reste = texte[debut.end():]
    fin = re.search(r"^## ", reste, re.MULTILINE)
    return reste[:fin.start()] if fin else reste


def analyser_entree(ligne: str) -> Reference:
    doi_m = DOI_RE.search(ligne)
    doi = doi_m.group(0).rstrip(".") if doi_m else None
    guillemets = GUILLEMETS_RE.search(ligne)
    italique = ITALIQUE_RE.search(ligne)
    titre_m = guillemets or italique
    titre = next(g for g in titre_m.groups() if g).strip().rstrip(".") if titre_m else ""
    apres_titre = ligne[titre_m.end():] if titre_m else ""
    est_livre = guillemets is None and italique is not None and not REVUE_RE.search(apres_titre)
    arxiv_m = ARXIV_RE.search(ligne)
    urls = [u.rstrip(".,;") for u in URL_RE.findall(ligne) if "doi.org/" not in u]
    hors_titre = ligne.replace(titre, " ") if titre else ligne
    sans_identifiants = ARXIV_RE.sub(" ", URL_RE.sub(" ", DOI_RE.sub(" ", hors_titre)))
    annee_m = ANNEE_RE.search(sans_identifiants)
    auteur = re.split(r"[,(]", ligne.replace("*", ""), maxsplit=1)[0].strip()
    return Reference(ligne.strip(), auteur, titre, int(annee_m.group(1)) if annee_m else None,
                     doi, est_livre=est_livre,
                     arxiv=arxiv_m.group(1) if arxiv_m else None, url=urls[0] if urls else None)


def extraire_references(texte: str) -> list[Reference]:
    refs = []
    for ligne in section_bibliographie(texte).splitlines():
        m = ENTREE_RE.match(ligne)
        if m and re.search(r"[^\W\d_]", m.group(1)):
            refs.append(analyser_entree(m.group(1)))
    return refs


# ── Comparaison ────────────────────────────────────────────────────────────

def normaliser(texte: str) -> str:
    sans_accents = unicodedata.normalize("NFD", texte).encode("ascii", "ignore").decode()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", sans_accents.lower()).split())


def similarite(a: str, b: str) -> float:
    na, nb = normaliser(a), normaliser(b)
    if not na or not nb:
        return 0.0
    if na in nb or nb in na:
        return max(0.9, difflib.SequenceMatcher(None, na, nb).ratio())
    return difflib.SequenceMatcher(None, na, nb).ratio()


def annee_compatible(attendue: int | None, trouvee: int | None) -> bool:
    return attendue is None or trouvee is None or abs(attendue - trouvee) <= 1


# ── Accès réseau ───────────────────────────────────────────────────────────

def contexte_ssl() -> ssl.SSLContext:
    """Utilise le magasin de certifi s'il est installé : sous Windows, Python ne voit pas toujours les autorités
    racines que le système télécharge à la demande (cas d'arXiv). Sinon, magasin par défaut du système."""
    try:
        import certifi
    except ImportError:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())


CONTEXTE_SSL = contexte_ssl()


def lire_json(url: str) -> dict:
    requete = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(requete, timeout=DELAI_RESEAU_S, context=CONTEXTE_SSL) as reponse:
            return json.loads(reponse.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        if err.code == 404:
            raise NonTrouve(url) from err
        raise OSError(f"HTTP {err.code} pour {url}") from err


def lire_page(url: str) -> tuple[str, str]:
    """Retourne (type de contenu, texte). Lève NonTrouve pour 404 ou 410, OSError pour toute autre panne."""
    requete = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(requete, timeout=DELAI_RESEAU_S, context=CONTEXTE_SSL) as reponse:
            type_contenu = reponse.headers.get_content_type()
            brut = reponse.read(TAILLE_MAX_PAGE)
            jeu = reponse.headers.get_content_charset() or "utf-8"
    except urllib.error.HTTPError as err:
        if err.code in (404, 410):
            raise NonTrouve(url) from err
        raise OSError(f"HTTP {err.code}") from err
    texte = "" if type_contenu == "application/pdf" else brut.decode(jeu, errors="replace")
    return type_contenu, texte


def q(texte: str) -> str:
    return urllib.parse.quote(texte, safe="")


def annee_crossref(item: dict) -> int | None:
    parties = (item.get("issued") or {}).get("date-parts") or [[None]]
    return parties[0][0] if parties and parties[0] else None


def candidats_crossref(ref: Reference, fetch) -> list[tuple[str, int | None, str | None]]:
    requete = " ".join(filter(None, [ref.titre, ref.auteur, str(ref.annee or "")]))
    donnees = fetch(f"https://api.crossref.org/works?rows=5&query.bibliographic={q(requete)}")
    return [((item.get("title") or [""])[0], annee_crossref(item), item.get("DOI"))
            for item in donnees.get("message", {}).get("items", [])]


def candidats_openalex(ref: Reference, fetch) -> list[tuple[str, int | None, str | None]]:
    donnees = fetch(f"https://api.openalex.org/works?per-page=5&search={q(ref.titre)}")
    return [(w.get("title") or "", w.get("publication_year"), (w.get("doi") or "").replace("https://doi.org/", "") or None)
            for w in donnees.get("results", [])]


def acces_libre(doi: str | None, fetch) -> str | None:
    if not doi:
        return None
    try:
        donnees = fetch(f"https://api.openalex.org/works/https://doi.org/{doi}")
    except (OSError, NonTrouve, ValueError):
        return None
    return (donnees.get("open_access") or {}).get("oa_url")


# ── Vérification ───────────────────────────────────────────────────────────

def verifier_par_doi(ref: Reference, fetch) -> Verdict:
    try:
        item = fetch(f"https://api.crossref.org/works/{ref.doi}").get("message", {})
    except NonTrouve:
        return Verdict(ref, INTROUVABLE, f"Le DOI {ref.doi} n'existe pas dans Crossref.")
    except (OSError, ValueError) as err:
        return Verdict(ref, ERREUR_RESEAU, f"Crossref injoignable : {err}")
    titre = (item.get("title") or [""])[0]
    if similarite(ref.titre, titre) < SEUIL_PROCHE:
        return Verdict(ref, DIVERGENT, f"Le DOI pointe vers « {titre} » ({annee_crossref(item)}).", ref.doi)
    return Verdict(ref, TROUVE, f"« {titre} », {annee_crossref(item)}, {(item.get('container-title') or [''])[0]}.",
                   ref.doi, acces_libre(ref.doi, fetch))


def verifier_par_recherche(ref: Reference, fetch) -> Verdict:
    candidats, erreurs = [], 0
    for source in (candidats_crossref, candidats_openalex):
        try:
            candidats += source(ref, fetch)
        except (OSError, NonTrouve, ValueError):
            erreurs += 1
    if erreurs == 2:
        return Verdict(ref, ERREUR_RESEAU, "Crossref et OpenAlex injoignables.")
    compatibles = [c for c in candidats if annee_compatible(ref.annee, c[1])]
    if not compatibles:
        return Verdict(ref, INTROUVABLE, "Aucune publication de ce titre et de cette année dans Crossref ni OpenAlex.")
    titre, annee, doi = max(compatibles, key=lambda c: similarite(ref.titre, c[0]))
    score = similarite(ref.titre, titre)
    if score >= SEUIL_TROUVE:
        return Verdict(ref, TROUVE, f"« {titre} » ({annee}).", doi, acces_libre(doi, fetch))
    if score >= SEUIL_PROCHE:
        return Verdict(ref, A_CONFIRMER, f"Titre le plus proche : « {titre} » ({annee}), DOI {doi}.", doi)
    return Verdict(ref, INTROUVABLE, f"Rien d'approchant ; meilleur résultat sans rapport : « {titre} ».")


def livre_concorde(ref: Reference, doc: dict) -> bool:
    auteurs = normaliser(" ".join(doc.get("author_name", [])))
    nom = normaliser(ref.auteur).split(" ")[0] if ref.auteur else ""
    return (similarite(ref.titre, doc.get("title", "")) >= SEUIL_TROUVE
            and annee_compatible(ref.annee, doc.get("first_publish_year"))
            and (not nom or nom in auteurs))


def recherches_open_library(ref: Reference) -> list[str]:
    """Recherche exacte par titre, puis repli large (catalogues qui n'enregistrent qu'un titre court)."""
    mots = " ".join(ref.titre.split()[:3])
    return [f"https://openlibrary.org/search.json?limit=5&title={q(ref.titre)}&author={q(ref.auteur)}",
            f"https://openlibrary.org/search.json?limit=5&q={q(mots + ' ' + ref.auteur)}"]


def verifier_livre(ref: Reference, fetch) -> Verdict:
    erreurs = 0
    for url in recherches_open_library(ref):
        try:
            docs = fetch(url).get("docs", [])
        except (OSError, NonTrouve, ValueError):
            erreurs += 1
            continue
        for doc in docs:
            if livre_concorde(ref, doc):
                return Verdict(ref, TROUVE, f"Open Library : « {doc.get('title')} », {doc.get('first_publish_year')}, "
                                            f"{', '.join(doc.get('author_name', [])[:2])}.")
    if erreurs == 2:
        return Verdict(ref, ERREUR_RESEAU, "Open Library injoignable.")
    return Verdict(ref, A_CONFIRMER, "Absent d'Open Library : vérifier dans le catalogue de la BnF, de la KBR ou WorldCat.")


def verifier_arxiv(ref: Reference, fetch_page) -> Verdict:
    try:
        _, xml = fetch_page(f"https://export.arxiv.org/api/query?id_list={q(ref.arxiv)}")
        # Flux Atom de l'API arXiv uniquement ; l'expat de Python ≥ 3.13 ne résout pas les entités
        # externes et limite l'expansion d'entités, ce qui évite d'ajouter defusedxml comme dépendance.
        entrees = ET.fromstring(xml).findall(f"{ATOM}entry")
    except (OSError, NonTrouve, ET.ParseError) as err:
        return Verdict(ref, ERREUR_RESEAU, f"API arXiv injoignable : {err}")
    titres = [" ".join((e.findtext(f"{ATOM}title") or "").split()) for e in entrees]
    titres = [t for t in titres if t and t.lower() != "error"]
    if not titres:
        return Verdict(ref, INTROUVABLE, f"L'identifiant arXiv {ref.arxiv} n'existe pas.")
    if similarite(ref.titre, titres[0]) < SEUIL_PROCHE:
        return Verdict(ref, DIVERGENT, f"arXiv {ref.arxiv} pointe vers « {titres[0]} ».")
    return Verdict(ref, TROUVE, f"arXiv {ref.arxiv} : « {titres[0]} ».", acces_libre=f"https://arxiv.org/abs/{ref.arxiv}")


def texte_visible(html: str) -> str:
    sans_scripts = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    return unescape(re.sub(r"<[^>]+>", " ", sans_scripts))


def verifier_par_url(ref: Reference, fetch_page) -> Verdict:
    """Dernier recours quand les bases bibliographiques ne connaissent pas la référence."""
    absent = "Absent de Crossref et d'OpenAlex"
    try:
        type_contenu, texte = fetch_page(ref.url)
    except NonTrouve:
        return Verdict(ref, INTROUVABLE, f"{absent}, et le lien {ref.url} est mort (404).")
    except OSError as err:
        return Verdict(ref, A_CONFIRMER, f"{absent} ; lien injoignable automatiquement ({err}) : l'ouvrir à la main.")
    if type_contenu == "application/pdf":
        return Verdict(ref, A_CONFIRMER, f"{absent} ; document PDF accessible ({ref.url}), titre non contrôlé.")
    debut_titre = " ".join(normaliser(ref.titre).split()[:MOTS_TITRE_DANS_PAGE])
    if debut_titre and debut_titre in normaliser(texte_visible(texte)):
        return Verdict(ref, TROUVE, f"Page en ligne qui porte le titre : {ref.url}.")
    return Verdict(ref, A_CONFIRMER, f"{absent} ; page accessible mais le titre n'y figure pas ({ref.url}).")


def verifier_reference(ref: Reference, fetch=lire_json, fetch_page=lire_page) -> Verdict:
    if not ref.titre:
        return Verdict(ref, A_CONFIRMER, "Titre non repéré (ni « guillemets » ni *italique* ni _italique_) : vérifier à la main.")
    if ref.arxiv:
        return verifier_arxiv(ref, fetch_page)
    if ref.doi:
        return verifier_par_doi(ref, fetch)
    if ref.est_livre:
        return verifier_livre(ref, fetch)
    verdict = verifier_par_recherche(ref, fetch)
    if verdict.statut == INTROUVABLE and ref.url:
        return verifier_par_url(ref, fetch_page)
    return verdict


# ── Point d'entrée ─────────────────────────────────────────────────────────

def afficher(verdicts: list[Verdict]) -> None:
    for v in verdicts:
        print(f"\n[{v.statut}] {v.reference.auteur} — {v.reference.titre or v.reference.texte[:60]}")
        print(f"    {v.detail}")
        if v.doi and v.doi != v.reference.doi:
            print(f"    DOI trouvé : {v.doi}")
        if v.acces_libre:
            print(f"    Texte intégral en accès libre : {v.acces_libre}")
    bilan = {s: sum(v.statut == s for v in verdicts) for s in (TROUVE, A_CONFIRMER, DIVERGENT, INTROUVABLE, ERREUR_RESEAU)}
    print("\n== Bilan : " + " · ".join(f"{n} {s}" for s, n in bilan.items() if n))


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Vérifie l'existence des références bibliographiques d'un article.")
    ap.add_argument("article", help="chemin du fichier .md")
    args = ap.parse_args(argv)
    try:
        texte = Path(args.article).read_text(encoding="utf-8")
    except OSError as err:
        print(f"Lecture impossible : {err}", file=sys.stderr)
        return 2
    refs = extraire_references(texte)
    if not refs:
        print("Aucune entrée trouvée sous « ## Bibliographie ».", file=sys.stderr)
        return 2
    verdicts = [verifier_reference(r) for r in refs]
    afficher(verdicts)
    return 1 if any(v.statut in (DIVERGENT, INTROUVABLE) for v in verdicts) else 0


if __name__ == "__main__":
    sys.exit(main())
