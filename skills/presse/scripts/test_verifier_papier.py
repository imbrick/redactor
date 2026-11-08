"""Tests du vérificateur de papiers de presse (stdlib unittest).

Lancer : python -m unittest discover  (depuis scripts/)
"""

import json
import shutil
import tempfile
import textwrap
import unittest
from pathlib import Path

import config_presse as cp
import verifier_papier as vp

BON_FRONTMATTER = textwrap.dedent('''\
    ---
    format: actualite
    rubrique: Économie
    surtitre: "Transport"
    titre: "Le port de Belcourt rouvre ses quais après trois semaines de grève"
    chapo: "Les dockers ont repris le travail lundi 2 novembre 2026, après un accord signé avec la direction du port sur les primes de risque. Les armateurs estiment le retard à rattraper à dix jours."
    slug: port-belcourt-reouverture
    signature: "Jeanne Exemple"
    date: "2026-11-03"
    statut: relecture
    seo_titre: "Belcourt : le port rouvre après trois semaines de grève"
    seo_description: "Les dockers du port de Belcourt ont repris le travail le 2 novembre après un accord sur les primes de risque. Les armateurs évaluent le retard à dix jours."
    mots_cles: [Belcourt, port, grève]
    exergues:
      - "Nous avons obtenu ce que nous demandions depuis deux ans"
    reseaux:
      x: "Le port de Belcourt rouvre après trois semaines de grève des dockers."
      facebook: "Après trois semaines de grève, les dockers de Belcourt ont repris le travail."
      linkedin: "Fin de la grève au port de Belcourt : ce que prévoit l'accord sur les primes de risque."
      newsletter: "Belcourt : fin de la grève des dockers"
    ---
    ''')

PARAGRAPHE = ("Les dockers ont repris le travail lundi 2 novembre 2026 au port de Belcourt, après la signature "
              "d'un accord avec la direction sur les primes de risque. Le délégué syndical a déclaré : "
              "« Nous avons obtenu ce que nous demandions depuis deux ans », selon l'enregistrement de "
              "l'entretien. La direction du port confirme la signature de l'accord dans un communiqué.")

BON_CORPS = "\n" + "\n\n".join([PARAGRAPHE] + [
    "Les armateurs estiment le retard à rattraper à dix jours, selon leur association professionnelle, "
    "qui a publié une note détaillée sur le nombre de navires en attente dans la rade. " * 2
] * 4) + "\n"

BON_DOSSIER = textwrap.dedent('''\
    # Dossier de vérification — Le port de Belcourt rouvre ses quais

    ## Faits

    | # | Affirmation | Source 1 | Source 2 | Sensible | Niveau | Traitement |
    |---|---|---|---|---|---|---|
    | F1 | Reprise du travail le 2 novembre | communiqué du port | délégué syndical | non | P4 | publié |
    | F2 | Retard de dix jours | association des armateurs | — | non | P2 | attribué |

    ## Citations

    | # | Citation | Locuteur | Recueillie | Statut |
    |---|---|---|---|---|
    | C1 | Nous avons obtenu ce que nous demandions depuis deux ans | délégué syndical | 2026-11-02, téléphone, enregistré | on |
    | C2 | La direction a cédé parce que les navires partaient à Port-Est | délégué syndical | 2026-11-02, téléphone | off |

    ## Anonymat des sources

    | Désignation dans le texte | Identité connue de | Raison de l'anonymat |
    |---|---|---|

    ## Contradictoire

    | Personne ou organisation mise en cause | Sollicitée le | Réponse |
    |---|---|---|
    | Direction du port | 2026-11-02 | communiqué, confirme l'accord |

    ## Sources

    - Port de Belcourt, communiqué du 2 novembre 2026.
    ''')


def codes(resultats):
    return {r.code for r in resultats}


def bloquants(resultats):
    return {r.code for r in resultats if r.bloquant}


class Base(unittest.TestCase):
    def setUp(self):
        self.racine = Path(tempfile.mkdtemp())
        cp._charger.cache_clear()

    def tearDown(self):
        shutil.rmtree(self.racine)
        cp._charger.cache_clear()

    def ecrire(self, relatif, texte):
        chemin = self.racine / relatif
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(texte, encoding="utf-8")
        return chemin

    def configurer(self, presse, **communs):
        self.ecrire("redactor.json", json.dumps({**communs, "presse": presse}))
        cp._charger.cache_clear()

    def papier(self, frontmatter=BON_FRONTMATTER, corps=BON_CORPS, dossier=BON_DOSSIER):
        chemin = self.ecrire("papiers/port-belcourt-reouverture.md", frontmatter + corps)
        if dossier is not None:
            self.ecrire("verification/port-belcourt-reouverture.md", dossier)
        return vp.verifier_papier(chemin, self.racine)


class TestConfig(Base):
    def test_valeurs_par_defaut_sans_redactor_json(self):
        cfg = cp.charger(self.racine)
        self.assertEqual(cfg.dossier_papiers, "papiers")
        self.assertIn("x", cfg.reseaux)
        self.assertEqual(cfg.longueurs["actualite"], cp.LONGUEURS_DEFAUT["actualite"])

    def test_section_presse_lue_et_charte_commune_heritee(self):
        self.configurer({"dossier_papiers": "copie", "longueurs": {"breve": [30, 90]}},
                        projet="Le Courrier", charte="docs/charte.md")
        cfg = cp.charger(self.racine)
        self.assertEqual((cfg.projet, cfg.charte, cfg.dossier_papiers), ("Le Courrier", "docs/charte.md", "copie"))
        self.assertEqual(cfg.longueurs["breve"], (30, 90))
        self.assertEqual(cfg.longueurs["enquete"], cp.LONGUEURS_DEFAUT["enquete"])

    def test_charte_de_la_section_prime(self):
        self.configurer({"charte": "presse/charte.md"}, charte="docs/charte.md")
        self.assertEqual(cp.charger(self.racine).charte, "presse/charte.md")

    def test_cle_inconnue_refusee(self):
        with self.assertRaises(cp.ConfigInvalide):
            cp.depuis_dict({"presse": {"dossier_papier": "x"}})

    def test_format_inconnu_dans_longueurs_refuse(self):
        with self.assertRaises(cp.ConfigInvalide):
            cp.depuis_dict({"presse": {"longueurs": {"feuilleton": [1, 2]}}})

    def test_longueur_mal_formee_refusee(self):
        with self.assertRaises(cp.ConfigInvalide):
            cp.depuis_dict({"presse": {"longueurs": {"breve": [90, 30]}}})


class TestPapierConforme(Base):
    def test_bon_papier_sans_bloquant(self):
        resultats = self.papier()
        self.assertEqual(bloquants(resultats), set(), resultats)

    def test_brouillon_sans_dossier_toleree(self):
        fm = BON_FRONTMATTER.replace("statut: relecture", "statut: brouillon")
        self.assertNotIn("DOSSIER_ABSENT", bloquants(self.papier(frontmatter=fm, dossier=None)))


class TestFrontmatter(Base):
    def test_champ_obligatoire_manquant(self):
        fm = BON_FRONTMATTER.replace('seo_titre: "Belcourt : le port rouvre après trois semaines de grève"\n', "")
        self.assertIn("CHAMP_MANQUANT", bloquants(self.papier(frontmatter=fm)))

    def test_breve_sans_chapo_admise(self):
        fm = BON_FRONTMATTER.replace("format: actualite", "format: breve")
        fm = "\n".join(l for l in fm.splitlines() if not l.startswith("chapo:")) + "\n"
        self.assertNotIn("CHAMP_MANQUANT", codes(self.papier(frontmatter=fm)))

    def test_format_inconnu(self):
        fm = BON_FRONTMATTER.replace("format: actualite", "format: feuilleton")
        self.assertIn("FORMAT_INCONNU", bloquants(self.papier(frontmatter=fm)))

    def test_statut_inconnu(self):
        fm = BON_FRONTMATTER.replace("statut: relecture", "statut: publie")
        self.assertIn("STATUT_INCONNU", bloquants(self.papier(frontmatter=fm)))

    def test_date_sans_guillemets(self):
        fm = BON_FRONTMATTER.replace('date: "2026-11-03"', "date: 2026-11-03")
        self.assertIn("DATE_FORMAT", bloquants(self.papier(frontmatter=fm)))

    def test_slug_invalide(self):
        fm = BON_FRONTMATTER.replace("slug: port-belcourt-reouverture", "slug: Port_Belcourt")
        self.assertIn("SLUG_FORMAT", bloquants(self.papier(frontmatter=fm)))

    def test_rubrique_hors_liste(self):
        self.configurer({"rubriques": ["Politique", "Culture"]})
        self.assertIn("RUBRIQUE_INCONNUE", bloquants(self.papier()))

    def test_yaml_invalide(self):
        self.assertIn("FRONTMATTER_YAML", bloquants(self.papier(frontmatter="---\ntitre: [\n---\n")))


class TestTitraille(Base):
    def test_seo_titre_trop_long(self):
        fm = BON_FRONTMATTER.replace("Belcourt : le port rouvre après trois semaines de grève",
                                     "Belcourt : le port rouvre enfin ses quais après trois longues semaines de grève des dockers")
        self.assertIn("SEO_TITRE_LONG", codes(self.papier(frontmatter=fm)))

    def test_seo_description_trop_courte(self):
        fm = BON_FRONTMATTER.replace(
            "seo_description: \"Les dockers du port de Belcourt ont repris le travail le 2 novembre après un accord "
            "sur les primes de risque. Les armateurs évaluent le retard à dix jours.\"",
            'seo_description: "Fin de grève à Belcourt."')
        self.assertIn("SEO_DESCRIPTION_COURTE", codes(self.papier(frontmatter=fm)))

    def test_chapo_trop_long(self):
        fm = BON_FRONTMATTER.replace("Les armateurs estiment", "Les armateurs, " + "très " * 60 + "inquiets, estiment")
        self.assertIn("CHAPO_LONGUEUR", codes(self.papier(frontmatter=fm)))

    def test_exergue_absente_du_texte(self):
        fm = BON_FRONTMATTER.replace("Nous avons obtenu ce que nous demandions depuis deux ans",
                                     "Une phrase que personne n'a prononcée dans le papier")
        self.assertIn("EXERGUE_ABSENTE", bloquants(self.papier(frontmatter=fm)))

    def test_reseau_manquant(self):
        fm = BON_FRONTMATTER.replace('  linkedin: "Fin de la grève au port de Belcourt : ce que prévoit l\'accord sur les primes de risque."\n', "")
        self.assertIn("RESEAU_MANQUANT", codes(self.papier(frontmatter=fm)))

    def test_message_x_trop_long(self):
        fm = BON_FRONTMATTER.replace("Le port de Belcourt rouvre après trois semaines de grève des dockers.",
                                     "Belcourt " * 50)
        self.assertIn("RESEAU_X_LONG", codes(self.papier(frontmatter=fm)))

    def test_tribune_sans_presentation_auteur(self):
        fm = BON_FRONTMATTER.replace("format: actualite", "format: tribune")
        self.assertIn("TRIBUNE_AUTEUR", codes(self.papier(frontmatter=fm)))


class TestCorps(Base):
    def test_h1_dans_le_corps(self):
        self.assertIn("H1_DANS_CORPS", bloquants(self.papier(corps="\n# Titre en double\n" + BON_CORPS)))

    def test_longueur_hors_fourchette(self):
        self.assertIn("LONGUEUR_FORMAT", codes(self.papier(corps="\n" + PARAGRAPHE + "\n")))

    def test_date_relative(self):
        corps = BON_CORPS.replace("Les armateurs estiment", "Aujourd'hui, les armateurs estiment", 1)
        self.assertIn("DATE_RELATIVE", codes(self.papier(corps=corps)))

    def test_long_papier_sans_intertitre(self):
        fm = BON_FRONTMATTER.replace("format: actualite", "format: enquete")
        corps = "\n" + "\n\n".join([PARAGRAPHE] * 20) + "\n"
        self.assertIn("SANS_INTERTITRE", codes(self.papier(frontmatter=fm, corps=corps)))

    def test_paragraphe_trop_long_pour_le_web(self):
        corps = BON_CORPS + "\n" + " ".join([PARAGRAPHE] * 3) + "\n"
        self.assertIn("PARAGRAPHE_LONG", codes(self.papier(corps=corps)))

    def test_image_sans_credit(self):
        corps = BON_CORPS + "\n![Les quais du port de Belcourt](belcourt.jpg)\n"
        self.assertIn("IMAGE_CREDIT", codes(self.papier(corps=corps)))

    def test_image_avec_credit(self):
        corps = BON_CORPS + "\n![Les quais du port de Belcourt. Photo : Jeanne Exemple](belcourt.jpg)\n"
        self.assertNotIn("IMAGE_CREDIT", codes(self.papier(corps=corps)))


class TestDossier(Base):
    def test_dossier_absent_hors_brouillon(self):
        self.assertIn("DOSSIER_ABSENT", bloquants(self.papier(dossier=None)))

    def test_citation_absente_du_dossier(self):
        corps = BON_CORPS.replace("depuis deux ans »", "depuis deux ans », puis « nous reprendrons la grève si rien ne bouge »")
        self.assertIn("CITATION_HORS_DOSSIER", bloquants(self.papier(corps=corps)))

    def test_citation_courte_ignoree(self):
        corps = BON_CORPS.replace("primes de risque", "« primes de risque »", 1)
        self.assertNotIn("CITATION_HORS_DOSSIER", codes(self.papier(corps=corps)))

    def test_citation_trouvee_malgre_typographie(self):
        dossier = BON_DOSSIER.replace("Nous avons obtenu ce que nous demandions depuis deux ans",
                                      "nous  avons obtenu ce que nous demandions depuis deux ans")
        self.assertNotIn("CITATION_HORS_DOSSIER", codes(self.papier(dossier=dossier)))

    def test_citation_off_publiee(self):
        corps = BON_CORPS.replace("depuis deux ans »",
                                  "depuis deux ans ». « La direction a cédé parce que les navires partaient à Port-Est »")
        self.assertIn("CITATION_OFF", bloquants(self.papier(corps=corps)))

    def test_fait_p0_non_retire(self):
        dossier = BON_DOSSIER.replace("| non | P2 | attribué |", "| non | P0 | publié |")
        self.assertIn("FAIT_P0", bloquants(self.papier(dossier=dossier)))

    def test_fait_p0_retire_admis(self):
        dossier = BON_DOSSIER.replace("| non | P2 | attribué |", "| non | P0 | retiré |")
        self.assertNotIn("FAIT_P0", codes(self.papier(dossier=dossier)))

    def test_fait_sensible_source_unique(self):
        dossier = BON_DOSSIER.replace("| — | non | P2 | attribué |", "| — | oui | P2 | publié |")
        self.assertIn("FAIT_SENSIBLE_SOURCE_UNIQUE", bloquants(self.papier(dossier=dossier)))

    def test_fait_sensible_source_unique_attribue_admis(self):
        dossier = BON_DOSSIER.replace("| — | non | P2 | attribué |", "| — | oui | P2 | attribué |")
        self.assertNotIn("FAIT_SENSIBLE_SOURCE_UNIQUE", codes(self.papier(dossier=dossier)))

    def test_contradictoire_non_sollicite(self):
        dossier = BON_DOSSIER.replace("| Direction du port | 2026-11-02 |", "| Direction du port | — |")
        self.assertIn("CONTRADICTOIRE", bloquants(self.papier(dossier=dossier)))

    def test_source_anonyme_non_documentee(self):
        corps = BON_CORPS.replace("Les armateurs estiment", "Selon une source proche de la direction, les armateurs estiment", 1)
        self.assertIn("SOURCE_ANONYME", codes(self.papier(corps=corps)))

    def test_source_anonyme_documentee(self):
        corps = BON_CORPS.replace("Les armateurs estiment", "Selon une source proche de la direction, les armateurs estiment", 1)
        dossier = BON_DOSSIER.replace("|---|---|---|\n\n## Contradictoire",
                                      "|---|---|---|\n| une source proche de la direction | rédaction en chef | risque de licenciement |\n\n## Contradictoire")
        self.assertNotIn("SOURCE_ANONYME", codes(self.papier(corps=corps, dossier=dossier)))


class TestRobustesse(Base):
    """Cas relevés à la relecture du code : fuites, plantages, faux positifs, contrôles muets."""

    def test_fragment_de_citation_off_publie(self):
        corps = BON_CORPS.replace("depuis deux ans »", "depuis deux ans ». « La direction a cédé parce que »")
        self.assertIn("CITATION_OFF", bloquants(self.papier(corps=corps)))

    def test_format_non_chaine_ne_plante_pas(self):
        fm = BON_FRONTMATTER.replace("format: actualite", "format: [actualite]")
        self.assertIn("FORMAT_INCONNU", bloquants(self.papier(frontmatter=fm)))

    def test_citation_avec_coupure(self):
        corps = BON_CORPS.replace("Nous avons obtenu ce que nous demandions depuis deux ans",
                                  "Nous avons obtenu […] depuis deux ans", 1)
        fm = BON_FRONTMATTER.replace("exergues:\n  - \"Nous avons obtenu ce que nous demandions depuis deux ans\"\n", "")
        self.assertNotIn("CITATION_HORS_DOSSIER", codes(self.papier(frontmatter=fm, corps=corps)))

    def test_identifiant_du_fait_dans_le_message(self):
        dossier = BON_DOSSIER.replace("| non | P2 | attribué |", "| non | P0 | publié |")
        messages = [r.message for r in self.papier(dossier=dossier) if r.code == "FAIT_P0"]
        self.assertTrue(any("F2" in m for m in messages), messages)

    def test_cellules_commentees(self):
        dossier = (BON_DOSSIER
                   .replace("| — | non | P2 | attribué |", "| — | Oui (accusation) | P0 (non vérifié) | publié |")
                   .replace("Port-Est | délégué syndical | 2026-11-02, téléphone | off |",
                            "Port-Est | délégué syndical | 2026-11-02, téléphone | off, non citable |"))
        corps = BON_CORPS.replace("depuis deux ans »",
                                  "depuis deux ans ». « La direction a cédé parce que les navires partaient à Port-Est »")
        resultats = bloquants(self.papier(corps=corps, dossier=dossier))
        self.assertTrue({"FAIT_P0", "FAIT_SENSIBLE_SOURCE_UNIQUE", "CITATION_OFF"} <= resultats, resultats)

    def test_attribution_commentee_admise(self):
        dossier = BON_DOSSIER.replace("| — | non | P2 | attribué |", "| — | oui | P2 | attribué aux armateurs |")
        self.assertNotIn("FAIT_SENSIBLE_SOURCE_UNIQUE", codes(self.papier(dossier=dossier)))

    def test_section_renommee_signalee(self):
        dossier = BON_DOSSIER.replace("## Faits", "## Faits vérifiés")
        self.assertIn("DOSSIER_SECTION", bloquants(self.papier(dossier=dossier)))

    def test_colonne_renommee_signalee(self):
        dossier = BON_DOSSIER.replace("| Sensible | Niveau |", "| Sensible | Fiabilité |")
        self.assertIn("DOSSIER_COLONNE", bloquants(self.papier(dossier=dossier)))

    def test_ligne_vide_ignoree(self):
        dossier = BON_DOSSIER.replace("| Direction du port | 2026-11-02 | communiqué, confirme l'accord |",
                                      "| Direction du port | 2026-11-02 | communiqué, confirme l'accord |\n|  |  |  |")
        self.assertNotIn("CONTRADICTOIRE", codes(self.papier(dossier=dossier)))

    def test_ligne_vide_ne_documente_pas_l_anonymat(self):
        corps = BON_CORPS.replace("Les armateurs estiment", "Selon une source proche de la direction, les armateurs estiment", 1)
        dossier = BON_DOSSIER.replace("|---|---|---|\n\n## Contradictoire", "|---|---|---|\n| | | |\n\n## Contradictoire")
        self.assertIn("SOURCE_ANONYME", codes(self.papier(corps=corps, dossier=dossier)))

    def test_pipe_echappe_dans_une_cellule(self):
        dossier = BON_DOSSIER.replace("| F2 | Retard de dix jours |", "| F2 | Retard \\| dix jours |")
        self.assertEqual(bloquants(self.papier(dossier=dossier)), set())

    def test_legende_sans_credit_malgre_le_mot_photo(self):
        for legende in ("Photo des dockers au travail", "Dr Martin devant le port"):
            corps = BON_CORPS + f"\n![{legende}](a.jpg)\n"
            self.assertIn("IMAGE_CREDIT", codes(self.papier(corps=corps)), legende)

    def test_legende_dr(self):
        corps = BON_CORPS + "\n![Le quai nord. DR](a.jpg)\n"
        self.assertNotIn("IMAGE_CREDIT", codes(self.papier(corps=corps)))

    def test_paragraphe_long_apres_intertitre_colle(self):
        corps = BON_CORPS + "\n## Intertitre\n" + " ".join([PARAGRAPHE] * 3) + "\n"
        self.assertIn("PARAGRAPHE_LONG", codes(self.papier(corps=corps)))

    def test_paragraphe_long_commencant_en_gras(self):
        corps = BON_CORPS + "\n**Grève.** " + " ".join([PARAGRAPHE] * 3) + "\n"
        self.assertIn("PARAGRAPHE_LONG", codes(self.papier(corps=corps)))

    def test_exergue_chaine_unique(self):
        fm = BON_FRONTMATTER.replace('exergues:\n  - "Nous avons obtenu ce que nous demandions depuis deux ans"',
                                     'exergues: "Nous avons obtenu ce que nous demandions depuis deux ans"')
        self.assertNotIn("EXERGUE_ABSENTE", codes(self.papier(frontmatter=fm)))

    def test_exergues_mal_formees(self):
        fm = BON_FRONTMATTER.replace('exergues:\n  - "Nous avons obtenu ce que nous demandions depuis deux ans"',
                                     "exergues: 5")
        self.assertIn("EXERGUES_FORMAT", bloquants(self.papier(frontmatter=fm)))

    def test_citation_entre_guillemets_anglais(self):
        corps = BON_CORPS + "\nIl ajoute : “nous reprendrons la grève si rien ne bouge”.\n"
        self.assertIn("CITATION_HORS_DOSSIER", bloquants(self.papier(corps=corps)))

    def test_date_entiere(self):
        fm = BON_FRONTMATTER.replace('date: "2026-11-03"', "date: 20261103")
        self.assertIn("DATE_FORMAT", bloquants(self.papier(frontmatter=fm)))

    def test_titre_liste_vide(self):
        fm = BON_FRONTMATTER.replace('titre: "Le port de Belcourt rouvre ses quais après trois semaines de grève"',
                                     "titre: []")
        self.assertIn("CHAMP_MANQUANT", bloquants(self.papier(frontmatter=fm)))

    def test_url_hors_decompte(self):
        self.assertEqual(vp.mots("[ici](https://exemple.org/un/long/chemin/vers/page)"), 1)

    def test_oe_normalise(self):
        self.assertEqual(vp.normaliser("Œuvre"), vp.normaliser("oeuvre"))


class TestLigneDeCommande(Base):
    def test_papier_absent_code_2(self):
        self.assertEqual(vp.main([str(self.racine / "papiers" / "absent.md"), "--root", str(self.racine)]), 2)

    def test_code_0_si_conforme(self):
        chemin = self.ecrire("papiers/port-belcourt-reouverture.md", BON_FRONTMATTER + BON_CORPS)
        self.ecrire("verification/port-belcourt-reouverture.md", BON_DOSSIER)
        self.assertEqual(vp.main([str(chemin), "--root", str(self.racine)]), 0)

    def test_code_1_si_bloquant(self):
        chemin = self.ecrire("papiers/port-belcourt-reouverture.md", BON_FRONTMATTER + BON_CORPS)
        self.assertEqual(vp.main([str(chemin), "--root", str(self.racine)]), 1)

    def test_dossier_designe_explicitement(self):
        chemin = self.ecrire("papiers/port-belcourt-reouverture.md", BON_FRONTMATTER + BON_CORPS)
        dossier = self.ecrire("ailleurs/verif.md", BON_DOSSIER)
        self.assertEqual(vp.main([str(chemin), "--root", str(self.racine), "--verification", str(dossier)]), 0)

    def test_configuration_invalide_code_2(self):
        self.ecrire("redactor.json", "{ pas du json")
        cp._charger.cache_clear()
        chemin = self.ecrire("papiers/port-belcourt-reouverture.md", BON_FRONTMATTER + BON_CORPS)
        self.assertEqual(vp.main([str(chemin), "--root", str(self.racine)]), 2)


class TestExemplesDuDepot(unittest.TestCase):
    """Les exemples publiés dans le dépôt doivent passer le vérificateur."""

    def test_exemple_presse_conforme(self):
        racine = Path(__file__).resolve().parents[3] / "exemples" / "presse"
        cp._charger.cache_clear()
        resultats = vp.verifier_papier(racine / "papiers" / "port-belcourt-reouverture.md", racine)
        cp._charger.cache_clear()
        self.assertEqual(bloquants(resultats), set(), resultats)


if __name__ == "__main__":
    unittest.main()
