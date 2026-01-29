import pyray as raylib
from adndpg.couleurs import Couleur, NOIR


class Texte:
    def __init__(self, contenu: str, x: float, y: float, 
                 taille: int = 20, couleur: Couleur = NOIR):
        self.contenu = contenu
        self.x = x
        self.y = y
        self.taille = taille
        self.couleur = couleur
        self.visible = True
    
    def dessiner(self) -> None:
        if not self.visible:
            return
        raylib.draw_text(
            self.contenu,
            int(self.x), int(self.y),
            self.taille,
            self.couleur
        )
    
    def deplacer(self, dx: float, dy: float) -> None:
        self.x += dx
        self.y += dy
    
    def aller_a(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
    
    @property
    def largeur(self) -> int:
        return raylib.measure_text(self.contenu, self.taille)
