from adndpg._testeur import TesteurVisuel, test
from adndpg.clavier import (
    touche_appuyee, touche_enfoncee, touche_relachee,
    HAUT, BAS, GAUCHE, DROITE, ESPACE, ENTREE, ECHAP,
    A, B, C, D, E, F, G, H, I, J, K, L, M,
    N, O, P, Q, R, S, T, U, V, W, X, Y, Z,
    CHIFFRE_0, CHIFFRE_1, CHIFFRE_2, CHIFFRE_3, CHIFFRE_4,
    CHIFFRE_5, CHIFFRE_6, CHIFFRE_7, CHIFFRE_8, CHIFFRE_9
)
from adndpg.formes import Carre
from adndpg.texte import Texte
from adndpg.couleurs import NOIR, ROUGE, VERT, BLEU, GRIS


class TestsClavier(TesteurVisuel):

    
    @test("Constantes de touches définies")
    def test_touches_definies(self):
        # Vérifier que les constantes existent et sont des entiers
        touches_directions = [HAUT, BAS, GAUCHE, DROITE]
        touches_speciales = [ESPACE, ENTREE, ECHAP]
        touches_lettres = [A, B, C, D, E, F, G, H, I, J, K, L, M,
                          N, O, P, Q, R, S, T, U, V, W, X, Y, Z]
        touches_chiffres = [CHIFFRE_0, CHIFFRE_1, CHIFFRE_2, CHIFFRE_3, CHIFFRE_4,
                           CHIFFRE_5, CHIFFRE_6, CHIFFRE_7, CHIFFRE_8, CHIFFRE_9]
        
        for touche in touches_directions + touches_speciales + touches_lettres + touches_chiffres:
            self.verifier_vrai(isinstance(touche, int), f"Touche {touche} devrait être un entier")
        
        # Afficher les codes
        texte = Texte(
            contenu=f"HAUT={HAUT}, BAS={BAS}, GAUCHE={GAUCHE}, DROITE={DROITE}",
            x=50, y=100, taille=20, couleur=NOIR
        )
        texte.dessiner()
        
        texte2 = Texte(
            contenu=f"ESPACE={ESPACE}, ENTREE={ENTREE}, ECHAP={ECHAP}",
            x=50, y=130, taille=20, couleur=NOIR
        )
        texte2.dessiner()
        
        texte3 = Texte(
            contenu=f"A={A}, Z={Z}, 0={CHIFFRE_0}, 9={CHIFFRE_9}",
            x=50, y=160, taille=20, couleur=NOIR
        )
        texte3.dessiner()
    
    @test("Fonctions de détection retournent bool")
    def test_fonctions_retour(self):
        # Les fonctions doivent retourner des booléens
        result_appuyee = touche_appuyee(ESPACE)
        result_enfoncee = touche_enfoncee(ESPACE)
        result_relachee = touche_relachee(ESPACE)
        
        self.verifier_vrai(isinstance(result_appuyee, bool), "touche_appuyee devrait retourner bool")
        self.verifier_vrai(isinstance(result_enfoncee, bool), "touche_enfoncee devrait retourner bool")
        self.verifier_vrai(isinstance(result_relachee, bool), "touche_relachee devrait retourner bool")
        
        texte = Texte(
            contenu="Les fonctions du clavier retournent bien des booléens",
            x=50, y=200, taille=20, couleur=VERT
        )
        texte.dessiner()


if __name__ == "__main__":
    from adndpg._testeur import lancer_tests
    lancer_tests(TestsClavier)
