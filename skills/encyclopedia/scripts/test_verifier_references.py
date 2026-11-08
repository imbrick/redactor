"""Tests du vérificateur de références (réseau simulé, stdlib unittest).

Lancer : python -m unittest test_verifier_references.py  (depuis scripts/)
"""

import textwrap
import unittest

import verifier_references as vr

ARTICLE = textwrap.dedent('''\
    # Titre

    Texte.

    ## Bibliographie

    - Tazieff, Haroun, « An exceptional eruption: Mt. Niragongo, Jan. 10th, 1977 », *Bulletin Volcanologique*, vol. 40, 1977, p. 189–200. DOI : 10.1007/BF02596999.
    - Smith, John W., et al. (2018). « The Dynamics of Nyiragongo Eruptions. » *Journal of Volcanology and Geothermal Research*, vol. 356.
    - Tazieff, Haroun, *Niragongo ou le volcan interdit*, Paris, Flammarion, 1975, 288 p.

    ## Notes

    [^1]: Note sans référence bibliographique.
    ''')


class FauxReseau:
    """Répond selon le premier motif d'URL trouvé ; lève OSError pour simuler une panne."""

    def __init__(self, reponses):
        self.reponses = reponses
        self.appels = []

    def __call__(self, url):
        self.appels.append(url)
        for motif, reponse in self.reponses.items():
            if motif in url:
                if isinstance(reponse, Exception):
                    raise reponse
                return reponse
        raise OSError("404")


def crossref_doi(titre, annee, revue="Bulletin Volcanologique"):
    return {"message": {"title": [titre], "issued": {"date-parts": [[annee]]},
                        "container-title": [revue], "DOI": "10.1007/BF02596999"}}


def crossref_recherche(*items):
    return {"message": {"items": [
        {"title": [t], "issued": {"date-parts": [[a]]}, "container-title": ["Revue"], "DOI": d}
        for t, a, d in items]}}


class TestExtraction(unittest.TestCase):
    def test_extrait_les_trois_references_de_la_bibliographie(self):
        refs = vr.extraire_references(ARTICLE)
        self.assertEqual(len(refs), 3)

    def test_champs_dun_article_avec_doi(self):
        ref = vr.extraire_references(ARTICLE)[0]
        self.assertEqual(ref.doi, "10.1007/BF02596999")
        self.assertTrue(ref.titre.startswith("An exceptional eruption"))
        self.assertEqual(ref.annee, 1977)
        self.assertEqual(ref.auteur, "Tazieff")
        self.assertFalse(ref.est_livre)

    def test_un_titre_en_italique_sans_guillemets_est_un_livre(self):
        ref = vr.extraire_references(ARTICLE)[2]
        self.assertTrue(ref.est_livre)
        self.assertEqual(ref.titre, "Niragongo ou le volcan interdit")

    def test_article_sans_bibliographie(self):
        self.assertEqual(vr.extraire_references("# Titre\n\nTexte.\n"), [])


ARTICLE_SOULIGNE = textwrap.dedent('''\
    # Titre

    ## Références bibliographiques

      * **Bird, P.** (2003). _An updated digital model of plate boundaries_. Geochemistry, Geophysics, Geosystems, 4(3). DOI: 10.1029/2001GC000252
      * **Hartnady, C. J. H.** (2002). _Earthquake hazard in Africa: perspectives on the Nubia-Somalia boundary_. South African Journal of Science, 98(9–10).
      * **Ndaywel è Nziem, I.** (1998). _Histoire générale du Congo_. Paris : De Boeck.


    * * *
    ''')


class TestExtractionSouligne(unittest.TestCase):
    def setUp(self):
        self.refs = vr.extraire_references(ARTICLE_SOULIGNE)

    def test_titre_en_italique_avec_tirets_bas_et_auteur_en_gras(self):
        self.assertEqual(len(self.refs), 3)
        self.assertEqual(self.refs[0].titre, "An updated digital model of plate boundaries")
        self.assertEqual(self.refs[0].auteur, "Bird")
        self.assertEqual(self.refs[0].annee, 2003)

    def test_article_de_revue_reconnu_meme_en_italique(self):
        self.assertFalse(self.refs[1].est_livre)

    def test_livre_en_italique_reste_un_livre(self):
        self.assertTrue(self.refs[2].est_livre)

    def test_ligne_de_separation_ignoree(self):
        self.assertNotIn("", [r.titre for r in self.refs])

    def test_titres_de_section_variantes(self):
        for titre in ("## Références", "## Sources et références", "## 20. Bibliographie", "## Bibliographie sélective"):
            texte = ARTICLE_SOULIGNE.replace("## Références bibliographiques", titre)
            self.assertEqual(len(vr.extraire_references(texte)), 3, titre)

    def test_doi_verifie_avant_la_piste_livre(self):
        ref = vr.Reference("x", "Bird", "An updated digital model of plate boundaries", 2003,
                           "10.1029/2001GC000252", est_livre=True)
        reseau = FauxReseau({
            "api.crossref.org/works/10.1029": crossref_doi("An updated digital model of plate boundaries", 2003),
            "api.openalex.org": {"open_access": {"oa_url": None}},
        })
        self.assertEqual(vr.verifier_reference(ref, reseau).statut, vr.TROUVE)


class TestVerification(unittest.TestCase):
    def setUp(self):
        self.refs = vr.extraire_references(ARTICLE)

    def test_doi_confirme_avec_titre_concordant(self):
        reseau = FauxReseau({
            "api.crossref.org/works/10.1007": crossref_doi("An exceptional eruption: Mt. Niragongo, Jan. 10th, 1977", 1977),
            "api.openalex.org": {"open_access": {"oa_url": None}},
        })
        self.assertEqual(vr.verifier_reference(self.refs[0], reseau).statut, vr.TROUVE)

    def test_doi_qui_pointe_vers_un_autre_article(self):
        reseau = FauxReseau({"api.crossref.org/works/10.1007": crossref_doi("Groundwater chemistry of the Alps", 2015)})
        self.assertEqual(vr.verifier_reference(self.refs[0], reseau).statut, vr.DIVERGENT)

    def test_reference_inventee_est_introuvable(self):
        reseau = FauxReseau({
            "api.crossref.org/works?": crossref_recherche(("Lava flow modelling at Etna", 2018, "10.1/x")),
            "api.openalex.org/works?": {"results": []},
        })
        self.assertEqual(vr.verifier_reference(self.refs[1], reseau).statut, vr.INTROUVABLE)

    def test_recherche_par_titre_retrouve_le_doi(self):
        reseau = FauxReseau({
            "api.crossref.org/works?": crossref_recherche(("The dynamics of Nyiragongo eruptions", 2018, "10.9/vrai")),
            "api.openalex.org/works/": {"open_access": {"oa_url": None}},
        })
        verdict = vr.verifier_reference(self.refs[1], reseau)
        self.assertEqual(verdict.statut, vr.TROUVE)
        self.assertEqual(verdict.doi, "10.9/vrai")

    def test_livre_confirme_par_open_library(self):
        reseau = FauxReseau({"openlibrary.org/search.json": {"docs": [
            {"title": "Niragongo ou le volcan interdit", "first_publish_year": 1975, "author_name": ["Haroun Tazieff"]}]}})
        self.assertEqual(vr.verifier_reference(self.refs[2], reseau).statut, vr.TROUVE)

    def test_livre_catalogue_sous_un_titre_court_retrouve_par_repli(self):
        reseau = FauxReseau({
            "search.json?limit=5&title=": {"docs": []},
            "search.json?limit=5&q=": {"docs": [
                {"title": "Niragongo volcanic activity", "first_publish_year": 1972, "author_name": ["Haroun Tazieff"]},
                {"title": "Niragongo", "first_publish_year": 1975, "author_name": ["Haroun Tazieff"]}]},
        })
        self.assertEqual(vr.verifier_reference(self.refs[2], reseau).statut, vr.TROUVE)

    def test_livre_dun_autre_auteur_nest_pas_confirme(self):
        reseau = FauxReseau({"openlibrary.org/search.json": {"docs": [
            {"title": "Niragongo", "first_publish_year": 1975, "author_name": ["Jean Dupont"]}]}})
        self.assertNotEqual(vr.verifier_reference(self.refs[2], reseau).statut, vr.TROUVE)

    def test_panne_reseau_nest_pas_une_reference_introuvable(self):
        reseau = FauxReseau({"api.crossref.org": OSError("timeout"), "api.openalex.org": OSError("timeout")})
        self.assertEqual(vr.verifier_reference(self.refs[0], reseau).statut, vr.ERREUR_RESEAU)

    def test_texte_integral_en_acces_libre_signale(self):
        reseau = FauxReseau({
            "api.crossref.org/works/10.1007": crossref_doi("An exceptional eruption: Mt. Niragongo, Jan. 10th, 1977", 1977),
            "api.openalex.org": {"open_access": {"oa_url": "https://depot.example.org/tazieff.pdf"}},
        })
        verdict = vr.verifier_reference(self.refs[0], reseau)
        self.assertEqual(verdict.acces_libre, "https://depot.example.org/tazieff.pdf")


ARTICLE_EN_LIGNE = textwrap.dedent('''\
    ## Bibliographie

    - Pletser, Vladimir et Huylebrouck, Dirk, « Contradictions and narrowness of views in the fables of Ishango », arXiv:1607.00860, 2016. URL : https://arxiv.org/abs/1607.00860.
    - Keller, Olivier, « Les fables d'Ishango, ou l'irrésistible tentation de la mathématique-fiction », *Bibnum*, août 2010. URL : https://www.bibnum.example.fr/Ishango-analyse.pdf.
    - Rapport, Collectif, « Les harpons de la Semliki », Kinshasa, 2015. URL : https://site.example.cd/harpons.html.
    ''')


def atom(titre):
    return ("text/xml", f'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>{titre}</title>'
                        "<published>2016-07-04T12:00:00Z</published></entry></feed>")


RECHERCHE_VIDE = {"api.crossref.org/works?": crossref_recherche(), "api.openalex.org/works?": {"results": []}}


class TestReferencesEnLigne(unittest.TestCase):
    def setUp(self):
        self.arxiv, self.bibnum, self.page = vr.extraire_references(ARTICLE_EN_LIGNE)

    def test_extraction_arxiv_url_et_annee_hors_identifiant(self):
        self.assertEqual(self.arxiv.arxiv, "1607.00860")
        self.assertEqual(self.arxiv.annee, 2016)
        self.assertEqual(self.bibnum.url, "https://www.bibnum.example.fr/Ishango-analyse.pdf")

    def test_arxiv_confirme_par_lapi(self):
        pages = FauxReseau({"export.arxiv.org": atom("Contradictions and narrowness of views in the fables of Ishango")})
        self.assertEqual(vr.verifier_reference(self.arxiv, FauxReseau({}), pages).statut, vr.TROUVE)

    def test_arxiv_qui_pointe_vers_un_autre_article(self):
        pages = FauxReseau({"export.arxiv.org": atom("Quantum gravity in five dimensions")})
        self.assertEqual(vr.verifier_reference(self.arxiv, FauxReseau({}), pages).statut, vr.DIVERGENT)

    def test_arxiv_inexistant(self):
        pages = FauxReseau({"export.arxiv.org": ("text/xml", '<feed xmlns="http://www.w3.org/2005/Atom"></feed>')})
        self.assertEqual(vr.verifier_reference(self.arxiv, FauxReseau({}), pages).statut, vr.INTROUVABLE)

    def test_page_html_qui_contient_le_titre(self):
        pages = FauxReseau({"site.example.cd": ("text/html", "<html><title>Accueil</title><h1>Les harpons de la "
                                                          "Semliki</h1></html>")})
        self.assertEqual(vr.verifier_reference(self.page, FauxReseau(RECHERCHE_VIDE), pages).statut, vr.TROUVE)

    def test_page_sans_le_titre_est_a_confirmer(self):
        pages = FauxReseau({"site.example.cd": ("text/html", "<html><title>Accueil</title>Bienvenue</html>")})
        self.assertEqual(vr.verifier_reference(self.page, FauxReseau(RECHERCHE_VIDE), pages).statut, vr.A_CONFIRMER)

    def test_lien_mort_reste_introuvable(self):
        pages = FauxReseau({"site.example.cd": vr.NonTrouve("404")})
        self.assertEqual(vr.verifier_reference(self.page, FauxReseau(RECHERCHE_VIDE), pages).statut, vr.INTROUVABLE)

    def test_pdf_accessible_est_a_confirmer(self):
        pages = FauxReseau({"bibnum.example.fr": ("application/pdf", "")})
        verdict = vr.verifier_reference(self.bibnum, FauxReseau(RECHERCHE_VIDE), pages)
        self.assertEqual(verdict.statut, vr.A_CONFIRMER)

    def test_lien_injoignable_nest_pas_introuvable(self):
        pages = FauxReseau({"bibnum.example.fr": OSError("certificat invalide")})
        verdict = vr.verifier_reference(self.bibnum, FauxReseau(RECHERCHE_VIDE), pages)
        self.assertEqual(verdict.statut, vr.A_CONFIRMER)
        self.assertIn("certificat invalide", verdict.detail)


class TestSimilarite(unittest.TestCase):
    def test_accents_casse_et_ponctuation_ignores(self):
        self.assertGreater(vr.similarite("L'Éruption du Niragongo.", "l eruption du niragongo"), 0.95)


if __name__ == "__main__":
    unittest.main()
