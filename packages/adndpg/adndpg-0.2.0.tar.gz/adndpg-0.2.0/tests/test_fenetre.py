

from adndpg._testeur import TesteurVisuel, test
from adndpg.fenetre import (
    obtenir_temps, obtenir_delta, 
    obtenir_largeur_fenetre, obtenir_hauteur_fenetre
)
from adndpg.formes import Carre, Rectangle
from adndpg.texte import Texte
from adndpg.couleurs import NOIR, ROUGE, BLEU, VERT


class TestsFenetre(TesteurVisuel):

    
    @test("Obtenir la taille de la fenêtre")
    def test_taille_fenetre(self):
        largeur = obtenir_largeur_fenetre()
        hauteur = obtenir_hauteur_fenetre()
        
        self.verifier_vrai(largeur > 0, "Largeur devrait être positive")
        self.verifier_vrai(hauteur > 0, "Hauteur devrait être positive")
        
        # Afficher les dimensions
        texte = Texte(
            contenu=f"Fenêtre: {largeur}x{hauteur} pixels", 
            x=50, y=100, taille=24, couleur=NOIR
        )
        texte.dessiner()
        
        # Dessiner un cadre aux bords
        bord_haut = Rectangle(x=0, y=0, largeur=largeur, hauteur=5, couleur=ROUGE)
        bord_bas = Rectangle(x=0, y=hauteur-5, largeur=largeur, hauteur=5, couleur=ROUGE)
        bord_gauche = Rectangle(x=0, y=0, largeur=5, hauteur=hauteur, couleur=BLEU)
        bord_droit = Rectangle(x=largeur-5, y=0, largeur=5, hauteur=hauteur, couleur=BLEU)
        
        bord_haut.dessiner()
        bord_bas.dessiner()
        bord_gauche.dessiner()
        bord_droit.dessiner()
    
    @test("Obtenir le temps écoulé")
    def test_obtenir_temps(self):
        temps = obtenir_temps()
        
        self.verifier_vrai(temps >= 0, "Le temps devrait être positif ou nul")
        
        texte = Texte(
            contenu=f"Temps écoulé: {temps:.2f} secondes", 
            x=50, y=200, taille=24, couleur=NOIR
        )
        texte.dessiner()
    
    @test("Obtenir le delta time")
    def test_obtenir_delta(self):
        delta = obtenir_delta()
        
        # Le delta devrait être un petit nombre positif (temps entre frames)
        self.verifier_vrai(delta >= 0, "Delta devrait être positif ou nul")
        self.verifier_vrai(delta < 1, "Delta devrait être inférieur à 1 seconde")
        
        texte = Texte(
            contenu=f"Delta: {delta*1000:.2f} ms", 
            x=50, y=200, taille=24, couleur=NOIR
        )
        texte.dessiner()
        
        # Afficher le FPS calculé
        if delta > 0:
            fps = 1.0 / delta
            fps_texte = Texte(
                contenu=f"FPS estimé: {fps:.0f}", 
                x=50, y=250, taille=24, couleur=VERT
            )
            fps_texte.dessiner()


if __name__ == "__main__":
    from adndpg._testeur import lancer_tests
    lancer_tests(TestsFenetre)
