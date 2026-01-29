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
        
        from adndpg.fenetre import _obtenir_police_defaut, _assurer_caracteres
        _assurer_caracteres(self.contenu)
        police = _obtenir_police_defaut()
        
        if police:
            # Conversion en codepoints pour un support Unicode robuste
            utf8_bytes = self.contenu.encode('utf-8')
            count = raylib.ffi.new("int *")
            codepoints = raylib.load_codepoints(utf8_bytes, count)
            
            raylib.draw_text_codepoints(
                police,
                codepoints,
                count[0],
                raylib.Vector2(self.x, self.y),
                float(self.taille),
                1.0, # Espacement
                self.couleur
            )
            raylib.unload_codepoints(codepoints)
        else:
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
        from adndpg.fenetre import _obtenir_police_defaut, _assurer_caracteres
        _assurer_caracteres(self.contenu)
        police = _obtenir_police_defaut()
        if police:
            utf8_bytes = self.contenu.encode('utf-8')
            count = raylib.ffi.new("int *")
            codepoints = raylib.load_codepoints(utf8_bytes, count)
            
            vect = raylib.measure_text_ex(
                police,
                self.contenu,
                float(self.taille),
                1.0
            )
            raylib.unload_codepoints(codepoints)
            return int(vect.x)
        return raylib.measure_text(self.contenu, self.taille)
