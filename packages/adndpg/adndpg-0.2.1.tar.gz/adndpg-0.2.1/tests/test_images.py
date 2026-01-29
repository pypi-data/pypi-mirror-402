import os
from adndpg._testeur import TesteurVisuel, test
from adndpg.images import Image
from adndpg.formes import Carre
from adndpg.couleurs import ROUGE

# Chemin vers l'image de test
ASSET_DIR = os.path.join(os.path.dirname(__file__), 'assets')
IMAGE_PATH = os.path.join(ASSET_DIR, 'test_image.bmp')


class TestsImages(TesteurVisuel):

    
    @test("Charger et afficher une image")
    def test_image_chargement(self):
        # Vérifier que le fichier existe
        if not os.path.exists(IMAGE_PATH):
            print(f"ATTENTION: Image de test non trouvée: {IMAGE_PATH}")
            return
            
        img = Image(chemin=IMAGE_PATH, x=100, y=100)
        
        # Vérifier les dimensions (notre image générée fait 32x32)
        self.verifier_egal(img.largeur, 32)
        self.verifier_egal(img.hauteur, 32)
        self.verifier_egal(img.x, 100)
        self.verifier_egal(img.y, 100)
        
        img.dessiner()
    
    @test("Redimensionner une image")
    def test_image_echelle(self):
        if not os.path.exists(IMAGE_PATH): return
        
        img = Image(chemin=IMAGE_PATH, x=200, y=200)
        
        # Doubler la taille
        img.echelle = 2.0
        self.verifier_egal(img.largeur, 64)  # 32 * 2
        self.verifier_egal(img.hauteur, 64)
        
        img.dessiner()
        
        # Réduire la taille
        img2 = Image(chemin=IMAGE_PATH, x=300, y=200)
        img2.echelle = 0.5
        img2.dessiner()
    
    @test("Rotation d'une image")
    def test_image_rotation(self):
        if not os.path.exists(IMAGE_PATH): return
        
        img = Image(chemin=IMAGE_PATH, x=100, y=300)
        img.rotation = 45  # 45 degrés
        
        self.verifier_egal(img.rotation, 45)
        img.dessiner()
    
    @test("Déplacer une image")
    def test_image_deplacer(self):
        if not os.path.exists(IMAGE_PATH): return
        
        img = Image(chemin=IMAGE_PATH, x=50, y=50)
        img.deplacer(dx=50, dy=50)
        
        self.verifier_egal(img.x, 100)
        self.verifier_egal(img.y, 100)
        img.dessiner()
    
    @test("Collision avec une image")
    def test_image_collision(self):
        if not os.path.exists(IMAGE_PATH): return
        
        # Image à (100, 100) de taille 32x32
        img = Image(chemin=IMAGE_PATH, x=100, y=100)
        
        # Carré qui touche l'image
        carre_touche = Carre(x=110, y=110, taille=10, couleur=ROUGE)
        
        # Carré loin
        carre_loin = Carre(x=300, y=300, taille=10, couleur=ROUGE)
        
        self.verifier_vrai(img.touche(carre_touche), "L'image devrait toucher le carré")
        self.verifier_faux(img.touche(carre_loin), "L'image ne devrait pas toucher le carré lointain")
        
        img.dessiner()
        carre_touche.dessiner()
        carre_loin.dessiner()

    @test("Utiliser redimensionner et orienter pour l'image")
    def test_image_methodes(self):
        if not os.path.exists(IMAGE_PATH): return
        img = Image(chemin=IMAGE_PATH, x=400, y=400)
        img.redimensionner(3.0)
        img.orienter(90)
        self.verifier_egal(img.echelle, 3.0)
        self.verifier_egal(img.rotation, 90)
        img.dessiner()


if __name__ == "__main__":
    from adndpg._testeur import lancer_tests
    lancer_tests(TestsImages)
