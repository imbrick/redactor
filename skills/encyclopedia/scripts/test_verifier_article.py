"""Tests du vérificateur d'articles (stdlib unittest).

Lancer : python -m unittest test_verifier_article.py  (depuis scripts/)
"""

import json
import shutil
import tempfile
import textwrap
import unittest
from pathlib import Path

import projet
import verifier_article as va

# Configuration d'un projet complet : celle de Kongopedia, qui a servi de modèle au skill.
CONFIG_COMPLETE = {
    "projet": "Kongopedia",
    "dossier_articles": "articles",
    "fichiers_index": ["INDEX.md", "INDEX-ALPHABETIQUE.md"],
    "dossier_brainstorm": "ressources/brainstorm",
    "suffixe_brainstorm": "-articles-derives.md",
    "champs_obligatoires": ["title", "titre_simple", "slug"],
    "champs_recommandes": ["excerpt|summary", "categories"],
    "champ_titre_court": "titre_simple",
    "prefixe_liens": "/article/",
}

BON_FRONTMATTER = textwrap.dedent('''\
    ---
    title: "Lac Kivu — Grand lac du Rift Albertin"
    titre_simple: "Lac Kivu"
    slug: "lac-kivu"
    date: "2026-11-07"
    excerpt: "Le lac Kivu est un lac du Rift Albertin partagé entre la RDC et le Rwanda."
    categories:
      - "Géographie › Hydrographie"
    ---
    ''')

BON_CORPS = textwrap.dedent('''\
    # Lac Kivu

    Le lac Kivu s'étend sur 2 700 km² entre la RDC et le Rwanda[^1].

    ## Géographie

    Il se situe à 1 460 m d'altitude[^1].

    ## Bibliographie

    - Auteur, *Titre*, éditeur, 2020.

    ## Notes

    [^1]: Source, « Titre », *Revue*, 2020.
    ''')


def codes(resultats):
    return {r.code for r in resultats}


class DepotTemporaire(unittest.TestCase):
    """Crée un faux projet complet : redactor.json, articles/, index, brainstorm."""

    config = CONFIG_COMPLETE

    def setUp(self):
        projet._charger.cache_clear()
        self.racine = Path(tempfile.mkdtemp())
        if self.config is not None:
            self.ecrire(projet.NOM_FICHIER, json.dumps(self.config))
        (self.racine / "articles" / "geographie").mkdir(parents=True)
        (self.racine / "ressources" / "brainstorm").mkdir(parents=True)
        self.ecrire_index([])

    def tearDown(self):
        shutil.rmtree(self.racine)

    def ecrire(self, rel, contenu):
        chemin = self.racine / rel
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(contenu, encoding="utf-8")
        return chemin

    def ecrire_index(self, chemins, annonce=None):
        lignes = "\n".join(f"| T | [{c}]({c}) | 2026-01-01 | RDC |" for c in chemins)
        n = len(chemins) if annonce is None else annonce
        self.ecrire("articles/INDEX.md", f"> **{n} articles indexés**\n\n{lignes}\n")
        lignes_a = "\n".join(f"| T | B | `{c}` | 2026-01-01 |" for c in chemins)
        self.ecrire("articles/INDEX-ALPHABETIQUE.md", f"> **{n} articles indexés**\n\n{lignes_a}\n")

    def verifier(self, frontmatter=BON_FRONTMATTER, corps=BON_CORPS, rel="articles/geographie/lac-kivu.md"):
        chemin = self.ecrire(rel, frontmatter + "\n" + corps)
        return va.verifier_article(chemin, self.racine)


class TestFrontmatter(DepotTemporaire):
    def test_article_conforme_et_publie_na_aucun_bloquant(self):
        self.ecrire_index(["articles/geographie/lac-kivu.md"])
        self.ecrire("ressources/brainstorm/lac-kivu-articles-derives.md", "# Brainstorm\n")
        resultats = self.verifier()
        self.assertEqual([r for r in resultats if r.bloquant], [])
        self.assertEqual(resultats, [])

    def test_frontmatter_absent_est_bloquant(self):
        resultats = self.verifier(frontmatter="")
        self.assertIn("FM_ABSENT", codes(resultats))

    def test_date_non_quotee_est_bloquante(self):
        fm = BON_FRONTMATTER.replace('date: "2026-11-07"', "date: 2026-11-07")
        self.assertIn("FM_DATE_NON_QUOTEE", codes(self.verifier(frontmatter=fm)))

    def test_slug_non_kebab_est_bloquant(self):
        fm = BON_FRONTMATTER.replace('slug: "lac-kivu"', 'slug: "Lac_Kivu"')
        self.assertIn("FM_SLUG_FORMAT", codes(self.verifier(frontmatter=fm)))

    def test_nom_de_fichier_different_du_slug_est_un_avertissement(self):
        resultats = self.verifier(rel="articles/geographie/kivu.md")
        nom = [r for r in resultats if r.code == "FICHIER_NOM"]
        self.assertEqual(len(nom), 1)
        self.assertFalse(nom[0].bloquant)

    def test_ancienne_version_publiee_est_signalee(self):
        resultats = self.verifier(rel="articles/geographie/lac-kivu-old.md")
        self.assertIn("FICHIER_ANCIENNE_VERSION", codes(resultats))

    def test_slug_duplique_dans_le_corpus(self):
        self.ecrire("articles/autre/lac-kivu.md", BON_FRONTMATTER + "\n" + BON_CORPS)
        self.assertIn("SLUG_DUPLIQUE", codes(self.verifier()))

    def test_titre_simple_absent_est_bloquant(self):
        fm = BON_FRONTMATTER.replace('titre_simple: "Lac Kivu"\n', "")
        self.assertIn("FM_TITRE_SIMPLE", codes(self.verifier(frontmatter=fm)))

    def test_titre_simple_avec_article_initial_est_signale(self):
        fm = BON_FRONTMATTER.replace('titre_simple: "Lac Kivu"', 'titre_simple: "Le Lac Kivu"')
        self.assertIn("FM_TITRE_SIMPLE_ARTICLE", codes(self.verifier(frontmatter=fm)))

    def test_publication_status_invalide(self):
        fm = BON_FRONTMATTER.replace("---\n", "---\npublication_status: \"publie\"\n", 1)
        self.assertIn("FM_STATUT", codes(self.verifier(frontmatter=fm)))

    def test_article_hors_dossier_articles(self):
        resultats = self.verifier(rel="brouillons/lac-kivu.md")
        self.assertIn("FICHIER_EMPLACEMENT", codes(resultats))


class TestRetoursRelecture(DepotTemporaire):
    """Cas relevés par la relecture de code (comportement gray-matter / js-yaml)."""

    def test_cle_yaml_dupliquee_est_bloquante(self):
        fm = BON_FRONTMATTER.replace('slug: "lac-kivu"\n', 'slug: "lac-kivu"\ntitle: "Autre"\n')
        self.assertIn("FM_INVALIDE", codes(self.verifier(frontmatter=fm)))

    def test_valeurs_yes_no_on_off_restent_des_chaines(self):
        fm = BON_FRONTMATTER.replace('titre_simple: "Lac Kivu"', "titre_simple: No")
        resultats = codes(self.verifier(frontmatter=fm))
        self.assertNotIn("FM_TITRE_SIMPLE", resultats)
        self.assertNotIn("FM_INVALIDE", resultats)

    def test_statut_vide_est_traite_comme_publie(self):
        fm = BON_FRONTMATTER.replace("---\n", "---\npublication_status:\n", 1)
        self.assertIn("INDEX_ABSENT", codes(self.verifier(frontmatter=fm)))

    def test_bom_en_tete_est_bloquant(self):
        self.assertIn("FM_BOM", codes(self.verifier(frontmatter="﻿" + BON_FRONTMATTER)))

    def test_bloc_de_code_avec_backticks_dans_la_ligne(self):
        corps = BON_CORPS.replace("## Géographie", "```a``` suite\n\n## Géographie")
        self.assertNotIn("CORPS_H1", codes(self.verifier(corps=corps)))

    def test_h1_dans_un_bloc_tilde_est_ignore(self):
        corps = BON_CORPS.replace("## Géographie", "~~~md\n# Exemple\n~~~\n\n## Géographie")
        self.assertNotIn("CORPS_H1", codes(self.verifier(corps=corps)))

    def test_appel_de_note_suivi_de_deux_points(self):
        corps = BON_CORPS.replace("le Rwanda[^1].", "le Rwanda[^1]: voir plus bas.")
        self.assertNotIn("NOTE_ORPHELINE", codes(self.verifier(corps=corps)))

    def test_doublon_avec_un_brouillon_ne_bloque_pas(self):
        brouillon = BON_FRONTMATTER.replace("---\n", "---\npublication_status: \"draft\"\n", 1)
        self.ecrire("articles/autre/lac-kivu-v2.md", brouillon + "\n" + BON_CORPS)
        self.assertNotIn("SLUG_DUPLIQUE", codes(self.verifier()))

    def test_slug_numerique_non_quote_est_bloquant(self):
        fm = BON_FRONTMATTER.replace('slug: "lac-kivu"', "slug: 1960")
        self.assertIn("FM_SLUG_FORMAT", codes(self.verifier(frontmatter=fm)))

    def test_fichier_inexistant_renvoie_le_code_2(self):
        self.assertEqual(va.main([str(self.racine / "articles" / "absent.md"), "--root", str(self.racine)]), 2)


class TestCorps(DepotTemporaire):
    def test_deux_h1_est_bloquant(self):
        corps = BON_CORPS.replace("## Géographie", "# Géographie")
        self.assertIn("CORPS_H1", codes(self.verifier(corps=corps)))

    def test_appel_de_note_sans_definition(self):
        corps = BON_CORPS.replace("altitude[^1].", "altitude[^1][^2].")
        self.assertIn("NOTE_NON_DEFINIE", codes(self.verifier(corps=corps)))

    def test_note_definie_jamais_appelee(self):
        corps = BON_CORPS + "\n[^3]: Source orpheline.\n"
        self.assertIn("NOTE_ORPHELINE", codes(self.verifier(corps=corps)))

    def test_section_conclusion_signalee(self):
        corps = BON_CORPS.replace("## Bibliographie", "## Conclusion\n\nTexte.\n\n## Bibliographie")
        self.assertIn("CORPS_CONCLUSION", codes(self.verifier(corps=corps)))

    def test_construction_ex_signalee(self):
        corps = BON_CORPS.replace("entre la RDC", "entre Kinshasa (ex-Léopoldville) et la RDC")
        self.assertIn("STYLE_EX", codes(self.verifier(corps=corps)))

    def test_citation_inline_signalee(self):
        corps = BON_CORPS.replace("altitude[^1].", "altitude (Radio Okapi, 2018)[^1].")
        self.assertIn("STYLE_CITATION_INLINE", codes(self.verifier(corps=corps)))

    def test_formule_anti_ia_signalee(self):
        corps = BON_CORPS.replace("Il se situe", "Il convient de souligner qu'il se situe")
        self.assertIn("STYLE_FORMULE_IA", codes(self.verifier(corps=corps)))

    def test_plus_dun_tiret_cadratin_par_paragraphe(self):
        corps = BON_CORPS.replace("Il se situe à 1 460 m d'altitude[^1].",
                                  "Il se situe — dit-on — à 1 460 m — environ — d'altitude[^1].")
        self.assertIn("STYLE_CADRATIN", codes(self.verifier(corps=corps)))

    def test_une_seule_incise_entre_cadratins_est_admise(self):
        corps = BON_CORPS.replace("Il se situe à 1 460 m d'altitude[^1].",
                                  "Il se situe — selon l'INS — à 1 460 m d'altitude[^1].")
        self.assertNotIn("STYLE_CADRATIN", codes(self.verifier(corps=corps)))

    def test_notes_doit_etre_la_derniere_section(self):
        corps = BON_CORPS + "\n## Voir aussi\n\n- Lac Tanganyika\n"
        self.assertIn("NOTES_POSITION", codes(self.verifier(corps=corps)))


class TestQualiteEtPreuve(DepotTemporaire):
    """Contrôles tirés du fact-check de l'os d'Ishango (fiche revision-enrichissement.md)."""

    def test_chiffre_sans_note_signale(self):
        corps = BON_CORPS.replace("d'altitude[^1].", "d'altitude[^1].\n\nSa profondeur atteint 485 m.")
        self.assertIn("PREUVE_CHIFFRE_SANS_NOTE", codes(self.verifier(corps=corps)))

    def test_chiffre_en_bibliographie_ou_en_chiffre_isole_non_signale(self):
        corps = BON_CORPS.replace("d'altitude[^1].", "d'altitude[^1].\n\nIl compte 3 îles principales.")
        self.assertNotIn("PREUVE_CHIFFRE_SANS_NOTE", codes(self.verifier(corps=corps)))

    def test_annee_seule_non_signalee_mais_milliers_signales(self):
        annee = BON_CORPS.replace("d'altitude[^1].", "d'altitude[^1].\n\nLes Belges l'explorent en 1898.")
        self.assertNotIn("PREUVE_CHIFFRE_SANS_NOTE", codes(self.verifier(corps=annee)))
        milliers = BON_CORPS.replace("d'altitude[^1].", "d'altitude[^1].\n\nIl est occupé il y a 20 000 ans.")
        self.assertIn("PREUVE_CHIFFRE_SANS_NOTE", codes(self.verifier(corps=milliers)))

    def test_affirmation_forte_signalee(self):
        corps = BON_CORPS.replace("Il se situe", "Cela démontre que l'Afrique est le berceau du calcul. Il se situe")
        self.assertIn("STYLE_AFFIRMATION_FORTE", codes(self.verifier(corps=corps)))

    def test_datation_mixte_signalee(self):
        corps = BON_CORPS.replace("d'altitude[^1].", "d'altitude[^1]. Occupé vers 18 000 av. J.-C., "
                                                     "soit 20 000 ans avant le présent[^1].")
        self.assertIn("DATATION_MIXTE", codes(self.verifier(corps=corps)))

    def test_datation_coherente_non_signalee(self):
        corps = BON_CORPS.replace("d'altitude[^1].", "d'altitude[^1]. Occupé vers 18 000 av. J.-C.[^1]")
        self.assertNotIn("DATATION_MIXTE", codes(self.verifier(corps=corps)))

    def test_bibliographie_suspecte_signalee(self):
        corps = BON_CORPS.replace("- Auteur, *Titre*, éditeur, 2020.",
                                  "- Université, *Recueil*, Kinshasa, 2012 (publication interne).")
        self.assertIn("BIBLIO_SUSPECTE", codes(self.verifier(corps=corps)))

    def test_section_dominee_par_les_puces_signalee(self):
        puces = "\n".join(f"- {n} encoches" for n in (9, 19, 21, 11))
        corps = BON_CORPS.replace("## Bibliographie", f"### Colonne gauche\n\n{puces}\n\n## Bibliographie")
        self.assertIn("PROSE_LISTES", codes(self.verifier(corps=corps)))

    def test_chronologie_en_puces_non_signalee(self):
        puces = "\n".join(f"- Étape {n}" for n in range(5))
        corps = BON_CORPS.replace("## Bibliographie", f"## Chronologie\n\n{puces}\n\n## Bibliographie")
        self.assertNotIn("PROSE_LISTES", codes(self.verifier(corps=corps)))

    def test_section_numerotee_voir_aussi_exclue(self):
        puces = "\n".join(f"- Article {n}" for n in range(5))
        corps = BON_CORPS.replace("## Bibliographie", f"## IV. Voir aussi\n\n{puces}\n\n## Bibliographie")
        self.assertNotIn("PROSE_LISTES", codes(self.verifier(corps=corps)))

    def test_prose_fragmentee_signalee(self):
        courts = "\n\n".join(f"Phrase courte numéro {n}." for n in range(6))
        corps = BON_CORPS.replace("## Bibliographie", f"## Histoire\n\n{courts}\n\n## Bibliographie")
        self.assertIn("PROSE_FRAGMENTEE", codes(self.verifier(corps=corps)))

    def test_prose_developpee_non_signalee(self):
        long = ("Le lac occupe un fossé d'effondrement de la branche ouest du Rift, ce qui explique sa grande "
                "profondeur, ses eaux stratifiées et la présence de gaz dissous dans ses couches inférieures, "
                "que les géologues étudient depuis les années 1930 pour évaluer le risque d'éruption limnique[^1].")
        corps = BON_CORPS.replace("## Bibliographie", "## Histoire\n\n" + "\n\n".join([long] * 6) + "\n\n## Bibliographie")
        self.assertNotIn("PROSE_FRAGMENTEE", codes(self.verifier(corps=corps)))


class TestPublication(DepotTemporaire):
    def test_absent_des_index_et_sans_brainstorm(self):
        resultats = codes(self.verifier())
        self.assertIn("INDEX_ABSENT", resultats)
        self.assertIn("INDEX_2_ABSENT", resultats)
        self.assertIn("BRAINSTORM_ABSENT", resultats)

    def test_publication_non_bloquante_pour_un_brouillon(self):
        fm = BON_FRONTMATTER.replace("---\n", "---\npublication_status: \"draft\"\n", 1)
        resultats = self.verifier(frontmatter=fm)
        self.assertNotIn("INDEX_ABSENT", codes(resultats))


FM_EDOUARD = BON_FRONTMATTER.replace("Lac Kivu — Grand lac du Rift Albertin", "Lac Édouard — Lac du Rift Albertin") \
    .replace('titre_simple: "Lac Kivu"', 'titre_simple: "Lac Édouard"').replace('slug: "lac-kivu"', 'slug: "lac-edouard"')


def corps_voir_aussi(*lignes):
    return BON_CORPS.replace("## Bibliographie", "## Voir aussi\n\n" + "\n".join(lignes) + "\n\n## Bibliographie")


class TestLiensInternes(DepotTemporaire):
    def test_slug_deduit_du_titre(self):
        self.assertEqual(va.slugifier("Os d'Ishango"), "os-dishango")
        self.assertEqual(va.slugifier("Lac Édouard"), "lac-edouard")
        self.assertEqual(va.slugifier("Le fleuve Congo"), "fleuve-congo")
        self.assertEqual(va.slugifier("L'Ubangi"), "ubangi")
        self.assertEqual(va.slugifier("Mouvement du 23 mars (M23)"), "mouvement-du-23-mars")
        self.assertEqual(va.slugifier("Hydrographie de la RDC"), "hydrographie-de-la-rdc")

    def test_lien_vers_article_existant_ou_a_venir_accepte(self):
        self.ecrire("articles/geographie/lac-edouard.md", FM_EDOUARD + "\n" + BON_CORPS)
        corps = corps_voir_aussi("- [Lac Édouard](/article/lac-edouard)", "- [Semliki](/article/semliki)")
        resultats = codes(self.verifier(corps=corps))
        self.assertFalse(resultats & {"LIEN_CHEMIN_MD", "LIEN_SLUG_INVALIDE", "LIEN_SLUG_CONVENTION",
                                      "VOIR_AUSSI_SANS_LIEN"})

    def test_lien_relatif_vers_un_fichier_md_signale(self):
        corps = corps_voir_aussi("- [Nyiragongo](../tectonique/nyiragongo.md)")
        self.assertIn("LIEN_CHEMIN_MD", codes(self.verifier(corps=corps)))

    def test_slug_mal_forme_signale(self):
        corps = corps_voir_aussi("- [Semliki](/article/Semliki_River)")
        self.assertIn("LIEN_SLUG_INVALIDE", codes(self.verifier(corps=corps)))

    def test_lien_a_venir_hors_convention_signale(self):
        corps = corps_voir_aussi("- [Rivière Semliki](/article/semliki)")
        self.assertIn("LIEN_SLUG_CONVENTION", codes(self.verifier(corps=corps)))

    def test_entree_voir_aussi_sans_lien_signalee(self):
        corps = corps_voir_aussi("- Semliki")
        self.assertIn("VOIR_AUSSI_SANS_LIEN", codes(self.verifier(corps=corps)))

    def test_liens_en_attente_sous_un_autre_slug(self):
        self.ecrire("articles/geographie/ishango.md", FM_EDOUARD.replace("lac-edouard", "os-dishango")
                    .replace("Lac Édouard", "Os d'Ishango") + "\n" + corps_voir_aussi("- [Lac Kivu](/article/lac-kivu-rdc)"))
        fm = BON_FRONTMATTER.replace('slug: "lac-kivu"', 'slug: "lac-kivu-rdc"')
        self.assertNotIn("LIENS_EN_ATTENTE", codes(self.verifier(frontmatter=fm)))
        autre = self.ecrire("articles/geographie/autre.md", FM_EDOUARD.replace("lac-edouard", "autre")
                            .replace("Lac Édouard", "Autre") + "\n" + corps_voir_aussi("- [Lac Kivu](/article/lac-kivu)"))
        self.assertTrue(autre.exists())
        self.assertIn("LIENS_EN_ATTENTE", codes(self.verifier(frontmatter=fm)))


class TestCorpus(DepotTemporaire):
    def test_derive_des_index_detectee(self):
        self.ecrire("articles/geographie/lac-kivu.md", BON_FRONTMATTER + "\n" + BON_CORPS)
        self.ecrire_index(["ressources/articles/geographie/ancien.md"], annonce=21)
        resultats = codes(va.verifier_corpus(self.racine))
        self.assertIn("CORPUS_COMPTEUR", resultats)
        self.assertIn("CORPUS_NON_INDEXE", resultats)
        self.assertIn("CORPUS_LIEN_MORT", resultats)


class TestProjetSansConfiguration(DepotTemporaire):
    """Sans redactor.json : seuls title et slug sont obligatoires, ni index ni fiche exigés."""

    config = None

    def test_titre_court_et_index_non_exiges(self):
        fm = BON_FRONTMATTER.replace('titre_simple: "Lac Kivu"\n', "")
        resultats = codes(self.verifier(frontmatter=fm))
        self.assertFalse(resultats & {"FM_TITRE_SIMPLE", "INDEX_ABSENT", "BRAINSTORM_ABSENT", "FM_EXCERPT"})

    def test_title_reste_obligatoire(self):
        fm = BON_FRONTMATTER.replace('title: "Lac Kivu — Grand lac du Rift Albertin"\n', "")
        self.assertIn("FM_TITLE", codes(self.verifier(frontmatter=fm)))

    def test_racine_detectee_par_le_dossier_articles(self):
        self.assertEqual(va.trouver_racine(self.racine / "articles" / "geographie"), self.racine)


class TestConfiguration(DepotTemporaire):
    config = dict(CONFIG_COMPLETE, dossier_articles="contenu", prefixe_liens="/wiki/", fichiers_index=[])

    def test_dossier_et_prefixe_personnalises(self):
        corps = corps_voir_aussi("- [Semliki](/wiki/semliki)")
        resultats = codes(self.verifier(corps=corps, rel="contenu/geographie/lac-kivu.md"))
        self.assertNotIn("FICHIER_EMPLACEMENT", resultats)
        self.assertNotIn("VOIR_AUSSI_SANS_LIEN", resultats)

    def test_article_hors_du_dossier_configure(self):
        self.assertIn("FICHIER_EMPLACEMENT", codes(self.verifier()))

    def test_racine_detectee_par_redactor_json(self):
        sous = self.racine / "contenu" / "geographie"
        sous.mkdir(parents=True)
        self.assertEqual(va.trouver_racine(sous), self.racine)

    def test_cle_inconnue_refusee(self):
        with self.assertRaises(projet.ConfigInvalide):
            projet.depuis_dict({"dossier_article": "x"})

    def test_section_d_un_autre_genre_ignoree(self):
        cfg = projet.depuis_dict({"dossier_articles": "contenu", "presse": {"dossier_papiers": "papiers"}})
        self.assertEqual(cfg.dossier_articles, "contenu")

    def test_configuration_invalide_code_2(self):
        self.ecrire(projet.NOM_FICHIER, "{ pas du json")
        projet._charger.cache_clear()
        chemin = self.ecrire("contenu/geographie/lac-kivu.md", BON_FRONTMATTER + "\n" + BON_CORPS)
        self.assertEqual(va.main([str(chemin), "--root", str(self.racine)]), 2)


if __name__ == "__main__":
    unittest.main()
