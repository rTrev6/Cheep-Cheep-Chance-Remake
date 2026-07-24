from pathlib import Path
import os
import pygame

# Rutas dinámicas obligatorias
RUTA_RAIZ = Path(__file__).resolve().parent.parent
RUTA_ASSETS = RUTA_RAIZ / "assets"
RUTA_IMAGENES = RUTA_ASSETS / "sprites"
RUTA_FUENTES = RUTA_ASSETS / "fonts"
RUTA_SONIDOS = RUTA_ASSETS / "sounds"

class Config:
    # Rutas absolutas expuestas en Config
    RUTA_IMAGENES = RUTA_IMAGENES
    RUTA_FUENTES = RUTA_FUENTES
    RUTA_SONIDOS = RUTA_SONIDOS

    # Dimensiones fijas a 1280x720 px
    ANCHO = 1280
    ALTO = 720
    FPS = 60
    
    # Colores
    CELESTE_CIELO = (135, 206, 235)
    AZUL_MAR = (10, 60, 120)
    BLANCO = (255, 255, 255)
    ROJO = (220, 20, 60)
    ROJO_OSCURO = (150, 10, 30)
    NEGRO = (0, 0, 0)
    AMARILLO = (255, 215, 0)
    MADERA_CUERDA = (210, 180, 140)
    GRIS = (70, 70, 70)
    GRIS_CLARO = (120, 120, 120)
    VERDE = (34, 139, 34)
    VERDE_REMANSO = (46, 204, 113)
    DARK_GRAY = (40, 40, 40)
    BLUE = (50, 120, 220)
    ACCENT_COLOR = (220, 80, 50)
    
    PERSONAJES = ["Mario", "Luigi", "Wario", "Yoshi", "Peach", "Daisy", "Waluigi", "Toad"]
    COLORES_JUGADORES = [
        (220, 20, 60),    # Mario: Rojo
        (34, 139, 34),    # Luigi: Verde
        (255, 215, 0),    # Wario: Amarillo
        (124, 252, 0),    # Yoshi: Verde claro
        (255, 105, 180),  # Peach: Rosa
        (255, 140, 0),    # Daisy: Naranja
        (138, 43, 226),  # Waluigi: Violeta
        (70, 130, 180)    # Toad: Azul/Celeste
    ]
    NIVEL_AGUA = 440

    # Dimensiones de los sprites y personajes
    CHAR_ANCHO = 60
    CHAR_ALTO = 75
    SPRITE_CREATURE_SIZE = 72

    # Dimensiones adaptadas a 1280x720 para el Salvavidas (Centrado)
    SALV_ANCHO = 520
    SALV_ALTO = 60
    SALV_X = (ANCHO - SALV_ANCHO) // 2 # 380
    SALV_Y = 240
    
    # NUEVA VARIABLE: Ruta dinámica al archivo .ttf personalizado
    FUENTE_PRINCIPAL = RUTA_FUENTES / "sm256.ttf"
    
    # Rutas absolutas a los archivos de sprites
    SPRITE_ROPE = RUTA_IMAGENES / "sprite_rope.png"
    SPRITE_FISH_LEFT = RUTA_IMAGENES / "sprite_fish_left.png"
    SPRITE_FISH_RIGHT = RUTA_IMAGENES / "sprite_fish_right.png"
    SPRITE_FISH_FISHED = RUTA_IMAGENES / "sprite_fished.png"
    SPRITE_MONSTER_LEFT = RUTA_IMAGENES / "sprite_monster_left.png"
    SPRITE_MONSTER_RIGHT = RUTA_IMAGENES / "sprite_monster_right.png"
    SPRITE_MONSTER_FISHED = RUTA_IMAGENES / "sprite_monster_fished.png"
    SPRITE_MONSTER2_LEFT = RUTA_IMAGENES / "sprite_monster2_left.png"
    SPRITE_MONSTER2_RIGHT = RUTA_IMAGENES / "sprite_monster2_right.png"
    SPRITE_MONSTER2_FISHED = RUTA_IMAGENES / "sprite_monster2_fished.png"
    SPRITE_BACKGROUND = RUTA_IMAGENES / "sea_background_claro.png"

    # Texturas estilo Mario para los botones de menú y el cursor de mano
    SPRITE_MENU = RUTA_IMAGENES / "menu_sprite.png"
    SPRITE_MENU_SELECTED = RUTA_IMAGENES / "menu_selected_sprite.png"
    SPRITE_HAND = RUTA_IMAGENES / "hand_sprtite.png"
    
    # Ajustes globales modificables desde el menú de opciones
    musica_activa = True
    sfx_activo = True

    # Volumen general (0.0 a 1.0), controlado con los sliders del menú de
    # opciones. La música arranca más baja que antes para que los efectos
    # de sonido (SFX) se escuchen bien por encima de ella.
    volumen_musica = 0.35
    volumen_sfx = 0.7


# ==============================================================================
# GESTOR DE SONIDO (SOUND MANAGER)
# ==============================================================================
class SoundManager:
    def __init__(self, sounds_dir=Config.RUTA_SONIDOS):
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            
        self.sounds_dir = sounds_dir
        self.music_volume = 0.5
        self.sfx_volume = 0.8
        self.current_music = None
        self.sfx = {}
        self.load_sfx()

    def load_sfx(self):
        """Carga en memoria todos los efectos de sonido (SFX)."""
        sfx_files = {
            "victory": "sfx_victory.wav",
            "hurry": "sfx_hurry.wav",
            "lose": "sfx_lose.wav",
            "pause": "sfx_pause.wav",
            "unpause": "sfx_unpause.wav",
            "menu_option": "sfx_menu_option.wav",
            "select": "sfx_select.wav"
        }
        for name, filename in sfx_files.items():
            path = self.sounds_dir / filename
            if path.exists():
                self.sfx[name] = pygame.mixer.Sound(str(path))
                self.sfx[name].set_volume(self.sfx_volume if Config.sfx_activo else 0.0)

    def play_music(self, music_name, loop=-1):
        """Reproduce la música especificada ('menu', 'game', 'duel')."""
        if not Config.musica_activa:
            return

        music_files = {
            "menu": "music_menu.oga",
            "game": "music_game.oga",
            "duel": "music_duel.oga"
        }
        if music_name in music_files and self.current_music != music_name:
            path = self.sounds_dir / music_files[music_name]
            if path.exists():
                self.current_music = music_name
                pygame.mixer.music.load(str(path))
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(loops=loop)

    def stop_music(self):
        pygame.mixer.music.stop()
        self.current_music = None

    def play_sfx(self, sfx_name):
        """Dispara un efecto de sonido."""
        if Config.sfx_activo and sfx_name in self.sfx:
            self.sfx[sfx_name].play()

    def set_music_volume(self, volume):
        """Ajusta el volumen de la música (rango 0.0 a 1.0)."""
        self.music_volume = max(0.0, min(1.0, volume))
        if Config.musica_activa:
            pygame.mixer.music.set_volume(self.music_volume)

    def set_sfx_volume(self, volume):
        """Ajusta el volumen de los efectos de sonido (rango 0.0 a 1.0)."""
        self.sfx_volume = max(0.0, min(1.0, volume))
        for sound in self.sfx.values():
            sound.set_volume(self.sfx_volume if Config.sfx_activo else 0.0)


# ==============================================================================
# COMPONENTE BARRA DESLIZANTE (SLIDER PARA MENÚ OPCIONES)
# ==============================================================================
class Slider:
    def __init__(self, x, y, w, h, initial_val, label=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.value = initial_val  # Valor entre 0.0 y 1.0
        self.label = label
        self.dragging = False
        self.handle_width = 16
        self.handle_rect = pygame.Rect(
            x + int(initial_val * w) - self.handle_width // 2, 
            y - 4, 
            self.handle_width, 
            h + 8
        )

    def handle_event(self, event):
        """Maneja interacciones de mouse. Retorna True si hubo cambio de valor."""
        changed = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.handle_rect.collidepoint(event.pos) or self.rect.collidepoint(event.pos):
                self.dragging = True
                self.update_val(event.pos[0])
                changed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.update_val(event.pos[0])
            changed = True
        return changed

    def update_val(self, mouse_x):
        mouse_x = max(self.rect.left, min(mouse_x, self.rect.right))
        self.value = (mouse_x - self.rect.left) / self.rect.width
        self.handle_rect.centerx = mouse_x

    def draw(self, surface, font):
        """Dibuja en pantalla la etiqueta, porcentaje y barra deslizante."""
        text_surf = font.render(f"{self.label}: {int(self.value * 100)}%", True, Config.BLANCO)
        surface.blit(text_surf, (self.rect.x, self.rect.y - 25))
        
        # Fondo de la barra
        pygame.draw.rect(surface, Config.DARK_GRAY, self.rect, border_radius=4)
        # Barra de nivel / Relleno
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, int(self.rect.width * self.value), self.rect.height)
        pygame.draw.rect(surface, Config.BLUE, fill_rect, border_radius=4)
        # Botón / Agarre deslizante
        pygame.draw.rect(surface, Config.ACCENT_COLOR if self.dragging else Config.BLANCO, self.handle_rect, border_radius=4)


# Instancia global del mezclador para importarse en cualquier parte del código
sound_manager = SoundManager()