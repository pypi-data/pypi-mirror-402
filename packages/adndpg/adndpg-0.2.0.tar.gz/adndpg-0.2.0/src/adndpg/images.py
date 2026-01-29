from __future__ import annotations
import pyray as raylib
from adndpg.couleurs import BLANC


class Image:
    def __init__(self, chemin: str, x: float = 0, y: float = 0):
        self._texture = raylib.load_texture(chemin)
        self.x = x
        self.y = y
        self.echelle = 1.0
        self.rotation = 0.0
        self.visible = True
        self._chemin = chemin
    
    @property
    def largeur(self) -> int:
        return int(self._texture.width * self.echelle)
    
    @property
    def hauteur(self) -> int:
        return int(self._texture.height * self.echelle)
    
    def dessiner(self) -> None:
        if not self.visible:
            return
        
        if self.rotation == 0 and self.echelle == 1.0:
            raylib.draw_texture(self._texture, int(self.x), int(self.y), BLANC)
        else:
            raylib.draw_texture_ex(
                self._texture,
                raylib.Vector2(self.x, self.y),
                self.rotation,
                self.echelle,
                BLANC
            )
    
    def deplacer(self, dx: float, dy: float) -> None:
        self.x += dx
        self.y += dy
    
    def aller_a(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
    
    def redimensionner(self, echelle: float) -> None:
        self.echelle = echelle

    def orienter(self, degres: float) -> None:
        self.rotation = degres

    def _obtenir_rect(self) -> raylib.Rectangle:
        return raylib.Rectangle(self.x, self.y, self.largeur, self.hauteur)

    def est_survole(self) -> bool:
        pos = raylib.get_mouse_position()
        return raylib.check_collision_point_rec(pos, self._obtenir_rect())

    def est_clique(self) -> bool:
        return self.est_survole() and raylib.is_mouse_button_pressed(raylib.MOUSE_BUTTON_LEFT)

    def touche(self, autre) -> bool:
        return raylib.check_collision_recs(self._obtenir_rect(), autre._obtenir_rect())

    def __del__(self):
        try:
            if hasattr(self, '_texture'):
                raylib.unload_texture(self._texture)
        except:
            pass
