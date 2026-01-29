import random
import pyray as raylib


Couleur = raylib.Color


ROUGE = raylib.RED
BLEU = raylib.BLUE
VERT = raylib.GREEN
JAUNE = raylib.YELLOW
ORANGE = raylib.ORANGE
VIOLET = raylib.VIOLET
ROSE = raylib.PINK
NOIR = raylib.BLACK
BLANC = raylib.WHITE
GRIS = raylib.GRAY
MARRON = raylib.BROWN
CYAN = raylib.SKYBLUE
TRANSPARENT = raylib.Color(0, 0, 0, 0)

CYAN = raylib.Color(0, 255, 255, 255)


_COULEURS = [ROUGE, BLEU, VERT, JAUNE, ORANGE, VIOLET, ROSE, CYAN, MARRON]


def couleur_aleatoire() -> Couleur:
    return random.choice(_COULEURS)
