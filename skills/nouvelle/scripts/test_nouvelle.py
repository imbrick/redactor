"""Tests du skill nouvelle : configuration, vérificateur, assembleur (stdlib unittest).

Lancer : python -m unittest discover  (depuis scripts/)
"""

import json
import shutil
import tempfile
import textwrap
import unittest
from datetime import date
from pathlib import Path

import assembler_nouvelle as an
import config_nouvelle as cn
import verifier_nouvelle as vn

CORPS = textwrap.dedent('''\
    La dernière fois que le phare s'est allumé, ma grand-mère tenait la lampe. Elle avait quatre-vingts ans
    et refusait qu'on l'aide à monter les cent douze marches. Je comptais derrière elle, à voix basse.

    * * *

    — Tu sais pourquoi on l'allume encore ? m'a-t-elle demandé en haut.

    Je ne savais pas. Il n'y avait plus de bateaux depuis longtemps, plus de pêcheurs, plus de port. Elle a tourné
    la manivelle et le faisceau a balayé la mer vide.

    — Pour ceux qui reviennent, a-t-elle dit.

    Elle est morte au printemps. Le soir de l'enterrement, j'ai monté les marches seule, et j'ai allumé la lampe.
    ''')


def nouvelle(titre="Le Phare", corps=CORPS, statut="revise", **champs):
    lignes = ["---", f'titre: "{titre}"', f"statut: {statut}",
              'effet: "la tendresse qui se révèle dans le geste final"']
    lignes += [f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in champs.items()]
    return "\n".join(lignes + ["---", "", corps])


REGLEMENT = textwrap.dedent('''\
    ---
    nom: "Prix des Embruns 2027"
    signes_max: 15000
    signes_min: 500
    phrase_imposee: "Pour ceux qui reviennent"
    phrase_position: libre
    mots_imposes: [phare, marches]
    anonymat: true
    titre_obligatoire: true
    date_limite: "2099-03-31"
    ---

    Thème : le retour. Texte inédit, en français.
    ''')

RECUEIL = textwrap.dedent('''\
    # Recueil — Marées

    ## Nouvelles

    | # | Titre | Fichier |
    |---|---|---|
    | 1 | Le Phare | le-phare.md |
    | 2 | La Digue | la-digue.md |
    ''')


class Base(unittest.TestCase):
    def setUp(self):
        self.racine = Path(tempfile.mkdtemp())
        self.configurer(auteur="Claire Exemple", titre_recueil="Marées")
        self.ecrire("nouvelles/le-phare.md", nouvelle())

    def tearDown(self):
        shutil.rmtree(self.racine)
        cn._charger.cache_clear()

    def ecrire(self, relatif, texte):
        chemin = self.racine / relatif
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(texte, encoding="utf-8")
        cn._charger.cache_clear()
        return chemin

    def configurer(self, **section):
        self.ecrire("redactor.json", json.dumps({"nouvelle": section}))

    def verifier(self, fichier="le-phare.md"):
        return vn.verifier_nouvelle(self.racine / "nouvelles" / fichier, self.racine)

    def codes(self, fichier="le-phare.md"):
        return {r.code for r in self.verifier(fichier).resultats}

    def bloquants(self, fichier="le-phare.md"):
        return {r.code for r in self.verifier(fichier).resultats if r.bloquant}


class TestConfig(Base):
    def test_defauts(self):
        (self.racine / "redactor.json").unlink()
        cn._charger.cache_clear()
        cfg = cn.charger(self.racine)
        self.assertEqual((cfg.dossier_nouvelles, cfg.statuts[-1]), ("nouvelles", "final"))

    def test_cle_inconnue(self):
        with self.assertRaises(cn.ConfigInvalide):
            cn.depuis_dict({"nouvelle": {"dossier": "x"}})

    def test_null_refuse_hors_facultatives(self):
        with self.assertRaises(cn.ConfigInvalide):
            cn.depuis_dict({"nouvelle": {"dossier_nouvelles": None}})
        self.assertIsNone(cn.depuis_dict({"nouvelle": {"auteur": None}}).auteur)


class TestNouvelle(Base):
    def test_conforme(self):
        rapport = self.verifier()
        self.assertEqual([(r.code, r.message) for r in rapport.resultats], [])
        self.assertGreater(rapport.mots, 100)
        self.assertGreater(rapport.signes, rapport.mots)

    def test_statut_inconnu(self):
        self.ecrire("nouvelles/le-phare.md", nouvelle(statut="fini"))
        self.assertIn("STATUT_INCONNU", self.bloquants())

    def test_effet_absent(self):
        texte = nouvelle().replace('effet: "la tendresse qui se révèle dans le geste final"\n', "")
        self.ecrire("nouvelles/le-phare.md", texte)
        self.assertIn("EFFET_ABSENT", self.codes())

    def test_titre_absent(self):
        self.ecrire("nouvelles/le-phare.md", nouvelle(titre=""))
        self.assertIn("TITRE_ABSENT", self.codes())

    def test_frontmatter_invalide(self):
        self.ecrire("nouvelles/le-phare.md", "---\ntitre: [\n---\nTexte.\n")
        self.assertIn("FRONTMATTER_YAML", self.bloquants())

    def test_style_repris_de_roman(self):
        corps = CORPS + "\n- Je ne savais pas, dis-je.\n"
        self.ecrire("nouvelles/le-phare.md", nouvelle(corps=corps))
        self.assertIn("DIALOGUE_TIRET", self.codes())

    def test_tics(self):
        self.configurer(tics=["marches"])
        self.assertIn("TIC", self.codes())

    def test_personnages_pas_comptes_en_repetition(self):
        corps = CORPS + " ".join(["Margaux et Margaux."] * 3)
        self.ecrire("nouvelles/le-phare.md", nouvelle(corps=corps, personnages=["Margaux"]))
        self.assertNotIn("REPETITION_PROCHE", self.codes())

    def test_signes_hors_balisage(self):
        sans = vn.compter_signes("Elle dit : « Viens. »")
        avec = vn.compter_signes("Elle *dit* : « Viens. »\n\n* * *\n\n")
        self.assertEqual(sans, avec)


class TestConcours(Base):
    def setUp(self):
        super().setUp()
        self.ecrire("concours/embruns-2027.md", REGLEMENT)

    def avec_concours(self, corps=CORPS, **champs):
        self.ecrire("nouvelles/le-phare.md", nouvelle(corps=corps, concours="embruns-2027", **champs))

    def test_conforme_au_reglement(self):
        self.avec_concours()
        self.assertEqual(self.bloquants(), set())

    def test_reglement_introuvable(self):
        self.ecrire("nouvelles/le-phare.md", nouvelle(concours="inconnu"))
        self.assertIn("CONCOURS_INCONNU", self.bloquants())

    def test_trop_de_signes(self):
        self.ecrire("concours/embruns-2027.md", REGLEMENT.replace("signes_max: 15000", "signes_max: 300").replace("signes_min: 500\n", ""))
        self.avec_concours()
        self.assertIn("SIGNES_MAX", self.bloquants())

    def test_pas_assez_de_signes(self):
        self.ecrire("concours/embruns-2027.md", REGLEMENT.replace("signes_min: 500", "signes_min: 90000").replace("signes_max: 15000\n", ""))
        self.avec_concours()
        self.assertIn("SIGNES_MIN", self.bloquants())

    def test_mots_max(self):
        self.ecrire("concours/embruns-2027.md", REGLEMENT.replace("signes_min: 500", "mots_max: 50"))
        self.avec_concours()
        self.assertIn("MOTS_MAX", self.bloquants())

    def test_phrase_imposee_absente(self):
        self.avec_concours(corps=CORPS.replace("Pour ceux qui reviennent", "Pour les absents"))
        self.assertIn("PHRASE_IMPOSEE", self.bloquants())

    def test_phrase_imposee_en_ouverture(self):
        self.ecrire("concours/embruns-2027.md", REGLEMENT.replace("phrase_position: libre", "phrase_position: debut"))
        self.avec_concours()
        self.assertIn("PHRASE_POSITION", self.bloquants())

    def test_phrase_imposee_en_cloture(self):
        reglement = REGLEMENT.replace("phrase_position: libre", "phrase_position: fin").replace(
            "Pour ceux qui reviennent", "j'ai allumé la lampe")
        self.ecrire("concours/embruns-2027.md", reglement)
        self.avec_concours()
        self.assertNotIn("PHRASE_POSITION", self.codes())

    def test_mot_impose_absent(self):
        self.ecrire("concours/embruns-2027.md", REGLEMENT.replace("[phare, marches]", "[phare, albatros]"))
        self.avec_concours()
        self.assertIn("MOT_IMPOSE", self.bloquants())

    def test_mot_impose_accorde_admis(self):
        self.ecrire("concours/embruns-2027.md", REGLEMENT.replace("[phare, marches]", "[Phare, marche]"))
        self.avec_concours()
        self.assertNotIn("MOT_IMPOSE", self.codes())

    def test_anonymat_nom_dans_le_texte(self):
        self.avec_concours(corps=CORPS + "\nClaire Exemple, Marseille.\n")
        self.assertIn("ANONYMAT", self.bloquants())

    def test_titre_obligatoire(self):
        self.ecrire("nouvelles/le-phare.md", nouvelle(titre="", concours="embruns-2027"))
        self.assertIn("TITRE_ABSENT", self.bloquants())

    def test_date_limite_depassee(self):
        self.ecrire("concours/embruns-2027.md", REGLEMENT.replace("2099-03-31", "2001-03-31"))
        self.avec_concours()
        self.assertIn("DATE_LIMITE", self.codes())

    def test_reglement_mal_forme(self):
        self.ecrire("concours/embruns-2027.md", REGLEMENT.replace("signes_max: 15000", 'signes_max: "beaucoup"'))
        self.avec_concours()
        self.assertIn("REGLEMENT_INVALIDE", self.bloquants())

    def test_cle_de_reglement_inconnue(self):
        self.ecrire("concours/embruns-2027.md", REGLEMENT.replace("anonymat: true", "anonyme: true"))
        self.avec_concours()
        self.assertIn("REGLEMENT_INVALIDE", self.bloquants())


class TestRobustesse(Base):
    """Cas relevés à la relecture du code."""

    def setUp(self):
        super().setUp()
        self.ecrire("concours/embruns-2027.md", REGLEMENT)

    def reglement(self, avant, apres):
        self.ecrire("concours/embruns-2027.md", REGLEMENT.replace(avant, apres))

    def avec_concours(self, corps=CORPS, **champs):
        self.ecrire("nouvelles/le-phare.md", nouvelle(corps=corps, concours="embruns-2027", **champs))

    def test_mot_impose_elide(self):
        self.reglement("[phare, marches]", "[eau, ombre]")
        self.avec_concours(corps=CORPS + "\nL'eau montait dans l'ombre.\n")
        self.assertNotIn("MOT_IMPOSE", self.codes())

    def test_mot_impose_compose(self):
        self.reglement("[phare, marches]", "[mer vide, grand-mère]")
        self.avec_concours()
        self.assertNotIn("MOT_IMPOSE", self.codes())

    def test_mot_impose_faux_ami(self):
        self.reglement("[phare, marches]", "[mer]")
        self.avec_concours(corps=CORPS.replace("la mer vide", "la plaine vide") + "\nSa mère dormait.\n")
        self.assertIn("MOT_IMPOSE", self.codes())

    def test_date_limite_avec_heure(self):
        self.reglement('date_limite: "2099-03-31"', "date_limite: 2001-01-01 10:00:00")
        self.avec_concours()
        self.assertIn("DATE_LIMITE", self.codes())

    def test_anonymat_frontiere_de_mot(self):
        self.configurer(auteur="Marie")
        self.avec_concours(corps=CORPS + "\nMariette passa.\n")
        self.assertNotIn("ANONYMAT", self.codes())

    def test_anonymat_nom_de_famille_seul(self):
        self.avec_concours(corps=CORPS + "\nMadame Exemple passa.\n")
        self.assertIn("ANONYMAT", self.bloquants())

    def test_booleen_du_reglement_valide(self):
        self.reglement("anonymat: true", 'anonymat: "non"')
        self.avec_concours()
        self.assertIn("REGLEMENT_INVALIDE", self.bloquants())

    def test_minimum_superieur_au_maximum(self):
        self.reglement("signes_min: 500", "signes_min: 20000")
        self.avec_concours()
        self.assertIn("REGLEMENT_INVALIDE", self.bloquants())

    def test_titre_en_tete_du_corps_ignore(self):
        self.reglement("phrase_position: libre", "phrase_position: debut")
        corps = "# Le Phare\n\nPour ceux qui reviennent, le phare brille.\n\n" + CORPS
        self.avec_concours(corps=corps)
        self.assertNotIn("PHRASE_POSITION", self.codes())

    def test_emphase_sur_deux_lignes(self):
        self.assertEqual(vn.compter_signes("a *b\nc* d"), len("a b c d"))

    def test_soulignes_et_listes(self):
        self.assertEqual(vn.compter_signes("snake_case"), len("snake_case"))
        self.assertEqual(vn.compter_signes("- un\n- deux"), len("un deux"))
        self.assertEqual(vn.compter_signes("texte <!-- note --> fin"), len("texte fin"))

    def test_mots_comme_un_traitement_de_texte(self):
        self.assertEqual(vn.compter_mots("— Grand-mère, a-t-elle dit, l'eau monte."), 6)

    def test_identifiant_de_concours_avec_chemin(self):
        self.ecrire("nouvelles/le-phare.md", nouvelle(concours="../nouvelles/le-phare"))
        self.assertIn("CONCOURS_INCONNU", self.bloquants())

    def test_assembleur_refuse_un_reglement_illisible(self):
        self.ecrire("nouvelles/le-phare.md", nouvelle(concours="tyop"))
        with self.assertRaises(cn.ConfigInvalide):
            an.assembler_nouvelle(self.racine / "nouvelles/le-phare.md", self.racine)

    def test_assembleur_signe_sur_demande_malgre_reglement_illisible(self):
        self.ecrire("nouvelles/le-phare.md", nouvelle(concours="tyop"))
        sortie = an.assembler_nouvelle(self.racine / "nouvelles/le-phare.md", self.racine, anonyme=False)
        self.assertIn("Claire Exemple", sortie.read_text(encoding="utf-8"))

    def test_recueil_ne_peut_ecraser_une_nouvelle(self):
        self.configurer(auteur="Claire Exemple", titre_recueil="Le Phare")
        self.ecrire("recueil.md", RECUEIL.replace("| 2 | La Digue | la-digue.md |\n", ""))
        seule = an.assembler_nouvelle(self.racine / "nouvelles/le-phare.md", self.racine)
        recueil = an.assembler_recueil(self.racine)
        self.assertNotEqual(seule, recueil)

    def test_recueil_anonyme(self):
        self.ecrire("recueil.md", RECUEIL.replace("| 2 | La Digue | la-digue.md |\n", ""))
        sortie = an.assembler_recueil(self.racine, anonyme=True)
        self.assertNotIn("Claire Exemple", sortie.read_text(encoding="utf-8"))


class TestRecueil(Base):
    def setUp(self):
        super().setUp()
        self.ecrire("recueil.md", RECUEIL)
        self.ecrire("nouvelles/la-digue.md", nouvelle(titre="La Digue", corps=CORPS.replace("phare", "digue")))

    def test_recueil_conforme(self):
        rapport = vn.verifier_recueil(self.racine)
        self.assertEqual([r.code for r in rapport.resultats if r.bloquant], [])
        self.assertEqual([n.titre for n in rapport.nouvelles], ["Le Phare", "La Digue"])

    def test_nouvelle_prevue_absente(self):
        (self.racine / "nouvelles/la-digue.md").unlink()
        self.assertIn("NOUVELLE_MANQUANTE", {r.code for r in vn.verifier_recueil(self.racine).resultats})

    def test_nouvelle_hors_recueil(self):
        self.ecrire("nouvelles/le-quai.md", nouvelle(titre="Le Quai"))
        self.assertIn("HORS_RECUEIL", {r.code for r in vn.verifier_recueil(self.racine).resultats})

    def test_recueil_absent(self):
        (self.racine / "recueil.md").unlink()
        self.assertIn("RECUEIL_ABSENT", {r.code for r in vn.verifier_recueil(self.racine).resultats})

    def test_assembler_recueil(self):
        sortie = an.assembler_recueil(self.racine)
        texte = sortie.read_text(encoding="utf-8")
        self.assertEqual(sortie.name, "recueil-marees.md")
        self.assertIn('title: "Marées"', texte)
        self.assertLess(texte.index("# Le Phare"), texte.index("# La Digue"))


class TestAssemblage(Base):
    def test_nouvelle_seule(self):
        sortie = an.assembler_nouvelle(self.racine / "nouvelles/le-phare.md", self.racine)
        texte = sortie.read_text(encoding="utf-8")
        self.assertEqual(sortie.name, "phare.md")
        self.assertIn('author: "Claire Exemple"', texte)
        self.assertNotIn("effet:", texte)
        self.assertIn("* * *", texte)

    def test_nouvelle_anonyme(self):
        sortie = an.assembler_nouvelle(self.racine / "nouvelles/le-phare.md", self.racine, anonyme=True)
        self.assertNotIn("Claire Exemple", sortie.read_text(encoding="utf-8"))

    def test_concours_anonyme_par_defaut(self):
        self.ecrire("concours/embruns-2027.md", REGLEMENT)
        self.ecrire("nouvelles/le-phare.md", nouvelle(concours="embruns-2027"))
        sortie = an.assembler_nouvelle(self.racine / "nouvelles/le-phare.md", self.racine)
        self.assertNotIn("Claire Exemple", sortie.read_text(encoding="utf-8"))


class TestLigneDeCommande(Base):
    def test_verifier_code_0(self):
        self.assertEqual(vn.main([str(self.racine / "nouvelles/le-phare.md"), "--root", str(self.racine)]), 0)

    def test_verifier_code_1(self):
        self.ecrire("nouvelles/le-phare.md", nouvelle(statut="fini"))
        self.assertEqual(vn.main([str(self.racine / "nouvelles/le-phare.md"), "--root", str(self.racine)]), 1)

    def test_verifier_recueil(self):
        self.ecrire("recueil.md", RECUEIL.replace("| 2 | La Digue | la-digue.md |\n", ""))
        self.assertEqual(vn.main(["--recueil", "--root", str(self.racine)]), 0)

    def test_assembler_code_0(self):
        self.assertEqual(an.main([str(self.racine / "nouvelles/le-phare.md"), "--root", str(self.racine)]), 0)

    def test_config_invalide_code_2(self):
        self.ecrire("redactor.json", "{ pas du json")
        self.assertEqual(vn.main([str(self.racine / "nouvelles/le-phare.md"), "--root", str(self.racine)]), 2)


class TestExempleDuDepot(unittest.TestCase):
    def test_exemple_nouvelle_sans_avertissement(self):
        racine = Path(__file__).resolve().parents[3] / "exemples" / "nouvelle"
        cn._charger.cache_clear()
        rapport = vn.verifier_recueil(racine)
        cn._charger.cache_clear()
        self.assertGreaterEqual(len(rapport.nouvelles), 2)
        self.assertEqual([(r.code, r.message) for r in rapport.resultats], [])


if __name__ == "__main__":
    unittest.main()
