"""Tests du skill manga : configuration, lecture du script, vérificateur, assembleur (stdlib unittest).

Lancer : python -m unittest discover  (depuis scripts/)
"""

import json
import shutil
import tempfile
import textwrap
import unittest
from pathlib import Path

import assembler_script as asm
import config_manga as cm
import verifier_manga as vm

PLAN = textwrap.dedent('''\
    # Plan — Les Gardiens du phare

    ## Chapitres

    | # | Titre | Fichier | Personnages | Résumé |
    |---|---|---|---|---|
    | 1 | La lumière | 01-la-lumiere.md | Aki, Rose | Aki découvre que le phare s'allume seul. |
    | 2 | La tempête | 02-la-tempete.md | Aki, Rose | La tempête révèle le gardien. |
    ''')

PERSONNAGES = textwrap.dedent('''\
    # Personnages

    ## Aki Moreau
    - alias : Aki
    - naissance : 2012
    - apparence : cheveux courts, ciré jaune trop grand

    ## Rose Moreau
    - alias : Rose, grand-mère
    - naissance : 1945
    ''')


def page(numero, cases, etiquette=""):
    corps = f"## Page {numero}{' ' + etiquette if etiquette else ''}\n\n"
    for i, contenu in enumerate(cases, 1):
        corps += f"### Case {i}\n{contenu}\n\n"
    return corps


CASE_SIMPLE = "Plan large du phare sous la pluie.\nAKI : Grand-mère, il s'allume tout seul !"
CASE_MUETTE = "Gros plan sur la lampe qui tourne.\nSFX : VRRRM"


def chapitre(numero=1, titre="La lumière", pages=None, statut="script", entete_extra="", nb_pages=4,
             corps=None):
    if corps is None:
        corps = ""
        for n in range(1, nb_pages + 1):
            etiquette = "(cliffhanger)" if n == nb_pages else ""
            corps += page(n, [CASE_SIMPLE, CASE_MUETTE], etiquette)
    lignes = ["---", f"numero: {numero}", f'titre: "{titre}"', f"statut: {statut}"]
    if pages is not None:
        lignes.append(f"pages: {pages}")
    return "\n".join(lignes) + entete_extra + "\n---\n\n" + corps


class Base(unittest.TestCase):
    def setUp(self):
        self.racine = Path(tempfile.mkdtemp())
        self.configurer(titre="Les Gardiens du phare", auteur="A. Exemple", format="serie", pages_par_chapitre=4)
        self.ecrire("plan.md", PLAN)
        self.ecrire("bible/personnages.md", PERSONNAGES)
        self.ecrire("chapitres/01-la-lumiere.md", chapitre())
        self.ecrire("chapitres/02-la-tempete.md", chapitre(2, "La tempête"))

    def tearDown(self):
        shutil.rmtree(self.racine)
        cm._charger.cache_clear()

    def ecrire(self, relatif, texte):
        chemin = self.racine / relatif
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(texte, encoding="utf-8")
        cm._charger.cache_clear()
        return chemin

    def configurer(self, **section):
        self.ecrire("redactor.json", json.dumps({"manga": section}))

    def chap1(self, **options):
        self.ecrire("chapitres/01-la-lumiere.md", chapitre(**options))

    def rapport(self):
        return vm.analyser(self.racine)

    def codes(self):
        return {r.code for r in self.rapport().resultats}


class TestConfig(Base):
    def test_defauts(self):
        cfg = cm.depuis_dict({})
        self.assertEqual((cfg.format, cfg.sens, cfg.page_revelation), ("serie", "rtl", "paire"))

    def test_choix_invalides(self):
        for cle, valeur in (("format", "bd"), ("sens", "haut-bas"), ("page_revelation", "droite")):
            with self.assertRaises(cm.ConfigInvalide, msg=cle):
                cm.depuis_dict({"manga": {cle: valeur}})

    def test_entiers_invalides(self):
        for valeur in (0, -1, "7", True):
            with self.assertRaises(cm.ConfigInvalide):
                cm.depuis_dict({"manga": {"cases_max_par_page": valeur}})

    def test_null(self):
        with self.assertRaises(cm.ConfigInvalide):
            cm.depuis_dict({"manga": {"format": None}})
        self.assertIsNone(cm.depuis_dict({"manga": {"pages_par_chapitre": None}}).pages_par_chapitre)


class TestLecture(Base):
    def test_pages_cases_bulles(self):
        corps = page(1, ["Description : la mer.\nAKI (pensée) : Encore lui…\nNARRATION : Ce soir-là.\nSFX : SPLASH"])
        pages = vm.lire_script(corps)
        case = pages[0].cases[0]
        self.assertEqual(pages[0].numeros, (1,))
        self.assertEqual(case.description, ["la mer."])
        self.assertEqual([(b.locuteur, b.nature) for b in case.bulles], [("AKI", "dialogue"), ("NARRATION", "narration")])
        self.assertEqual(case.bulles[0].texte, "Encore lui…")
        self.assertEqual(case.sfx, ["SPLASH"])

    def test_double_page_et_etiquettes(self):
        pages = vm.lire_script("## Pages 4-5 (double page) (révélation)\n\n### Case 1\nLe phare entier.\n")
        self.assertEqual(pages[0].numeros, (4, 5))
        self.assertEqual(pages[0].etiquettes, {"double page", "revelation"})

    def test_ligne_avec_deux_points_dans_une_description(self):
        pages = vm.lire_script(page(1, ["Une enseigne : « Café du port ».\nAKI : Ici."]))
        self.assertEqual(len(pages[0].cases[0].bulles), 1)
        self.assertEqual(pages[0].cases[0].description, ["Une enseigne : « Café du port »."])

    def test_sequences_de_webtoon(self):
        pages = vm.lire_script("## Séquence 1\n\n### Case 1\nLe ciel.\n\n### Case 2\nLa mer.\n")
        self.assertEqual((pages[0].numeros, len(pages[0].cases)), ((1,), 2))


class TestProjetConforme(Base):
    def test_aucun_avertissement(self):
        self.assertEqual([(r.code, r.message) for r in self.rapport().resultats], [])

    def test_avancement(self):
        rapport = self.rapport()
        self.assertEqual([(c.numero, c.pages) for c in rapport.chapitres], [(1, 4), (2, 4)])
        self.assertEqual(rapport.chapitres[0].cases, 8)
        self.assertEqual(rapport.chapitres[0].bulles, 4)


class TestMiseEnPage(Base):
    def test_pages_hors_cible(self):
        self.chap1(nb_pages=6)
        self.assertIn("PAGES_CIBLE", self.codes())

    def test_cible_du_chapitre_prime(self):
        self.chap1(nb_pages=6, pages=6)
        self.assertNotIn("PAGES_CIBLE", self.codes())

    def test_page_vide(self):
        self.chap1(corps=page(1, [CASE_SIMPLE]) + "## Page 2\n\n" + page(3, [CASE_SIMPLE]) + page(4, [CASE_SIMPLE], "(cliffhanger)"))
        self.assertIn("PAGE_VIDE", self.codes())

    def test_numerotation(self):
        self.chap1(corps=page(1, [CASE_SIMPLE]) + page(3, [CASE_SIMPLE]) + page(4, [CASE_SIMPLE], "(cliffhanger)"))
        self.assertIn("NUMEROTATION", self.codes())

    def test_trop_de_cases(self):
        self.chap1(corps=page(1, [CASE_MUETTE] * 9) + page(2, [CASE_SIMPLE]) + page(3, [CASE_SIMPLE])
                   + page(4, [CASE_SIMPLE], "(cliffhanger)"))
        self.assertIn("CASES_PAR_PAGE", self.codes())

    def test_double_page_compte_double(self):
        corps = (page(1, [CASE_SIMPLE]) + "## Pages 2-3 (double page)\n\n"
                 + "".join(f"### Case {i}\n{CASE_MUETTE}\n\n" for i in range(1, 11)) + page(4, [CASE_SIMPLE], "(cliffhanger)"))
        self.chap1(corps=corps)
        self.assertNotIn("CASES_PAR_PAGE", self.codes())

    def test_case_sans_description(self):
        self.chap1(corps=page(1, ["AKI : Bonjour."]) + page(2, [CASE_SIMPLE]) + page(3, [CASE_SIMPLE])
                   + page(4, [CASE_SIMPLE], "(cliffhanger)"))
        self.assertIn("CASE_SANS_DESCRIPTION", self.codes())


class TestBulles(Base):
    def test_trop_de_bulles(self):
        case = "La cuisine.\n" + "\n".join(["AKI : Oui.", "ROSE : Non.", "AKI : Si.", "ROSE : Bon."])
        self.chap1(corps=page(1, [case]) + page(2, [CASE_SIMPLE]) + page(3, [CASE_SIMPLE]) + page(4, [CASE_SIMPLE], "(cliffhanger)"))
        self.assertIn("BULLES_PAR_CASE", self.codes())

    def test_bulle_trop_longue(self):
        case = "La cuisine.\nROSE : " + " ".join(["mot"] * 30)
        self.chap1(corps=page(1, [case]) + page(2, [CASE_SIMPLE]) + page(3, [CASE_SIMPLE]) + page(4, [CASE_SIMPLE], "(cliffhanger)"))
        self.assertIn("MOTS_PAR_BULLE", self.codes())

    def test_onomatopees_pas_comptees(self):
        case = "La tempête.\n" + "\n".join(["SFX : BOUM"] * 6) + "\nAKI : Vite !"
        self.chap1(corps=page(1, [case]) + page(2, [CASE_SIMPLE]) + page(3, [CASE_SIMPLE]) + page(4, [CASE_SIMPLE], "(cliffhanger)"))
        self.assertNotIn("BULLES_PAR_CASE", self.codes())


class TestRythme(Base):
    def test_revelation_sur_page_impaire(self):
        self.chap1(corps=page(1, [CASE_SIMPLE]) + page(2, [CASE_SIMPLE]) + page(3, [CASE_SIMPLE], "(révélation)")
                   + page(4, [CASE_SIMPLE], "(cliffhanger)"))
        self.assertIn("REVELATION_TOURNE", self.codes())

    def test_revelation_sur_page_paire(self):
        self.chap1(corps=page(1, [CASE_SIMPLE]) + page(2, [CASE_SIMPLE], "(révélation)") + page(3, [CASE_SIMPLE])
                   + page(4, [CASE_SIMPLE], "(cliffhanger)"))
        self.assertNotIn("REVELATION_TOURNE", self.codes())

    def test_parite_configurable(self):
        self.configurer(titre="T", format="serie", pages_par_chapitre=4, page_revelation="impaire")
        self.chap1(corps=page(1, [CASE_SIMPLE]) + page(2, [CASE_SIMPLE]) + page(3, [CASE_SIMPLE], "(révélation)")
                   + page(4, [CASE_SIMPLE], "(cliffhanger)"))
        self.assertNotIn("REVELATION_TOURNE", self.codes())

    def test_double_page_mal_placee(self):
        corps = (page(1, [CASE_SIMPLE]) + page(2, [CASE_SIMPLE]) + "## Pages 3-4 (double page)\n\n### Case 1\nLa mer.\n\n")
        self.chap1(corps=corps, entete_extra='\ncliffhanger: "le gardien apparaît"')
        self.assertIn("DOUBLE_PAGE", self.codes())

    def test_serie_sans_cliffhanger(self):
        self.chap1(corps="".join(page(n, [CASE_SIMPLE]) for n in range(1, 5)))
        self.assertIn("CLIFFHANGER", self.codes())

    def test_cliffhanger_dans_le_frontmatter(self):
        self.chap1(corps="".join(page(n, [CASE_SIMPLE]) for n in range(1, 5)), entete_extra='\ncliffhanger: "la porte s\'ouvre"')
        self.assertNotIn("CLIFFHANGER", self.codes())

    def test_oneshot_sans_cliffhanger_admis(self):
        self.configurer(titre="T", format="oneshot")
        self.chap1(corps="".join(page(n, [CASE_SIMPLE]) for n in range(1, 5)))
        self.assertNotIn("CLIFFHANGER", self.codes())

    def test_webtoon_sans_controle_de_tourne(self):
        self.configurer(titre="T", format="webtoon")
        corps = "## Séquence 1 (révélation)\n\n### Case 1\nLe ciel.\nAKI : Là-haut !\n\n"
        self.chap1(corps=corps, entete_extra='\ncliffhanger: "une ombre"')
        self.assertNotIn("REVELATION_TOURNE", self.codes())
        self.assertNotIn("PAGES_CIBLE", self.codes())


class TestContinuite(Base):
    def test_locuteur_inconnu(self):
        case = "La cuisine.\nLUCIE : Bonsoir."
        self.chap1(corps=page(1, [case]) + page(2, [CASE_SIMPLE]) + page(3, [CASE_SIMPLE]) + page(4, [CASE_SIMPLE], "(cliffhanger)"))
        self.assertIn("LOCUTEUR_INCONNU", self.codes())

    def test_locuteurs_speciaux_admis(self):
        case = "La rue.\nNARRATION : Plus tard.\nRÉCITATIF : Le soir.\nVOIX : Qui est là ?\nTOUS : Non !"
        self.chap1(corps=page(1, [case]) + page(2, [CASE_SIMPLE]) + page(3, [CASE_SIMPLE]) + page(4, [CASE_SIMPLE], "(cliffhanger)"))
        self.assertNotIn("LOCUTEUR_INCONNU", self.codes())

    def test_variante_de_nom_dans_les_descriptions(self):
        case = "Plus tard, Moreaux referme la porte.\nAKI : Voilà."
        self.chap1(corps=page(1, [case]) + page(2, [CASE_SIMPLE]) + page(3, [CASE_SIMPLE]) + page(4, [CASE_SIMPLE], "(cliffhanger)"))
        self.assertIn("NOM_VARIANTE", self.codes())

    def test_chapitre_hors_plan(self):
        self.ecrire("chapitres/03-bonus.md", chapitre(3, "Bonus"))
        self.assertIn("CHAPITRE_HORS_PLAN", self.codes())

    def test_statut_inconnu(self):
        self.chap1(statut="fini")
        self.assertIn("STATUT_INCONNU", {r.code for r in self.rapport().resultats if r.bloquant})


class TestRobustesse(Base):
    """Cas relevés à la relecture du code."""

    def quatre_pages(self, page1, etiquette1=""):
        return page(1, [page1], etiquette1) + page(2, [CASE_SIMPLE]) + page(3, [CASE_SIMPLE]) + page(4, [CASE_SIMPLE], "(cliffhanger)")

    def test_etiquettes_separees_par_des_virgules(self):
        pages = vm.lire_script("## Page 2 (révélation, cliffhanger)\n\n### Case 1\nLa mer.\n")
        self.assertEqual(pages[0].etiquettes, {"revelation", "cliffhanger"})

    def test_etiquette_inconnue_signalee(self):
        self.chap1(corps=self.quatre_pages(CASE_SIMPLE, "(revelaton)"))
        self.assertIn("ETIQUETTE_INCONNUE", self.codes())

    def test_replique_sur_deux_lignes(self):
        case = vm.lire_script("## Page 1\n\n### Case 1\nLa cuisine.\nAKI : Je ne sais\npas pourquoi.\n")[0].cases[0]
        self.assertEqual(case.bulles[0].texte, "Je ne sais pas pourquoi.")
        self.assertEqual(case.description, ["La cuisine."])

    def test_formats_de_locuteur(self):
        corps = "## Page 1\n\n### Case 1\nLa rue.\n**AKI** : Un.\n- ROSE : Deux.\nAKI, ROSE : Trois.\nAKI & ROSE : Quatre.\n??? : Qui ?\n"
        bulles = vm.lire_script(corps)[0].cases[0].bulles
        self.assertEqual([b.locuteur for b in bulles], ["AKI", "ROSE", "AKI, ROSE", "AKI & ROSE", "???"])

    def test_plusieurs_locuteurs_connus(self):
        case = "La rue.\nAKI, ROSE : Ensemble !\n??? : Qui est là ?"
        self.chap1(corps=self.quatre_pages(case))
        self.assertNotIn("LOCUTEUR_INCONNU", self.codes())

    def test_cliffhanger_false(self):
        self.chap1(corps="".join(page(n, [CASE_SIMPLE]) for n in range(1, 5)), entete_extra="\ncliffhanger: false")
        self.assertIn("CLIFFHANGER", self.codes())

    def test_pages_en_texte(self):
        self.chap1(nb_pages=6, entete_extra='\npages: "6"')
        self.assertNotIn("PAGES_CIBLE", self.codes())

    def test_ligne_pathologique_rapide(self):
        import time
        debut = time.perf_counter()
        vm.lire_script("## Page 1\n\n### Case 1\nA" + " " * 4000 + "x\n")
        self.assertLess(time.perf_counter() - debut, 1)

    def test_plage_inversee(self):
        self.chap1(corps=page(1, [CASE_SIMPLE]) + "## Pages 3-2\n\n### Case 1\nLa mer.\n\n" + page(4, [CASE_SIMPLE], "(cliffhanger)"))
        self.assertIn("NUMEROTATION", self.codes())

    def test_tiret_cadratin_dans_une_plage(self):
        self.assertEqual(vm.lire_script("## Pages 2—3\n\n### Case 1\nLa mer.\n")[0].numeros, (2, 3))

    def test_plage_geante_rapide(self):
        self.chap1(corps="## Pages 1-99999999\n\n### Case 1\nLa mer.\n")
        self.assertIn("NUMEROTATION", self.codes())

    def test_bloc_de_code_ignore(self):
        corps = self.quatre_pages(CASE_SIMPLE) + "```\n## Page 9\n```\n"
        self.chap1(corps=corps)
        self.assertNotIn("NUMEROTATION", self.codes())

    def test_case_sans_numero(self):
        pages = vm.lire_script("## Page 1\n\n### Case\nLa mer.\n\n### Case\nLe ciel.\n")
        self.assertEqual([c.numero for c in pages[0].cases], [1, 2])

    def test_assemblage_titre_interne_decale(self):
        self.chap1(corps="# Notes\n\n" + self.quatre_pages(CASE_SIMPLE))
        texte = asm.assembler_script(self.racine).read_text(encoding="utf-8")
        self.assertNotIn("\n# Notes", texte)

    def test_plan_avec_ligne_en_double(self):
        self.ecrire("plan.md", PLAN.replace("| 2 | La tempête |", "| 1 | La lumière | 01-la-lumiere.md | Aki | doublon |\n| 2 | La tempête |"))
        avertissements = []
        asm.assembler_script(self.racine, signaler=avertissements.append)
        self.assertFalse(any("pas écrit" in a for a in avertissements), avertissements)


class TestAssemblage(Base):
    def test_script_complet(self):
        sortie = asm.assembler_script(self.racine)
        texte = sortie.read_text(encoding="utf-8")
        self.assertEqual(sortie.name, "gardiens-du-phare-script.md")
        self.assertLess(texte.index("# Chapitre 1 — La lumière"), texte.index("# Chapitre 2 — La tempête"))
        self.assertIn("### Page 1", texte)
        self.assertIn("#### Case 1", texte)
        self.assertNotIn("statut:", texte)

    def test_feuille_de_lettrage(self):
        sortie = asm.feuille_de_lettrage(self.racine)
        texte = sortie.read_text(encoding="utf-8")
        self.assertEqual(sortie.name, "gardiens-du-phare-lettrage.md")
        self.assertIn("| 1 | 1 | AKI | dialogue | Grand-mère, il s'allume tout seul ! |", texte)
        self.assertIn("| 1 | 2 | SFX | onomatopée | VRRRM |", texte)

    def test_pipe_echappe_dans_le_lettrage(self):
        corps = page(1, ["La mer.\nAKI : Oui | non ?"]) + page(2, [CASE_SIMPLE]) + page(3, [CASE_SIMPLE]) + page(4, [CASE_SIMPLE], "(cliffhanger)")
        self.chap1(corps=corps)
        self.assertIn("Oui \\| non ?", asm.feuille_de_lettrage(self.racine).read_text(encoding="utf-8"))

    def test_main(self):
        self.assertEqual(asm.main(["--root", str(self.racine), "--lettrage"]), 0)


class TestLigneDeCommande(Base):
    def test_code_0(self):
        self.assertEqual(vm.main(["--root", str(self.racine)]), 0)

    def test_code_1(self):
        self.chap1(statut="fini")
        self.assertEqual(vm.main(["--root", str(self.racine)]), 1)

    def test_un_chapitre(self):
        self.assertEqual(vm.main(["--root", str(self.racine), "--chapitre", "2"]), 0)

    def test_config_invalide(self):
        self.ecrire("redactor.json", "{ pas du json")
        self.assertEqual(vm.main(["--root", str(self.racine)]), 2)


class TestExempleDuDepot(unittest.TestCase):
    def test_exemple_manga_sans_avertissement(self):
        racine = Path(__file__).resolve().parents[3] / "exemples" / "manga"
        cm._charger.cache_clear()
        rapport = vm.analyser(racine)
        cm._charger.cache_clear()
        self.assertGreaterEqual(len(rapport.chapitres), 1)
        self.assertEqual([(r.code, r.message) for r in rapport.resultats], [])


if __name__ == "__main__":
    unittest.main()
