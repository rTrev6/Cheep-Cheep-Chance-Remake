import pygame
import random
import math
import sys
from src.config import *
from src.entity import *

# Aseguramos la inicialización de Pygame y su mixer
pygame.init()
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=2) # 2 channels for stereo mix
except Exception as e:
    print(f"No se pudo inicializar el mixer de Pygame: {e}")

class ManejadorJuego:
    def __init__(self, pantalla):
        self.pantalla = pantalla
        self.reloj = pygame.time.Clock()
        self.ejecutando = True
        
        # --- ESTADO INICIAL ---
        # Se inicia en la Pantalla de Título parpadeante con música chiptune
        self.estado = "PANTALLA_TITULO"
        self.estado_previo_opciones = "MENU_PRINCIPAL"
        
        # Sistema de debug / FPS
        self.mostrar_debug_fps = False
        
        # --- FUENTES EN MEMORIA ---
        self.fuente_titulo = pygame.font.Font(Config.FUENTE_PRINCIPAL, 38)
        self.fuente_pausa = pygame.font.Font(Config.FUENTE_PRINCIPAL, 40)
        self.fuente_subtitulo = pygame.font.Font(Config.FUENTE_PRINCIPAL, 20)
        self.fuente_ui = pygame.font.Font(Config.FUENTE_PRINCIPAL, 16)
        self.fuente_fps = pygame.font.Font(Config.FUENTE_PRINCIPAL, 14)
        # Fuente más grande para el panel lateral de jugadores (rondas, selección, etc.)
        self.fuente_panel = pygame.font.Font(Config.FUENTE_PRINCIPAL, 21)
        
        # --- CARGAR SONIDOS SINTETIZADOS RETRO Y MÚSICA DE FONDO ---
        self.cargar_sonidos()
        self.reproducir_musica()
        
        # --- CARGAR FONDO DE PANTALLA DE MAR ---
        try:
            self.bg_image = pygame.image.load(str(Config.SPRITE_BACKGROUND)).convert()
            self.bg_image = pygame.transform.scale(self.bg_image, (Config.ANCHO, Config.ALTO))
        except Exception as e:
            print(f"Error cargando fondo de mar: {e}")
            self.bg_image = pygame.Surface((Config.ANCHO, Config.ALTO))
            self.bg_image.fill(Config.CELESTE_CIELO)

        # --- CARGAR FONDO ANIMADO GIF (STARS) ---
        self.frames_stars = self.cargar_gif_animado(str(Config.RUTA_IMAGENES / "stars.gif"))
        self.indice_frame_stars = 0
        self.ultimo_tiempo_frame_stars = 0

        # --- CARGAR ICONO DE KAMEK ---
        self.sprite_kamek = None
        path_kamek = Config.RUTA_IMAGENES / "icon_Kamek.png"
        if not path_kamek.exists() and Config.RUTA_IMAGENES.exists():
            for f in Config.RUTA_IMAGENES.iterdir():
                if f.is_file() and f.name.lower() == "icon_kamek.png":
                    path_kamek = f
                    break
        if path_kamek.exists():
            try:
                self.sprite_kamek = pygame.image.load(str(path_kamek)).convert_alpha()
                self.sprite_kamek = pygame.transform.scale(self.sprite_kamek, (100, 100))
            except Exception as e:
                print(f"Error cargando icono de Kamek: {e}")

        # --- CORRECCIÓN DE BUG DE RENDIMIENTO ---
        # Antes, la pantalla "MENU_SELECCION_PERSONAJES" cargaba y reescalaba
        # cada sel_{Personaje}_icon_sprite.png DESDE DISCO en cada fotograma
        # (60 veces por segundo x 8 personajes), generando I/O innecesario y
        # posibles tirones. Ahora se precargan una única vez aquí y se
        # reutilizan desde memoria en el render.
        self.sprites_seleccion = {}
        for nombre_char in Config.PERSONAJES:
            filename_sel = f"sel_{nombre_char}_icon_sprite.png"
            path_sel = Config.RUTA_IMAGENES / filename_sel
            if not path_sel.exists() and Config.RUTA_IMAGENES.exists():
                for f in Config.RUTA_IMAGENES.iterdir():
                    if f.is_file() and f.name.lower() == filename_sel.lower():
                        path_sel = f
                        break
            if path_sel.exists():
                try:
                    img = pygame.image.load(str(path_sel)).convert_alpha()
                    img = pygame.transform.scale(img, (110, 110))
                    self.sprites_seleccion[nombre_char] = img
                except Exception as e:
                    print(f"Error cargando sprite de selección {nombre_char}: {e}")

        # --- CAPA DE PROFUNDIDAD DEL AGUA ---
        alto_agua = Config.ALTO - Config.NIVEL_AGUA
        self.tinte_agua = pygame.Surface((Config.ANCHO, alto_agua), pygame.SRCALPHA)
        paso = 4
        for y in range(0, alto_agua, paso):
            progreso = y / alto_agua
            alpha = int(35 + progreso * 70)
            pygame.draw.rect(self.tinte_agua, (*Config.AZUL_MAR, alpha), (0, y, Config.ANCHO, paso))
            
        # --- CRIATURAS MARINAS EN EL FONDO ---
        self.criaturas = []
        for _ in range(4):
            self.criaturas.append(CriaturaAmbiental(str(Config.SPRITE_FISH_LEFT), str(Config.SPRITE_FISH_RIGHT), es_pez=True))
        for _ in range(2):
            self.criaturas.append(CriaturaAmbiental(str(Config.SPRITE_MONSTER2_LEFT), str(Config.SPRITE_MONSTER2_RIGHT), es_pez=False))
            
        # --- BURBUJAS Y ALGAS ---
        self.burbujas = [[random.randint(10, Config.ANCHO - 10), random.randint(Config.NIVEL_AGUA, Config.ALTO), random.uniform(0.5, 1.5)] for _ in range(12)]
        # Distribuir algas sobre la resolución 1280
        self.algas_x = [80, 220, 380, 540, 700, 860, 1020, 1180]

        # --- BOTONES DINÁMICAMENTE CENTRADOS ---
        btn_w = 300
        btn_h = 50
        cx = (Config.ANCHO - btn_w) // 2 # 490 en 1280
        
        # --- BOTONES: MENÚ PRINCIPAL ---
        self.btn_jugar = Boton(cx, 260, btn_w, btn_h, "JUGAR", Config.VERDE, Config.VERDE_REMANSO)
        self.btn_opciones = Boton(cx, 325, btn_w, btn_h, "OPCIONES", Config.GRIS, Config.GRIS_CLARO)
        self.btn_instrucciones = Boton(cx, 390, btn_w, btn_h, "INSTRUCCIONES", Config.AMARILLO, Config.VERDE_REMANSO)
        self.btn_salir = Boton(cx, 455, btn_w, btn_h, "VOLVER AL LAUNCHER", Config.ROJO, Config.ROJO_OSCURO)

        # --- BOTÓN: VOLVER DE LA PANTALLA DE INSTRUCCIONES ---
        self.btn_instrucciones_volver = Boton(cx, 630, btn_w, btn_h, "VOLVER", Config.GRIS, Config.GRIS_CLARO)
        
        # --- BOTONES: MENÚ DE SELECCIÓN DE MODOS ---
        self.btn_vs_cpu = Boton(cx, 260, btn_w, btn_h, "VS CPU (1 VS 3)", Config.VERDE, Config.VERDE_REMANSO)
        self.btn_multi = Boton(cx, 330, btn_w, btn_h, "MULTIJUGADOR LOCAL", Config.VERDE, Config.VERDE_REMANSO)
        self.btn_duelo = Boton(cx, 400, btn_w, btn_h, "MODO DUELO (1VS1)", Config.AMARILLO, Config.VERDE_REMANSO)
        self.btn_volver_menu = Boton(cx, 490, btn_w, btn_h, "VOLVER", Config.GRIS, Config.GRIS_CLARO)

        # --- BOTONES: SELECCIÓN DE JUGADORES (CANTIDAD) ---
        self.btn_cant_2 = Boton(cx, 260, btn_w, btn_h, "2 JUGADORES", Config.VERDE, Config.VERDE_REMANSO)
        self.btn_cant_3 = Boton(cx, 330, btn_w, btn_h, "3 JUGADORES", Config.VERDE, Config.VERDE_REMANSO)
        self.btn_cant_4 = Boton(cx, 400, btn_w, btn_h, "4 JUGADORES", Config.VERDE, Config.VERDE_REMANSO)
        self.btn_cant_volver = Boton(cx, 490, btn_w, btn_h, "VOLVER", Config.GRIS, Config.GRIS_CLARO)
        
        # --- BOTONES: PANTALLA DE OPCIONES ---
        self.btn_toggle_musica = Boton(cx, 130, btn_w, btn_h, "MUSICA: SI" if Config.musica_activa else "MUSICA: NO", Config.VERDE, Config.VERDE_REMANSO)
        self.btn_toggle_sfx = Boton(cx, 195, btn_w, btn_h, "SFX: SI" if Config.sfx_activo else "SFX: NO", Config.VERDE, Config.VERDE_REMANSO)
        # --- SLIDERS: VOLUMEN DE MÚSICA Y EFECTOS ---
        self.slider_musica = Slider(cx, 300, btn_w, 14, Config.volumen_musica, "VOLUMEN MUSICA")
        self.slider_sfx = Slider(cx, 360, btn_w, 14, Config.volumen_sfx, "VOLUMEN EFECTOS")
        self.btn_reset_scores = Boton(cx, 410, btn_w, btn_h, "RESETEAR MARCADOR", Config.ROJO, Config.ROJO_OSCURO)
        self.btn_volver = Boton(cx, 610, btn_w, btn_h, "VOLVER", Config.GRIS, Config.GRIS_CLARO)
        
        # --- BOTONES: PAUSA ---
        self.btn_reanudar = Boton(cx, 280, btn_w, btn_h, "REANUDAR", Config.VERDE, Config.VERDE_REMANSO)
        self.btn_pausa_opciones = Boton(cx, 350, btn_w, btn_h, "OPCIONES", Config.GRIS, Config.GRIS_CLARO)
        self.btn_pausa_menu = Boton(cx, 420, btn_w, btn_h, "MENÚ PRINCIPAL", Config.ROJO, Config.ROJO_OSCURO)
        
        # --- BOTONES: FIN DE JUEGO ---
        self.btn_reiniciar = Boton(cx, 330, btn_w, btn_h, "VOLVER A JUGAR", Config.VERDE, Config.VERDE_REMANSO)
        self.btn_fin_menu = Boton(cx, 400, btn_w, btn_h, "MENÚ PRINCIPAL", Config.GRIS, Config.GRIS_CLARO)
        
        # Variables de animación dramática
        self.jugadores_en_orden_revelacion = []
        self.indice_revelacion_actual = 0
        self.sub_estado_animacion = "CAMINANDO"  
        self.tiempo_inicio_sub_estado = 0
        self.duracion_animacion_jalon = 1500  
        self.duracion_subida_pez = 1200       
        self.duracion_caida_jugador = 1500    
        self.x_original_jugador = 0
        self.y_original_jugador = 0
        self.y_al_soltar = 0  
        self.cuerdas_reveladas_indices = set()
        self.sonido_ataque_reproducido = False

        # Altura base unificada de reposo para el agua profunda
        self.altura_reposo_cuerda = Config.ALTO - 80

        # Variables de control de partida
        self.jugadores = []
        self.cuerdas = []
        self.num_ronda = 1
        self.turno_actual = 0
        self.revelado = False
        self.muerte_subita_activa = False
        self.mensaje_partida = ""
        
        # --- LÓGICA DEL MODO DUELO ---
        self.modo_actual = "" 
        self.victorias_j1 = 0
        self.victorias_j2 = 0
        self.duelo_finalizado = False
        self.esperando_confirmacion_set = False

        # --- SELECCIÓN DE PERSONAJES ---
        self.cantidad_humanos = 1
        self.indice_seleccion_actual = 0
        self.personaje_resaltado = 0
        self.personajes_seleccionados = {} # index -> character_name

        # Temporizadores
        self.tiempo_limite = 5000
        self.momento_inicio_turno = 0
        self.segundos_restantes = 5
        self.ultimo_segundo_alerta = 5
        self.momento_inicio_pensamiento_cpu = 0  
        self.momento_pausa_post_seleccion = 0
        self.jugadores_vivos_para_revelar = []
        self.estado_previo_a_pausa = "" 
        self.momento_pausa = 0

        # --- SELECCIÓN DE CUERDA CON MOUSE ---
        self.cuerda_resaltada = None

        # --- NAVEGACIÓN POR TECLADO EN MENÚS CON BOTONES (mano indicadora) ---
        self.indice_menu_actual = 0
        self._ultimo_estado_menu_check = self.estado

    # --- CARGAR GIF CON PILLOW ---
    def cargar_gif_animado(self, ruta_gif):
        try:
            from PIL import Image
            img = Image.open(ruta_gif)
            frames = []
            try:
                while True:
                    frame_rgba = img.convert("RGBA")
                    data = frame_rgba.tobytes()
                    surf = pygame.image.fromstring(data, img.size, "RGBA")
                    surf = pygame.transform.scale(surf, (Config.ANCHO, Config.ALTO))
                    frames.append(surf)
                    img.seek(img.tell() + 1)
            except EOFError:
                pass
            print(f"GIF animado {ruta_gif} cargado con éxito: {len(frames)} frames.")
            return frames
        except Exception as e:
            print(f"Error cargando GIF animado {ruta_gif}: {e}")
            return []

    # --- SÍNTESIS DE SONIDOS RETRO ---
    def generar_sonido_sintetico(self, frecuencia, duracion, tipo="sine", volumen=0.08):
        if not pygame.mixer.get_init():
            return None
        try:
            import array
            import math
            sample_rate = 22050
            num_muestras = int(sample_rate * duracion)
            datos = array.array('h')
            for i in range(num_muestras):
                t = i / sample_rate
                if tipo == "sine":
                    val = math.sin(2 * math.pi * frecuencia * t)
                elif tipo == "square":
                    val = 1.0 if math.sin(2 * math.pi * frecuencia * t) >= 0 else -1.0
                elif tipo == "triangle":
                    val = 2.0 * abs(2.0 * (t * frecuencia - math.floor(t * frecuencia + 0.5))) - 1.0
                else:
                    val = math.sin(2 * math.pi * frecuencia * t)
                
                if i < 100:
                    val *= (i / 100)
                elif i > num_muestras - 100:
                    val *= ((num_muestras - i) / 100)
                    
                val_int = int(val * 32767 * volumen)
                val_int = max(-32768, min(32767, val_int))
                datos.append(val_int)
            return pygame.mixer.Sound(buffer=datos.tobytes())
        except Exception as e:
            print(f"Error generando sonido: {e}")
            return None

    def generar_sonido_splash(self):
        if not pygame.mixer.get_init():
            return None
        try:
            import array
            import random
            sample_rate = 22050
            duracion = 0.5
            num_muestras = int(sample_rate * duracion)
            datos = array.array('h')
            for i in range(num_muestras):
                progreso = i / num_muestras
                val = (random.random() * 2.0 - 1.0) * (1.0 - progreso)
                val_int = int(val * 32767 * 0.15)
                val_int = max(-32768, min(32767, val_int))
                datos.append(val_int)
            return pygame.mixer.Sound(buffer=datos.tobytes())
        except Exception as e:
            print(f"Error generando splash sound: {e}")
            return None

    def generar_sonido_victoria(self):
        if not pygame.mixer.get_init():
            return None
        try:
            import array
            import math
            sample_rate = 22050
            notas = [523.25, 659.25, 783.99, 1046.50]
            dur_nota = 0.12
            muestras_por_nota = int(sample_rate * dur_nota)
            datos = array.array('h')
            for f in notas:
                for i in range(muestras_por_nota):
                    t = i / sample_rate
                    val = math.sin(2 * math.pi * f * t)
                    if i < 100:
                        val *= (i / 100)
                    elif i > muestras_por_nota - 100:
                        val *= ((muestras_por_nota - i) / 100)
                    val_int = int(val * 32767 * 0.08)
                    val_int = max(-32768, min(32767, val_int))
                    datos.append(val_int)
            return pygame.mixer.Sound(buffer=datos.tobytes())
        except Exception as e:
            print(f"Error victoria sound: {e}")
            return None

    def generar_sonido_derrota(self):
        if not pygame.mixer.get_init():
            return None
        try:
            import array
            import math
            sample_rate = 22050
            notas = [523.25, 392.00, 329.63, 261.63]
            dur_nota = 0.15
            muestras_por_nota = int(sample_rate * dur_nota)
            datos = array.array('h')
            for f in notas:
                for i in range(muestras_por_nota):
                    t = i / sample_rate
                    val = 0.6 * math.sin(2 * math.pi * f * t) + 0.4 * (1.0 if math.sin(2 * math.pi * f * t) >= 0 else -1.0)
                    if i < 100:
                        val *= (i / 100)
                    elif i > muestras_por_nota - 100:
                        val *= ((muestras_por_nota - i) / 100)
                    val_int = int(val * 32767 * 0.08)
                    val_int = max(-32768, min(32767, val_int))
                    datos.append(val_int)
            return pygame.mixer.Sound(buffer=datos.tobytes())
        except Exception as e:
            print(f"Error derrota sound: {e}")
            return None

    def generar_sonido_tension(self):
        if not pygame.mixer.get_init():
            return None
        try:
            import array
            import math
            import random
            sample_rate = 22050
            duracion = 1.4
            num_muestras = int(sample_rate * duracion)
            datos = array.array('h')
            for i in range(num_muestras):
                t = i / sample_rate
                progreso = i / num_muestras
                frecuencia = 200 - 90 * progreso
                tremolo = 0.7 + 0.3 * math.sin(2 * math.pi * 7 * t)
                ruido = (random.random() * 2.0 - 1.0) * 0.15
                val = math.sin(2 * math.pi * frecuencia * t) * tremolo + ruido
                if i < 200:
                    val *= (i / 200)
                elif i > num_muestras - 300:
                    val *= ((num_muestras - i) / 300)
                val_int = int(val * 32767 * 0.06)
                val_int = max(-32768, min(32767, val_int))
                datos.append(val_int)
            return pygame.mixer.Sound(buffer=datos.tobytes())
        except Exception as e:
            print(f"Error generando sonido de tension: {e}")
            return None

    def generar_musica_fondo(self):
        """Sintetiza un bucle de música retro (chiptune) de 8 segundos."""
        if not pygame.mixer.get_init():
            return None
        try:
            import array
            import math
            sample_rate = 22050
            duracion = 8.0
            num_muestras = int(sample_rate * duracion)
            datos = array.array('h', [0] * num_muestras)
            
            melodia = [
                523.25, 659.25, 783.99, 659.25,  # C
                493.88, 587.33, 783.99, 587.33,  # G
                440.00, 523.25, 659.25, 523.25,  # Am
                349.23, 440.00, 523.25, 440.00   # F
            ]
            bajo_frecuencias = [130.81, 98.00, 110.00, 87.31] # C3, G2, A2, F2
            
            nota_dur = 0.5
            muestras_nota = int(sample_rate * nota_dur)
            
            for tick in range(16):
                freq_mel = melodia[tick]
                freq_bajo = bajo_frecuencias[tick // 4]
                
                inicio = tick * muestras_nota
                for i in range(muestras_nota):
                    idx = inicio + i
                    if idx >= num_muestras:
                        break
                    t = idx / sample_rate
                    
                    val_mel = math.sin(2 * math.pi * freq_mel * t)
                    tf = t * freq_bajo
                    val_bajo = 2.0 * abs(2.0 * (tf - math.floor(tf + 0.5))) - 1.0
                    
                    val_mezcla = (val_mel * 0.05) + (val_bajo * 0.07)
                    
                    env = 1.0
                    if i < 250:
                        env = i / 250
                    elif i > muestras_nota - 250:
                        env = (muestras_nota - i) / 250
                    
                    val_mezcla *= env
                    val_int = int(val_mezcla * 32767)
                    val_int = max(-32768, min(32767, val_int))
                    datos[idx] = val_int
                    
            return pygame.mixer.Sound(buffer=datos.tobytes())
        except Exception as e:
            print(f"Error generando música de fondo: {e}")
            return None

    def _cargar_sfx_real(self, nombre_archivo, volumen=0.6):
        """Carga un efecto de sonido real desde assets/sounds. Si falla, retorna None."""
        ruta = Config.RUTA_SONIDOS / nombre_archivo
        try:
            snd = pygame.mixer.Sound(str(ruta))
            snd.set_volume(volumen)
            return snd
        except Exception as e:
            print(f"No se pudo cargar {nombre_archivo}: {e}")
            return None

    def cargar_sonidos(self):
        # --- SFX reales (assets/sounds) ---
        self.snd_click = self._cargar_sfx_real("sfx_menu_option.mp3")
        self.snd_seleccion = self._cargar_sfx_real("sfx_select.mp3")
        self.snd_alerta = self._cargar_sfx_real("sfx_hurry.oga", volumen=0.5)
        self.snd_victoria = self._cargar_sfx_real("sfx_victory.oga")
        self.snd_derrota = self._cargar_sfx_real("sfx_lose.oga")
        self.snd_pausa = self._cargar_sfx_real("sfx_pause.mp3")
        self.snd_reanudar = self._cargar_sfx_real("sfx_unpause.mp3")
        self.snd_salir = self._cargar_sfx_real("sfx_exit_game.oga")
        self.snd_kamek = self._cargar_sfx_real("sfx_kamek.mp3")

        # --- Sin archivo real equivalente: se mantienen sintetizados ---
        self.snd_pez = self.generar_sonido_sintetico(950, 0.15, "triangle", volumen=0.08)
        self.snd_splash = self.generar_sonido_splash()
        self.snd_tension = self.generar_sonido_tension()

        # Pista de música actualmente sonando ("menu", "game", "duel" o None)
        self._pista_actual = None

        # --- VOLUMEN BASE DE CADA SFX (para reescalar con el slider de Opciones) ---
        # Cada sonido conserva su "mezcla" relativa original (por ejemplo, el
        # de kamek siempre un poco más fuerte que el del pez) y luego se
        # multiplica por Config.volumen_sfx, que es lo que mueve el slider.
        self._volumenes_base_sfx = {}
        for nombre_attr in dir(self):
            if nombre_attr.startswith("snd_"):
                snd = getattr(self, nombre_attr)
                if snd is not None:
                    self._volumenes_base_sfx[nombre_attr] = snd.get_volume()
        self.aplicar_volumen_sfx()

    def aplicar_volumen_sfx(self):
        """Reaplica el volumen de todos los SFX cargados según Config.volumen_sfx."""
        for nombre_attr, volumen_base in self._volumenes_base_sfx.items():
            snd = getattr(self, nombre_attr, None)
            if snd is not None:
                snd.set_volume(volumen_base * Config.volumen_sfx)

    def aplicar_volumen_musica(self):
        """Reaplica el volumen de la música actual según Config.volumen_musica."""
        pygame.mixer.music.set_volume(Config.volumen_musica)

    def reproducir_sonido(self, sonido):
        if Config.sfx_activo and sonido:
            sonido.play()

    def reproducir_musica(self, pista="menu"):
        """Reproduce la pista de música real indicada ('menu', 'game' o 'duel')."""
        if not Config.musica_activa:
            return
        archivos_musica = {
            "menu": "music_menu.oga",
            "game": "music_game.oga",
            "duel": "music_duel.oga",
        }
        if pista not in archivos_musica:
            return
        if self._pista_actual == pista:
            return
        ruta = Config.RUTA_SONIDOS / archivos_musica[pista]
        try:
            pygame.mixer.music.load(str(ruta))
            pygame.mixer.music.set_volume(Config.volumen_musica)
            pygame.mixer.music.play(loops=-1)
            self._pista_actual = pista
        except Exception as e:
            print(f"No se pudo cargar la música '{pista}': {e}")

    def detener_musica(self):
        pygame.mixer.music.stop()
        self._pista_actual = None

    def _pista_para_estado_actual(self):
        """Determina qué pista de música corresponde al estado de juego actual."""
        estados_musica_menu = (
            "PANTALLA_TITULO", "MENU_PRINCIPAL", "MENU_MODOS",
            "MENU_OPCIONES", "INSTRUCCIONES", "MENU_SELECCION_PERSONAJES",
            "SELECCION_CANTIDAD_JUGADORES",
        )
        if self.estado in estados_musica_menu:
            return "menu"
        return "duel" if self.modo_actual == "DUELO" else "game"

    def iniciar_revelacion_dramatica(self, jugadores_vivos):
        self.jugadores_en_orden_revelacion = list(jugadores_vivos)
        self.cuerdas_reveladas_indices.clear()
        
        if len(self.jugadores_en_orden_revelacion) == 0:
            self.revelado = True
            self.estado = "EN_JUEGO"
            self.procesar_enter()
        else:
            self.estado = "REVELANDO_CUERDAS"
            self.indice_revelacion_actual = 0
            self.sub_estado_animacion = "CAMINANDO"
            self.tiempo_inicio_sub_estado = pygame.time.get_ticks()
            
            j_primero = self.jugadores_en_orden_revelacion[0]
            self.x_original_jugador = j_primero.x
            self.y_original_jugador = j_primero.y
            self.y_al_soltar = 0

    def obtener_y_elipse(self, x, obtener_borde_inferior=True):
        cx = Config.SALV_X + Config.SALV_ANCHO // 2
        cy = Config.SALV_Y + Config.SALV_ALTO // 2
        rx = Config.SALV_ANCHO // 2
        ry = Config.SALV_ALTO // 2
        val = 1.0 - ((x - cx) / rx) ** 2
        val = max(0, val)
        desplazamiento_y = int(ry * math.sqrt(val))
        return cy + desplazamiento_y if obtener_borde_inferior else cy - desplazamiento_y

    def generar_ronda(self, jugadores_vivos, muerte_subita=False):
        num_jugadores = len(jugadores_vivos)
        num_cuerdas = 2 if muerte_subita else num_jugadores * 2
        
        destinos = ["Pez Bueno"] * (1 if muerte_subita else num_jugadores) + ["Monstruo"] * (1 if muerte_subita else num_jugadores)
        random.shuffle(destinos)
        
        inicio_x = Config.SALV_X + 30
        fin_x = Config.SALV_X + Config.SALV_ANCHO - 30
        ancho_util = fin_x - inicio_x
        espaciado = ancho_util // (num_cuerdas - 1) if num_cuerdas > 1 else 0
        
        self.cuerdas = []
        for i in range(num_cuerdas):
            pos_x = inicio_x + (i * espaciado)
            y_curvo = self.obtener_y_elipse(pos_x, obtener_borde_inferior=True)
            c = Cuerda(i + 1, pos_x, y_curvo)
            c.contenido = destinos[i]
            c.y_fin = self.altura_reposo_cuerda
            self.cuerdas.append(c)
            
        # Se distribuye a cada jugador en una franja propia y del mismo ancho
        # dentro de la plataforma, centrándolo dentro de esa franja. Así,
        # sin importar cuántos jugadores haya (hasta 8), cada uno cuenta con
        # más espacio propio que el ancho de su sprite y no se solapan entre sí.
        space_j = Config.SALV_ANCHO // num_jugadores if num_jugadores > 0 else 0
        for idx, j in enumerate(jugadores_vivos):
            centro_franja = Config.SALV_X + idx * space_j + space_j // 2
            j.x = centro_franja - Config.CHAR_ANCHO // 2
            y_curvo_pies = self.obtener_y_elipse(j.x + Config.CHAR_ANCHO // 2, obtener_borde_inferior=False)
            j.y = y_curvo_pies - (Config.CHAR_ALTO - 5)
            j.cuerda_elegida = None

    def obtener_grupo_botones_actual(self):
        """Devuelve la lista ordenada (de arriba a abajo) de botones del menú
        actual, usada tanto para sincronizar la mano indicadora como para la
        navegación con teclado (flechas + ENTER/ESPACIO)."""
        mapa = {
            "MENU_PRINCIPAL": [self.btn_jugar, self.btn_opciones, self.btn_instrucciones, self.btn_salir],
            "MENU_MODOS": [self.btn_vs_cpu, self.btn_multi, self.btn_duelo, self.btn_volver_menu],
            "SELECCION_CANTIDAD_JUGADORES": [self.btn_cant_2, self.btn_cant_3, self.btn_cant_4, self.btn_cant_volver],
            "MENU_OPCIONES": [self.btn_toggle_musica, self.btn_toggle_sfx, self.btn_reset_scores, self.btn_volver],
            "INSTRUCCIONES": [self.btn_instrucciones_volver],
            "PAUSA": [self.btn_reanudar, self.btn_pausa_opciones, self.btn_pausa_menu],
            "FIN_JUEGO": [self.btn_reiniciar, self.btn_fin_menu],
        }
        return mapa.get(self.estado)

    def procesar_click_menu(self, pos_m):
        """Confirma la opción de un menú de botones en la posición pos_m.
        Se usa tanto para clics de mouse reales como para ENTER/ESPACIO al
        navegar con teclado (en ese caso pos_m es el centro del botón
        resaltado por la mano indicadora)."""
        if self.estado == "MENU_PRINCIPAL":
            if self.btn_jugar.fue_clicado(pos_m):
                self.reproducir_sonido(self.snd_click)
                self.estado = "MENU_MODOS"
            elif self.btn_opciones.fue_clicado(pos_m):
                self.reproducir_sonido(self.snd_click)
                self.estado_previo_opciones = "MENU_PRINCIPAL"
                self.estado = "MENU_OPCIONES"
            elif self.btn_instrucciones.fue_clicado(pos_m):
                self.reproducir_sonido(self.snd_click)
                self.estado = "INSTRUCCIONES"
            elif self.btn_salir.fue_clicado(pos_m):
                self.reproducir_sonido(self.snd_salir)
                self.ejecutando = False

        elif self.estado == "INSTRUCCIONES":
            if self.btn_instrucciones_volver.fue_clicado(pos_m):
                self.reproducir_sonido(self.snd_click)
                self.estado = "MENU_PRINCIPAL"

        elif self.estado == "MENU_MODOS":
            if self.btn_vs_cpu.fue_clicado(pos_m):
                self.reproducir_sonido(self.snd_click)
                self.modo_actual = "VS_CPU"
                self.cantidad_humanos = 1
                self.indice_seleccion_actual = 0
                self.personajes_seleccionados = {}
                self.estado = "MENU_SELECCION_PERSONAJES"
            elif self.btn_multi.fue_clicado(pos_m):
                self.reproducir_sonido(self.snd_click)
                self.estado = "SELECCION_CANTIDAD_JUGADORES"
            elif self.btn_duelo.fue_clicado(pos_m):
                self.reproducir_sonido(self.snd_click)
                self.modo_actual = "DUELO"
                self.cantidad_humanos = 1
                self.indice_seleccion_actual = 0
                self.personajes_seleccionados = {}
                self.victorias_j1 = 0
                self.victorias_j2 = 0
                self.duelo_finalizado = False
                self.esperando_confirmacion_set = False
                self.estado = "MENU_SELECCION_PERSONAJES"
            elif self.btn_volver_menu.fue_clicado(pos_m):
                self.reproducir_sonido(self.snd_click)
                self.estado = "MENU_PRINCIPAL"

        elif self.estado == "SELECCION_CANTIDAD_JUGADORES":
            if self.btn_cant_2.fue_clicado(pos_m):
                self.reproducir_sonido(self.snd_click)
                self.cantidad_humanos = 2
                self.modo_actual = "MULTI"
                self.indice_seleccion_actual = 0
                self.personajes_seleccionados = {}
                self.estado = "MENU_SELECCION_PERSONAJES"
            elif self.btn_cant_3.fue_clicado(pos_m):
                self.reproducir_sonido(self.snd_click)
                self.cantidad_humanos = 3
                self.modo_actual = "MULTI"
                self.indice_seleccion_actual = 0
                self.personajes_seleccionados = {}
                self.estado = "MENU_SELECCION_PERSONAJES"
            elif self.btn_cant_4.fue_clicado(pos_m):
                self.reproducir_sonido(self.snd_click)
                self.cantidad_humanos = 4
                self.modo_actual = "MULTI"
                self.indice_seleccion_actual = 0
                self.personajes_seleccionados = {}
                self.estado = "MENU_SELECCION_PERSONAJES"
            elif self.btn_cant_volver.fue_clicado(pos_m):
                self.reproducir_sonido(self.snd_click)
                self.estado = "MENU_MODOS"

        elif self.estado == "MENU_OPCIONES":
            if self.btn_toggle_musica.fue_clicado(pos_m):
                self.reproducir_sonido(self.snd_click)
                Config.musica_activa = not Config.musica_activa
                self.btn_toggle_musica.definir_texto("MUSICA: SI" if Config.musica_activa else "MUSICA: NO")
                if Config.musica_activa:
                    self._pista_actual = None  # forzar recarga de la pista correcta
                    self.reproducir_musica(self._pista_para_estado_actual())
                else:
                    self.detener_musica()
            elif self.btn_toggle_sfx.fue_clicado(pos_m):
                Config.sfx_activo = not Config.sfx_activo
                self.reproducir_sonido(self.snd_click)
                self.btn_toggle_sfx.definir_texto("SFX: SI" if Config.sfx_activo else "SFX: NO")
            elif self.btn_reset_scores.fue_clicado(pos_m):
                self.reproducir_sonido(self.snd_click)
                self.victorias_j1 = 0
                self.victorias_j2 = 0
                self.btn_reset_scores.definir_texto("RESETEADO OK!")
                pygame.time.set_timer(pygame.USEREVENT + 1, 1000)
            elif self.btn_volver.fue_clicado(pos_m):
                self.reproducir_sonido(self.snd_click)
                self.estado = self.estado_previo_opciones

        elif self.estado == "PAUSA":
            if self.btn_reanudar.fue_clicado(pos_m):
                self.reproducir_sonido(self.snd_reanudar)
                ahora = pygame.time.get_ticks()
                delta_pausa = ahora - self.momento_pausa
                if self.estado_previo_a_pausa == "EN_JUEGO":
                    self.momento_inicio_turno += delta_pausa
                elif self.estado_previo_a_pausa == "REVELANDO_CUERDAS":
                    self.tiempo_inicio_sub_estado += delta_pausa
                elif self.estado_previo_a_pausa == "ESPERA_POST_SELECCION":
                    self.momento_pausa_post_seleccion += delta_pausa
                self.estado = self.estado_previo_a_pausa
            elif self.btn_pausa_opciones.fue_clicado(pos_m):
                self.reproducir_sonido(self.snd_click)
                self.estado_previo_opciones = "PAUSA"
                self.estado = "MENU_OPCIONES"
            elif self.btn_pausa_menu.fue_clicado(pos_m):
                self.reproducir_sonido(self.snd_click)
                self.revelado = False
                self.estado = "MENU_PRINCIPAL"

        elif self.estado == "FIN_JUEGO":
            if self.btn_reiniciar.fue_clicado(pos_m):
                self.reproducir_sonido(self.snd_click)
                if self.modo_actual == "DUELO" and self.duelo_finalizado:
                    self.victorias_j1 = 0
                    self.victorias_j2 = 0
                    self.duelo_finalizado = False
                self.indice_seleccion_actual = 0
                self.personajes_seleccionados = {}
                self.estado = "MENU_SELECCION_PERSONAJES"
            elif self.btn_fin_menu.fue_clicado(pos_m):
                self.reproducir_sonido(self.snd_click)
                self.revelado = False
                self.estado = "MENU_PRINCIPAL"

    def ejecutar(self):
        while self.ejecutando:
            pos_mouse = pygame.mouse.get_pos()
            self.actualizar_logica(pos_mouse)
            self.renderizar(pos_mouse)
            self.reloj.tick(Config.FPS)

    def actualizar_logica(self, pos_mouse):
        ahora = pygame.time.get_ticks()

        # Al entrar a un menú nuevo, la mano indicadora vuelve a la primera opción
        if self.estado != self._ultimo_estado_menu_check:
            estado_anterior = self._ultimo_estado_menu_check
            self.indice_menu_actual = 0
            self._ultimo_estado_menu_check = self.estado

            if self._pista_para_estado_actual() == "menu":
                self.reproducir_musica("menu")
                # El sonido de Kamek solo debe sonar la primera vez que se
                # entra al Menú Principal (viniendo de la Pantalla de Título),
                # no cada vez que se vuelve a él desde Opciones, Pausa, etc.
                if self.estado == "MENU_PRINCIPAL" and estado_anterior == "PANTALLA_TITULO":
                    self.reproducir_sonido(self.snd_kamek)

        if self.estado == "PANTALLA_TITULO":
            # Animación del GIF de fondo
            if self.frames_stars:
                if ahora - self.ultimo_tiempo_frame_stars >= 80:
                    self.indice_frame_stars = (self.indice_frame_stars + 1) % len(self.frames_stars)
                    self.ultimo_tiempo_frame_stars = ahora
            
            for b in self.burbujas:
                b[1] -= b[2]
                b[0] += math.sin(ahora * 0.003 + b[1] * 0.01) * 0.4
                if b[1] < -10:
                    b[0] = random.randint(10, Config.ANCHO - 10)
                    b[1] = Config.ALTO + random.randint(10, 50)
                
        elif self.estado == "MENU_PRINCIPAL":
            self.btn_jugar.actualizar(pos_mouse)
            self.btn_opciones.actualizar(pos_mouse)
            self.btn_instrucciones.actualizar(pos_mouse)
            self.btn_salir.actualizar(pos_mouse)
        elif self.estado == "INSTRUCCIONES":
            self.btn_instrucciones_volver.actualizar(pos_mouse)
        elif self.estado == "MENU_MODOS":
            self.btn_vs_cpu.actualizar(pos_mouse)
            self.btn_multi.actualizar(pos_mouse)
            self.btn_duelo.actualizar(pos_mouse)
            self.btn_volver_menu.actualizar(pos_mouse)
        elif self.estado == "SELECCION_CANTIDAD_JUGADORES":
            self.btn_cant_2.actualizar(pos_mouse)
            self.btn_cant_3.actualizar(pos_mouse)
            self.btn_cant_4.actualizar(pos_mouse)
            self.btn_cant_volver.actualizar(pos_mouse)
        elif self.estado == "MENU_SELECCION_PERSONAJES":
            # Resaltar tarjeta de personaje en 1280x720
            chars = Config.PERSONAJES
            for i in range(8):
                row = i // 4
                col = i % 4
                card_x = 140 + col * 260
                card_y = 150 + row * 260
                if pygame.Rect(card_x, card_y, 220, 220).collidepoint(pos_mouse):
                    tomado = False
                    for p_name in self.personajes_seleccionados.values():
                        if p_name == chars[i]:
                            tomado = True
                            break
                    if not tomado:
                        self.personaje_resaltado = i
        elif self.estado == "MENU_OPCIONES":
            self.btn_toggle_musica.actualizar(pos_mouse)
            self.btn_toggle_sfx.actualizar(pos_mouse)
            self.btn_reset_scores.actualizar(pos_mouse)
            self.btn_volver.actualizar(pos_mouse)
        elif self.estado == "PAUSA":
            self.btn_reanudar.actualizar(pos_mouse)
            self.btn_pausa_opciones.actualizar(pos_mouse)
            self.btn_pausa_menu.actualizar(pos_mouse)
        elif self.estado == "FIN_JUEGO":
            self.btn_reiniciar.actualizar(pos_mouse)
            self.btn_fin_menu.actualizar(pos_mouse)

        # --- SINCRONIZAR MANO INDICADORA (mouse + navegación por teclado) ---
        grupo_botones = self.obtener_grupo_botones_actual()
        if grupo_botones:
            indice_hover = next((i for i, b in enumerate(grupo_botones) if b.hover), None)
            if indice_hover is not None:
                self.indice_menu_actual = indice_hover
            for i, b in enumerate(grupo_botones):
                b.set_resaltado_teclado(i == self.indice_menu_actual)

        if self.estado in ["EN_JUEGO", "REVELANDO_CUERDAS", "ESPERA_POST_SELECCION", "FIN_JUEGO"]:
            if self.estado != "PAUSA":
                for c in self.criaturas:
                    c.actualizar()
                
                for b in self.burbujas:
                    b[1] -= b[2]
                    b[0] += math.sin(ahora * 0.003 + b[1] * 0.01) * 0.4
                    if b[1] < Config.NIVEL_AGUA:
                        b[0] = random.randint(10, Config.ANCHO - 10)
                        b[1] = Config.ALTO + random.randint(10, 50)

        if self.estado == "ESPERA_POST_SELECCION":
            if ahora - self.momento_pausa_post_seleccion >= 1500:
                self.iniciar_revelacion_dramatica(self.jugadores_vivos_para_revelar)

        elif self.estado == "REVELANDO_CUERDAS":
            transcurrido = ahora - self.tiempo_inicio_sub_estado
            j_actual = self.jugadores_en_orden_revelacion[self.indice_revelacion_actual]
            cuerda_afectada = self.cuerdas[j_actual.cuerda_elegida]
            
            if self.sub_estado_animacion == "CAMINANDO":
                x_destino = cuerda_afectada.x - Config.CHAR_ANCHO // 2
                y_destino = self.obtener_y_elipse(cuerda_afectada.x, obtener_borde_inferior=True) - (Config.CHAR_ALTO - 10)
                duracion_caminata = 800
                if transcurrido < duracion_caminata:
                    progreso = transcurrido / duracion_caminata
                    j_actual.x = self.x_original_jugador + (x_destino - self.x_original_jugador) * progreso
                    j_actual.y = self.y_original_jugador + (y_destino - self.y_original_jugador) * progreso
                else:
                    j_actual.x = x_destino
                    j_actual.y = y_destino
                    self.sub_estado_animacion = "JALANDO"
                    self.tiempo_inicio_sub_estado = pygame.time.get_ticks()
                    self.reproducir_sonido(self.snd_tension)
            
            elif self.sub_estado_animacion == "JALANDO":
                self.cuerdas_reveladas_indices.add(j_actual.cuerda_elegida)
                if transcurrido < self.duracion_animacion_jalon:
                    progreso_jalon = transcurrido / self.duracion_animacion_jalon
                    es_monstruo = cuerda_afectada.contenido != "Pez Bueno"
                    
                    if es_monstruo:
                        amplitud = 6 + int(progreso_jalon * 10)
                        velocidad_osc = 0.08 + progreso_jalon * 0.10
                    else:
                        amplitud = 5
                        velocidad_osc = 0.08
                    
                    vibracion_y = int(math.sin(transcurrido * velocidad_osc) * amplitud)
                    vibracion_x = int(math.cos(transcurrido * velocidad_osc) * (amplitud * 0.6))
                    j_actual.x = (cuerda_afectada.x - Config.CHAR_ANCHO // 2) + vibracion_x
                    j_actual.y = (self.obtener_y_elipse(cuerda_afectada.x, obtener_borde_inferior=True) - (Config.CHAR_ALTO - 10)) + vibracion_y
                    cuerda_afectada.y_fin = self.altura_reposo_cuerda + vibracion_y * 1.5
                else:
                    if cuerda_afectada.contenido == "Pez Bueno":
                        self.sub_estado_animacion = "SUBIENDO_PEZ"
                        self.reproducir_sonido(self.snd_pez)
                    else:
                        self.sub_estado_animacion = "CAYENDO"
                        self.reproducir_sonido(self.snd_derrota)
                        self.y_al_soltar = j_actual.y
                        self.sonido_ataque_reproducido = False
                    self.tiempo_inicio_sub_estado = pygame.time.get_ticks()

            elif self.sub_estado_animacion == "SUBIENDO_PEZ":
                if transcurrido < self.duracion_subida_pez:
                    progreso = transcurrido / self.duracion_subida_pez
                    y_fondo = self.altura_reposo_cuerda
                    y_superficie = Config.NIVEL_AGUA + 25
                    cuerda_afectada.y_fin = y_fondo - (y_fondo - y_superficie) * progreso
                else:
                    cuerda_afectada.y_fin = Config.NIVEL_AGUA + 25
                    self.pasar_al_siguiente_jugador()

            elif self.sub_estado_animacion == "CAYENDO":
                if transcurrido < self.duracion_caida_jugador:
                    progreso = transcurrido / self.duracion_caida_jugador
                    fase_ataque = 0.22
                    y_profundo_inicio = self.altura_reposo_cuerda
                    y_ataque = Config.NIVEL_AGUA - 15
                    y_profundo_final = self.altura_reposo_cuerda + 40
                    
                    if progreso < fase_ataque:
                        sub = progreso / fase_ataque
                        cuerda_afectada.y_fin = y_profundo_inicio + (y_ataque - y_profundo_inicio) * math.sin(sub * math.pi / 2)
                        if sub >= 0.9 and not self.sonido_ataque_reproducido:
                            self.reproducir_sonido(self.snd_splash)
                            self.sonido_ataque_reproducido = True
                    else:
                        sub = (progreso - fase_ataque) / (1 - fase_ataque)
                        cuerda_afectada.y_fin = y_ataque + (y_profundo_final - y_ataque) * sub
                    
                    distancia_caida = (self.altura_reposo_cuerda - 10) - self.y_al_soltar
                    j_actual.y = self.y_al_soltar + (distancia_caida * progreso)

                    # El personaje desaparece apenas su sprite toca la superficie del
                    # agua (no al llegar al fondo), ya que ahí lo atrapa el monstruo.
                    if not j_actual.sumergido and j_actual.y + Config.CHAR_ALTO >= Config.NIVEL_AGUA:
                        j_actual.sumergido = True
                else:
                    self.reproducir_sonido(self.snd_splash)
                    cuerda_afectada.y_fin = self.altura_reposo_cuerda
                    j_actual.vivo = False  
                    self.pasar_al_siguiente_jugador()
            
        elif self.estado == "EN_JUEGO":
            jugadores_vivos = [j for j in self.jugadores if j.vivo]
            
            if self.turno_actual < len(jugadores_vivos) and not self.revelado:
                j_actual = jugadores_vivos[self.turno_actual]
                if self.momento_inicio_turno == 0:
                    self.momento_inicio_turno = pygame.time.get_ticks()
                    self.ultimo_segundo_alerta = 5
                
                transcurrido = ahora - self.momento_inicio_turno
                self.segundos_restantes = max(0, (self.tiempo_limite - transcurrido) // 1000)
                
                if self.segundos_restantes != self.ultimo_segundo_alerta:
                    self.ultimo_segundo_alerta = self.segundos_restantes
                    if self.segundos_restantes <= 2 and self.segundos_restantes > 0 and not j_actual.es_cpu:
                        self.reproducir_sonido(self.snd_alerta)

                if not j_actual.es_cpu:
                    self.cuerda_resaltada = self.obtener_cuerda_bajo_mouse(pos_mouse)
                else:
                    self.cuerda_resaltada = None
                
                if j_actual.es_cpu:
                    if self.momento_inicio_pensamiento_cpu == 0:
                        self.momento_inicio_pensamiento_cpu = pygame.time.get_ticks()
                    if pygame.time.get_ticks() - self.momento_inicio_pensamiento_cpu >= 600:
                        self.evaluar_seleccion_jugador(j_actual, jugadores_vivos)
                        self.reproducir_sonido(self.snd_seleccion)
                
                elif transcurrido >= self.tiempo_limite:
                    self.forzar_seleccion_automatica(j_actual)
                    self.reproducir_sonido(self.snd_seleccion)
                    self.turno_actual += 1
                    self.momento_inicio_turno = 0
                    self.momento_inicio_pensamiento_cpu = 0
                    if self.turno_actual >= len(jugadores_vivos):
                        self.preparar_pausa_post_seleccion(jugadores_vivos)
            else:
                self.cuerda_resaltada = None

            try:
                cursor = pygame.SYSTEM_CURSOR_HAND if self.cuerda_resaltada is not None else pygame.SYSTEM_CURSOR_ARROW
                pygame.mouse.set_cursor(cursor)
            except Exception:
                pass

        self.manejar_eventos()

    def pasar_al_siguiente_jugador(self):
        self.indice_revelacion_actual += 1
        self.tiempo_inicio_sub_estado = pygame.time.get_ticks()
        
        if self.indice_revelacion_actual < len(self.jugadores_en_orden_revelacion):
            self.sub_estado_animacion = "CAMINANDO"
            j_sig = self.jugadores_en_orden_revelacion[self.indice_revelacion_actual]
            self.x_original_jugador = j_sig.x
            self.y_original_jugador = j_sig.y
        else:
            self.estado = "EN_JUEGO"
            self.revelado = True
            vivos_reales = [j for j in self.jugadores if j.vivo]
            
            if self.modo_actual == "DUELO":
                if len(vivos_reales) == 1:
                    ganador_set = vivos_reales[0].id
                    if ganador_set == 1: self.victorias_j1 += 1
                    else: self.victorias_j2 += 1
                    
                    if self.victorias_j1 == 2 or self.victorias_j2 == 2:
                        self.duelo_finalizado = True
                        nombre_g = self.jugadores[0].nombre if self.victorias_j1 == 2 else self.jugadores[1].nombre
                        self.mensaje_partida = f"GANADOR DEFINITIVO: {nombre_g}! [PRESIONA UNA TECLA]"
                        self.reproducir_sonido(self.snd_victoria)
                    else:
                        self.mensaje_partida = f"Set para Jugador {ganador_set}. Marcador: {self.victorias_j1}-{self.victorias_j2}. [PRESIONA UNA TECLA]"
                        self.reproducir_sonido(self.snd_victoria)
                        self.esperando_confirmacion_set = True
                elif len(vivos_reales) == 0:
                    self.muerte_subita_activa = True
                    self.mensaje_partida = "¡Empate en el Set! Muerte Súbita Activa. [PRESIONA UNA TECLA]"
                    self.reproducir_sonido(self.snd_derrota)
                    self.esperando_confirmacion_set = True
            else:
                if len(vivos_reales) == 1:
                    self.mensaje_partida = f"¡GANADOR: {vivos_reales[0].nombre}! [PRESIONA UNA TECLA]"
                    self.reproducir_sonido(self.snd_victoria)
                elif len(vivos_reales) == 0:
                    self.mensaje_partida = "¡NADIE SOBREVIVIÓ! [PRESIONA UNA TECLA]"
                    self.reproducir_sonido(self.snd_derrota)
                else:
                    self.mensaje_partida = "¡Ronda terminada! Presiona cualquier tecla para continuar"

    def obtener_cuerda_bajo_mouse(self, pos_mouse):
        mejor_idx = None
        mejor_dist = 9999
        for idx, c in enumerate(self.cuerdas):
            if c.ocupada_por is not None:
                continue
            if c.contiene_punto(pos_mouse):
                dist = abs(c.x - pos_mouse[0])
                if dist < mejor_dist:
                    mejor_dist = dist
                    mejor_idx = idx
        return mejor_idx

    def seleccionar_cuerda_para_jugador(self, idx, jugador, jugadores_vivos):
        if idx is None or not (0 <= idx < len(self.cuerdas)):
            return False
        if self.cuerdas[idx].ocupada_por is not None:
            return False
        
        self.cuerdas[idx].ocupada_por = jugador
        jugador.cuerda_elegida = idx
        self.reproducir_sonido(self.snd_seleccion)
        self.cuerda_resaltada = None
        self.turno_actual += 1
        self.momento_inicio_turno = 0
        self.momento_inicio_pensamiento_cpu = 0
        
        if self.turno_actual >= len(jugadores_vivos):
            self.preparar_pausa_post_seleccion(jugadores_vivos)
        return True

    def forzar_seleccion_automatica(self, jugador):
        cuerdas_libres = [c for c in self.cuerdas if c.ocupada_por is None]
        if cuerdas_libres:
            elegida = random.choice(cuerdas_libres)
            idx = self.cuerdas.index(elegida)
            elegida.ocupada_por = jugador
            jugador.cuerda_elegida = idx

    def evaluar_seleccion_jugador(self, j_actual, jugadores_vivos):
        self.forzar_seleccion_automatica(j_actual)
        self.turno_actual += 1
        self.momento_inicio_turno = 0
        self.momento_inicio_pensamiento_cpu = 0 
        if self.turno_actual >= len(jugadores_vivos):
            self.preparar_pausa_post_seleccion(jugadores_vivos)

    def preparar_pausa_post_seleccion(self, jugadores_vivos):
        self.estado = "ESPERA_POST_SELECCION"
        self.momento_pausa_post_seleccion = pygame.time.get_ticks()
        self.jugadores_vivos_para_revelar = jugadores_vivos

    def manejar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.ejecutando = False

            if self.estado == "MENU_OPCIONES":
                if self.slider_musica.handle_event(evento):
                    Config.volumen_musica = self.slider_musica.value
                    self.aplicar_volumen_musica()
                if self.slider_sfx.handle_event(evento):
                    Config.volumen_sfx = self.slider_sfx.value
                    self.aplicar_volumen_sfx()

            if self.estado == "PANTALLA_TITULO":
                if evento.type == pygame.KEYDOWN or (evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1):
                    self.reproducir_sonido(self.snd_click)
                    self.estado = "MENU_PRINCIPAL"
                    continue

            # CORRECCIÓN DE BUG: antes esta condición solo verificaba "self.revelado",
            # una bandera que queda en True luego de terminar una ronda y NO se
            # reiniciaba al volver a los menús (Menú Principal, Pausa, Fin de Juego, etc.).
            # Esto provocaba que, tras jugar una partida, presionar cualquier tecla en
            # esos menús ejecutara procesar_enter() por error (a veces saltando de golpe
            # a la pantalla "PARTIDA FINALIZADA"). Se restringe explícitamente a que solo
            # ocurra mientras se está EN_JUEGO, que es el único estado donde este atajo
            # de "avanzar de ronda con cualquier tecla" tiene sentido.
            if self.revelado and self.estado == "EN_JUEGO" and evento.type == pygame.KEYDOWN:
                if evento.key != pygame.K_ESCAPE and evento.key != pygame.K_F3:
                    self.reproducir_sonido(self.snd_click)
                    self.procesar_enter()
                    continue

            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                pos_m = pygame.mouse.get_pos()

                self.procesar_click_menu(pos_m)

                if self.estado == "MENU_SELECCION_PERSONAJES":
                    chars = Config.PERSONAJES
                    for i in range(8):
                        row = i // 4
                        col = i % 4
                        card_x = 140 + col * 260
                        card_y = 150 + row * 260
                        if pygame.Rect(card_x, card_y, 220, 220).collidepoint(pos_m):
                            tomado = False
                            for p_name in self.personajes_seleccionados.values():
                                if p_name == chars[i]:
                                    tomado = True
                                    break
                            if not tomado:
                                self.seleccionar_personaje_activo(chars[i])

                elif self.estado == "EN_JUEGO":
                    jugadores_vivos = [j for j in self.jugadores if j.vivo]
                    if self.turno_actual < len(jugadores_vivos) and not jugadores_vivos[self.turno_actual].es_cpu and not self.revelado:
                        idx_clic = self.obtener_cuerda_bajo_mouse(pos_m)
                        if idx_clic is not None:
                            self.seleccionar_cuerda_para_jugador(idx_clic, jugadores_vivos[self.turno_actual], jugadores_vivos)

            if evento.type == pygame.USEREVENT + 1:
                self.btn_reset_scores.definir_texto("RESETEAR MARCADOR")
                pygame.time.set_timer(pygame.USEREVENT + 1, 0)

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_F3:
                    self.mostrar_debug_fps = not self.mostrar_debug_fps

                if evento.key == pygame.K_ESCAPE:
                    if self.estado in ["EN_JUEGO", "REVELANDO_CUERDAS", "ESPERA_POST_SELECCION"]:
                        self.reproducir_sonido(self.snd_pausa)
                        self.momento_pausa = pygame.time.get_ticks()
                        self.estado_previo_a_pausa = self.estado
                        self.estado = "PAUSA"
                    elif self.estado == "PAUSA":
                        self.reproducir_sonido(self.snd_reanudar)
                        ahora = pygame.time.get_ticks()
                        delta_pausa = ahora - self.momento_pausa
                        if self.estado_previo_a_pausa == "EN_JUEGO":
                            self.momento_inicio_turno += delta_pausa
                        elif self.estado_previo_a_pausa == "REVELANDO_CUERDAS":
                            self.tiempo_inicio_sub_estado += delta_pausa
                        elif self.estado_previo_a_pausa == "ESPERA_POST_SELECCION":
                            self.momento_pausa_post_seleccion += delta_pausa
                        self.estado = self.estado_previo_a_pausa
                    elif self.estado in ["MENU_MODOS", "SELECCION_CANTIDAD_JUGADORES", "MENU_SELECCION_PERSONAJES", "MENU_OPCIONES", "INSTRUCCIONES"]:
                        self.reproducir_sonido(self.snd_click)
                        self.estado = "MENU_PRINCIPAL"
                    elif self.estado == "FIN_JUEGO":
                        self.reproducir_sonido(self.snd_click)
                        self.revelado = False
                        self.estado = "MENU_PRINCIPAL"
                    else:
                        self.reproducir_sonido(self.snd_salir)
                        self.ejecutando = False
                
                if self.estado == "MENU_SELECCION_PERSONAJES":
                    chars = Config.PERSONAJES
                    if evento.key in (pygame.K_LEFT, pygame.K_a):
                        self.reproducir_sonido(self.snd_seleccion)
                        intentos = 8
                        while intentos > 0:
                            self.personaje_resaltado = (self.personaje_resaltado - 1) % 8
                            tomado = False
                            for p_name in self.personajes_seleccionados.values():
                                if p_name == chars[self.personaje_resaltado]:
                                    tomado = True
                                    break
                            if not tomado:
                                break
                            intentos -= 1
                    elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                        self.reproducir_sonido(self.snd_seleccion)
                        intentos = 8
                        while intentos > 0:
                            self.personaje_resaltado = (self.personaje_resaltado + 1) % 8
                            tomado = False
                            for p_name in self.personajes_seleccionados.values():
                                if p_name == chars[self.personaje_resaltado]:
                                    tomado = True
                                    break
                            if not tomado:
                                break
                            intentos -= 1
                    elif evento.key in (pygame.K_UP, pygame.K_w):
                        self.reproducir_sonido(self.snd_seleccion)
                        intentos = 8
                        while intentos > 0:
                            self.personaje_resaltado = (self.personaje_resaltado - 4) % 8
                            tomado = False
                            for p_name in self.personajes_seleccionados.values():
                                if p_name == chars[self.personaje_resaltado]:
                                    tomado = True
                                    break
                            if not tomado:
                                break
                            intentos -= 1
                    elif evento.key in (pygame.K_DOWN, pygame.K_s):
                        self.reproducir_sonido(self.snd_seleccion)
                        intentos = 8
                        while intentos > 0:
                            self.personaje_resaltado = (self.personaje_resaltado + 4) % 8
                            tomado = False
                            for p_name in self.personajes_seleccionados.values():
                                if p_name == chars[self.personaje_resaltado]:
                                    tomado = True
                                    break
                            if not tomado:
                                break
                            intentos -= 1
                    elif evento.key in [pygame.K_RETURN, pygame.K_SPACE]:
                        char_name = chars[self.personaje_resaltado]
                        tomado = False
                        for p_name in self.personajes_seleccionados.values():
                            if p_name == char_name:
                                tomado = True
                                break
                        if not tomado:
                            self.seleccionar_personaje_activo(char_name)

                elif self.estado == "EN_JUEGO":
                    jugadores_vivos = [j for j in self.jugadores if j.vivo]
                    if self.turno_actual < len(jugadores_vivos) and not jugadores_vivos[self.turno_actual].es_cpu and not self.revelado:
                        idx = -1
                        if pygame.K_1 <= evento.key <= pygame.K_8:
                            idx = evento.key - pygame.K_1
                        if idx >= 0:
                            self.seleccionar_cuerda_para_jugador(idx, jugadores_vivos[self.turno_actual], jugadores_vivos)

                else:
                    # --- NAVEGACIÓN CON TECLADO EN MENÚS DE BOTONES ---
                    # Flechas mueven la mano indicadora; ENTER/ESPACIO confirma
                    # la opción resaltada (igual que un clic de mouse).
                    grupo = self.obtener_grupo_botones_actual()
                    if grupo:
                        if evento.key in (pygame.K_UP, pygame.K_LEFT, pygame.K_w, pygame.K_a):
                            self.indice_menu_actual = (self.indice_menu_actual - 1) % len(grupo)
                            self.reproducir_sonido(self.snd_seleccion)
                        elif evento.key in (pygame.K_DOWN, pygame.K_RIGHT, pygame.K_s, pygame.K_d):
                            self.indice_menu_actual = (self.indice_menu_actual + 1) % len(grupo)
                            self.reproducir_sonido(self.snd_seleccion)
                        elif evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.procesar_click_menu(grupo[self.indice_menu_actual].rect.center)

    def seleccionar_personaje_activo(self, char_name):
        self.reproducir_sonido(self.snd_click)
        self.personajes_seleccionados[self.indice_seleccion_actual] = char_name
        self.indice_seleccion_actual += 1
        
        chars = Config.PERSONAJES
        for i in range(8):
            tomado = False
            for p_name in self.personajes_seleccionados.values():
                if p_name == chars[i]:
                    tomado = True
                    break
            if not tomado:
                self.personaje_resaltado = i
                break
                
        if self.indice_seleccion_actual >= self.cantidad_humanos:
            max_players = 2 if self.modo_actual == "DUELO" else 4
            available_chars = [c for c in chars if c not in self.personajes_seleccionados.values()]
            random.shuffle(available_chars)
            
            self.jugadores = []
            for i in range(self.cantidad_humanos):
                p_char = self.personajes_seleccionados[i]
                self.jugadores.append(Jugador(i + 1, es_cpu=False, personaje=p_char))
            
            cpu_needed = max_players - self.cantidad_humanos
            for i in range(cpu_needed):
                p_char = available_chars.pop()
                self.jugadores.append(Jugador(self.cantidad_humanos + i + 1, es_cpu=True, personaje=p_char))
                
            self.reiniciar_partida_completa()

    def reiniciar_partida_completa(self):
        self.num_ronda = 1
        self.muerte_subita_activa = False
        self.cuerdas_reveladas_indices.clear()
        self.generar_ronda([j for j in self.jugadores if j.vivo], self.muerte_subita_activa)
        self.turno_actual = 0
        self.revelado = False
        self.momento_inicio_turno = 0
        self.ultimo_segundo_alerta = 5
        self.momento_inicio_pensamiento_cpu = 0
        self.mensaje_partida = ""
        self.esperando_confirmacion_set = False
        self.estado = "EN_JUEGO"
        self.reproducir_musica("duel" if self.modo_actual == "DUELO" else "game")

    def procesar_enter(self):
        vivos_reales = [j for j in self.jugadores if j.vivo]
        
        if "GANADOR DEFINITIVO:" in self.mensaje_partida or "¡GANADOR:" in self.mensaje_partida or "¡NADIE SOBREVIVIÓ!" in self.mensaje_partida:
            self.estado = "FIN_JUEGO"
            return
            
        if self.modo_actual == "DUELO" and self.esperando_confirmacion_set:
            self.esperando_confirmacion_set = False
            self.forzar_resurreccion_duelo()
            return

        if len(vivos_reales) <= 1:
            self.estado = "FIN_JUEGO"
            return

        self.num_ronda += 1
        self.cuerdas_reveladas_indices.clear()
        self.generar_ronda([j for j in self.jugadores if j.vivo], self.muerte_subita_activa)
        self.turno_actual = 0
        self.revelado = False
        self.momento_inicio_turno = 0
        self.ultimo_segundo_alerta = 5
        self.momento_inicio_pensamiento_cpu = 0
        self.mensaje_partida = ""

    def forzar_resurreccion_duelo(self):
        for j in self.jugadores:
            j.vivo = True
            j.sumergido = False
        self.num_ronda = 1
        self.cuerdas_reveladas_indices.clear()
        self.generar_ronda(self.jugadores, self.muerte_subita_activa)
        self.turno_actual = 0
        self.revelado = False
        self.momento_inicio_turno = 0
        self.ultimo_segundo_alerta = 5
        self.momento_inicio_pensamiento_cpu = 0
        self.mensaje_partida = ""

    def dibujar_fondo_marino(self):
        puntos_arena = [(0, Config.ALTO)]
        for x in range(0, Config.ANCHO + 10, 20):
            y = Config.ALTO - 45 + int(math.sin(x * 0.015) * 8)
            puntos_arena.append((x, y))
        puntos_arena.append((Config.ANCHO, Config.ALTO))
        pygame.draw.polygon(self.pantalla, (218, 165, 32), puntos_arena)
        pygame.draw.polygon(self.pantalla, (139, 90, 0), puntos_arena, width=2)
        
        for i, ax in enumerate(self.algas_x):
            tiempo = pygame.time.get_ticks() * 0.0015
            oscilacion = math.sin(tiempo + i) * 12
            
            puntos_alga = []
            altura_alga = 90 + (i % 3) * 20
            for paso in range(0, 11):
                porcentaje = paso / 10
                y = Config.ALTO - 20 - (altura_alga * porcentaje)
                desplazamiento = oscilacion * (porcentaje ** 1.5)
                desplazamiento += math.sin(porcentaje * math.pi) * 8
                puntos_alga.append((int(ax + desplazamiento), int(y)))
                
            for paso in range(len(puntos_alga) - 1):
                p1 = puntos_alga[paso]
                p2 = puntos_alga[paso + 1]
                ancho_linea = int(8 * (1.0 - (paso / len(puntos_alga)) * 0.5))
                pygame.draw.line(self.pantalla, (34, 139, 34), p1, p2, ancho_linea)

    def renderizar(self, pos_mouse):
        self.pantalla.blit(self.bg_image, (0, 0))
        
        if self.estado == "PANTALLA_TITULO":
            # Dibujar el GIF animado de fondo (si se cargó)
            if self.frames_stars:
                self.pantalla.blit(self.frames_stars[self.indice_frame_stars], (0, 0))
            
            for b in self.burbujas:
                burbuja_surf = pygame.Surface((10, 10), pygame.SRCALPHA)
                pygame.draw.circle(burbuja_surf, (255, 255, 255, 150), (5, 5), int(b[2] * 3), 1)
                pygame.draw.circle(burbuja_surf, (200, 240, 255, 60), (5, 5), int(b[2] * 3) - 1)
                self.pantalla.blit(burbuja_surf, (int(b[0] - 5), int(b[1] - 5)))
                
            t = pygame.time.get_ticks()
            
            # --- TÍTULO ESTILO MARIO PARTY ---
            # Letras gigantes que ondulan de forma independiente con múltiples colores
            texto_titulo = "CHEEP CHEEP CHANCE"
            fuente_grande = pygame.font.Font(Config.FUENTE_PRINCIPAL, 60)
            
            colores_mp = [
                (220, 20, 60),    # Rojo
                (30, 144, 255),   # Azul
                (34, 139, 34),    # Verde
                (255, 215, 0),    # Amarillo
                (138, 43, 226),   # Violeta
                (255, 140, 0),    # Naranja
                (0, 255, 255),    # Celeste
                (255, 105, 180)   # Rosa
            ]
            
            # Pre-calcular ancho total de la frase para centrarla
            ancho_total = 0
            surfs_letras = []
            for i, char in enumerate(texto_titulo):
                color = colores_mp[i % len(colores_mp)]
                surf_c = fuente_grande.render(char, True, color)
                surfs_letras.append((char, surf_c))
                ancho_total += surf_c.get_width()
                
            x_cursor = (Config.ANCHO - ancho_total) // 2
            base_y = Config.ALTO // 2 - 90
            
            for i, (char, surf_c) in enumerate(surfs_letras):
                # Calcular el desplazamiento vertical individual (onda de Mario Party)
                y_wave = math.sin(t * 0.007 + i * 0.4) * 18
                pos_y = base_y + y_wave
                
                # Sombra de la letra
                surf_shadow = fuente_grande.render(char, True, Config.NEGRO)
                self.pantalla.blit(surf_shadow, (x_cursor + 4, pos_y + 4))
                # Letra original coloreada
                self.pantalla.blit(surf_c, (x_cursor, pos_y))
                
                x_cursor += surf_c.get_width()
                
            # REMAKE parpadeante
            txt_remake = self.fuente_titulo.render("REMAKE", True, Config.BLANCO)
            if (t // 300) % 2 == 0:
                txt_remake = self.fuente_titulo.render("REMAKE", True, Config.AMARILLO)
            rect_remake = txt_remake.get_rect(center=(Config.ANCHO // 2, base_y + 90))
            
            shadow_remake = self.fuente_titulo.render("REMAKE", True, Config.NEGRO)
            rect_shadow_remake = shadow_remake.get_rect(center=(Config.ANCHO // 2 + 2, base_y + 90 + 2))
            
            self.pantalla.blit(shadow_remake, rect_shadow_remake)
            self.pantalla.blit(txt_remake, rect_remake)
            
            # Mensaje pulsante
            alpha_pulsante = int(127 + 128 * math.sin(t * 0.005))
            txt_press = self.fuente_subtitulo.render("PRESIONA CUALQUIER TECLA PARA CONTINUAR", True, Config.BLANCO)
            
            surf_press = txt_press.copy()
            surf_press.set_alpha(alpha_pulsante)
            rect_press = surf_press.get_rect(center=(Config.ANCHO // 2, Config.ALTO // 2 + 160))
            self.pantalla.blit(surf_press, rect_press)
            
        elif self.estado == "MENU_PRINCIPAL":
            capa_oscura = pygame.Surface((Config.ANCHO, Config.ALTO), pygame.SRCALPHA)
            capa_oscura.fill((10, 20, 40, 160))
            self.pantalla.blit(capa_oscura, (0, 0))
            
            txt = self.fuente_titulo.render("CHEEP CHEEP CHANCE REMAKE", True, Config.AMARILLO)
            rect_txt = txt.get_rect(center=(Config.ANCHO // 2, 120))
            self.pantalla.blit(txt, rect_txt)
            
            self.btn_jugar.dibujar(self.pantalla)
            self.btn_opciones.dibujar(self.pantalla)
            self.btn_instrucciones.dibujar(self.pantalla)
            self.btn_salir.dibujar(self.pantalla)
            
            if self.sprite_kamek:
                self.pantalla.blit(self.sprite_kamek, (Config.ANCHO - 120, Config.ALTO - 120))
            
        elif self.estado == "MENU_MODOS":
            capa_oscura = pygame.Surface((Config.ANCHO, Config.ALTO), pygame.SRCALPHA)
            capa_oscura.fill((10, 20, 40, 160))
            self.pantalla.blit(capa_oscura, (0, 0))
            
            txt = self.fuente_titulo.render("SELECCIONA UN MODO", True, Config.AMARILLO)
            rect_txt = txt.get_rect(center=(Config.ANCHO // 2, 120))
            self.pantalla.blit(txt, rect_txt)
            
            self.btn_vs_cpu.dibujar(self.pantalla)
            self.btn_multi.dibujar(self.pantalla)
            self.btn_duelo.dibujar(self.pantalla)
            self.btn_volver_menu.dibujar(self.pantalla)

        elif self.estado == "SELECCION_CANTIDAD_JUGADORES":
            capa_oscura = pygame.Surface((Config.ANCHO, Config.ALTO), pygame.SRCALPHA)
            capa_oscura.fill((10, 20, 40, 160))
            self.pantalla.blit(capa_oscura, (0, 0))
            
            txt = self.fuente_titulo.render("¿CUÁNTOS JUGADORES?", True, Config.AMARILLO)
            rect_txt = txt.get_rect(center=(Config.ANCHO // 2, 120))
            self.pantalla.blit(txt, rect_txt)
            
            self.btn_cant_2.dibujar(self.pantalla)
            self.btn_cant_3.dibujar(self.pantalla)
            self.btn_cant_4.dibujar(self.pantalla)
            self.btn_cant_volver.dibujar(self.pantalla)
            
        elif self.estado == "MENU_SELECCION_PERSONAJES":
            capa_oscura = pygame.Surface((Config.ANCHO, Config.ALTO), pygame.SRCALPHA)
            capa_oscura.fill((10, 20, 40, 200))
            self.pantalla.blit(capa_oscura, (0, 0))
            
            nombre_jugador_eligiendo = f"JUGADOR {self.indice_seleccion_actual + 1}"
            txt = self.fuente_titulo.render(f"{nombre_jugador_eligiendo}: ELIGE PERSONAJE", True, Config.AMARILLO)
            self.pantalla.blit(txt, txt.get_rect(center=(Config.ANCHO // 2, 70)))
            
            chars = Config.PERSONAJES
            
            for i, name in enumerate(chars):
                row = i // 4
                col = i % 4
                card_x = 140 + col * 260
                card_y = 150 + row * 260
                rect_card = pygame.Rect(card_x, card_y, 220, 220)
                
                seleccionado_por = None
                for idx_p, p_name in self.personajes_seleccionados.items():
                    if p_name == name:
                        seleccionado_por = idx_p
                        break
                
                rect_sombra = rect_card.copy()
                rect_sombra.x += 4
                rect_sombra.y += 4
                pygame.draw.rect(self.pantalla, (0, 0, 0, 120), rect_sombra, border_radius=12)
                
                color_bg = (50, 50, 50)
                if seleccionado_por is None:
                    color_bg = Config.COLORES_JUGADORES[i]
                
                pygame.draw.rect(self.pantalla, color_bg, rect_card, border_radius=12)
                
                if i == self.personaje_resaltado and seleccionado_por is None:
                    pygame.draw.rect(self.pantalla, Config.BLANCO, rect_card, width=4, border_radius=12)
                else:
                    pygame.draw.rect(self.pantalla, Config.NEGRO, rect_card, width=2, border_radius=12)
                
                txt_name = self.fuente_subtitulo.render(name, True, Config.NEGRO if seleccionado_por is None else Config.GRIS_CLARO)
                self.pantalla.blit(txt_name, txt_name.get_rect(center=(rect_card.centerx, rect_card.top + 25)))
                
                sprite_dibujado = False
                char_img = self.sprites_seleccion.get(name)
                if char_img is not None:
                    self.pantalla.blit(char_img, char_img.get_rect(center=(rect_card.centerx, rect_card.top + 110)))
                    sprite_dibujado = True
                
                if not sprite_dibujado:
                    cx = rect_card.centerx
                    cy = rect_card.top + 105
                    
                    c_camisa = (200, 0, 0)
                    c_overol = (10, 30, 150)
                    c_gorra = (200, 0, 0)
                    c_pelo = (100, 50, 0)
                    es_hongo = False
                    es_corona = False
                    es_yoshi = False

                    if name == "Luigi":
                        c_camisa = (0, 180, 0)
                        c_overol = (10, 30, 150)
                        c_gorra = (0, 180, 0)
                    elif name == "Wario":
                        c_camisa = (255, 215, 0)
                        c_overol = (128, 0, 128)
                        c_gorra = (255, 215, 0)
                    elif name == "Yoshi":
                        es_yoshi = True
                        c_camisa = (50, 205, 50)
                        c_overol = (255, 255, 255)
                        c_gorra = (255, 100, 0)
                    elif name == "Peach":
                        c_camisa = (255, 182, 193)
                        c_overol = (255, 105, 180)
                        c_gorra = (255, 215, 0)
                        c_pelo = (255, 220, 100)
                        es_corona = True
                    elif name == "Daisy":
                        c_camisa = (255, 215, 0)
                        c_overol = (255, 140, 0)
                        c_gorra = (255, 215, 0)
                        c_pelo = (139, 69, 19)
                        es_corona = True
                    elif name == "Waluigi":
                        c_camisa = (128, 0, 128)
                        c_overol = (40, 40, 50)
                        c_gorra = (128, 0, 128)
                    elif name == "Toad":
                        es_hongo = True
                        c_camisa = (255, 255, 255)
                        c_overol = (10, 30, 150)
                        c_gorra = (220, 20, 60)

                    if es_yoshi:
                        pygame.draw.circle(self.pantalla, (50, 205, 50), (cx, cy + 10), 24)
                        pygame.draw.circle(self.pantalla, (255, 255, 255), (cx, cy + 10), 16)
                        pygame.draw.circle(self.pantalla, (50, 205, 50), (cx, cy - 14), 16)
                        pygame.draw.ellipse(self.pantalla, (255, 255, 255), (cx - 16, cy - 18, 24, 18))
                        pygame.draw.ellipse(self.pantalla, (50, 205, 50), (cx, cy - 10, 10, 10))
                        pygame.draw.ellipse(self.pantalla, Config.BLANCO, (cx - 6, cy - 24, 8, 12))
                        pygame.draw.ellipse(self.pantalla, Config.BLANCO, (cx + 3, cy - 24, 8, 12))
                        pygame.draw.ellipse(self.pantalla, (0, 0, 255), (cx - 4, cy - 20, 4, 8))
                        pygame.draw.ellipse(self.pantalla, (0, 0, 255), (cx + 5, cy - 20, 4, 8))
                        pygame.draw.circle(self.pantalla, (200, 0, 0), (cx + 14, cy - 18), 5)
                        pygame.draw.circle(self.pantalla, (200, 0, 0), (cx + 14, cy - 8), 5)
                    elif es_hongo:
                        pygame.draw.rect(self.pantalla, (255, 255, 255), (cx - 16, cy + 10, 32, 24), border_radius=4)
                        pygame.draw.rect(self.pantalla, (10, 30, 150), (cx - 18, cy + 10, 36, 14), border_radius=3)
                        pygame.draw.circle(self.pantalla, (255, 218, 185), (cx, cy - 2), 14)
                        pygame.draw.ellipse(self.pantalla, Config.BLANCO, (cx - 30, cy - 30, 60, 38))
                        pygame.draw.ellipse(self.pantalla, Config.NEGRO, (cx - 30, cy - 30, 60, 38), 2)
                        pygame.draw.circle(self.pantalla, (220, 20, 60), (cx, cy - 20), 9)
                        pygame.draw.circle(self.pantalla, (220, 20, 60), (cx - 20, cy - 14), 7)
                        pygame.draw.circle(self.pantalla, (220, 20, 60), (cx + 20, cy - 14), 7)
                    else:
                        if es_corona:
                            pygame.draw.circle(self.pantalla, c_pelo, (cx - 16, cy), 13)
                            pygame.draw.circle(self.pantalla, c_pelo, (cx + 16, cy), 13)
                            pygame.draw.rect(self.pantalla, c_overol, (cx - 20, cy + 10, 40, 30), border_radius=6)
                            pygame.draw.circle(self.pantalla, (255, 218, 185), (cx, cy - 2), 14)
                            puntos = [(cx - 16, cy - 14), (cx - 10, cy - 24), (cx, cy - 14), (cx + 10, cy - 24), (cx + 16, cy - 14)]
                            pygame.draw.polygon(self.pantalla, c_gorra, puntos)
                            pygame.draw.polygon(self.pantalla, Config.NEGRO, puntos, 2)
                        else:
                            pygame.draw.rect(self.pantalla, c_overol, (cx - 20, cy + 10, 40, 30), border_radius=4)
                            pygame.draw.rect(self.pantalla, c_camisa, (cx - 16, cy + 2, 32, 10))
                            pygame.draw.circle(self.pantalla, (255, 218, 185), (cx, cy - 2), 14)
                            pygame.draw.ellipse(self.pantalla, c_gorra, (cx - 18, cy - 20, 36, 16))
                            pygame.draw.line(self.pantalla, c_gorra, (cx - 16, cy - 12), (cx + 16, cy - 12), 4)
                            pygame.draw.ellipse(self.pantalla, Config.NEGRO, (cx - 18, cy - 20, 36, 16), 2)
                        
                        pygame.draw.circle(self.pantalla, Config.BLANCO, (cx - 6, cy - 4), 3)
                        pygame.draw.circle(self.pantalla, Config.BLANCO, (cx + 6, cy - 4), 3)
                        pygame.draw.circle(self.pantalla, Config.NEGRO, (cx - 6, cy - 4), 1)
                        pygame.draw.circle(self.pantalla, Config.NEGRO, (cx + 6, cy - 4), 1)
                        
                        if name in ["Mario", "Luigi", "Wario", "Waluigi"]:
                            c_bigote = Config.NEGRO
                            if name == "Wario": c_bigote = (90, 50, 0)
                            pygame.draw.rect(self.pantalla, c_bigote, (cx - 8, cy + 2, 16, 4), border_radius=1)

                if seleccionado_por is not None:
                    txt_sel = self.fuente_ui.render(f"JUGADOR {seleccionado_por + 1}", True, Config.BLANCO)
                    banner_rect = pygame.Rect(card_x + 5, card_y + 175, 210, 40)
                    pygame.draw.rect(self.pantalla, (20, 20, 20, 200), banner_rect, border_radius=6)
                    self.pantalla.blit(txt_sel, txt_sel.get_rect(center=banner_rect.center))
                    
            txt_inst = self.fuente_ui.render("FLECHAS para moverte | ENTER, ESPACIO o CLIC para elegir", True, Config.BLANCO)
            self.pantalla.blit(txt_inst, txt_inst.get_rect(center=(Config.ANCHO // 2, 700)))

        elif self.estado == "MENU_OPCIONES":
            capa_oscura = pygame.Surface((Config.ANCHO, Config.ALTO), pygame.SRCALPHA)
            capa_oscura.fill((10, 20, 40, 200))
            self.pantalla.blit(capa_oscura, (0, 0))
            
            txt = self.fuente_titulo.render("OPCIONES Y CONTROLES", True, Config.AMARILLO)
            rect_txt = txt.get_rect(center=(Config.ANCHO // 2, 80))
            self.pantalla.blit(txt, rect_txt)
            
            self.btn_toggle_musica.dibujar(self.pantalla)
            self.btn_toggle_sfx.dibujar(self.pantalla)
            self.slider_musica.draw(self.pantalla, self.fuente_ui)
            self.slider_sfx.draw(self.pantalla, self.fuente_ui)
            self.btn_reset_scores.dibujar(self.pantalla)
            self.btn_volver.dibujar(self.pantalla)
            
            txt_controles = self.fuente_subtitulo.render("--- CONTROLES ---", True, Config.AMARILLO)
            self.pantalla.blit(txt_controles, txt_controles.get_rect(center=(Config.ANCHO // 2, 500)))
            
            txt_teclas = self.fuente_ui.render("Teclas del 1 al 8 o CLIC del mouse: Seleccionar cuerda", True, Config.BLANCO)
            self.pantalla.blit(txt_teclas, txt_teclas.get_rect(center=(Config.ANCHO // 2, 530)))
            
            txt_escape = self.fuente_ui.render("Tecla ESC: Pausar partida o volver atrás", True, Config.BLANCO)
            self.pantalla.blit(txt_escape, txt_escape.get_rect(center=(Config.ANCHO // 2, 558)))
            
        elif self.estado == "INSTRUCCIONES":
            capa_oscura = pygame.Surface((Config.ANCHO, Config.ALTO), pygame.SRCALPHA)
            capa_oscura.fill((10, 20, 40, 200))
            self.pantalla.blit(capa_oscura, (0, 0))
            
            txt = self.fuente_titulo.render("INSTRUCCIONES", True, Config.AMARILLO)
            self.pantalla.blit(txt, txt.get_rect(center=(Config.ANCHO // 2, 70)))
            
            lineas = [
                "Cada jugador elige un personaje y, por turnos, una cuerda.",
                "Al final de la ronda se revela qué había en cada cuerda.",
                "¡Cuidado! Si eliges una cuerda con un monstruo, quedas ELIMINADO.",
                "Si eliges una cuerda con un pez bueno, sigues en juego.",
                "Gana quien quede vivo al final de la partida.",
                "",
                "--- CONTROLES ---",
                "Flechas o WASD: moverte entre botones y personajes",
                "Teclas del 1 al 8 o CLIC del mouse: elegir una cuerda",
                "ENTER o ESPACIO: confirmar la opción resaltada",
                "Tecla ESC: pausar la partida o volver atrás",
            ]
            
            y_linea = 140
            for linea in lineas:
                if linea == "--- CONTROLES ---":
                    color_linea = Config.AMARILLO
                    fuente_linea = self.fuente_subtitulo
                elif linea == "":
                    y_linea += 20
                    continue
                else:
                    color_linea = Config.BLANCO
                    fuente_linea = self.fuente_ui
                txt_linea = fuente_linea.render(linea, True, color_linea)
                self.pantalla.blit(txt_linea, txt_linea.get_rect(center=(Config.ANCHO // 2, y_linea)))
                y_linea += 36
            
            self.btn_instrucciones_volver.dibujar(self.pantalla)
            
        elif self.estado in ["EN_JUEGO", "PAUSA", "FIN_JUEGO", "REVELANDO_CUERDAS", "ESPERA_POST_SELECCION"]:
            pygame.draw.ellipse(self.pantalla, Config.ROJO, (Config.SALV_X, Config.SALV_Y, Config.SALV_ANCHO, Config.SALV_ALTO))
            pygame.draw.ellipse(self.pantalla, Config.CELESTE_CIELO, (Config.SALV_X + 20, Config.SALV_Y + 6, Config.SALV_ANCHO - 40, Config.SALV_ALTO - 12))
            
            self.pantalla.blit(self.tinte_agua, (0, Config.NIVEL_AGUA))
            self.dibujar_fondo_marino()
            
            for c in self.criaturas:
                c.dibujar(self.pantalla)
            
            for b in self.burbujas:
                burbuja_surf = pygame.Surface((10, 10), pygame.SRCALPHA)
                pygame.draw.circle(burbuja_surf, (255, 255, 255, 150), (5, 5), int(b[2] * 3), 1)
                pygame.draw.circle(burbuja_surf, (200, 240, 255, 60), (5, 5), int(b[2] * 3) - 1)
                self.pantalla.blit(burbuja_surf, (int(b[0] - 5), int(b[1] - 5)))
            
            for idx, c in enumerate(self.cuerdas):
                en_proceso = idx in self.cuerdas_reveladas_indices
                c.dibujar(self.pantalla, self.revelado, en_proceso=en_proceso, resaltada=(idx == self.cuerda_resaltada))
            
            for j in self.jugadores: 
                j.dibujar(self.pantalla)
            
            vivos_iniciales = [j for j in self.jugadores if j.vivo]
            if self.turno_actual < len(vivos_iniciales) and self.estado == "EN_JUEGO" and not self.revelado:
                vivos_iniciales[self.turno_actual].dibujar_flecha(self.pantalla)

            # --- PANEL LATERAL REDISEÑADO PARA 1280x720 ---
            # Ubicado a la izquierda, tono marrón claro/grisáceo, y con alto
            # ajustado a la cantidad de jugadores para no tapar tanto el mar
            panel_x = 20
            panel_y = 60
            panel_w = 230
            fila_alto = 40
            panel_h = 45 + len(self.jugadores) * fila_alto + 12
            
            panel_sombra = pygame.Rect(panel_x + 3, panel_y + 3, panel_w, panel_h)
            pygame.draw.rect(self.pantalla, (0, 0, 0, 100), panel_sombra, border_radius=8)
            
            panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
            pygame.draw.rect(self.pantalla, (208, 196, 178, 225), panel_rect, border_radius=8)
            pygame.draw.rect(self.pantalla, (110, 90, 65), panel_rect, width=2, border_radius=8)
            
            txt_tit_p = self.fuente_panel.render("CUERDAS:", True, (85, 65, 45))
            self.pantalla.blit(txt_tit_p, txt_tit_p.get_rect(center=(panel_x + panel_w // 2, panel_y + 22)))
            
            pygame.draw.line(self.pantalla, (150, 135, 115), (panel_x + 10, panel_y + 38), (panel_x + panel_w - 10, panel_y + 38), 1)
            
            for idx_j, j in enumerate(self.jugadores):
                # Tonos más oscuros/saturados para que se lean bien sobre el panel claro
                char_color = Config.GRIS
                if j.personaje == "Mario": char_color = (200, 30, 30)
                elif j.personaje == "Luigi": char_color = (20, 130, 30)
                elif j.personaje == "Wario": char_color = (180, 140, 0)
                elif j.personaje == "Yoshi": char_color = (50, 150, 50)
                elif j.personaje == "Peach": char_color = (210, 80, 145)
                elif j.personaje == "Daisy": char_color = (210, 110, 0)
                elif j.personaje == "Waluigi": char_color = (110, 30, 175)
                elif j.personaje == "Toad": char_color = (30, 95, 165)
                
                nombre_mostrado = f"{j.personaje}"
                if j.es_cpu:
                    nombre_mostrado += " (CPU)"
                
                txt_j = self.fuente_panel.render(nombre_mostrado, True, char_color if j.vivo else Config.GRIS_CLARO)
                self.pantalla.blit(txt_j, (panel_x + 15, panel_y + 46 + idx_j * fila_alto))
                
                if not j.vivo:
                    txt_sel = self.fuente_panel.render("ELIMINADO", True, Config.ROJO_OSCURO)
                elif j.cuerda_elegida is not None:
                    txt_sel = self.fuente_panel.render(f"Cuerda {j.cuerda_elegida + 1}", True, Config.NEGRO)
                elif not self.revelado and self.estado == "EN_JUEGO" and idx_j < len(vivos_iniciales) and vivos_iniciales[self.turno_actual] == j:
                    if (pygame.time.get_ticks() // 400) % 2 == 0:
                        txt_sel = self.fuente_panel.render("ELIGE...", True, (170, 110, 0))
                    else:
                        txt_sel = self.fuente_panel.render("", True, (170, 110, 0))
                else:
                    txt_sel = self.fuente_panel.render("Espera...", True, Config.GRIS)
                
                self.pantalla.blit(txt_sel, (panel_x + 15, panel_y + 64 + idx_j * fila_alto))


            if self.modo_actual == "DUELO":
                tag = f"MODO DUELO | MARCADOR: {self.victorias_j1} - {self.victorias_j2}"
                if self.muerte_subita_activa: tag += " [¡MUERTE SÚBITA!]"
            else:
                tag = "MODO: MUERTE SÚBITA" if self.muerte_subita_activa else f"RONDA: {self.num_ronda}"
                
            self.pantalla.blit(self.fuente_panel.render(tag, True, Config.ROJO if self.muerte_subita_activa else Config.NEGRO), (20, 20))

            if self.turno_actual < len(vivos_iniciales) and not self.revelado:
                j_act = vivos_iniciales[self.turno_actual]
                txt_b = self.fuente_panel.render(f"Turno de: {j_act.nombre} | Tiempo: {self.segundos_restantes}s", True, Config.ROJO if self.segundos_restantes <= 2 else Config.NEGRO)
            elif not self.revelado and (self.turno_actual >= len(vivos_iniciales) or self.estado == "ESPERA_POST_SELECCION"):
                txt_b = self.fuente_panel.render("¡SELECCIÓN COMPLETADA! PREPARANDO REVELACIÓN...", True, Config.VERDE)
            else:
                txt_b = self.fuente_panel.render(self.mensaje_partida, True, Config.ROJO_OSCURO if self.revelado else Config.VERDE)
            
            self.pantalla.blit(txt_b, txt_b.get_rect(center=(Config.ANCHO // 2, 28)))
            
            # --- OVERLAY DE PAUSA ---
            if self.estado == "PAUSA":
                capa_oscura = pygame.Surface((Config.ANCHO, Config.ALTO), pygame.SRCALPHA)
                capa_oscura.fill((0, 0, 0, 160))
                self.pantalla.blit(capa_oscura, (0, 0))
                txt_pausa = self.fuente_pausa.render("JUEGO PAUSADO", True, Config.AMARILLO)
                txt_pausa_rect = txt_pausa.get_rect(center=(Config.ANCHO // 2, 210))
                self.pantalla.blit(txt_pausa, txt_pausa_rect)
                self.btn_reanudar.dibujar(self.pantalla)
                self.btn_pausa_opciones.dibujar(self.pantalla)
                self.btn_pausa_menu.dibujar(self.pantalla)
                
            # --- OVERLAY DE FIN DE JUEGO ---
            elif self.estado == "FIN_JUEGO":
                capa_oscura = pygame.Surface((Config.ANCHO, Config.ALTO), pygame.SRCALPHA)
                capa_oscura.fill((15, 20, 30, 220))
                self.pantalla.blit(capa_oscura, (0, 0))
                
                txt_fin = self.fuente_titulo.render("PARTIDA FINALIZADA", True, Config.AMARILLO)
                rect_fin = txt_fin.get_rect(center=(Config.ANCHO // 2, 180))
                self.pantalla.blit(txt_fin, rect_fin)
                
                if self.modo_actual == "DUELO":
                    texto_final_limpio = f"¡GANADOR DEFINITIVO: {self.jugadores[0].nombre if self.victorias_j1 == 2 else self.jugadores[1].nombre}!"
                else:
                    ganador_real = [j for j in self.jugadores if j.vivo]
                    texto_final_limpio = f"¡GANADOR: {ganador_real[0].nombre}!" if len(ganador_real) == 1 else "¡NADIE SOBREVIVIÓ!"
                    
                txt_res = self.fuente_subtitulo.render(texto_final_limpio, True, Config.BLANCO)
                self.pantalla.blit(txt_res, txt_res.get_rect(center=(Config.ANCHO // 2, 250)))
                
                self.btn_reiniciar.dibujar(self.pantalla)
                self.btn_fin_menu.dibujar(self.pantalla)

        if self.mostrar_debug_fps:
            fps_reales = int(self.reloj.get_fps())
            txt_fps = self.fuente_fps.render(f"FPS: {fps_reales} / {Config.FPS}", True, Config.AMARILLO)
            self.pantalla.blit(txt_fps, (15, Config.ALTO - 30))
            
        pygame.display.flip()