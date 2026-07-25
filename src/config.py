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
    NIVEL_AGUA = 340

    # Dimensiones de los sprites y personajes (Escalados para perspectiva lejana equilibrada)
    CHAR_ANCHO = 52
    CHAR_ALTO = 66
    SPRITE_CREATURE_SIZE = 78

    # Dimensiones adaptadas a 1280x720 para la Plataforma Circular Flotante (450x160)
    SALV_ANCHO = 450
    SALV_ALTO = 220
    SALV_X = (ANCHO - SALV_ANCHO) // 2 # 415
    SALV_Y = 140
    
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
    SPRITE_BACKGROUND_TOP = RUTA_IMAGENES / "sea_background_claro.png"
    SPRITE_BACKGROUND_BOTTOM = RUTA_IMAGENES / "sea_background.png"
    SPRITE_BACKGROUND = RUTA_IMAGENES / "sea_background.png"
    SPRITE_PLATFORM = RUTA_IMAGENES / "platform_texture.png"
    SPRITE_BORDER_TEXTURE = RUTA_IMAGENES / "border_texture.png"

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
# COMPONENTE BARRA DESLIZANTE (SLIDER PARA MENÚ OPCIONES)
# ==============================================================================
# ==============================================================================
# COMPONENTE BARRA DESLIZANTE (SLIDER PARA MENÚ OPCIONES)
# ==============================================================================
class Slider:
    _tex_hand_raw = None
    _textura_mano_cargada = False

    @classmethod
    def _cargar_mano(cls):
        if cls._textura_mano_cargada:
            return
        cls._textura_mano_cargada = True
        try:
            cls._tex_hand_raw = pygame.image.load(str(Config.SPRITE_HAND)).convert_alpha()
        except Exception as e:
            print(f"Error cargando sprite de mano en Slider: {e}")

    def __init__(self, x, y, w, h, initial_val, label=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.value = initial_val  # Valor entre 0.0 y 1.0
        self.label = label
        self.dragging = False
        self.hover = False
        self.resaltado_teclado = False
        self.handle_width = 16
        self.handle_rect = pygame.Rect(
            x + int(initial_val * w) - self.handle_width // 2, 
            y - 4, 
            self.handle_width, 
            h + 8
        )
        
        # Carga sprite de mano indicadora (cursor estilo Mario Party)
        Slider._cargar_mano()
        self.hand_img = None
        if Slider._tex_hand_raw:
            alto_mano = 32
            ancho_mano = int(Slider._tex_hand_raw.get_width() * (alto_mano / Slider._tex_hand_raw.get_height()))
            self.hand_img = pygame.transform.scale(Slider._tex_hand_raw, (ancho_mano, alto_mano))

    def actualizar(self, pos_mouse):
        """Actualiza el estado hover cuando el mouse se posiciona sobre el slider."""
        zona = pygame.Rect(self.rect.x - 10, self.rect.y - 30, self.rect.width + 20, self.rect.height + 40)
        self.hover = zona.collidepoint(pos_mouse)

    def set_resaltado_teclado(self, valor):
        self.resaltado_teclado = valor

    def modificar_valor(self, delta):
        """Modifica el valor del slider por delta (+0.05 / -0.05) y ajusta el botón deslizante."""
        nuevo_val = max(0.0, min(1.0, self.value + delta))
        if abs(nuevo_val - self.value) > 0.001:
            self.value = round(nuevo_val, 2)
            self.handle_rect.centerx = self.rect.left + int(self.value * self.rect.width)
            return True
        return False

    def handle_event(self, event):
        """Maneja interacciones de mouse y teclado. Retorna True si hubo cambio de valor."""
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
        elif event.type == pygame.KEYDOWN and (self.hover or self.resaltado_teclado):
            if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_MINUS, pygame.K_KP_MINUS):
                changed = self.modificar_valor(-0.05)
            elif event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS):
                changed = self.modificar_valor(0.05)
            elif event.key == pygame.K_PAGEUP:
                changed = self.modificar_valor(0.10)
            elif event.key == pygame.K_PAGEDOWN:
                changed = self.modificar_valor(-0.10)
            elif event.key == pygame.K_HOME:
                changed = self.modificar_valor(-1.0)
            elif event.key == pygame.K_END:
                changed = self.modificar_valor(1.0)
        return changed

    def update_val(self, mouse_x):
        mouse_x = max(self.rect.left, min(mouse_x, self.rect.right))
        self.value = round((mouse_x - self.rect.left) / self.rect.width, 2)
        self.handle_rect.centerx = mouse_x

    def draw(self, surface, font):
        """Dibuja en pantalla la etiqueta, porcentaje, barra deslizante y mano indicadora."""
        seleccionado = self.resaltado_teclado
        color_texto = Config.AMARILLO if seleccionado else Config.BLANCO
        
        text_surf = font.render(f"{self.label}: {int(self.value * 100)}%", True, color_texto)
        surface.blit(text_surf, (self.rect.x, self.rect.y - 25))
        
        # Borde exterior resaltado cuando está enfocado
        if seleccionado:
            rect_glow = self.rect.inflate(6, 6)
            pygame.draw.rect(surface, Config.AMARILLO, rect_glow, border_radius=6, width=2)
        
        # Fondo de la barra
        pygame.draw.rect(surface, Config.DARK_GRAY, self.rect, border_radius=4)
        # Barra de nivel / Relleno
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, int(self.rect.width * self.value), self.rect.height)
        color_relleno = Config.ACCENT_COLOR if seleccionado else Config.BLUE
        pygame.draw.rect(surface, color_relleno, fill_rect, border_radius=4)
        # Botón / Agarre deslizante
        color_handle = Config.AMARILLO if seleccionado or self.dragging else Config.BLANCO
        pygame.draw.rect(surface, color_handle, self.handle_rect, border_radius=4)

        # Mano indicadora estilo Mario Party
        if seleccionado and self.hand_img:
            import math
            bamboleo = int(math.sin(pygame.time.get_ticks() * 0.008) * 4)
            hand_rect = self.hand_img.get_rect(midright=(self.rect.left - 12 + bamboleo, self.rect.centery))
            surface.blit(self.hand_img, hand_rect)
