"""Tests du skill roman : configuration, vérificateur et assembleur (stdlib unittest).

Lancer : python -m unittest discover  (depuis scripts/)
"""

import json
import shutil
import tempfile
import textwrap
import unittest
from pathlib import Path

import assembler_manuscrit as am
import config_roman as cr
import verifier_roman as vr

PLAN = textwrap.dedent('''\
    # Plan — La Nuit du quai nord

    ## Chapitres

    | # | Titre | Fichier | PDV | Personnages | Jalon | Résumé |
    |---|---|---|---|---|---|---|
    | 1 | Le corps | 01-le-corps.md | Mathilde Arnaud | Mathilde Arnaud, Paul Verdier | incident déclencheur | On retrouve Paul sur le quai. |
    | 2 | Les dockers | 02-les-dockers.md | Mathilde Arnaud | Mathilde Arnaud, Jean Morel | | Mathilde interroge l'équipe de nuit. |
    | 3 | La grue | 03-la-grue.md | Mathilde Arnaud | Mathilde Arnaud, Jean Morel | révélation | La cabine de la grue parle. |
    ''')

PERSONNAGES = textwrap.dedent('''\
    # Personnages

    ## Mathilde Arnaud
    - alias : la commissaire, Arnaud
    - naissance : 1978
    - rôle : enquêtrice

    ## Paul Verdier
    - naissance : 1990
    - mort : 2026
    - rôle : victime

    ## Jean Morel
    - alias : le grutier
    - naissance : 1965
    ''')

LIEUX = textwrap.dedent('''\
    # Lieux

    ## Belcourt
    ## Quai nord
    - alias : le quai
    ''')

INDICES = textwrap.dedent('''\
    # Indices et révélations

    ## Indices

    | # | Indice | Posé | Exploité |
    |---|---|---|---|
    | I1 | Le casque fendu | 1 | 3 |
    | I2 | Les clés de la cabine | 2 | 3 |

    ## Révélations

    | # | Révélation | Chapitre | Préparée par |
    |---|---|---|---|
    | R1 | Morel était dans la cabine | 3 | I1, I2 |
    ''')


def chapitre(numero, titre, corps, statut="brouillon", date='"2026-03-14"', pdv="Mathilde Arnaud"):
    return (f'---\nnumero: {numero}\ntitre: "{titre}"\npdv: "{pdv}"\ndate_recit: {date}\nstatut: {statut}\n---\n\n'
            + corps.strip() + "\n")


CORPS_1 = '''
La pluie tombait sur le quai depuis minuit. Mathilde Arnaud descendit de voiture et releva son col.
Le corps de Paul Verdier gisait entre deux conteneurs, un casque fendu posé à côté de sa main.

* * *

— Qui l'a trouvé ? demanda-t-elle.
— L'équipe de relève, répondit le brigadier.
'''

CORPS_2 = '''
Jean Morel attendait dans la salle de pause, les mains autour d'un gobelet froid. Mathilde posa sur la table
le trousseau retrouvé dans la poche de la victime : les clés de la cabine de la grue.
— Je ne les avais jamais vues, dit Morel.
'''

CORPS_3 = '''
La cabine sentait l'huile et le tabac. Mathilde ouvrit la porte avec les clés du trousseau et vit, sur le siège,
la marque d'un casque fendu. Morel avait menti : il était monté dans la grue cette nuit-là.
'''


class Base(unittest.TestCase):
    def setUp(self):
        self.racine = Path(tempfile.mkdtemp())
        cr._charger.cache_clear()
        self.ecrire("redactor.json", json.dumps({"roman": {"titre": "La Nuit du quai nord", "auteur": "A. Exemple",
                                                           "genre": "polar", "objectif_mots": 60000}}))
        self.ecrire("plan.md", PLAN)
        self.ecrire("bible/personnages.md", PERSONNAGES)
        self.ecrire("bible/lieux.md", LIEUX)
        self.ecrire("bible/indices.md", INDICES)
        self.ecrire("chapitres/01-le-corps.md", chapitre(1, "Le corps", CORPS_1))
        self.ecrire("chapitres/02-les-dockers.md", chapitre(2, "Les dockers", CORPS_2))
        self.ecrire("chapitres/03-la-grue.md", chapitre(3, "La grue", CORPS_3))

    def tearDown(self):
        shutil.rmtree(self.racine)
        cr._charger.cache_clear()

    def ecrire(self, relatif, texte):
        chemin = self.racine / relatif
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(texte, encoding="utf-8")
        cr._charger.cache_clear()
        return chemin

    def configurer(self, **roman):
        self.ecrire("redactor.json", json.dumps({"roman": roman}))

    def rapport(self):
        return vr.analyser(self.racine)

    def codes(self):
        return {r.code for r in self.rapport().resultats}

    def bloquants(self):
        return {r.code for r in self.rapport().resultats if r.bloquant}


class TestConfig(Base):
    def test_defauts_sans_redactor_json(self):
        (self.racine / "redactor.json").unlink()
        cfg = cr.charger(self.racine)
        self.assertEqual((cfg.genre, cfg.dossier_chapitres, cfg.objectif_mots), ("litterature", "chapitres", None))

    def test_genre_inconnu(self):
        with self.assertRaises(cr.ConfigInvalide):
            cr.depuis_dict({"roman": {"genre": "western"}})

    def test_objectif_invalide(self):
        for valeur in (0, -5, "60000", True):
            with self.assertRaises(cr.ConfigInvalide, msg=valeur):
                cr.depuis_dict({"roman": {"objectif_mots": valeur}})

    def test_cle_inconnue(self):
        with self.assertRaises(cr.ConfigInvalide):
            cr.depuis_dict({"roman": {"chapitre": "x"}})

    def test_charte_commune_heritee(self):
        cfg = cr.depuis_dict({"charte": "voix.md", "roman": {}})
        self.assertEqual(cfg.charte, "voix.md")


class TestProjetConforme(Base):
    def test_aucun_bloquant_ni_avertissement(self):
        rapport = self.rapport()
        self.assertEqual([(r.code, r.message) for r in rapport.resultats], [])

    def test_avancement(self):
        rapport = self.rapport()
        self.assertEqual([c.numero for c in rapport.chapitres], [1, 2, 3])
        self.assertEqual(rapport.total, sum(c.mots for c in rapport.chapitres))
        self.assertEqual(rapport.objectif, 60000)
        self.assertEqual(rapport.manquants, [])


class TestPlanEtAvancement(Base):
    def test_chapitre_prevu_non_ecrit(self):
        (self.racine / "chapitres/03-la-grue.md").unlink()
        rapport = self.rapport()
        self.assertEqual([m.numero for m in rapport.manquants], [3])

    def test_chapitre_hors_plan(self):
        self.ecrire("chapitres/04-epilogue.md", chapitre(4, "Épilogue", "Mathilde rentra chez elle."))
        self.assertIn("CHAPITRE_HORS_PLAN", self.codes())

    def test_plan_absent(self):
        (self.racine / "plan.md").unlink()
        self.assertIn("PLAN_ABSENT", self.codes())

    def test_numero_different_du_plan(self):
        self.ecrire("chapitres/02-les-dockers.md", chapitre(5, "Les dockers", CORPS_2))
        self.assertIn("NUMERO_PLAN", self.codes())

    def test_statut_inconnu(self):
        self.ecrire("chapitres/02-les-dockers.md", chapitre(2, "Les dockers", CORPS_2, statut="fini"))
        self.assertIn("STATUT_INCONNU", self.bloquants())

    def test_date_recit_invalide(self):
        self.ecrire("chapitres/02-les-dockers.md", chapitre(2, "Les dockers", CORPS_2, date="2026-03-14"))
        self.assertIn("DATE_RECIT", self.bloquants())

    def test_date_recit_annee_seule_admise(self):
        self.ecrire("chapitres/02-les-dockers.md", chapitre(2, "Les dockers", CORPS_2, date='"2026"'))
        self.assertNotIn("DATE_RECIT", self.codes())

    def test_frontmatter_yaml_invalide(self):
        self.ecrire("chapitres/02-les-dockers.md", "---\ntitre: [\n---\nTexte.\n")
        self.assertIn("FRONTMATTER_YAML", self.bloquants())


class TestContinuite(Base):
    def test_personnage_du_plan_absent_de_la_bible(self):
        self.ecrire("plan.md", PLAN.replace("Mathilde Arnaud, Jean Morel | |", "Mathilde Arnaud, Lucie Fabre | |"))
        self.assertIn("PERSONNAGE_INCONNU", self.codes())

    def test_variante_de_nom(self):
        self.ecrire("chapitres/02-les-dockers.md",
                    chapitre(2, "Les dockers", CORPS_2.replace("Mathilde posa", "Puis Mathide posa")))
        resultats = [r for r in self.rapport().resultats if r.code == "NOM_VARIANTE"]
        self.assertTrue(resultats and "Mathilde" in resultats[0].message, resultats)

    def test_nom_recurrent_absent_de_la_bible(self):
        ajout = " Lucie Fabre fumait. Lucie Fabre attendait. On parlait de Lucie Fabre."
        self.ecrire("chapitres/02-les-dockers.md", chapitre(2, "Les dockers", CORPS_2 + ajout))
        self.assertIn("NOM_HORS_BIBLE", self.codes())

    def test_mots_courants_en_majuscule_ignores(self):
        ajout = " Lundi, Madame la juge appela. En Mars, Dieu sait pourquoi. Lundi encore, Lundi toujours."
        self.ecrire("chapitres/02-les-dockers.md", chapitre(2, "Les dockers", CORPS_2 + ajout))
        self.assertNotIn("NOM_HORS_BIBLE", self.codes())

    def test_point_de_vue_apres_la_mort(self):
        self.ecrire("chapitres/02-les-dockers.md",
                    chapitre(2, "Les dockers", CORPS_2, pdv="Paul Verdier", date='"2027-01-10"'))
        self.assertIn("PDV_CHRONOLOGIE", self.codes())

    def test_point_de_vue_avant_la_naissance(self):
        self.ecrire("chapitres/02-les-dockers.md",
                    chapitre(2, "Les dockers", CORPS_2, pdv="Mathilde Arnaud", date='"1970"'))
        self.assertIn("PDV_CHRONOLOGIE", self.codes())

    def test_pdv_par_alias(self):
        self.ecrire("chapitres/02-les-dockers.md",
                    chapitre(2, "Les dockers", CORPS_2, pdv="le grutier", date='"1960"'))
        self.assertIn("PDV_CHRONOLOGIE", self.codes())


class TestStyle(Base):
    def test_repetitions_proches(self):
        texte = ("Le conteneur rouge bloquait l'allée. Derrière le conteneur, un autre conteneur, "
                 "et encore un conteneur ouvert. ") * 2
        self.ecrire("chapitres/02-les-dockers.md", chapitre(2, "Les dockers", CORPS_2 + texte))
        resultats = [r for r in self.rapport().resultats if r.code == "REPETITION_PROCHE"]
        self.assertTrue(resultats and "conteneur" in resultats[0].message, resultats)

    def test_noms_de_personnages_pas_comptes_comme_repetitions(self):
        texte = " ".join(["Mathilde et Morel."] * 6)
        self.ecrire("chapitres/02-les-dockers.md", chapitre(2, "Les dockers", CORPS_2 + texte))
        self.assertNotIn("REPETITION_PROCHE", self.codes())

    def test_adverbes_en_ment(self):
        texte = ("Elle avança lentement, prudemment, silencieusement, puis regarda attentivement "
                 "et soigneusement la cabine, finalement vide. ")
        self.ecrire("chapitres/02-les-dockers.md", chapitre(2, "Les dockers", texte))
        self.assertIn("ADVERBES_MENT", self.codes())

    def test_noms_en_ment_non_comptes(self):
        texte = ("Au moment du changement d'équipe, le gouvernement du port publia un document "
                 "sur le comportement et le mouvement des équipes dans le bâtiment. ")
        self.ecrire("chapitres/02-les-dockers.md", chapitre(2, "Les dockers", texte))
        self.assertNotIn("ADVERBES_MENT", self.codes())

    def test_tics_declares(self):
        self.configurer(genre="polar", tics=["soudain"])
        texte = "Soudain, la porte claqua. Soudain, un cri. Il se retourna soudain."
        self.ecrire("chapitres/02-les-dockers.md", chapitre(2, "Les dockers", CORPS_2 + texte))
        self.assertIn("TIC", self.codes())

    def test_dialogue_au_trait_d_union(self):
        texte = CORPS_2.replace("— Je ne les avais", "- Je ne les avais")
        self.ecrire("chapitres/02-les-dockers.md", chapitre(2, "Les dockers", texte))
        self.assertIn("DIALOGUE_TIRET", self.codes())


class TestIndices(Base):
    def test_indice_non_exploite(self):
        self.ecrire("bible/indices.md", INDICES.replace("| I2 | Les clés de la cabine | 2 | 3 |",
                                                        "| I2 | Les clés de la cabine | 2 | — |"))
        self.assertIn("INDICE_NON_EXPLOITE", self.codes())

    def test_indice_exploite_avant_d_etre_pose(self):
        self.ecrire("bible/indices.md", INDICES.replace("| I1 | Le casque fendu | 1 | 3 |",
                                                        "| I1 | Le casque fendu | 3 | 2 |"))
        self.assertIn("INDICE_ORDRE", self.bloquants())

    def test_revelation_non_preparee(self):
        self.ecrire("bible/indices.md", INDICES.replace("| 3 | I1, I2 |", "| 3 | — |"))
        self.assertIn("REVELATION_NON_PREPAREE", self.codes())

    def test_revelation_preparee_trop_tard(self):
        self.ecrire("bible/indices.md", INDICES.replace("| I2 | Les clés de la cabine | 2 | 3 |",
                                                        "| I2 | Les clés de la cabine | 3 | 3 |"))
        self.assertIn("REVELATION_TROP_TOT", self.bloquants())

    def test_indice_inconnu_dans_une_revelation(self):
        self.ecrire("bible/indices.md", INDICES.replace("| 3 | I1, I2 |", "| 3 | I1, I9 |"))
        self.assertIn("INDICE_INCONNU", self.codes())

    def test_chapitre_inconnu(self):
        self.ecrire("bible/indices.md", INDICES.replace("| I1 | Le casque fendu | 1 | 3 |",
                                                        "| I1 | Le casque fendu | 1 | 12 |"))
        self.assertIn("INDICE_CHAPITRE", self.codes())

    def test_polar_sans_fichier_d_indices(self):
        (self.racine / "bible/indices.md").unlink()
        self.assertIn("INDICES_ABSENTS", self.codes())

    def test_litterature_sans_indices_admise(self):
        self.configurer(genre="litterature")
        (self.racine / "bible/indices.md").unlink()
        self.assertNotIn("INDICES_ABSENTS", self.codes())


class TestAssemblage(Base):
    def test_manuscrit_dans_l_ordre_du_plan(self):
        sortie = am.assembler(self.racine)
        texte = sortie.read_text(encoding="utf-8")
        self.assertEqual(sortie.name, "nuit-du-quai-nord.md")
        self.assertIn('title: "La Nuit du quai nord"', texte)
        self.assertLess(texte.index("Chapitre 1 — Le corps"), texte.index("Chapitre 2 — Les dockers"))
        self.assertLess(texte.index("Chapitre 2 — Les dockers"), texte.index("Chapitre 3 — La grue"))
        self.assertNotIn("statut:", texte)

    def test_saut_de_scene_normalise(self):
        self.ecrire("chapitres/01-le-corps.md", chapitre(1, "Le corps", CORPS_1.replace("* * *", "***")))
        texte = am.assembler(self.racine).read_text(encoding="utf-8")
        self.assertIn("\n\n* * *\n\n", texte)

    def test_chapitre_manquant_signale(self):
        (self.racine / "chapitres/03-la-grue.md").unlink()
        avertissements = []
        am.assembler(self.racine, signaler=avertissements.append)
        self.assertTrue(any("3" in a for a in avertissements), avertissements)

    def test_titre_de_chapitre_configurable(self):
        self.configurer(titre="La Nuit du quai nord", titre_chapitre="{numero}. {titre}")
        texte = am.assembler(self.racine).read_text(encoding="utf-8")
        self.assertIn("# 1. Le corps", texte)

    def test_export_par_pandoc(self):
        appels = []
        sortie = am.assembler(self.racine)
        am.exporter(sortie, "docx", executer=lambda cmd: appels.append(cmd) or 0, trouver=lambda nom: "pandoc")
        self.assertEqual(appels[0][0], "pandoc")
        self.assertTrue(appels[0][-1].endswith(".docx"))

    def test_export_sans_pandoc(self):
        sortie = am.assembler(self.racine)
        with self.assertRaises(am.ExportImpossible):
            am.exporter(sortie, "pdf", executer=lambda cmd: 0, trouver=lambda nom: None)


class TestRobustesse(Base):
    """Cas relevés à la relecture du code."""

    def remplacer_chapitre_2(self, ajout, **options):
        self.ecrire("chapitres/02-les-dockers.md", chapitre(2, "Les dockers", CORPS_2 + ajout, **options))

    def test_repliques_entre_guillemets_pas_des_noms(self):
        self.remplacer_chapitre_2(" « Bonjour, dit Morel. » « Bonjour ! » « Bonjour… » \"Merci\". \"Merci\". \"Merci\". "
                                  "(Viens.) (Viens.) (Viens.)")
        self.assertNotIn("NOM_HORS_BIBLE", self.codes())

    def test_prenom_seul_dans_le_plan(self):
        self.ecrire("plan.md", PLAN.replace("Mathilde Arnaud, Jean Morel | |", "Mathilde, Morel | |"))
        self.assertNotIn("PERSONNAGE_INCONNU", self.codes())

    def test_pdv_par_prenom_seul(self):
        self.remplacer_chapitre_2("", pdv="Paul", date='"2027-01-10"')
        self.assertIn("PDV_CHRONOLOGIE", self.codes())

    def test_pdv_inconnu_signale(self):
        self.remplacer_chapitre_2("", pdv="Lucie Fabre")
        self.assertIn("PDV_INCONNU", self.codes())

    def test_elisions_pas_des_repetitions(self):
        self.remplacer_chapitre_2(" Il dit qu'il venait. Elle savait qu'il mentait, et qu'il fuyait, qu'il revenait.")
        self.assertNotIn("REPETITION_PROCHE", self.codes())

    def test_annee_sans_guillemets_admise(self):
        self.remplacer_chapitre_2("", date="2026")
        self.assertNotIn("DATE_RECIT", self.codes())

    def test_titres_usuels_ignores(self):
        self.remplacer_chapitre_2(" Le Commissaire entra. Le Commissaire sortit. Puis le Commissaire revint.")
        self.assertNotIn("NOM_HORS_BIBLE", self.codes())

    def test_noms_ignores_configurables(self):
        self.configurer(genre="polar", noms_ignores=["Brigadier"])
        self.remplacer_chapitre_2(" Le Brigadier entra. Le Brigadier sortit. Puis le Brigadier revint.")
        self.assertNotIn("NOM_HORS_BIBLE", self.codes())

    def test_nom_apres_elision_detecte(self):
        self.remplacer_chapitre_2(" Le souvenir d'Élodie. Le rire d'Élodie. La voix d'Élodie.")
        self.assertIn("NOM_HORS_BIBLE", self.codes())

    def test_bible_non_utf8_ne_plante_pas(self):
        (self.racine / "bible/lieux.md").write_bytes("## Élodie\n".encode("cp1252"))
        self.rapport()

    def test_chemin_du_plan_avec_dossier(self):
        self.ecrire("plan.md", PLAN.replace("| 01-le-corps.md |", "| chapitres/01-le-corps.md |"))
        rapport = self.rapport()
        self.assertEqual(rapport.manquants, [])
        self.assertNotIn("CHAPITRE_HORS_PLAN", {r.code for r in rapport.resultats})

    def test_long_chapitre_rapide(self):
        import time
        phrase = "Mathilde marchait le long du quai, puis Morel la rejoignit près de la grue. "
        self.remplacer_chapitre_2(phrase * 6000)
        debut = time.perf_counter()
        self.rapport()
        self.assertLess(time.perf_counter() - debut, 10)

    def test_config_null_refusee(self):
        for cle in ("plan", "dossier_chapitres", "titre_chapitre", "genre"):
            with self.assertRaises(cr.ConfigInvalide, msg=cle):
                cr.depuis_dict({"roman": {cle: None}})

    def test_assemblage_chapitre_hors_plan_signale(self):
        self.ecrire("chapitres/04-epilogue.md", chapitre(4, "Épilogue", "Mathilde rentra chez elle."))
        avertissements = []
        texte = am.assembler(self.racine, signaler=avertissements.append).read_text(encoding="utf-8")
        self.assertTrue(any("04-epilogue.md" in a for a in avertissements), avertissements)
        self.assertNotIn("Mathilde rentra chez elle", texte)

    def test_titre_avec_guillemets(self):
        import yaml
        self.configurer(titre='Le "Grand" Soir', auteur='A. "Exemple"')
        texte = am.assembler(self.racine).read_text(encoding="utf-8")
        entete = yaml.safe_load(texte.split("---")[1])
        self.assertEqual(entete["title"], 'Le "Grand" Soir')

    def test_format_de_titre_de_chapitre_invalide(self):
        self.configurer(titre="T", titre_chapitre="Chapitre {chapitre}")
        with self.assertRaises(cr.ConfigInvalide):
            am.assembler(self.racine)

    def test_format_numerique_sans_numero(self):
        self.assertEqual(am.titre_de_chapitre("Chapitre {numero:02d} — {titre}", None, "Prologue"), "Prologue")
        self.assertEqual(am.titre_de_chapitre("Chapitre {numero:02d} — {titre}", 3, "La grue"), "Chapitre 03 — La grue")

    def test_titre_terminant_par_points_de_suspension(self):
        self.assertEqual(am.titre_de_chapitre("{numero}. {titre}", 4, "La fin…"), "4. La fin…")


class TestLigneDeCommande(Base):
    def test_verifier_code_0(self):
        self.assertEqual(vr.main(["--root", str(self.racine)]), 0)

    def test_verifier_code_1_si_bloquant(self):
        self.ecrire("chapitres/02-les-dockers.md", chapitre(2, "Les dockers", CORPS_2, statut="fini"))
        self.assertEqual(vr.main(["--root", str(self.racine)]), 1)

    def test_verifier_un_chapitre(self):
        self.assertEqual(vr.main(["--root", str(self.racine), "--chapitre", "2"]), 0)

    def test_configuration_invalide_code_2(self):
        self.ecrire("redactor.json", "{ pas du json")
        self.assertEqual(vr.main(["--root", str(self.racine)]), 2)

    def test_assembler_code_0(self):
        self.assertEqual(am.main(["--root", str(self.racine)]), 0)
        self.assertTrue((self.racine / "manuscrit" / "nuit-du-quai-nord.md").is_file())


class TestExempleDuDepot(unittest.TestCase):
    def test_exemple_roman_sans_bloquant(self):
        racine = Path(__file__).resolve().parents[3] / "exemples" / "roman"
        cr._charger.cache_clear()
        rapport = vr.analyser(racine)
        cr._charger.cache_clear()
        self.assertGreaterEqual(len(rapport.chapitres), 2)
        self.assertEqual([(r.code, r.message) for r in rapport.resultats], [])


if __name__ == "__main__":
    unittest.main()
