import pyray as raylib
import os
import sys
import traceback
import time
from adndpg.couleurs import Couleur, BLANC

_fenetre_ouverte = False
_largeur_init = 800
_hauteur_init = 600

# Variables pour la police
_police_defaut = None
_caracteres_presents = set(range(32, 255)) # ASCII + Latin-1 par défaut
_mtime_initiale = 0.0
_fichier_cible = None
_hot_reload_active = False
_chemin_police_personnalisee = None


def _obtenir_police_defaut():
    """Retourne la police par défaut du module (Interne)."""
    global _police_defaut
    return _police_defaut


def _afficher_ecran_erreur(titre_err: str, details: str) -> None:
    """Affiche un écran rouge avec l'erreur et attend une modification du fichier."""
    global _mtime_initiale
    
    # On s'assure que la fenêtre est prête
    if not raylib.is_window_ready():
        try:
            raylib.init_window(_largeur_init, _hauteur_init, "ERREUR - adndpg")
        except:
            return

    while True:
        try:
            # Vérifier si le fichier a été corrigé
            if os.path.exists(_fichier_cible) and os.path.getmtime(_fichier_cible) > _mtime_initiale:
                # Tenter une compilation silencieuse pour voir si c'est réparé
                with open(_fichier_cible, 'r', encoding='utf-8') as f:
                    try:
                        compile(f.read(), _fichier_cible, 'exec')
                        # Si ça compile, on relance !
                        _relancer_processus()
                    except:
                        # Toujours une erreur de syntaxe, on rafraîchit l'affichage
                        _mtime_initiale = os.path.getmtime(_fichier_cible)
        except:
            pass

        raylib.begin_drawing()
        raylib.clear_background(raylib.Color(120, 20, 20, 255))
        
        # Titre
        _assurer_caracteres(titre_err)
        _assurer_caracteres("Corrige ton code et sauvegarde pour relancer automatiquement.")
        police = _obtenir_police_defaut()
        if police:
            raylib.draw_text_ex(police, titre_err, raylib.Vector2(30, 40), 30, 1, raylib.WHITE)
            raylib.draw_text_ex(police, "Corrige ton code et sauvegarde pour relancer automatiquement.", raylib.Vector2(30, 85), 18, 1, raylib.LIGHTGRAY)
        else:
            raylib.draw_text(titre_err, 30, 40, 30, raylib.WHITE)
            raylib.draw_text("Corrige ton code et sauvegarde pour relancer automatiquement.", 30, 85, 18, raylib.LIGHTGRAY)
        
        # Affichage du traceback/détails
        y = 130
        for line in details.split('\n')[-20:]: # 20 dernières lignes
            if not line.strip(): continue
            _assurer_caracteres(line[:100])
            police = _obtenir_police_defaut() # Refresh police in case it changed
            if police:
                raylib.draw_text_ex(police, line[:100], raylib.Vector2(30, y), 14, 1, raylib.Color(255, 255, 255, 200))
            else:
                raylib.draw_text(line[:100], 30, y, 14, raylib.Color(255, 255, 255, 200))
            y += 20
            if y > 550: break
            
        raylib.end_drawing()
        
        if raylib.window_should_close():
            raylib.close_window()
            sys.exit(0)
            
        time.sleep(0.1)


def _relancer_processus() -> None:
    """Sauvegarde l'état de la fenêtre et relance le script."""
    global _fenetre_ouverte
    try:
        if _fenetre_ouverte:
            pos = raylib.get_window_position()
            os.environ["ADNDPG_WINDOW_X"] = str(int(pos.x))
            os.environ["ADNDPG_WINDOW_Y"] = str(int(pos.y))
            os.environ["ADNDPG_WINDOW_W"] = str(raylib.get_screen_width())
            os.environ["ADNDPG_WINDOW_H"] = str(raylib.get_screen_height())
            
            fermer_fenetre()
    except:
        pass
    
    os.execv(sys.executable, [sys.executable] + sys.argv)
    sys.exit(0)


def _moniteur_exceptions(etype, value, tb) -> None:
    """Capture les crashs pour éviter de fermer le watcher."""
    if not _hot_reload_active:
        sys.__excepthook__(etype, value, tb)
        return

    err_details = "".join(traceback.format_exception(etype, value, tb))
    print(err_details, file=sys.stderr)
    _afficher_ecran_erreur("CRASH DURANT L'EXECUTION", err_details)


def _activer_hot_reload() -> None:
    """Active le rechargement automatique si le fichier principal change."""
    global _hot_reload_active, _mtime_initiale, _fichier_cible
    import __main__
    if hasattr(__main__, "__file__"):
        _fichier_cible = os.path.abspath(__main__.__file__)
        try:
            _mtime_initiale = os.path.getmtime(_fichier_cible)
            _hot_reload_active = True
            # Installer le hook d'exception
            sys.excepthook = _moniteur_exceptions
        except OSError:
            pass


_nouveaux_caracteres_a_charger = set()

def _assurer_caracteres(texte: str) -> None:
    """Marque les nouveaux caractères pour chargement au prochain cycle (Interne)."""
    global _caracteres_presents, _nouveaux_caracteres_a_charger
    if not texte:
        return
    
    for char in texte:
        cp = ord(char)
        if cp > 0 and cp not in _caracteres_presents:
            _nouveaux_caracteres_a_charger.add(cp)


def _recharger_si_besoin() -> None:
    """Recharge la police si de nouveaux caractères ont été détectés (Interne)."""
    global _nouveaux_caracteres_a_charger, _caracteres_presents, _fenetre_ouverte
    if _nouveaux_caracteres_a_charger:
        _caracteres_presents.update(_nouveaux_caracteres_a_charger)
        _nouveaux_caracteres_a_charger.clear()
        if _fenetre_ouverte:
            _charger_ressources_module()


def _charger_ressources_module():
    """Charge les ressources internes du module (Police, etc.)."""
    global _police_defaut, _caracteres_presents, _chemin_police_personnalisee
    
    # On cherche d'abord la police pan-unicode téléchargée
    chemins_possibles = []
    if _chemin_police_personnalisee:
        chemins_possibles.append(_chemin_police_personnalisee)
    
    # 1. Noto Sans SC (Fichier riche téléchargé)
    chemins_possibles.append(os.path.join(os.path.dirname(__file__), "fonts", "NotoSansSC-Regular.otf"))
    # 2. Noto Sans Medium (Fichier de base léger)
    chemins_possibles.append(os.path.join(os.path.dirname(__file__), "fonts", "NotoSans-Medium.ttf"))
    
    chemin_final = None
    for p in chemins_possibles:
        if os.path.exists(p):
            chemin_final = p
            break

    if chemin_final:
        if _police_defaut:
            raylib.unload_font(_police_defaut)
        
        cps = sorted(list(_caracteres_presents))
        try:
            # On s'assure que le point de code 0xFFFD (replacement character) est présent
            # pour éviter les '?' si un glyphe manque vraiment.
            if 0xFFFD not in _caracteres_presents:
                cps.append(0xFFFD)
                cps.sort()

            cps_ptr = raylib.ffi.new(f"int[{len(cps)}]", cps)
            cps_ptr_casted = raylib.ffi.cast("int *", cps_ptr)
            
            # Taille 48px pour un bon équilibre entre netteté et performance atlas
            _police_defaut = raylib.load_font_ex(chemin_final, 48, cps_ptr_casted, len(cps))
            raylib.set_texture_filter(_police_defaut.texture, raylib.TextureFilter.TEXTURE_FILTER_BILINEAR)
        except Exception as e:
            print(f"Avertissement: Échec du chargement de {chemin_final}: {e}")
            _police_defaut = raylib.get_font_default()


def ouvrir_fenetre(titre: str = "Mon Application @DN") -> None:
    global _fenetre_ouverte, _police_defaut
    
    # Configuration de l'anti-aliasing global (doit être fait AVANT init_window)
    raylib.set_config_flags(
        raylib.ConfigFlags.FLAG_MSAA_4X_HINT | 
        raylib.ConfigFlags.FLAG_VSYNC_HINT |
        raylib.ConfigFlags.FLAG_WINDOW_HIGHDPI
    )

    # Récupérer les anciennes propriétés si on vient d'un hot reload
    x = os.environ.get("ADNDPG_WINDOW_X")
    y = os.environ.get("ADNDPG_WINDOW_Y")
    w = os.environ.get("ADNDPG_WINDOW_W")
    h = os.environ.get("ADNDPG_WINDOW_H")

    largeur = int(w) if w else _largeur_init
    hauteur = int(h) if h else _hauteur_init

    raylib.init_window(largeur, hauteur, titre)
    
    # Charger la police Noto Sans par défaut
    _charger_ressources_module()
    
    if x and y:
        raylib.set_window_position(int(x), int(y))
        
    raylib.set_target_fps(60)
    _fenetre_ouverte = True
    
    # Hot reload activé par défaut
    if not _hot_reload_active:
        _activer_hot_reload()


def fermer_fenetre() -> None:
    global _fenetre_ouverte, _police_defaut
    if _fenetre_ouverte:
        if raylib.is_audio_device_ready():
            raylib.close_audio_device()
        
        if _police_defaut:
            raylib.unload_font(_police_defaut)
            _police_defaut = None
            
        raylib.close_window()
        _fenetre_ouverte = False


def fenetre_est_ouverte() -> bool:
    global _fenetre_ouverte, _mtime_initiale
    
    if not _fenetre_ouverte:
        return False
    
    # Vérification du Hot Reload
    if _hot_reload_active and _fichier_cible:
        try:
            mtime_actuelle = os.path.getmtime(_fichier_cible)
            if mtime_actuelle > _mtime_initiale:
                # 1. Vérifier la syntaxe avant de tenter quoi que ce soit
                try:
                    with open(_fichier_cible, 'r', encoding='utf-8') as f:
                        compile(f.read(), _fichier_cible, 'exec')
                except Exception as e:
                    # Erreur de syntaxe détectée ! On passe en mode erreur
                    _mtime_initiale = mtime_actuelle
                    _afficher_ecran_erreur("ERREUR DE SYNTAXE", str(e))
                
                # 2. Si on arrive ici, la syntaxe est OK, on relance
                _relancer_processus()
        except OSError:
            pass
            
    if raylib.is_window_ready():
        try:
            raylib.end_drawing()
        except:
            pass
    
    if raylib.window_should_close():
        return False
    
    # On recharge la police AVANT begin_drawing si nécessaire
    _recharger_si_besoin()
    
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
