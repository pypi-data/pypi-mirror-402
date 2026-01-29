import pyray as raylib


HAUT = raylib.KEY_UP
BAS = raylib.KEY_DOWN
GAUCHE = raylib.KEY_LEFT
DROITE = raylib.KEY_RIGHT

ESPACE = raylib.KEY_SPACE
ENTREE = raylib.KEY_ENTER
ECHAP = raylib.KEY_ESCAPE
RETOUR = raylib.KEY_BACKSPACE
TAB = raylib.KEY_TAB
A = raylib.KEY_A
B = raylib.KEY_B
C = raylib.KEY_C
D = raylib.KEY_D
E = raylib.KEY_E
F = raylib.KEY_F
G = raylib.KEY_G
H = raylib.KEY_H
I = raylib.KEY_I
J = raylib.KEY_J
K = raylib.KEY_K
L = raylib.KEY_L
M = raylib.KEY_M
N = raylib.KEY_N
O = raylib.KEY_O
P = raylib.KEY_P
Q = raylib.KEY_Q
R = raylib.KEY_R
S = raylib.KEY_S
T = raylib.KEY_T
U = raylib.KEY_U
V = raylib.KEY_V
W = raylib.KEY_W
X = raylib.KEY_X
Y = raylib.KEY_Y
Z = raylib.KEY_Z

CHIFFRE_0 = raylib.KEY_ZERO
CHIFFRE_1 = raylib.KEY_ONE
CHIFFRE_2 = raylib.KEY_TWO
CHIFFRE_3 = raylib.KEY_THREE
CHIFFRE_4 = raylib.KEY_FOUR
CHIFFRE_5 = raylib.KEY_FIVE
CHIFFRE_6 = raylib.KEY_SIX
CHIFFRE_7 = raylib.KEY_SEVEN
CHIFFRE_8 = raylib.KEY_EIGHT
CHIFFRE_9 = raylib.KEY_NINE


def touche_appuyee(touche: int) -> bool:
    return raylib.is_key_pressed(touche)


def touche_enfoncee(touche: int) -> bool:
    return raylib.is_key_down(touche)


def touche_relachee(touche: int) -> bool:
    return raylib.is_key_released(touche)
