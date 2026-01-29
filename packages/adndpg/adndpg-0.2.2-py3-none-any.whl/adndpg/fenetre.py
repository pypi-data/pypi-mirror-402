import pyray as raylib
from adndpg.couleurs import Couleur, BLANC

_fenetre_ouverte = False
_largeur_defaut = 800
_hauteur_defaut = 600


def ouvrir_fenetre(titre: str = "Mon Application @DN") -> None:
    global _fenetre_ouverte
    raylib.init_window(_largeur_defaut, _hauteur_defaut, titre)
    raylib.set_target_fps(60)
    raylib.set_config_flags(raylib.ConfigFlags.FLAG_VSYNC_HINT)
    _fenetre_ouverte = True


def fermer_fenetre() -> None:
    global _fenetre_ouverte
    raylib.close_window()
    _fenetre_ouverte = False


def fenetre_est_ouverte() -> bool:
    global _fenetre_ouverte
    
    if not _fenetre_ouverte:
        return False
    
    if raylib.is_window_ready():
        try:
            raylib.end_drawing()
        except:
            pass
    
    if raylib.window_should_close():
        return False
    
    raylib.begin_drawing()
    return True


def effacer_ecran(couleur: Couleur = BLANC) -> None:
    raylib.clear_background(couleur)


def redimensionner_fenetre(largeur: int, hauteur: int) -> None:
    raylib.set_window_size(largeur, hauteur)


def definir_images_par_seconde(fps: int) -> None:
    raylib.set_target_fps(fps)


def obtenir_temps() -> float:
    return raylib.get_time()


def obtenir_delta() -> float:
    return raylib.get_frame_time()


def obtenir_largeur_fenetre() -> int:
    return raylib.get_screen_width()


def obtenir_hauteur_fenetre() -> int:
    return raylib.get_screen_height()
