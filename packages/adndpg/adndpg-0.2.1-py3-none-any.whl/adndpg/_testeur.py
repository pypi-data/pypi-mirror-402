from __future__ import annotations
import traceback
from typing import Callable, List, Optional, Any, Tuple
from dataclasses import dataclass
import pyray as raylib
import os

from adndpg.couleurs import BLANC, NOIR, ROUGE, VERT, JAUNE, GRIS, ORANGE


@dataclass
class _ResultatTest:
    nom: str
    classe: str
    reussi: bool
    erreur: Optional[str] = None


def test(nom: str):
    def decorateur(func):
        func._est_test = True
        func._nom_test = nom
        return func
    return decorateur


class EchecTest(Exception):
    pass


class TesteurVisuel:
    def __init__(self):
        self._resultats: List[_ResultatTest] = []
        self._test_courant: Optional[str] = None
        self._classe_courante: Optional[str] = None
        self._message_erreur = ""
    
    def verifier_egal(self, valeur: Any, attendu: Any, message: str = "") -> None:
        if valeur != attendu:
            msg = message or f"Attendu {attendu}, obtenu {valeur}"
            raise EchecTest(msg)
    
    def verifier_vrai(self, condition: bool, message: str = "") -> None:
        if not condition:
            raise EchecTest(message or "La condition devrait être vraie")
    
    def verifier_faux(self, condition: bool, message: str = "") -> None:
        if condition:
            raise EchecTest(message or "La condition devrait être fausse")
    
    def verifier_erreur(self, exception_type: type, fonction: Callable) -> None:
        try:
            fonction()
            raise EchecTest(f"Devrait lever {exception_type.__name__}")
        except exception_type:
            pass
    
    def _collecter_tests(self) -> List[Callable]:
        tests = []
        for nom in dir(self):
            if nom.startswith('_'):
                continue
            methode = getattr(self, nom)
            if callable(methode) and hasattr(methode, '_est_test'):
                tests.append(methode)
        return tests


def _afficher_entete(classe: str, test_nom: str, index: int, total: int) -> None:
    raylib.draw_rectangle(0, 0, 800, 50, GRIS)
    raylib.draw_text(f"[{index + 1}/{total}] {classe}", 10, 5, 18, ORANGE)
    raylib.draw_text(f"Test: {test_nom}", 10, 27, 18, BLANC)


def _afficher_barre_progression(index: int, total: int) -> None:
    largeur = int((index + 1) / total * 800)
    raylib.draw_rectangle(0, 592, 800, 8, GRIS)
    raylib.draw_rectangle(0, 592, largeur, 8, VERT)


def _afficher_erreur(classe: str, test_nom: str, message: str) -> None:
    raylib.draw_rectangle(0, 0, 800, 600, raylib.Color(0, 0, 0, 200))
    raylib.draw_text("ECHEC DU TEST", 280, 80, 36, ROUGE)
    raylib.draw_text(f"Classe: {classe}", 50, 150, 22, ORANGE)
    raylib.draw_text(f"Test: {test_nom}", 50, 180, 22, JAUNE)
    
    lignes = message.split('\n')
    y = 230
    for ligne in lignes[:12]:
        raylib.draw_text(ligne[:90], 50, y, 16, BLANC)
        y += 22
    
    raylib.draw_text("ESPACE = continuer  |  ECHAP = quitter", 180, 540, 20, GRIS)


def _afficher_resume(resultats: List[_ResultatTest], passes: int, echecs: int, logo_texture=None) -> None:
    raylib.draw_rectangle(0, 0, 800, 600, NOIR)
    
    y = 50
    
    if logo_texture and logo_texture.id > 0:
        scale = 1.0
        target_height = 80
        if logo_texture.height > target_height:
            scale = target_height / logo_texture.height
        
        raylib.draw_texture_ex(logo_texture, raylib.Vector2(50, y), 0.0, scale, BLANC)
        y += int(logo_texture.height * scale) + 20
    
    titre = "TOUS LES TESTS PASSES!" if echecs == 0 else "TESTS TERMINES"
    couleur = VERT if echecs == 0 else JAUNE
    raylib.draw_text(titre, 50, y, 36, couleur)
    y += 50
    
    raylib.draw_text(f"Tests reussis: {passes}", 50, y, 28, VERT)
    y += 35
    raylib.draw_text(f"Tests echoues: {echecs}", 50, y, 28, 
                (ROUGE if echecs > 0 else GRIS))
    
    y += 50
    raylib.draw_text("Details:", 50, y, 20, BLANC)
    y += 35
    
    base_y_details = y
    for resultat in resultats:
        if y > 530:
            raylib.draw_text("...", 50, y, 18, GRIS)
            break
        
        if resultat.reussi:
            raylib.draw_text(f"  OK  {resultat.classe}.{resultat.nom}", 50, y, 16, VERT)
        else:
            raylib.draw_text(f"  X   {resultat.classe}.{resultat.nom}", 50, y, 16, ROUGE)
        y += 22
    
    raylib.draw_text("ECHAP = quitter", 600, 560, 18, GRIS)


def lancer_tests(*classes_test: type) -> bool:
    tous_tests: List[Tuple[str, TesteurVisuel, Callable]] = []
    
    for classe in classes_test:
        testeur = classe()
        tests = testeur._collecter_tests()
        for test_func in tests:
            tous_tests.append((classe.__name__, testeur, test_func))
    
    if not tous_tests:
        print("Aucun test trouvé!")
        return True
    
    raylib.init_window(800, 600, "Tests Visuels adndpg")
    raylib.set_target_fps(60)
    
    logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'tests', 'assets', 'cropped-logo-adnpg.png'))
    logo_texture = None
    if os.path.exists(logo_path):
        try:
            logo_texture = raylib.load_texture(logo_path)
        except:
            pass
    
    resultats: List[_ResultatTest] = []
    passes = 0
    echecs = 0
    index_test = 0
    phase = "tests"
    
    classe_courante = ""
    test_courant = ""
    message_erreur = ""
    
    while not raylib.window_should_close():
        raylib.begin_drawing()
        raylib.clear_background(BLANC)
        
        if phase in ("tests", "pause"):
            if index_test < len(tous_tests):
                classe_nom, testeur, test_func = tous_tests[index_test]
                classe_courante = classe_nom
                test_courant = getattr(test_func, "_nom_test", test_func.__name__)

                _afficher_entete(classe_courante, test_courant, index_test, len(tous_tests))
                _afficher_barre_progression(index_test, len(tous_tests))

                try:
                    test_func()
                    if phase == "tests":
                        resultats.append(_ResultatTest(
                            nom=test_courant,
                            classe=classe_courante,
                            reussi=True
                        ))
                        passes += 1
                        index_test += 1
                except EchecTest as e:
                    if phase == "tests":
                        message_erreur = str(e)
                        resultats.append(_ResultatTest(
                            nom=test_courant,
                            classe=classe_courante,
                            reussi=False,
                            erreur=message_erreur
                        ))
                        echecs += 1
                        phase = "pause"
                except Exception as e:
                    if phase == "tests":
                        message_erreur = f"{type(e).__name__}: {e}\n\n{traceback.format_exc()}"
                        resultats.append(_ResultatTest(
                            nom=test_courant,
                            classe=classe_courante,
                            reussi=False,
                            erreur=message_erreur
                        ))
                        echecs += 1
                        phase = "pause"

                if phase == "pause":
                    _afficher_erreur(classe_courante, test_courant, message_erreur)
                    if raylib.is_key_pressed(raylib.KEY_SPACE):
                        index_test += 1
                        phase = "tests"
                    elif raylib.is_key_pressed(raylib.KEY_ESCAPE):
                        break
            else:
                phase = "resume"

        if phase == "resume":
            _afficher_resume(resultats, passes, echecs, logo_texture)
            if raylib.is_key_pressed(raylib.KEY_ESCAPE) or raylib.is_key_pressed(raylib.KEY_SPACE):
                break
        
        raylib.end_drawing()
    
    if logo_texture and logo_texture.id > 0:
        raylib.unload_texture(logo_texture)
        
    raylib.close_window()
    
    print(f"\n{'='*50}")
    print(f"RESULTATS: {passes} reussis, {echecs} echoues")
    if echecs > 0:
        print("\nEchecs:")
        for r in resultats:
            if not r.reussi:
                print(f"  X {r.classe}.{r.nom}: {r.erreur}")
    print(f"{'='*50}\n")
    
    return echecs == 0
