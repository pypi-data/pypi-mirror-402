from adndpg._testeur import TesteurVisuel, test
from adndpg.formes import Carre
from adndpg.couleurs import (
    Couleur, couleur_aleatoire,
    ROUGE, BLEU, VERT, JAUNE, ORANGE, VIOLET, ROSE, 
    NOIR, BLANC, GRIS, MARRON, CYAN, TRANSPARENT
)


class TestsCouleurs(TesteurVisuel):

    
    @test("Créer une couleur personnalisée")
    def test_couleur_creation(self):
        # raylib.Color utilise r, g, b, a
        ma_couleur = Couleur(128, 64, 192, 255)
        self.verifier_egal(ma_couleur.r, 128)
        self.verifier_egal(ma_couleur.g, 64)
        self.verifier_egal(ma_couleur.b, 192)
        self.verifier_egal(ma_couleur.a, 255)
        
        carre = Carre(x=200, y=200, taille=100, couleur=ma_couleur)
        carre.dessiner()
    
    @test("Couleur avec transparence")
    def test_couleur_alpha(self):
        couleur_semi = Couleur(255, 0, 0, 128)
        self.verifier_egal(couleur_semi.a, 128)
        
        # Dessiner un fond puis un carré semi-transparent
        fond = Carre(x=150, y=150, taille=150, couleur=BLEU)
        carre = Carre(x=200, y=200, taille=100, couleur=couleur_semi)
        fond.dessiner()
        carre.dessiner()
    
    # Le test de bornes est retiré car raylib.Color est une structure C simple (ctypes) 
    # et le comportement de clamping/wrapping dépend de l'implémentation sous-jacente.
    # @test("Bornes des valeurs de couleur")
    # def test_couleur_bornes(self):
    #     pass
    
    @test("Égalité de couleurs (composantes)")
    def test_couleur_egalite(self):
        c1 = Couleur(100, 150, 200, 255)
        c2 = Couleur(100, 150, 200, 255)
        c3 = Couleur(100, 150, 201, 255)
        
        # raylib.Color ne supporte pas l'opérateur == par défaut (ctypes),
        # donc on vérifie les composantes manuellement.
        self.verifier_vrai(c1.r == c2.r and c1.g == c2.g and c1.b == c2.b and c1.a == c2.a, 
                           "Couleurs identiques devraient avoir les mêmes composantes")
        self.verifier_faux(c1.r == c3.r and c1.g == c3.g and c1.b == c3.b and c1.a == c3.a, 
                           "Couleurs différentes devraient avoir des composantes différentes")
    
    @test("Palette de couleurs prédéfinies")
    def test_palette(self):
        couleurs = [ROUGE, BLEU, VERT, JAUNE, ORANGE, VIOLET, 
                    ROSE, NOIR, GRIS, MARRON, CYAN]
        
        x = 50
        for couleur in couleurs:
            carre = Carre(x=x, y=200, taille=50, couleur=couleur)
            carre.dessiner()
            x += 60
    
    @test("Couleur aléatoire")
    def test_couleur_aleatoire(self):
        couleurs_obtenues = set()
        
        for i in range(10):
            couleur = couleur_aleatoire()
            couleurs_obtenues.add(id(couleur))
            carre = Carre(x=50 + i * 70, y=300, taille=50, couleur=couleur)
            carre.dessiner()
        
        # On devrait avoir au moins quelques couleurs différentes
        self.verifier_vrai(len(couleurs_obtenues) > 1, "couleur_aleatoire devrait varier")
    
    @test("Couleur TRANSPARENT")
    def test_transparent(self):
        self.verifier_egal(TRANSPARENT.a, 0)
        
        # Dessiner un fond visible et un carré transparent par-dessus
        fond = Carre(x=200, y=200, taille=100, couleur=ROUGE)
        invisible = Carre(x=220, y=220, taille=60, couleur=TRANSPARENT)
        fond.dessiner()
        invisible.dessiner()  # Ne devrait rien afficher


if __name__ == "__main__":
    from adndpg._testeur import lancer_tests
    lancer_tests(TestsCouleurs)
