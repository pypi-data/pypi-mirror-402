from typing import Tuple
import pyray as raylib


CLIQUE_GAUCHE = raylib.MOUSE_BUTTON_LEFT
CLIQUE_DROITE = raylib.MOUSE_BUTTON_RIGHT
CLIQUE_MILIEU = raylib.MOUSE_BUTTON_MIDDLE


def position_souris() -> Tuple[int, int]:
    pos = raylib.get_mouse_position()
    return (int(pos.x), int(pos.y))


def clic(bouton: int = CLIQUE_GAUCHE) -> bool:
    return raylib.is_mouse_button_pressed(bouton)


def bouton_enfonce(bouton: int = CLIQUE_GAUCHE) -> bool:
    return raylib.is_mouse_button_down(bouton)


def bouton_relache(bouton: int = CLIQUE_GAUCHE) -> bool:
    return raylib.is_mouse_button_released(bouton)


def molette() -> float:
    return raylib.get_mouse_wheel_move()
