from __future__ import annotations
import pyray as raylib
import math
from adndpg.couleurs import Couleur, BLANC

class _Forme:
    def __init__(self, x: float, y: float, couleur: Couleur):
        self.x = x
        self.y = y
        self.couleur = couleur
        self.visible = True
        self.rotation = 0.0
        self.echelle = 1.0

    def dessiner(self) -> None:
        pass

    def deplacer(self, dx: float, dy: float) -> None:
        self.x += dx
        self.y += dy

    def aller_a(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def redimensionner(self, *args) -> None:
        pass

    def orienter(self, degres: float) -> None:
        self.rotation = degres

    def _obtenir_rect(self) -> raylib.Rectangle:
        return raylib.Rectangle(self.x, self.y, 0, 0)

    def est_survole(self) -> bool:
        pos = raylib.get_mouse_position()
        return raylib.check_collision_point_rec(pos, self._obtenir_rect())

    def est_clique(self) -> bool:
        return self.est_survole() and raylib.is_mouse_button_pressed(raylib.MOUSE_BUTTON_LEFT)

    def touche(self, autre: _Forme) -> bool:
        if isinstance(autre, Cercle):
            return autre.touche(self)
        return raylib.check_collision_recs(self._obtenir_rect(), autre._obtenir_rect())


class Carre(_Forme):
    def __init__(self, x: float, y: float, taille: float = 50, couleur: Couleur = BLANC):
        super().__init__(x, y, couleur)
        self.taille = taille

    def dessiner(self) -> None:
        if not self.visible:
            return
        if self.rotation == 0:
            raylib.draw_rectangle(
                int(self.x), int(self.y),
                int(self.taille), int(self.taille),
                self.couleur
            )
        else:
            rec = raylib.Rectangle(self.x, self.y, self.taille, self.taille)
            origin = raylib.Vector2(0, 0)
            raylib.draw_rectangle_pro(rec, origin, self.rotation, self.couleur)

    def _obtenir_rect(self) -> raylib.Rectangle:
        if self.rotation == 0:
            return raylib.Rectangle(self.x, self.y, self.taille, self.taille)
        pts = self._obtenir_coins_abs()
        min_x = min(p.x for p in pts)
        max_x = max(p.x for p in pts)
        min_y = min(p.y for p in pts)
        max_y = max(p.y for p in pts)
        return raylib.Rectangle(min_x, min_y, max_x - min_x, max_y - min_y)

    def _obtenir_coins_abs(self) -> list[raylib.Vector2]:
        angle_rad = self.rotation * math.pi / 180
        pts_rel = [
            raylib.Vector2(0, 0),
            raylib.Vector2(self.taille, 0),
            raylib.Vector2(self.taille, self.taille),
            raylib.Vector2(0, self.taille)
        ]
        return [raylib.Vector2(self.x + raylib.vector2_rotate(p, angle_rad).x,
                               self.y + raylib.vector2_rotate(p, angle_rad).y) for p in pts_rel]

    def est_survole(self) -> bool:
        if self.rotation == 0:
            return super().est_survole()
        pos = raylib.get_mouse_position()
        pts = self._obtenir_coins_abs()
        return raylib.check_collision_point_poly(pos, pts, 4)

    def redimensionner(self, taille: float) -> None:
        self.taille = taille


class Rectangle(_Forme):
    def __init__(self, x: float, y: float, largeur: float = 100,
                 hauteur: float = 50, couleur: Couleur = BLANC):
        super().__init__(x, y, couleur)
        self.largeur = largeur
        self.hauteur = hauteur

    def dessiner(self) -> None:
        if not self.visible:
            return
        if self.rotation == 0:
            raylib.draw_rectangle(
                int(self.x), int(self.y),
                int(self.largeur), int(self.hauteur),
                self.couleur
            )
        else:
            rec = raylib.Rectangle(self.x, self.y, self.largeur, self.hauteur)
            origin = raylib.Vector2(0, 0)
            raylib.draw_rectangle_pro(rec, origin, self.rotation, self.couleur)

    def _obtenir_rect(self) -> raylib.Rectangle:
        if self.rotation == 0:
            return raylib.Rectangle(self.x, self.y, self.largeur, self.hauteur)
        pts = self._obtenir_coins_abs()
        min_x = min(p.x for p in pts)
        max_x = max(p.x for p in pts)
        min_y = min(p.y for p in pts)
        max_y = max(p.y for p in pts)
        return raylib.Rectangle(min_x, min_y, max_x - min_x, max_y - min_y)

    def _obtenir_coins_abs(self) -> list[raylib.Vector2]:
        angle_rad = self.rotation * math.pi / 180
        pts_rel = [
            raylib.Vector2(0, 0),
            raylib.Vector2(self.largeur, 0),
            raylib.Vector2(self.largeur, self.hauteur),
            raylib.Vector2(0, self.hauteur)
        ]
        return [raylib.Vector2(self.x + raylib.vector2_rotate(p, angle_rad).x,
                               self.y + raylib.vector2_rotate(p, angle_rad).y) for p in pts_rel]

    def est_survole(self) -> bool:
        if self.rotation == 0:
            return super().est_survole()
        pos = raylib.get_mouse_position()
        pts = self._obtenir_coins_abs()
        return raylib.check_collision_point_poly(pos, pts, 4)

    def redimensionner(self, largeur: float, hauteur: float) -> None:
        self.largeur = largeur
        self.hauteur = hauteur


class Cercle(_Forme):
    def __init__(self, x: float, y: float, rayon: float = 25, couleur: Couleur = BLANC):
        super().__init__(x, y, couleur)
        self.rayon = rayon

    def dessiner(self) -> None:
        if not self.visible:
            return
        raylib.draw_circle(int(self.x), int(self.y), self.rayon, self.couleur)

    def _obtenir_rect(self) -> raylib.Rectangle:
        return raylib.Rectangle(
            self.x - self.rayon,
            self.y - self.rayon,
            self.rayon * 2,
            self.rayon * 2
        )

    def est_survole(self) -> bool:
        pos = raylib.get_mouse_position()
        return raylib.check_collision_point_circle(pos, raylib.Vector2(self.x, self.y), self.rayon)

    def redimensionner(self, rayon: float) -> None:
        self.rayon = rayon

    def touche(self, autre: _Forme) -> bool:
        if isinstance(autre, Cercle):
            return raylib.check_collision_circles(
                raylib.Vector2(self.x, self.y), self.rayon,
                raylib.Vector2(autre.x, autre.y), autre.rayon
            )
        if isinstance(autre, (Carre, Rectangle)):
            return raylib.check_collision_circle_rec(
                raylib.Vector2(self.x, self.y), self.rayon,
                autre._obtenir_rect()
            )
        if isinstance(autre, Ligne):
             pts = autre._obtenir_pts_abs()
             return raylib.check_collision_circle_line(
                raylib.Vector2(self.x, self.y), self.rayon,
                pts[0], pts[1]
            )
        return super().touche(autre)


class Triangle(_Forme):
    def __init__(self, x1: float, y1: float, x2: float, y2: float,
                 x3: float, y3: float, couleur: Couleur = BLANC):
        cx = (x1 + x2 + x3) / 3
        cy = (y1 + y2 + y3) / 3
        super().__init__(cx, cy, couleur)
        self._pts_base = [
            raylib.Vector2(x1 - cx, y1 - cy),
            raylib.Vector2(x2 - cx, y2 - cy),
            raylib.Vector2(x3 - cx, y3 - cy)
        ]

    def _obtenir_pts_abs(self) -> list[raylib.Vector2]:
        angle_rad = self.rotation * math.pi / 180
        pts = []
        for p in self._pts_base:
            ps = raylib.Vector2(p.x * self.echelle, p.y * self.echelle)
            pr = raylib.vector2_rotate(ps, angle_rad)
            pts.append(raylib.Vector2(self.x + pr.x, self.y + pr.y))
        return pts

    def dessiner(self) -> None:
        if not self.visible:
            return
        pts = self._obtenir_pts_abs()
        raylib.draw_triangle(pts[0], pts[1], pts[2], self.couleur)

    def _obtenir_rect(self) -> raylib.Rectangle:
        pts = self._obtenir_pts_abs()
        min_x = min(p.x for p in pts)
        max_x = max(p.x for p in pts)
        min_y = min(p.y for p in pts)
        max_y = max(p.y for p in pts)
        return raylib.Rectangle(min_x, min_y, max_x - min_x, max_y - min_y)

    def est_survole(self) -> bool:
        pos = raylib.get_mouse_position()
        pts = self._obtenir_pts_abs()
        return raylib.check_collision_point_triangle(pos, pts[0], pts[1], pts[2])

    def redimensionner(self, facteur: float) -> None:
        self.echelle = facteur


class Ligne(_Forme):
    def __init__(self, x1: float, y1: float, x2: float, y2: float,
                 couleur: Couleur = BLANC, epaisseur: float = 1):
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        super().__init__(cx, cy, couleur)
        self._pts_base = [
            raylib.Vector2(x1 - cx, y1 - cy),
            raylib.Vector2(x2 - cx, y2 - cy)
        ]
        self.epaisseur = epaisseur

    def _obtenir_pts_abs(self) -> list[raylib.Vector2]:
        angle_rad = self.rotation * math.pi / 180
        pts = []
        for p in self._pts_base:
            ps = raylib.Vector2(p.x * self.echelle, p.y * self.echelle)
            pr = raylib.vector2_rotate(ps, angle_rad)
            pts.append(raylib.Vector2(self.x + pr.x, self.y + pr.y))
        return pts

    def dessiner(self) -> None:
        if not self.visible:
            return
        pts = self._obtenir_pts_abs()
        raylib.draw_line_ex(pts[0], pts[1], self.epaisseur * self.echelle, self.couleur)

    def _obtenir_rect(self) -> raylib.Rectangle:
        pts = self._obtenir_pts_abs()
        min_x = min(pts[0].x, pts[1].x)
        max_x = max(pts[0].x, pts[1].x)
        min_y = min(pts[0].y, pts[1].y)
        max_y = max(pts[0].y, pts[1].y)
        return raylib.Rectangle(min_x, min_y, max(1, max_x - min_x), max(1, max_y - min_y))

    def est_survole(self) -> bool:
        pos = raylib.get_mouse_position()
        pts = self._obtenir_pts_abs()
        return raylib.check_collision_point_line(
            pos, pts[0], pts[1], int(self.epaisseur * self.echelle)
        )

    def redimensionner(self, facteur: float) -> None:
        self.echelle = facteur

    def touche(self, autre: _Forme) -> bool:
        if isinstance(autre, Ligne):
            pts1 = self._obtenir_pts_abs()
            pts2 = autre._obtenir_pts_abs()
            return raylib.check_collision_lines(
                pts1[0], pts1[1], pts2[0], pts2[1], None
            )
        return super().touche(autre)

    @property
    def x1(self): pts = self._obtenir_pts_abs(); return pts[0].x
    @property
    def y1(self): pts = self._obtenir_pts_abs(); return pts[0].y
    @property
    def x2(self): pts = self._obtenir_pts_abs(); return pts[1].x
    @property
    def y2(self): pts = self._obtenir_pts_abs(); return pts[1].y
