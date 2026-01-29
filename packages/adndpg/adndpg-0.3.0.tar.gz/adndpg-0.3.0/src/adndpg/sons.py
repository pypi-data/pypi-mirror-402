import pyray as raylib


_audio_initialise = False


def _initialiser_audio():
    global _audio_initialise
    if not _audio_initialise:
        raylib.init_audio_device()
        _audio_initialise = True


class Son:
    def __init__(self, chemin: str):
        _initialiser_audio()
        self._son = raylib.load_sound(chemin)
        self._chemin = chemin
    
    def jouer(self) -> None:
        raylib.play_sound(self._son)
    
    def arreter(self) -> None:
        raylib.stop_sound(self._son)
    
    def changer_volume(self, volume: float) -> None:
        raylib.set_sound_volume(self._son, max(0.0, min(1.0, volume)))
    
    def est_en_lecture(self) -> bool:
        return raylib.is_sound_playing(self._son)
    
    def __del__(self):
        try:
            if hasattr(self, '_son'):
                raylib.unload_sound(self._son)
        except:
            pass


class Musique:
    def __init__(self, chemin: str):
        _initialiser_audio()
        self._musique = raylib.load_music_stream(chemin)
        self._chemin = chemin
    
    def jouer(self) -> None:
        raylib.play_music_stream(self._musique)
    
    def continue_a_jouer(self) -> None:
        raylib.update_music_stream(self._musique)
    
    def mettre_en_pause(self) -> None:
        raylib.pause_music_stream(self._musique)
    
    def reprendre(self) -> None:
        raylib.resume_music_stream(self._musique)
    
    def arreter(self) -> None:
        raylib.stop_music_stream(self._musique)
    
    def est_en_boucle(self, oui: bool) -> None:
        self._musique.looping = oui
    
    def changer_volume(self, volume: float) -> None:
        raylib.set_music_volume(self._musique, max(0.0, min(1.0, volume)))
    
    def est_en_lecture(self) -> bool:
        return raylib.is_music_stream_playing(self._musique)
    
    def __del__(self):
        try:
            if hasattr(self, '_musique'):
                raylib.unload_music_stream(self._musique)
        except:
            pass
