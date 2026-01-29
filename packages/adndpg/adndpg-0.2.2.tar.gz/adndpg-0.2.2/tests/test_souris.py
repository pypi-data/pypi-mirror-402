from adndpg._testeur import TesteurVisuel, test
from adndpg.souris import (
    position_souris, clic, bouton_enfonce, bouton_relache, molette,
    CLIQUE_GAUCHE, CLIQUE_DROITE, CLIQUE_MILIEU
)
from adndpg.formes import Cercle
from adndpg.texte import Texte
from adndpg.couleurs import NOIR, ROUGE, VERT, BLEU


class TestsSouris(TesteurVisuel):

    
    @test("Constantes de boutons définies")
    def test_boutons_definis(self):
        # Vérifier que les constantes existent et sont des entiers
        self.verifier_vrai(isinstance(CLIQUE_GAUCHE, int), "GAUCHE devrait être un entier")
        self.verifier_vrai(isinstance(CLIQUE_DROITE, int), "DROITE devrait être un entier")
        self.verifier_vrai(isinstance(CLIQUE_MILIEU, int), "MILIEU devrait être un entier")
        
        texte = Texte(
            contenu=f"GAUCHE={CLIQUE_GAUCHE}, DROITE={CLIQUE_DROITE}, MILIEU={CLIQUE_MILIEU}",
            x=50, y=100, taille=20, couleur=NOIR
        )
        texte.dessiner()
    
    @test("Position de la souris retourne un tuple")
    def test_position_type(self):
        pos = position_souris()
        
        self.verifier_vrai(isinstance(pos, tuple), "position_souris devrait retourner un tuple")
        self.verifier_egal(len(pos), 2)
        self.verifier_vrai(isinstance(pos[0], int), "x devrait être un entier")
        self.verifier_vrai(isinstance(pos[1], int), "y devrait être un entier")
        
        x, y = pos
        texte = Texte(
            contenu=f"Position souris: ({x}, {y})",
            x=50, y=150, taille=20, couleur=NOIR
        )
        texte.dessiner()
        
        # Dessiner un cercle à la position de la souris
        curseur = Cercle(x=x, y=y, rayon=10, couleur=ROUGE)
        curseur.dessiner()
    
    @test("Fonctions de clic retournent bool")
    def test_fonctions_clic(self):
        result_clic = clic(CLIQUE_GAUCHE)
        result_enfonce = bouton_enfonce(CLIQUE_GAUCHE)
        result_relache = bouton_relache(CLIQUE_GAUCHE)
        result_molette = molette()
        
        self.verifier_vrai(isinstance(result_clic, bool), "clic devrait retourner bool")
        self.verifier_vrai(isinstance(result_enfonce, bool), "bouton_enfonce devrait retourner bool")
        self.verifier_vrai(isinstance(result_relache, bool), "bouton_relache devrait retourner bool")
        self.verifier_vrai(isinstance(result_molette, float), "molette devrait retourner float")
        
        texte = Texte(
            contenu="Les fonctions de souris ont les bons types de retour",
            x=50, y=200, taille=20, couleur=VERT
        )
        texte.dessiner()


if __name__ == "__main__":
    from adndpg._testeur import lancer_tests
    lancer_tests(TestsSouris)
