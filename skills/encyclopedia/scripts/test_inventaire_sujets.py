"""Tests de l'inventaire des sujets dérivés (stdlib unittest).

Lancer : python -m unittest test_inventaire_sujets.py  (depuis scripts/)
"""

import json
import shutil
import tempfile
import textwrap
import unittest
from pathlib import Path

import inventaire_sujets as inv
import projet

CONFIG = {
    "dossier_brainstorm": "ressources/brainstorm",
    "fichiers_index": ["INDEX.md"],
    "champ_titre_court": "titre_simple",
}

FICHE_HYDRO = textwrap.dedent('''\
    # Brainstorm — Articles dérivables de l'article « Hydrographie de la RDC »

    ## A. Cours d'eau

    | Titre pressenti | Branche taxonomique | Priorité | Rédigé |
    |---|---|---|---|
    | Le fleuve Congo | Géographie › Hydrographie | ⭐⭐⭐ | |
    | Le lac Mai-Ndombe | Géographie › Hydrographie | ⭐⭐ | |
    | La Lufira | Géographie › Hydrographie | ⭐ | |
    | Le lac Kivu | Géographie › Hydrographie | ⭐⭐ | # |

    ## Récapitulatif

    | Catégorie | Articles pressentis |
    |---|---|
    | Cours d'eau | 4 |
    ''')

FICHE_WAGENIA = textwrap.dedent('''\
    # Brainstorm — Articles dérivables de l'article « Wagénia »

    | Titre pressenti | Branche taxonomique | Priorité | Rédigé |
    |---|---|---|---|
    | Fleuve Congo (le) | Géographie › Hydrographie | ⭐⭐ | |
    | Les chutes Boyoma | Géographie › Hydrographie | ⭐⭐⭐ | |
    ''')


def article(titre_simple, slug):
    return f'---\ntitle: "{titre_simple} — Titre long"\ntitre_simple: "{titre_simple}"\nslug: "{slug}"\n---\n\n# {titre_simple}\n'


class DepotTemporaire(unittest.TestCase):
    def setUp(self):
        projet._charger.cache_clear()
        self.racine = Path(tempfile.mkdtemp())
        self.ecrire(projet.NOM_FICHIER, json.dumps(CONFIG))
        self.ecrire("ressources/brainstorm/hydrographie-de-la-rdc-articles-derives.md", FICHE_HYDRO)
        self.ecrire("ressources/brainstorm/wagenia-articles-derives.md", FICHE_WAGENIA)
        self.ecrire("articles/geographie/lac-mai-ndombe.md", article("Lac Mai-Ndombe", "lac-mai-ndombe"))
        self.ecrire("articles/geographie/lac-mai-ndombe-old.md", article("Lac Mai-Ndombe", "lac-mai-ndombe"))
        self.ecrire("articles/INDEX.md", "# Index\n")

    def tearDown(self):
        shutil.rmtree(self.racine)

    def ecrire(self, rel, contenu):
        chemin = self.racine / rel
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(contenu, encoding="utf-8")


class TestLecture(DepotTemporaire):
    def test_lit_les_lignes_avec_priorite_et_ignore_le_recapitulatif(self):
        sujets = inv.lire_fiches(self.racine)
        self.assertEqual(len(sujets), 6)
        lufira = next(s for s in sujets if s.titre == "La Lufira")
        self.assertEqual(lufira.priorite, 1)
        self.assertEqual(lufira.fiche, "hydrographie-de-la-rdc")
        self.assertFalse(lufira.redige)

    def test_colonne_redige_cochee(self):
        kivu = next(s for s in inv.lire_fiches(self.racine) if s.titre == "Le lac Kivu")
        self.assertTrue(kivu.redige)


class TestNormalisation(unittest.TestCase):
    def test_article_initial_parentheses_et_accents_ignores(self):
        self.assertEqual(inv.cle("Le fleuve Congo"), inv.cle("Fleuve Congo (le)"))
        self.assertEqual(inv.cle("L'Ubangi"), "ubangi")
        self.assertEqual(inv.cle("Les chutes Boyoma"), "chutes boyoma")


class TestInventaire(DepotTemporaire):
    def setUp(self):
        super().setUp()
        self.rapport = inv.inventorier(self.racine)

    def test_doublons_fusionnes_avec_la_priorite_maximale(self):
        congo = next(c for c in self.rapport.candidats if c.cle == "fleuve congo")
        self.assertEqual(congo.priorite, 3)
        self.assertEqual(sorted(congo.fiches), ["hydrographie-de-la-rdc", "wagenia"])

    def test_sujet_deja_redige_mais_non_coche(self):
        self.assertIn("lac mai ndombe", [c.cle for c in self.rapport.redige_non_coche])

    def test_sujet_coche_sans_article(self):
        self.assertIn("lac kivu", [c.cle for c in self.rapport.coche_sans_article])

    def test_a_rediger_trie_par_priorite_puis_nombre_de_fiches(self):
        cles = [c.cle for c in self.rapport.a_rediger]
        self.assertEqual(cles[0], "fleuve congo")
        self.assertNotIn("lac mai ndombe", cles)
        self.assertNotIn("lac kivu", cles)
        self.assertEqual(cles[-1], "lufira")

    def test_filtre_par_branche(self):
        rapport = inv.inventorier(self.racine, branche="Histoire")
        self.assertEqual(rapport.a_rediger, [])


class TestLiensEnAttente(DepotTemporaire):
    def test_lien_vers_un_sujet_non_redige_compte_et_remonte(self):
        self.ecrire("articles/geographie/kasai.md", article("Kasaï", "kasai")
                    + "\n## Voir aussi\n\n- [La Lufira](/article/lufira)\n- [Lac Mai-Ndombe](/article/lac-mai-ndombe)\n")
        rapport = inv.inventorier(self.racine)
        self.assertIn(("lufira", 1), list(rapport.liens_en_attente))
        self.assertNotIn("lac-mai-ndombe", [s for s, _ in rapport.liens_en_attente])
        lufira = next(c for c in rapport.a_rediger if c.cle == "lufira")
        self.assertEqual(lufira.liens, 1)


class TestPointEntree(DepotTemporaire):
    def test_sortie_normale(self):
        self.assertEqual(inv.main(["--root", str(self.racine), "--top", "2"]), 0)

    def test_dossier_de_fiches_non_declare(self):
        self.ecrire(projet.NOM_FICHIER, "{}")
        projet._charger.cache_clear()
        self.assertEqual(inv.main(["--root", str(self.racine)]), 2)

    def test_sans_dossier_brainstorm(self):
        shutil.rmtree(self.racine / "ressources")
        self.assertEqual(inv.main(["--root", str(self.racine)]), 2)


if __name__ == "__main__":
    unittest.main()
