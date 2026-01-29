import os
import time
from adndpg._testeur import TesteurVisuel, test
from adndpg.sons import Son, Musique
from adndpg.texte import Texte
from adndpg.couleurs import NOIR

# Chemin vers le son de test
ASSET_DIR = os.path.join(os.path.dirname(__file__), 'assets')
SOUND_PATH = os.path.join(ASSET_DIR, 'test_sound.wav')


class TestsSons(TesteurVisuel):

    
    @test("Charger et jouer un son")
    def test_son_lecture(self):
        if not os.path.exists(SOUND_PATH):
            print(f"ATTENTION: Son de test non trouvé: {SOUND_PATH}")
            return
            
        son = Son(chemin=SOUND_PATH)
        son.jouer()
        
        # On ne peut pas facilement vérifier l'audio programmatiquement,
        # mais on vérifie au moins que pas d'erreur n'est levée.
        
        texte = Texte("Un son devrait être joué!", 50, 100, 24, NOIR)
        texte.dessiner()
    
    @test("Modifier le volume")
    def test_son_volume(self):
        if not os.path.exists(SOUND_PATH): return
        
        son = Son(chemin=SOUND_PATH)
        son.changer_volume(0.5)  # 50%
        # son.jouer() # Optionnel pour pas spammer
        
        texte = Texte("Volume modifié testé", 50, 150, 24, NOIR)
        texte.dessiner()
    
    @test("Musique (streaming)")
    def test_musique(self):
        if not os.path.exists(SOUND_PATH): return
        
        # On utilise le même fichier wav comme "musique" pour le test
        musique = Musique(chemin=SOUND_PATH)
        musique.jouer()
        musique.changer_volume(0.2)
        
        # Vérification d'état
        en_lecture = musique.est_en_lecture()
        self.verifier_vrai(en_lecture, "La musique devrait être marquée comme en lecture")
        
        texte = Texte(f"Musique en lecture: {en_lecture}", 50, 200, 24, NOIR)
        texte.dessiner()
        
        # Nettoyage
        musique.arreter()


if __name__ == "__main__":
    from adndpg._testeur import lancer_tests
    lancer_tests(TestsSons)
