from adndpg._testeur import TesteurVisuel, test
from adndpg.texte import Texte
from adndpg.couleurs import NOIR, ROUGE, BLEU, VERT, BLANC


class TestsTexte(TesteurVisuel):

    
    @test("Créer un texte simple")
    def test_texte_creation(self):
        texte = Texte(contenu="Bonjour!", x=100, y=100, taille=30, couleur=NOIR)
        self.verifier_egal(texte.contenu, "Bonjour!")
        self.verifier_egal(texte.x, 100)
        self.verifier_egal(texte.y, 100)
        self.verifier_egal(texte.taille, 30)
        texte.dessiner()
    
    @test("Texte avec différentes tailles")
    def test_texte_tailles(self):
        petit = Texte(contenu="Petit texte", x=50, y=100, taille=16, couleur=NOIR)
        moyen = Texte(contenu="Moyen texte", x=50, y=150, taille=24, couleur=NOIR)
        grand = Texte(contenu="Grand texte", x=50, y=200, taille=40, couleur=NOIR)
        enorme = Texte(contenu="Énorme!", x=50, y=280, taille=60, couleur=NOIR)
        
        petit.dessiner()
        moyen.dessiner()
        grand.dessiner()
        enorme.dessiner()
    
    @test("Texte avec différentes couleurs")
    def test_texte_couleurs(self):
        rouge = Texte(contenu="Texte rouge", x=100, y=100, taille=30, couleur=ROUGE)
        bleu = Texte(contenu="Texte bleu", x=100, y=150, taille=30, couleur=BLEU)
        vert = Texte(contenu="Texte vert", x=100, y=200, taille=30, couleur=VERT)
        
        rouge.dessiner()
        bleu.dessiner()
        vert.dessiner()
    
    @test("Déplacer un texte")
    def test_texte_deplacer(self):
        texte = Texte(contenu="Je bouge!", x=100, y=100, taille=24, couleur=NOIR)
        texte.deplacer(150, 100)
        
        self.verifier_egal(texte.x, 250)
        self.verifier_egal(texte.y, 200)
        texte.dessiner()
    
    @test("Téléporter un texte")
    def test_texte_aller_a(self):
        texte = Texte(contenu="Téléportation!", x=100, y=100, taille=24, couleur=NOIR)
        texte.aller_a(400, 300)
        
        self.verifier_egal(texte.x, 400)
        self.verifier_egal(texte.y, 300)
        texte.dessiner()
    
    @test("Mesurer la largeur du texte")
    def test_texte_largeur(self):
        texte = Texte(contenu="ABCDEFGH", x=100, y=200, taille=30, couleur=NOIR)
        
        # La largeur doit être positive
        self.verifier_vrai(texte.largeur > 0, "La largeur devrait être positive")
        texte.dessiner()
    
    @test("Texte invisible")
    def test_texte_invisible(self):
        texte = Texte(contenu="Tu ne me vois pas!", x=200, y=200, taille=30, couleur=ROUGE)
        texte.visible = False
        
        self.verifier_faux(texte.visible)
        texte.dessiner()  # Ne devrait rien afficher
    
    @test("Modifier le contenu du texte")
    def test_texte_modifier_contenu(self):
        texte = Texte(contenu="Avant", x=200, y=200, taille=30, couleur=NOIR)
        texte.contenu = "Après"
        
        self.verifier_egal(texte.contenu, "Après")
        texte.dessiner()


if __name__ == "__main__":
    from adndpg._testeur import lancer_tests
    lancer_tests(TestsTexte)
