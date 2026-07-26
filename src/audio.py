import pygame
import random
from src.config import Config

class GestorAudio:
    """
    Gestor central de audio del juego.
    Administra la reproducción de música de fondo, listas de reproducción (playlists),
    efectos de sonido (SFX), escalado de volúmenes y la función de silencio global (F1).
    """
    def __init__(self):
        self.snd_click = None
        self.snd_seleccion = None
        self.snd_alerta = None
        self.snd_victoria = None
        self.snd_derrota = None
        self.snd_pausa = None
        self.snd_reanudar = None
        self.snd_salir = None
        self.snd_pez = None
        self.snd_splash = None
        self.snd_tension = None
        self.snd_empate = None # Domingo 26/07: Nuevo sonido añadido
        self.snd_kamek = None
        self._pista_actual = None
        self.lista_actual = []
        self.indice_cancion_actual = 0
        self._volumenes_base_sfx = {}

        self.cargar_sonidos()

    def _cargar_sfx_real(self, nombre_archivo, volumen=0.6):
        """Carga un efecto de sonido real desde assets/sounds. Si falla, retorna None."""
        ruta = Config.RUTA_SFX / nombre_archivo
        try:
            snd = pygame.mixer.Sound(str(ruta))
            snd.set_volume(volumen)
            return snd
        except Exception as e:
            print(f"No se pudo cargar {nombre_archivo}: {e}")
            return None

#Sabado 25/07: Se cargaron más sonidos y se añadió más soporte al bucle for
    def cargar_sonidos(self):
        """Carga todos los efectos de sonido y registra sus volúmenes base."""
        self.snd_click = self._cargar_sfx_real("sfx_menu_option.mp3")
        self.snd_seleccion = self._cargar_sfx_real("sfx_select.mp3")
        self.snd_alerta = self._cargar_sfx_real("sfx_hurry.mp3", volumen=0.5)

        self.snd_victoria = [self._cargar_sfx_real("sfx_victory.mp3"),  self._cargar_sfx_real("sfx_victory1.mp3"),
                             self._cargar_sfx_real("sfx_victory2.mp3"), self._cargar_sfx_real("sfx_victory3.mp3"),
                             self._cargar_sfx_real("sfx_victory4.mp3"), self._cargar_sfx_real("sfx_victory5.mp3")]

        self.snd_derrota = [self._cargar_sfx_real("sfx_lose.mp3"), self._cargar_sfx_real("sfx_lose1.mp3"),
                            self._cargar_sfx_real("sfx_lose2.mp3")]
        
        self.snd_splash = [self._cargar_sfx_real("sfx_splash_wet.mp3"), self._cargar_sfx_real("sfx_splash_wet1.mp3")]

        self.snd_empate = [self._cargar_sfx_real("sfx_draw_game.mp3"), self._cargar_sfx_real("sfx_draw_game1.mp3"),
                           self._cargar_sfx_real("sfx_draw_game2.mp3"), self._cargar_sfx_real("sfx_draw_game3.mp3"),
                           self._cargar_sfx_real("sfx_draw_game4.mp3"), self._cargar_sfx_real("sfx_draw_game5.mp3"), ]

        self.snd_tension = [self._cargar_sfx_real("sfx_tension_cuerda.mp3"), self._cargar_sfx_real("sfx_tension_cuerda1.mp3")]
        
        self.snd_pausa = self._cargar_sfx_real("sfx_pause.mp3")
        self.snd_reanudar = self._cargar_sfx_real("sfx_unpause.mp3")
        self.snd_salir = self._cargar_sfx_real("sfx_exit_game.mp3")
        self.snd_kamek = self._cargar_sfx_real("sfx_kamek.mp3", volumen=0.8)

        # Guardar volúmenes base para permitir escalado con el slider de opciones
        self._volumenes_base_sfx = {}
        for nombre_attr in dir(self):
            if nombre_attr.startswith("snd_"):
                snd = getattr(self, nombre_attr)
                if snd is not None:
                    if isinstance(snd, list):
                        self._volumenes_base_sfx[nombre_attr]= [s.get_volume() for s in snd if s is not None]
                    else:
                        self._volumenes_base_sfx[nombre_attr] = snd.get_volume()

        self.aplicar_volumen_sfx()

#Domingo 26/07: Modificación para el soporte de sonido en lista
    def aplicar_volumen_sfx(self):
        """Reaplica el volumen de todos los SFX cargados según Config.volumen_sfx."""
        for nombre_attr, volumen_base in self._volumenes_base_sfx.items():
            snd = getattr(self, nombre_attr, None)
            if snd is not None:
                if isinstance(snd, list) and isinstance(volumen_base, list):
                    for s, v_base in zip(snd, volumen_base):
                        if s is not None:
                            s.set_volume(v_base * Config.volumen_sfx)
                            
                elif not isinstance(snd, list):
                    snd.set_volume(volumen_base * Config.volumen_sfx)

    def aplicar_volumen_musica(self):
        """Reaplica el volumen de la música actual según Config.volumen_musica."""
        mult = 0.45 if self._pista_actual in ("game", "duel") else 1.0
        pygame.mixer.music.set_volume(Config.volumen_musica * mult)

#Domingo 26/07: Se modificó la función para que soportara listas, y reproducir algunos efectos en bucle 
    def reproducir_sonido(self, sonido, loops=0):
        """Reproduce un efecto de sonido o escoge uno al azar si es una lista si SFX está activo.
            Permite especificar el número de repeticiones/bucles con loops."""
        if Config.sfx_activo and sonido:
            if isinstance(sonido, list):
                sfx_elegido = random.choice(sonido)
                if sfx_elegido:
                    return sfx_elegido.play(loops=loops)
            else:
                if sonido:
                    return sonido.play(loops=loops)
        return None

    def reproducir_musica(self, pista="menu"):
        """Reproduce la lista de música correspondiente al modo indicado."""
        if not Config.musica_activa:
            return
        if self._pista_actual == pista:
            return

        archivos_musica = {
            "menu": ["music_menu.mp3", "music_menu2.mp3", "music_menu3.mp3"],
            "game": ["music_game.mp3", "music_game2.mp3", "music_game3.mp3"],
            "duel": ["music_duel.mp3", "music_duel1.mp3", "music_duel2.mp3", "music_duel3.mp3"],
        }

        if pista not in archivos_musica:
            return

        pistas = archivos_musica[pista]

        try:
            if isinstance(pistas, list):
                self.lista_actual = pistas
                self.indice_cancion_actual = random.randint(0, len(self.lista_actual) - 1)
                
                pygame.mixer.music.set_endevent(pygame.USEREVENT + 1)
                primera = Config.RUTA_MUSICA / self.lista_actual[self.indice_cancion_actual]
                pygame.mixer.music.load(str(primera))
                self.aplicar_volumen_musica()
                pygame.mixer.music.play()
            else:
                pygame.mixer.music.set_endevent()
                ruta = Config.RUTA_MUSICA / pistas
                pygame.mixer.music.load(str(ruta))
                self.aplicar_volumen_musica()
                pygame.mixer.music.play(loops=-1)

            self._pista_actual = pista
        except Exception as e:
            print(f"No se pudo cargar la música '{pista}': {e}")

    def detener_musica(self):
        """Detiene la reproducción de música de fondo de forma limpia."""
        pygame.mixer.music.set_endevent()
        pygame.mixer.music.stop()
        self._pista_actual = None

    def procesar_fin_pista(self):
        """Avanza automáticamente al siguiente tema de la lista al terminar una canción."""
        if Config.musica_activa and self.lista_actual:
            self.indice_cancion_actual = (self.indice_cancion_actual + 1) % len(self.lista_actual)
            siguiente = Config.RUTA_MUSICA / self.lista_actual[self.indice_cancion_actual]
            try:
                pygame.mixer.music.load(str(siguiente))
                self.aplicar_volumen_musica()
                pygame.mixer.music.play()
            except Exception as e:
                print(f"Error cambiando a siguiente pista: {e}")

#Sabado 25/07: Implementación de un nuevo método 
    def reproducir_sonido_salir(self):
        """Reproduce sfx_exit_game.mp3 por completo antes de cerrar el juego y volver al Launcher."""
        self.detener_musica()
        if Config.sfx_activo and self.snd_salir:
            try:
                canal = self.snd_salir.play()
                duracion_ms = int(self.snd_salir.get_length() * 1000)
                tiempo_inicio = pygame.time.get_ticks()      
                while canal and canal.get_busy() and (pygame.time.get_ticks() - tiempo_inicio < min(duracion_ms + 100, 3000)):
                    pygame.time.wait(20)
            except Exception as e:
                print(f"Error reproduciondo sfx_exit_game: {e}")

#Sabado 25/07: Implementación de un nuevo método 
    def alternar_silencio_global(self, pista_actual, estado_juego):
        """Alterna el silencio global (MUTE / UNMUTE) para Música y SFX desde cualquier pantalla con F1."""
        estaba_activo = Config.musica_activa or Config.sfx_activo
        nuevo_estado = not estaba_activo
        Config.musica_activa = nuevo_estado
        Config.sfx_activo = nuevo_estado
        if Config.musica_activa:
            self.reproducir_sonido(self.snd_click)
            if estado_juego not in ("FIN_JUEGO",):
                self.reproducir_musica(pista_actual)
        else:
            self.detener_musica()
        return nuevo_estado