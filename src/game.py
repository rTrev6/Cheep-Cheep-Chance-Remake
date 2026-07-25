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
        self.fuente_titulo = pygame.font.Font(Config.FUENTE_PRINCIPAL, 44)
        self.fuente_pausa = pygame.font.Font(Config.FUENTE_PRINCIPAL, 48)
        self.fuente_subtitulo = pygame.font.Font(Config.FUENTE_PRINCIPAL, 24)
        self.fuente_ui = pygame.font.Font(Config.FUENTE_PRINCIPAL, 20)
        self.fuente_fps = pygame.font.Font(Config.FUENTE_PRINCIPAL, 18)
        # Fuente más grande para el panel lateral y banner HUD de partida
        self.fuente_panel = pygame.font.Font(Config.FUENTE_PRINCIPAL, 24)
        self.fuente_hud_banner = pygame.font.Font(Config.FUENTE_PRINCIPAL, 28)
        self.fuente_fases_grandes = pygame.font.Font(Config.FUENTE_PRINCIPAL, 34)
        
        # --- CARGAR SONIDOS SINTETIZADOS RETRO Y MÚSICA DE FONDO ---
        self.cargar_sonidos()
        self.reproducir_musica()
        
        # --- CARGAR FONDOS DE PANTALLA DUALES (SUPERFICIE Y SUBMARINO) ---
        try:
            raw_top = pygame.image.load(str(Config.SPRITE_BACKGROUND_TOP)).convert()
            self.bg_image_top = pygame.transform.scale(raw_top, (Config.ANCHO, Config.NIVEL_AGUA))
        except Exception as e:
            print(f"Error cargando fondo superior: {e}")
            self.bg_image_top = pygame.Surface((Config.ANCHO, Config.NIVEL_AGUA))
            self.bg_image_top.fill(Config.CELESTE_CIELO)

        try:
            alto_bottom = Config.ALTO - Config.NIVEL_AGUA
            raw_bot = pygame.image.load(str(Config.SPRITE_BACKGROUND_BOTTOM)).convert()
            self.bg_image_bottom = pygame.transform.scale(raw_bot, (Config.ANCHO, alto_bottom))
        except Exception as e:
            print(f"Error cargando fondo inferior: {e}")
            self.bg_image_bottom = pygame.Surface((Config.ANCHO, Config.ALTO - Config.NIVEL_AGUA))
            self.bg_image_bottom.fill(Config.AZUL_MAR)

        # --- CARGAR TEXTURA PERSONALIZADA DE PLATAFORMA ---
        self.sprite_platform = None
        path_plat = Config.SPRITE_PLATFORM
        if not path_plat.exists() and Config.RUTA_IMAGENES.exists():
            for f in Config.RUTA_IMAGENES.iterdir():
                if f.is_file() and f.name.lower() in ("platform_texture.png", "plataforma.png", "salvavidas.png"):
                    path_plat = f
                    break
        if path_plat.exists():
            try:
                img_p = pygame.image.load(str(path_plat)).convert_alpha()
                self.sprite_platform = pygame.transform.scale(img_p, (Config.SALV_ANCHO, Config.SALV_ALTO))
            except Exception as e:
                print(f"Error cargando textura de plataforma: {e}")

        # --- CARGAR TEXTURA DE BORDE DE PLATAFORMA (border_texture.png) ---
        self.sprite_border_texture = None
        path_border = Config.SPRITE_BORDER_TEXTURE
        if not path_border.exists() and Config.RUTA_IMAGENES.exists():
            for f in Config.RUTA_IMAGENES.iterdir():
                if f.is_file() and f.name.lower() == "border_texture.png":
                    path_border = f
                    break
        if path_border.exists():
            try:
                img_b = pygame.image.load(str(path_border)).convert_alpha()
                self.sprite_border_texture = pygame.transform.scale(img_b, (Config.SALV_ANCHO, 30))
            except Exception as e:
                print(f"Error cargando textura de borde: {e}")

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

        # --- CARGAR IMÁGENES DE CONTROLES (ctrl_*.png) PARA LA PANTALLA DE INSTRUCCIONES ---
        self.img_ctrl_wasd = None
        self.img_ctrl_arrow = None
        self.img_ctrl_mouse = None
        try:
            p_wasd = Config.RUTA_IMAGENES / "ctrl_wasd.png"
            if p_wasd.exists():
                raw = pygame.image.load(str(p_wasd)).convert_alpha()
                ancho = int(raw.get_width() * (85 / raw.get_height()))
                self.img_ctrl_wasd = pygame.transform.scale(raw, (ancho, 85))
        except Exception as e:
            print(f"Error cargando ctrl_wasd.png: {e}")

        try:
            p_arrow = Config.RUTA_IMAGENES / "ctrl_arrow.png"
            if p_arrow.exists():
                raw = pygame.image.load(str(p_arrow)).convert_alpha()
                ancho = int(raw.get_width() * (85 / raw.get_height()))
                self.img_ctrl_arrow = pygame.transform.scale(raw, (ancho, 85))
        except Exception as e:
            print(f"Error cargando ctrl_arrow.png: {e}")

        try:
            p_mouse = Config.RUTA_IMAGENES / "ctrl_mouse.png"
            if p_mouse.exists():
                raw = pygame.image.load(str(p_mouse)).convert_alpha()
                ancho = int(raw.get_width() * (95 / raw.get_height()))
                self.img_ctrl_mouse = pygame.transform.scale(raw, (ancho, 95))
        except Exception as e:
            print(f"Error cargando ctrl_mouse.png: {e}")

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
        for _ in range(8):
            self.criaturas.append(CriaturaAmbiental(str(Config.SPRITE_FISH_LEFT), str(Config.SPRITE_FISH_RIGHT), es_pez=True))
        for _ in range(4):
            self.criaturas.append(CriaturaAmbiental(str(Config.SPRITE_MONSTER_LEFT), str(Config.SPRITE_MONSTER_RIGHT), es_pez=False, escala_factor=1.0))
        for _ in range(4):
            self.criaturas.append(CriaturaAmbiental(str(Config.SPRITE_MONSTER2_LEFT), str(Config.SPRITE_MONSTER2_RIGHT), es_pez=False, escala_factor=1.0))
            
        # --- BURBUJAS Y ALGAS ---
        self.burbujas = [[random.randint(10, Config.ANCHO - 10), random.randint(Config.NIVEL_AGUA, Config.ALTO), random.uniform(0.5, 1.5)] for _ in range(12)]
        # Distribuir algas sobre la resolución 1280
        self.algas_x = [80, 220, 380, 540, 700, 860, 1020, 1180]

        # --- BOTONES DINÁMICAMENTE CENTRADOS ---
        btn_w = 340
        btn_h = 52
        cx = (Config.ANCHO - btn_w) // 2
        
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
        
        # --- BOTONES Y SLIDERS: PANTALLA DE OPCIONES ---
        self.btn_toggle_musica = Boton(cx, 160, btn_w, btn_h, "MUSICA: SI" if Config.musica_activa else "MUSICA: NO", Config.VERDE, Config.VERDE_REMANSO)
        self.slider_musica = Slider(cx, 250, btn_w, 16, Config.volumen_musica, "VOLUMEN MUSICA")
        self.btn_toggle_sfx = Boton(cx, 325, btn_w, btn_h, "SFX: SI" if Config.sfx_activo else "SFX: NO", Config.VERDE, Config.VERDE_REMANSO)
        self.slider_sfx = Slider(cx, 415, btn_w, 16, Config.volumen_sfx, "VOLUMEN EFECTOS")
        self.btn_volver = Boton(cx, 530, btn_w, btn_h, "VOLVER", Config.GRIS, Config.GRIS_CLARO)
        
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
        self.duracion_animacion_jalon = 3800  # Animación lenta y dramática de 3.8s para máximo suspenso
        self.duracion_subida_pez = 1200       
        self.duracion_caida_jugador = 2000    
        self.x_original_jugador = 0
        self.y_original_jugador = 0
        self.angulo_original_jugador = 0.0
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
        self.siguiente_set_muerte_subita = False

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
        self.modo_entrada = "TECLADO"  # "TECLADO" o "MOUSE" (evita que el mouse inmóvil interfiera)
        self._ultimo_estado_menu_check = self.estado
        self.mensaje_mute_tiempo = 0
        self.mensaje_mute_texto = ""

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
        self.snd_alerta = self._cargar_sfx_real("sfx_hurry.mp3", volumen=0.5)
        self.snd_victoria = self._cargar_sfx_real("sfx_victory.mp3")
        self.snd_derrota = self._cargar_sfx_real("sfx_lose.mp3")
        self.snd_pausa = self._cargar_sfx_real("sfx_pause.mp3")
        self.snd_reanudar = self._cargar_sfx_real("sfx_unpause.mp3")
        self.snd_salir = self._cargar_sfx_real("sfx_exit_game.mp3")
        self.snd_kamek = None

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
        mult = 0.45 if self._pista_actual in ("game", "duel") else 1.0
        pygame.mixer.music.set_volume(Config.volumen_musica * mult)

    def reproducir_sonido(self, sonido):
        if Config.sfx_activo and sonido:
            sonido.play()

    def toggle_silencio_global(self):
        """Alterna el silencio global (MUTE / UNMUTE) para Música y SFX desde cualquier pantalla con F1."""
        estaba_activo = Config.musica_activa or Config.sfx_activo
        nuevo_estado = not estaba_activo
        
        Config.musica_activa = nuevo_estado
        Config.sfx_activo = nuevo_estado

        if hasattr(self, 'btn_toggle_musica') and self.btn_toggle_musica:
            self.btn_toggle_musica.definir_texto("MUSICA: SI" if Config.musica_activa else "MUSICA: NO")
        if hasattr(self, 'btn_toggle_sfx') and self.btn_toggle_sfx:
            self.btn_toggle_sfx.definir_texto("SFX: SI" if Config.sfx_activo else "SFX: NO")

        if Config.musica_activa:
            self.reproducir_sonido(self.snd_click)
            self._pista_actual = None
            pista = self._pista_para_estado_actual()
            if self.estado not in ("FIN_JUEGO",):
                self.reproducir_musica(pista)
        else:
            self.detener_musica()

        self.mensaje_mute_tiempo = pygame.time.get_ticks()
        self.mensaje_mute_texto = "SONIDO: SILENCIADO (MUTE)" if not nuevo_estado else "SONIDO: ACTIVADO"

    def reproducir_musica(self, pista="menu"):
        """Reproduce la pista de música real indicada ('menu', 'game' o 'duel')."""
        if not Config.musica_activa:
            return
        archivos_musica = {
            "menu": "music_menu.mp3",
            "game": "music_game.mp3",
            "duel": "music_duel.mp3",
        }
        if pista not in archivos_musica:
            return
        if self._pista_actual == pista:
            return
        ruta = Config.RUTA_SONIDOS / archivos_musica[pista]
        try:
            pygame.mixer.music.load(str(ruta))
            mult = 0.45 if pista in ("game", "duel") else 1.0
            pygame.mixer.music.set_volume(Config.volumen_musica * mult)
            pygame.mixer.music.play(loops=-1)
            self._pista_actual = pista
        except Exception as e:
            print(f"No se pudo cargar la música '{pista}': {e}")

    def detener_musica(self):
        pygame.mixer.music.stop()
        self._pista_actual = None

    def salir_del_juego(self):
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
                print(f"Error reproduciendo sfx_exit_game: {e}")
        self.ejecutando = False

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
            self.angulo_original_jugador = j_primero.angulo_actual
            self.y_al_soltar = 0

    def obtener_posicion_en_anillo(self, angulo):
        """Devuelve las coordenadas (x, y) del sprite de un jugador sobre el anillo salvavidas
        correspondiente al ángulo especificado (en radianes)."""
        cx = Config.SALV_X + Config.SALV_ANCHO // 2
        cy = Config.SALV_Y + Config.SALV_ALTO // 2
        rx = Config.SALV_ANCHO // 2 - 25
        ry = Config.SALV_ALTO // 2 - 18
        
        pos_x = cx + rx * math.cos(angulo) - Config.CHAR_ANCHO // 2
        pos_y = cy + ry * math.sin(angulo) - (Config.CHAR_ALTO - 6)
        return pos_x, pos_y

    def obtener_angulo_cuerda(self, x_cuerda):
        """Devuelve el ángulo en la elipse frontal (borde inferior) correspondiente a la posición X de una cuerda."""
        cx = Config.SALV_X + Config.SALV_ANCHO // 2
        rx = Config.SALV_ANCHO // 2 - 25
        diff_x = max(-1.0, min(1.0, (x_cuerda - cx) / rx))
        return math.acos(diff_x)

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
        
        cant_monstruos = 1 if muerte_subita else num_jugadores
        monstruos = [random.choice(["Monstruo 1", "Monstruo 2"]) for _ in range(cant_monstruos)]
        destinos = ["Pez Bueno"] * (1 if muerte_subita else num_jugadores) + monstruos
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
            
        # Distribución circular de los personajes a lo largo del arco trasero del salvavidas (estilo Mario Party)
        if num_jugadores == 1:
            angulos_inicio = [3 * math.pi / 2]
        else:
            ang_inicio = math.pi + 0.35
            ang_fin = 2 * math.pi - 0.35
            paso = (ang_fin - ang_inicio) / (num_jugadores - 1)
            angulos_inicio = [ang_inicio + idx * paso for idx in range(num_jugadores)]

        for idx, j in enumerate(jugadores_vivos):
            ang = angulos_inicio[idx]
            j.angulo_actual = ang
            px, py = self.obtener_posicion_en_anillo(ang)
            j.x = px
            j.y = py
            j.cuerda_elegida = None

    def obtener_grupo_botones_actual(self):
        """Devuelve la lista ordenada (de arriba a abajo) de botones del menú
        actual, usada tanto para sincronizar la mano indicadora como para la
        navegación con teclado (flechas + ENTER/ESPACIO)."""
        mapa = {
            "MENU_PRINCIPAL": [self.btn_jugar, self.btn_opciones, self.btn_instrucciones, self.btn_salir],
            "MENU_MODOS": [self.btn_vs_cpu, self.btn_multi, self.btn_duelo, self.btn_volver_menu],
            "SELECCION_CANTIDAD_JUGADORES": [self.btn_cant_2, self.btn_cant_3, self.btn_cant_4, self.btn_cant_volver],
            "MENU_OPCIONES": [self.btn_toggle_musica, self.slider_musica, self.btn_toggle_sfx, self.slider_sfx, self.btn_volver],
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
                self.salir_del_juego()

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
            # Resaltar tarjeta de personaje solo si el usuario movió el mouse
            if self.modo_entrada == "MOUSE":
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
            self.slider_musica.actualizar(pos_mouse)
            self.btn_toggle_sfx.actualizar(pos_mouse)
            self.slider_sfx.actualizar(pos_mouse)
            self.btn_volver.actualizar(pos_mouse)
        elif self.estado == "PAUSA":
            self.btn_reanudar.actualizar(pos_mouse)
            self.btn_pausa_opciones.actualizar(pos_mouse)
            self.btn_pausa_menu.actualizar(pos_mouse)
        elif self.estado == "FIN_JUEGO":
            self.btn_reiniciar.actualizar(pos_mouse)
            self.btn_fin_menu.actualizar(pos_mouse)

        # --- SINCRONIZAR MANO INDICADORA (mouse activo vs navegación por teclado) ---
        grupo_botones = self.obtener_grupo_botones_actual()
        if grupo_botones:
            if self.modo_entrada == "MOUSE":
                indice_hover = next((i for i, b in enumerate(grupo_botones) if b.hover), None)
                if indice_hover is not None:
                    self.indice_menu_actual = indice_hover
            
            self.indice_menu_actual = max(0, min(self.indice_menu_actual, len(grupo_botones) - 1))
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
                ang_destino = self.obtener_angulo_cuerda(cuerda_afectada.x)
                ang_inicio = self.angulo_original_jugador
                duracion_caminata = 1000
                if transcurrido < duracion_caminata:
                    progreso = transcurrido / duracion_caminata
                    diff_ang = (ang_destino - ang_inicio) % (2 * math.pi)
                    if diff_ang > math.pi:
                        diff_ang -= 2 * math.pi
                    ang_actual = ang_inicio + diff_ang * progreso
                    px, py = self.obtener_posicion_en_anillo(ang_actual)
                    # Brincos rítmicos al caminar estilo Mario Party
                    bamboleo_pasos = abs(math.sin(progreso * math.pi * 6)) * 14
                    j_actual.x = px
                    j_actual.y = py - bamboleo_pasos
                    j_actual.angulo_actual = ang_actual
                else:
                    px, py = self.obtener_posicion_en_anillo(ang_destino)
                    j_actual.x = px
                    j_actual.y = py
                    j_actual.angulo_actual = ang_destino
                    self.sub_estado_animacion = "JALANDO"
                    self.tiempo_inicio_sub_estado = pygame.time.get_ticks()
                    self.reproducir_sonido(self.snd_tension)
            
            elif self.sub_estado_animacion == "JALANDO":
                # SUSPENSO: Durante los 4 tirones NO se revela la recompensa bajo el agua.
                if transcurrido < self.duracion_animacion_jalon:
                    progreso_jalon = transcurrido / self.duracion_animacion_jalon
                    
                    # 4 tirones intensos y pausados con gran suspenso
                    num_tirones = 4
                    fase_tiron = progreso_jalon * num_tirones
                    progreso_sub = fase_tiron - int(fase_tiron)
                    
                    # Curva de esfuerzo pesado (tira hacia atrás y suelta ligeramente)
                    fuerza_y = math.sin(progreso_sub * math.pi) * 12
                    fuerza_x = math.cos(progreso_sub * math.pi) * 5
                    
                    ang_cuerda = self.obtener_angulo_cuerda(cuerda_afectada.x)
                    px, py = self.obtener_posicion_en_anillo(ang_cuerda)
                    j_actual.x = px + fuerza_x
                    j_actual.y = py + fuerza_y
                    cuerda_afectada.y_fin = self.altura_reposo_cuerda + fuerza_y * 0.8
                else:
                    # REVELACIÓN: Al completar los 4 tirones de suspenso, se revela el item
                    self.cuerdas_reveladas_indices.add(j_actual.cuerda_elegida)
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
                    y_superficie = Config.NIVEL_AGUA + 60
                    cuerda_afectada.y_fin = y_fondo - (y_fondo - y_superficie) * progreso
                    # Salto festivo del personaje al pescar un Pez Bueno
                    bamboleo_vic = abs(math.sin(progreso * math.pi * 4)) * 10
                    ang_cuerda = self.obtener_angulo_cuerda(cuerda_afectada.x)
                    px, py = self.obtener_posicion_en_anillo(ang_cuerda)
                    j_actual.x = px
                    j_actual.y = py - bamboleo_vic
                else:
                    cuerda_afectada.y_fin = Config.NIVEL_AGUA + 60
                    cuerda_afectada.atrapado = True
                    self.pasar_al_siguiente_jugador()

            elif self.sub_estado_animacion == "CAYENDO":
                if transcurrido < self.duracion_caida_jugador:
                    progreso = transcurrido / self.duracion_caida_jugador
                    fase_monstruo = 0.35  # Primeros 35% del tiempo: el monstruo sube y cae de regreso al mar
                    
                    y_profundo_inicio = self.altura_reposo_cuerda
                    y_ataque = Config.NIVEL_AGUA + 30
                    
                    ang_cuerda = self.obtener_angulo_cuerda(cuerda_afectada.x)
                    px, py = self.obtener_posicion_en_anillo(ang_cuerda)
                    
                    if progreso < fase_monstruo:
                        # Fase 1: El monstruo sale del agua a morder y vuelve a caer al fondo del mar
                        sub = progreso / fase_monstruo
                        altura_sinus = math.sin(sub * math.pi)
                        cuerda_afectada.y_fin = y_profundo_inicio - (y_profundo_inicio - y_ataque) * altura_sinus
                        
                        if sub >= 0.4 and not self.sonido_ataque_reproducido:
                            self.reproducir_sonido(self.snd_splash)
                            self.sonido_ataque_reproducido = True
                        
                        # El personaje tiembla asustado exactamente en su posición del salvavidas
                        sacudida_caida = math.sin(transcurrido * 0.03) * 4
                        j_actual.x = px + sacudida_caida
                        j_actual.y = py
                    else:
                        # Fase 2: El monstruo ya cayó al mar. El personaje cae visiblemente hacia el agua a velocidad mediana
                        cuerda_afectada.y_fin = self.altura_reposo_cuerda
                        sub = (progreso - fase_monstruo) / (1.0 - fase_monstruo)
                        
                        distancia_caida = (Config.NIVEL_AGUA + 80) - py
                        sacudida_caida = math.sin(transcurrido * 0.015) * 3
                        j_actual.x = px + sacudida_caida
                        j_actual.y = py + (distancia_caida * (sub ** 1.4))
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
                    if self.segundos_restantes == 2 and not j_actual.es_cpu:
                        if Config.sfx_activo and self.snd_alerta:
                            self.snd_alerta.stop()
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
        
        # Resetear altura de cuerdas NO pescadas para que permanezcan en el fondo,
        # pero MANTENER ARRIBA las cuerdas que ya fueron pescadas exitosamente (c.atrapado == True).
        for c in self.cuerdas:
            if not c.atrapado:
                c.y_fin = self.altura_reposo_cuerda
            else:
                c.y_fin = Config.NIVEL_AGUA + 60

        if self.indice_revelacion_actual < len(self.jugadores_en_orden_revelacion):
            self.sub_estado_animacion = "CAMINANDO"
            j_sig = self.jugadores_en_orden_revelacion[self.indice_revelacion_actual]
            self.x_original_jugador = j_sig.x
            self.y_original_jugador = j_sig.y
            self.angulo_original_jugador = j_sig.angulo_actual
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
                        self.mensaje_partida = f"GANADOR DEFINITIVO: {nombre_g}!"
                        self.detener_musica()
                        self.reproducir_sonido(self.snd_victoria)
                        self.estado = "FIN_JUEGO"
                    else:
                        self.mensaje_partida = f"¡Set para Jugador {ganador_set}! Marcador: {self.victorias_j1} - {self.victorias_j2}  [Haz clic para continuar]"
                        self.detener_musica()
                        self.reproducir_sonido(self.snd_victoria)
                        self.esperando_confirmacion_set = True
                        self.siguiente_set_muerte_subita = False
                elif len(vivos_reales) == 0:
                    if self.victorias_j1 == 1 and self.victorias_j2 == 1:
                        self.muerte_subita_activa = True
                        self.siguiente_set_muerte_subita = True
                        self.mensaje_partida = "¡Empate a 1-1! Muerte Súbita Activa  [Haz clic para continuar]"
                    else:
                        self.muerte_subita_activa = False
                        self.siguiente_set_muerte_subita = False
                        self.mensaje_partida = f"¡Empate en el Set! Marcador: {self.victorias_j1} - {self.victorias_j2}  [Haz clic para continuar]"
                    self.detener_musica()
                    self.reproducir_sonido(self.snd_derrota)
                    self.esperando_confirmacion_set = True
                else:
                    self.mensaje_partida = "¡Ronda terminada! Haz clic o presiona una tecla para continuar"
            else:
                if len(vivos_reales) == 1:
                    self.mensaje_partida = f"¡GANADOR: {vivos_reales[0].nombre}!"
                    self.detener_musica()
                    self.reproducir_sonido(self.snd_victoria)
                    self.estado = "FIN_JUEGO"
                elif len(vivos_reales) == 0:
                    self.mensaje_partida = "¡NADIE SOBREVIVIÓ!"
                    self.detener_musica()
                    self.reproducir_sonido(self.snd_derrota)
                    self.estado = "FIN_JUEGO"
                else:
                    self.mensaje_partida = "¡Ronda terminada! Haz clic o presiona una tecla para continuar"

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
                self.salir_del_juego()

            if evento.type == pygame.MOUSEMOTION:
                if evento.rel != (0, 0):
                    self.modo_entrada = "MOUSE"
            elif evento.type == pygame.KEYDOWN:
                self.modo_entrada = "TECLADO"

            if self.estado == "MENU_OPCIONES":
                if self.slider_musica.handle_event(evento):
                    Config.volumen_musica = self.slider_musica.value
                    self.aplicar_volumen_musica()
                if self.slider_sfx.handle_event(evento):
                    Config.volumen_sfx = self.slider_sfx.value
                    self.aplicar_volumen_sfx()

            teclas_reservadas = (
                pygame.K_ESCAPE, pygame.K_F1, pygame.K_F2, pygame.K_F3, pygame.K_F4,
                pygame.K_F5, pygame.K_F6, pygame.K_F7, pygame.K_F8, pygame.K_F9,
                pygame.K_F10, pygame.K_F11, pygame.K_F12
            )

            if self.estado == "PANTALLA_TITULO":
                es_tecla = (evento.type == pygame.KEYDOWN and evento.key not in teclas_reservadas)
                es_clic = (evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1)
                if es_tecla or es_clic:
                    self.reproducir_sonido(self.snd_click)
                    self.estado = "MENU_PRINCIPAL"
                    continue

            if self.revelado and self.estado == "EN_JUEGO":
                es_tecla = (evento.type == pygame.KEYDOWN and evento.key not in teclas_reservadas)
                es_clic = (evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1)
                if es_tecla or es_clic:
                    self.reproducir_sonido(self.snd_click)
                    self.procesar_enter()
                    continue

            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                pos_m = pygame.mouse.get_pos()

                estado_antes_click = self.estado
                self.procesar_click_menu(pos_m)

                if self.estado == estado_antes_click:
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

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_F1:
                    self.toggle_silencio_global()
                elif evento.key == pygame.K_F3:
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
                    elif self.estado == "MENU_OPCIONES":
                        self.reproducir_sonido(self.snd_click)
                        self.estado = self.estado_previo_opciones
                    elif self.estado in ["MENU_MODOS", "SELECCION_CANTIDAD_JUGADORES", "MENU_SELECCION_PERSONAJES", "INSTRUCCIONES"]:
                        self.reproducir_sonido(self.snd_click)
                        self.estado = "MENU_PRINCIPAL"
                    elif self.estado == "FIN_JUEGO":
                        self.reproducir_sonido(self.snd_click)
                        self.revelado = False
                        self.estado = "MENU_PRINCIPAL"
                    else:
                        self.salir_del_juego()
                
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
                    # --- NAVEGACIÓN CON TECLADO EN MENÚS DE BOTONES Y SLIDERS ---
                    grupo = self.obtener_grupo_botones_actual()
                    if grupo:
                        self.indice_menu_actual = max(0, min(self.indice_menu_actual, len(grupo) - 1))
                        elem_actual = grupo[self.indice_menu_actual]
                        
                        if evento.key in (pygame.K_UP, pygame.K_w):
                            self.indice_menu_actual = (self.indice_menu_actual - 1) % len(grupo)
                            self.reproducir_sonido(self.snd_seleccion)
                        elif evento.key in (pygame.K_DOWN, pygame.K_s):
                            self.indice_menu_actual = (self.indice_menu_actual + 1) % len(grupo)
                            self.reproducir_sonido(self.snd_seleccion)
                        elif self.estado == "MENU_OPCIONES" and evento.key in (pygame.K_LEFT, pygame.K_a, pygame.K_MINUS, pygame.K_KP_MINUS):
                            if elem_actual == self.slider_musica:
                                if self.slider_musica.modificar_valor(-0.05):
                                    Config.volumen_musica = self.slider_musica.value
                                    self.aplicar_volumen_musica()
                                    self.reproducir_sonido(self.snd_seleccion)
                            elif elem_actual == self.slider_sfx:
                                if self.slider_sfx.modificar_valor(-0.05):
                                    Config.volumen_sfx = self.slider_sfx.value
                                    self.aplicar_volumen_sfx()
                                    self.reproducir_sonido(self.snd_seleccion)
                            else:
                                self.indice_menu_actual = (self.indice_menu_actual - 1) % len(grupo)
                                self.reproducir_sonido(self.snd_seleccion)
                        elif self.estado == "MENU_OPCIONES" and evento.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS):
                            if elem_actual == self.slider_musica:
                                if self.slider_musica.modificar_valor(0.05):
                                    Config.volumen_musica = self.slider_musica.value
                                    self.aplicar_volumen_musica()
                                    self.reproducir_sonido(self.snd_seleccion)
                            elif elem_actual == self.slider_sfx:
                                if self.slider_sfx.modificar_valor(0.05):
                                    Config.volumen_sfx = self.slider_sfx.value
                                    self.aplicar_volumen_sfx()
                                    self.reproducir_sonido(self.snd_seleccion)
                            else:
                                self.indice_menu_actual = (self.indice_menu_actual + 1) % len(grupo)
                                self.reproducir_sonido(self.snd_seleccion)
                        elif evento.key not in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d) and evento.key in (pygame.K_UP, pygame.K_LEFT, pygame.K_w, pygame.K_a):
                            self.indice_menu_actual = (self.indice_menu_actual - 1) % len(grupo)
                            self.reproducir_sonido(self.snd_seleccion)
                        elif evento.key in (pygame.K_LEFT, pygame.K_a):
                            self.indice_menu_actual = (self.indice_menu_actual - 1) % len(grupo)
                            self.reproducir_sonido(self.snd_seleccion)
                        elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                            self.indice_menu_actual = (self.indice_menu_actual + 1) % len(grupo)
                            self.reproducir_sonido(self.snd_seleccion)
                        elif evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                            if hasattr(elem_actual, 'rect'):
                                self.procesar_click_menu(elem_actual.rect.center)

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
        self.siguiente_set_muerte_subita = False
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
        if getattr(self, 'siguiente_set_muerte_subita', False):
            self.muerte_subita_activa = True
        else:
            self.muerte_subita_activa = False
        self.generar_ronda(self.jugadores, self.muerte_subita_activa)
        self.turno_actual = 0
        self.revelado = False
        self.momento_inicio_turno = 0
        self.ultimo_segundo_alerta = 5
        self.momento_inicio_pensamiento_cpu = 0
    def dibujar_plataforma_modular(self):
        """Dibuja la plataforma circular/elíptica de 430x175 px con la textura de borde incorporada claramente visible."""
        if self.sprite_platform:
            self.pantalla.blit(self.sprite_platform, (Config.SALV_X, Config.SALV_Y))
            return

        w = Config.SALV_ANCHO
        h = Config.SALV_ALTO
        cx = Config.SALV_X + w // 2
        cy = Config.SALV_Y + h // 2
        
        # 1. Base / Borde 3D inferior bajo el agua (Efecto de volumen náutico)
        profundidad_3d = 14
        for offset_y in range(profundidad_3d, 0, -2):
            grosor_color = (130, 20, 20) if offset_y > 6 else (170, 30, 30)
            pygame.draw.ellipse(self.pantalla, grosor_color, (Config.SALV_X, Config.SALV_Y + offset_y, w, h))

        # 2. Anillo exterior circular sólido (Rojo Mario)
        rect_ext = pygame.Rect(Config.SALV_X, Config.SALV_Y, w, h)
        pygame.draw.ellipse(self.pantalla, (215, 40, 40), rect_ext)
        pygame.draw.ellipse(self.pantalla, Config.NEGRO, rect_ext, width=3)

        # 3. Franja decorativa circular blanca (Salvavidas Mario Party)
        m_x = 24
        m_y = 15
        rect_franja = pygame.Rect(Config.SALV_X + m_x, Config.SALV_Y + m_y, w - m_x * 2, h - m_y * 2)
        pygame.draw.ellipse(self.pantalla, (245, 245, 245), rect_franja, width=12)

        # 4. Relleno interior uniforme del piso (Tono cálido pulido sin agujeros huecos)
        p_x = 36
        p_y = 22
        rect_piso = pygame.Rect(Config.SALV_X + p_x, Config.SALV_Y + p_y, w - p_x * 2, h - p_y * 2)
        pygame.draw.ellipse(self.pantalla, (190, 40, 40), rect_piso)
        pygame.draw.ellipse(self.pantalla, (140, 25, 25), rect_piso, width=2)

        # 5. TEXTURA DE BORDE (border_texture.png): Renderizada AL FINAL sobre el borde frontal para máxima visibilidad
        if self.sprite_border_texture:
            b_w = Config.SALV_ANCHO
            b_h = int(self.sprite_border_texture.get_height() * (b_w / self.sprite_border_texture.get_width()))
            tex_escalada = pygame.transform.scale(self.sprite_border_texture, (b_w, max(25, b_h)))
            
            pos_x = Config.SALV_X
            pos_y = Config.SALV_Y + (h // 2) - 5
            self.pantalla.blit(tex_escalada, (pos_x, pos_y))
            pygame.draw.arc(self.pantalla, Config.NEGRO, (Config.SALV_X, Config.SALV_Y + (h // 2) - 5, b_w, max(25, b_h)), math.pi, 2 * math.pi, 2)

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

    def dibujar_estela_flotacion_agua(self):
        """Método reservado para efectos de oleaje ambiental."""
        pass

    def dibujar_titulo_animado(self, texto_titulo="CHEEP CHEEP CHANCE", texto_sub="REMAKE", centro_x=None, base_y=110, tamano_titulo=56, tamano_sub=32):
        if centro_x is None:
            centro_x = Config.ANCHO // 2
            
        t = pygame.time.get_ticks()
        fuente_grande = pygame.font.Font(Config.FUENTE_PRINCIPAL, tamano_titulo)
        
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
        
        ancho_total = 0
        surfs_letras = []
        for i, char in enumerate(texto_titulo):
            color = colores_mp[i % len(colores_mp)]
            surf_c = fuente_grande.render(char, True, color)
            surfs_letras.append((char, surf_c))
            ancho_total += surf_c.get_width()
            
        x_cursor = centro_x - (ancho_total // 2)
        
        for i, (char, surf_c) in enumerate(surfs_letras):
            y_wave = math.sin(t * 0.007 + i * 0.4) * 14
            pos_y = base_y - 25 + y_wave
            
            # Sombra de la letra
            surf_shadow = fuente_grande.render(char, True, Config.NEGRO)
            self.pantalla.blit(surf_shadow, (x_cursor + 3, pos_y + 3))
            # Letra coloreada
            self.pantalla.blit(surf_c, (x_cursor, pos_y))
            
            x_cursor += surf_c.get_width()
            
        if texto_sub:
            fuente_sub = pygame.font.Font(Config.FUENTE_PRINCIPAL, tamano_sub)
            color_sub = Config.AMARILLO if (t // 300) % 2 == 0 else Config.BLANCO
            
            txt_sub = fuente_sub.render(texto_sub, True, color_sub)
            rect_sub = txt_sub.get_rect(center=(centro_x, base_y + 42))
            
            shadow_sub = fuente_sub.render(texto_sub, True, Config.NEGRO)
            rect_shadow_sub = shadow_sub.get_rect(center=(centro_x + 2, base_y + 44))
            
            self.pantalla.blit(shadow_sub, rect_shadow_sub)
            self.pantalla.blit(txt_sub, rect_sub)

    def renderizar(self, pos_mouse):
        self.pantalla.blit(self.bg_image_top, (0, 0))
        self.pantalla.blit(self.bg_image_bottom, (0, Config.NIVEL_AGUA))
        
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
            
            # --- TÍTULO ESTILO MARIO PARTY EN PANTALLA DE INICIO ---
            self.dibujar_titulo_animado("CHEEP CHEEP CHANCE", "REMAKE", base_y=Config.ALTO // 2 - 80, tamano_titulo=62, tamano_sub=36)
            
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
            
            # --- TÍTULO ANIMADO CON EFECTO MARIO PARTY EN MENÚ PRINCIPAL ---
            self.dibujar_titulo_animado("CHEEP CHEEP CHANCE", "REMAKE", base_y=110, tamano_titulo=54, tamano_sub=30)
            
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
            
            txt_shadow = self.fuente_titulo.render("SELECCIONA UN MODO", True, Config.NEGRO)
            self.pantalla.blit(txt_shadow, txt_shadow.get_rect(center=(Config.ANCHO // 2 + 3, 123)))
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
            
            txt_shadow = self.fuente_titulo.render("¿CUÁNTOS JUGADORES?", True, Config.NEGRO)
            self.pantalla.blit(txt_shadow, txt_shadow.get_rect(center=(Config.ANCHO // 2 + 3, 123)))
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
            
            txt_shadow = self.fuente_titulo.render("OPCIONES", True, Config.NEGRO)
            self.pantalla.blit(txt_shadow, txt_shadow.get_rect(center=(Config.ANCHO // 2 + 3, 83)))
            txt = self.fuente_titulo.render("OPCIONES", True, Config.AMARILLO)
            rect_txt = txt.get_rect(center=(Config.ANCHO // 2, 80))
            self.pantalla.blit(txt, rect_txt)
            
            self.btn_toggle_musica.dibujar(self.pantalla)
            self.slider_musica.draw(self.pantalla, self.fuente_ui)
            self.btn_toggle_sfx.dibujar(self.pantalla)
            self.slider_sfx.draw(self.pantalla, self.fuente_ui)
            self.btn_volver.dibujar(self.pantalla)
            
        elif self.estado == "INSTRUCCIONES":
            capa_oscura = pygame.Surface((Config.ANCHO, Config.ALTO), pygame.SRCALPHA)
            capa_oscura.fill((10, 20, 40, 215))
            self.pantalla.blit(capa_oscura, (0, 0))
            
            txt_shadow = self.fuente_titulo.render("INSTRUCCIONES", True, Config.NEGRO)
            self.pantalla.blit(txt_shadow, txt_shadow.get_rect(center=(Config.ANCHO // 2 + 3, 53)))
            txt = self.fuente_titulo.render("INSTRUCCIONES", True, Config.AMARILLO)
            self.pantalla.blit(txt, txt.get_rect(center=(Config.ANCHO // 2, 50)))
            
            lineas = [
                "• Cada jugador elige un personaje y, por turnos, una cuerda.",
                "• Al final de la ronda se revela el contenido de cada cuerda.",
                "• ¡Cuidado! Si eliges una cuerda con monstruo, quedas ELIMINADO.",
                "• Gana la partida el último jugador que quede con vida.",
            ]
            y_linea = 105
            for linea in lineas:
                txt_l = self.fuente_ui.render(linea, True, Config.BLANCO)
                self.pantalla.blit(txt_l, txt_l.get_rect(center=(Config.ANCHO // 2, y_linea)))
                y_linea += 28

            txt_sub_shadow = self.fuente_subtitulo.render("--- CONTROLES Y MANDOS ---", True, Config.NEGRO)
            self.pantalla.blit(txt_sub_shadow, txt_sub_shadow.get_rect(center=(Config.ANCHO // 2 + 2, 237)))
            txt_sub = self.fuente_subtitulo.render("--- CONTROLES Y MANDOS ---", True, Config.AMARILLO)
            self.pantalla.blit(txt_sub, txt_sub.get_rect(center=(Config.ANCHO // 2, 235)))

            # TARJETA 1: Movimiento y Navegación (WASD + Flechas)
            card1_rect = pygame.Rect(100, 270, 520, 280)
            pygame.draw.rect(self.pantalla, (15, 25, 45, 220), card1_rect, border_radius=12)
            pygame.draw.rect(self.pantalla, Config.AMARILLO, card1_rect, width=2, border_radius=12)

            txt_c1 = self.fuente_subtitulo.render("Navegación / Movimiento", True, Config.AMARILLO)
            self.pantalla.blit(txt_c1, txt_c1.get_rect(center=(card1_rect.centerx, card1_rect.top + 25)))

            if self.img_ctrl_wasd:
                r_wasd = self.img_ctrl_wasd.get_rect(center=(card1_rect.centerx - 110, card1_rect.top + 115))
                self.pantalla.blit(self.img_ctrl_wasd, r_wasd)
            if self.img_ctrl_arrow:
                r_arr = self.img_ctrl_arrow.get_rect(center=(card1_rect.centerx + 110, card1_rect.top + 115))
                self.pantalla.blit(self.img_ctrl_arrow, r_arr)

            t_desc1 = self.fuente_ui.render("WASD o Flechas de Dirección", True, Config.BLANCO)
            self.pantalla.blit(t_desc1, t_desc1.get_rect(center=(card1_rect.centerx, card1_rect.top + 195)))
            t_subdesc1 = self.fuente_ui.render("Moverse entre opciones y personajes", True, Config.GRIS_CLARO)
            self.pantalla.blit(t_subdesc1, t_subdesc1.get_rect(center=(card1_rect.centerx, card1_rect.top + 225)))

            # TARJETA 2: Interacción y Cuerdas (Mouse + Teclas 1-8 / ENTER / ESC)
            card2_rect = pygame.Rect(660, 270, 520, 280)
            pygame.draw.rect(self.pantalla, (15, 25, 45, 220), card2_rect, border_radius=12)
            pygame.draw.rect(self.pantalla, Config.AMARILLO, card2_rect, width=2, border_radius=12)

            txt_c2 = self.fuente_subtitulo.render("Interacción y Cuerdas", True, Config.AMARILLO)
            self.pantalla.blit(txt_c2, txt_c2.get_rect(center=(card2_rect.centerx, card2_rect.top + 25)))

            if self.img_ctrl_mouse:
                r_mouse = self.img_ctrl_mouse.get_rect(center=(card2_rect.centerx, card2_rect.top + 115))
                self.pantalla.blit(self.img_ctrl_mouse, r_mouse)

            t_desc2 = self.fuente_ui.render("Clic del Mouse o Teclas del 1 al 8", True, Config.BLANCO)
            self.pantalla.blit(t_desc2, t_desc2.get_rect(center=(card2_rect.centerx, card2_rect.top + 195)))
            t_subdesc2 = self.fuente_ui.render("Elegir cuerda | ENTER: Confirmar | ESC: Pausa", True, Config.GRIS_CLARO)
            self.pantalla.blit(t_subdesc2, t_subdesc2.get_rect(center=(card2_rect.centerx, card2_rect.top + 225)))

            self.btn_instrucciones_volver.dibujar(self.pantalla)
            
        elif self.estado in ["EN_JUEGO", "PAUSA", "FIN_JUEGO", "REVELANDO_CUERDAS", "ESPERA_POST_SELECCION"]:
            self.dibujar_plataforma_modular()
            
            self.pantalla.blit(self.tinte_agua, (0, Config.NIVEL_AGUA))
            self.dibujar_estela_flotacion_agua()
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
            
            jugadores_ordenados = sorted(self.jugadores, key=lambda p: p.y)
            for j in jugadores_ordenados: 
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


            # --- HUD SUPERIOR: MODO / MARCADOR (TEXTO LIMPIO SIN BURBUJA) ---
            if self.modo_actual == "DUELO":
                tag = f"DUELO | MARCADOR {self.victorias_j1} - {self.victorias_j2}"
                if self.muerte_subita_activa: tag += " (M. SÚBITA)"
            else:
                tag = "MUERTE SÚBITA" if self.muerte_subita_activa else f"RONDA {self.num_ronda}"
                
            color_tag = Config.AMARILLO if self.modo_actual == "DUELO" else Config.BLANCO
            txt_tag_shadow = self.fuente_hud_banner.render(tag, True, Config.NEGRO)
            txt_tag = self.fuente_hud_banner.render(tag, True, color_tag)
            
            rect_tag = txt_tag.get_rect(topleft=(25, 18))
            rect_tag_shadow = txt_tag_shadow.get_rect(topleft=(27, 20))
            self.pantalla.blit(txt_tag_shadow, rect_tag_shadow)
            self.pantalla.blit(txt_tag, rect_tag)

            # --- ANUNCIO DE FASES / TURNOS (TEXTO MÁS GRANDE Y MÁS BAJO SIN BURBUJA) ---
            ahora_ms = pygame.time.get_ticks()
            bamboleo_y = 0
            
            if self.turno_actual < len(vivos_iniciales) and not self.revelado:
                j_act = vivos_iniciales[self.turno_actual]
                txt_b_str = f"Turno de: {j_act.nombre}  |  Tiempo: {self.segundos_restantes}s"
                color_txt_b = (255, 100, 100) if self.segundos_restantes <= 2 else Config.AMARILLO
            elif not self.revelado and (self.turno_actual >= len(vivos_iniciales) or self.estado == "ESPERA_POST_SELECCION"):
                txt_b_str = "¡SELECCIÓN COMPLETADA! PREPARANDO REVELACIÓN..."
                color_txt_b = (100, 255, 160)
            else:
                txt_b_str = self.mensaje_partida
                bamboleo_y = int(math.sin(ahora_ms * 0.007) * 4)
                pulso_c = int(math.sin(ahora_ms * 0.009) * 35)
                g_val = max(180, min(255, 220 + pulso_c))
                color_txt_b = (255, g_val, 80) if self.revelado else (100, 255, 160)
            
            # Posición más baja en pantalla (Y = 65) con fuente grande (34px) y sin contenedor de fondo
            target_center_x = max(rect_tag.right + 180, Config.ANCHO // 2 + 50)
            target_center_y = 65 + bamboleo_y

            txt_b_shadow = self.fuente_fases_grandes.render(txt_b_str, True, Config.NEGRO)
            txt_b = self.fuente_fases_grandes.render(txt_b_str, True, color_txt_b)
            
            rect_b = txt_b.get_rect(center=(target_center_x, target_center_y))
            rect_b_shadow = txt_b_shadow.get_rect(center=(target_center_x + 2, target_center_y + 2))
            
            self.pantalla.blit(txt_b_shadow, rect_b_shadow)
            self.pantalla.blit(txt_b, rect_b)
            
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
                capa_oscura.fill((15, 20, 30, 225))
                self.pantalla.blit(capa_oscura, (0, 0))
                
                txt_fin_shadow = self.fuente_titulo.render("PARTIDA FINALIZADA", True, Config.NEGRO)
                self.pantalla.blit(txt_fin_shadow, txt_fin_shadow.get_rect(center=(Config.ANCHO // 2 + 3, 153)))
                txt_fin = self.fuente_titulo.render("PARTIDA FINALIZADA", True, Config.AMARILLO)
                rect_fin = txt_fin.get_rect(center=(Config.ANCHO // 2, 150))
                self.pantalla.blit(txt_fin, rect_fin)
                
                if self.modo_actual == "DUELO":
                    ganador_obj = self.jugadores[0] if self.victorias_j1 == 2 else self.jugadores[1]
                    texto_final_limpio = f"¡GANADOR DEFINITIVO: {ganador_obj.nombre}!"
                    color_ganador = Jugador.COLORES_NOMBRE.get(ganador_obj.personaje, Config.AMARILLO)
                else:
                    ganador_real = [j for j in self.jugadores if j.vivo]
                    if len(ganador_real) == 1:
                        ganador_obj = ganador_real[0]
                        texto_final_limpio = f"¡GANADOR: {ganador_obj.nombre}!"
                        color_ganador = Jugador.COLORES_NOMBRE.get(ganador_obj.personaje, Config.AMARILLO)
                    else:
                        texto_final_limpio = "¡NADIE SOBREVIVIÓ!"
                        color_ganador = (255, 110, 110)
                    
                fuente_ganador = pygame.font.Font(Config.FUENTE_PRINCIPAL, 38)
                
                txt_res_shadow = fuente_ganador.render(texto_final_limpio, True, Config.NEGRO)
                txt_res = fuente_ganador.render(texto_final_limpio, True, color_ganador)
                
                rect_res = txt_res.get_rect(center=(Config.ANCHO // 2, 245))
                rect_res_shadow = txt_res_shadow.get_rect(center=(Config.ANCHO // 2 + 3, 248))
                
                self.pantalla.blit(txt_res_shadow, rect_res_shadow)
                self.pantalla.blit(txt_res, rect_res)
                
                self.btn_reiniciar.dibujar(self.pantalla)
                self.btn_fin_menu.dibujar(self.pantalla)

        if self.mostrar_debug_fps:
            fps_reales = int(self.reloj.get_fps())
            txt_fps = self.fuente_fps.render(f"FPS: {fps_reales} / {Config.FPS}", True, Config.NEGRO)
            rect_fps = txt_fps.get_rect(topright=(Config.ANCHO - 18, 14))
            
            # Fondo traslúcido para legibilidad perfecta del contador en color negro en la esquina superior derecha
            bg_fps = rect_fps.inflate(16, 8)
            pygame.draw.rect(self.pantalla, (255, 255, 255, 220), bg_fps, border_radius=6)
            pygame.draw.rect(self.pantalla, Config.NEGRO, bg_fps, width=2, border_radius=6)
            
            self.pantalla.blit(txt_fps, rect_fps)
            
        # Banner flotante de notificación F1 (MUTE / UNMUTE) durante 2 segundos
        ahora_ms = pygame.time.get_ticks()
        if ahora_ms - self.mensaje_mute_tiempo < 2000 and self.mensaje_mute_texto:
            txt_mute = self.fuente_hud_banner.render(self.mensaje_mute_texto, True, Config.BLANCO)
            rect_mute = txt_mute.get_rect(topright=(Config.ANCHO - 25, 15 if not self.mostrar_debug_fps else 45))
            badge_mute = rect_mute.inflate(20, 10)
            
            surf_mute = pygame.Surface((badge_mute.width, badge_mute.height), pygame.SRCALPHA)
            color_bg = (180, 30, 30, 220) if "SILENCIADO" in self.mensaje_mute_texto else (30, 140, 50, 220)
            surf_mute.fill(color_bg)
            self.pantalla.blit(surf_mute, badge_mute.topleft)
            pygame.draw.rect(self.pantalla, Config.BLANCO, badge_mute, width=2, border_radius=6)
            self.pantalla.blit(txt_mute, rect_mute)

        pygame.display.flip()
