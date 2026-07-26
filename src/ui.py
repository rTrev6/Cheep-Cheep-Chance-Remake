import pygame
import math
from src.config import Config

class Boton:
    """
    Componente de botón estilizado Mario Party con soporte de texturas escaladas,
    hover con ratón y cursor de mano animado para navegación con teclado.
    """
    _tex_normal_raw = None
    _tex_selected_raw = None
    _tex_hand_raw = None
    _texturas_cargadas = False

    @classmethod
    def _cargar_texturas(cls):
        if cls._texturas_cargadas:
            return
        cls._texturas_cargadas = True
        try:
            cls._tex_normal_raw = pygame.image.load(str(Config.SPRITE_MENU)).convert_alpha()
        except Exception as e:
            print(f"Error cargando textura de menú: {e}")
        try:
            cls._tex_selected_raw = pygame.image.load(str(Config.SPRITE_MENU_SELECTED)).convert_alpha()
        except Exception as e:
            print(f"Error cargando textura de menú seleccionado: {e}")
        try:
            cls._tex_hand_raw = pygame.image.load(str(Config.SPRITE_HAND)).convert_alpha()
        except Exception as e:
            print(f"Error cargando sprite de mano: {e}")

    def __init__(self, x, y, ancho, alto, texto, color_base, color_hover):
        self.rect = pygame.Rect(x, y, ancho, alto)
        self.texto = texto
        self.color_base = color_base
        self.color_hover = color_hover
        self.color_actual = color_base

        self.fuente = pygame.font.Font(Config.FUENTE_PRINCIPAL, 28)
        self.texto_surf = self.fuente.render(self.texto, True, Config.NEGRO)
        self.texto_rect = self.texto_surf.get_rect(center=self.rect.center)

        Boton._cargar_texturas()
        self.tex_normal = None
        self.tex_selected = None
        if Boton._tex_normal_raw:
            self.tex_normal = pygame.transform.scale(Boton._tex_normal_raw, (ancho, alto))
        if Boton._tex_selected_raw:
            crecimiento = 10
            self.tex_selected = pygame.transform.scale(
                Boton._tex_selected_raw, (ancho + crecimiento, alto + crecimiento)
            )

        self.hover = False
        self.resaltado_teclado = False

        self.hand_img = None
        if Boton._tex_hand_raw:
            alto_mano = int(alto * 0.85)
            ancho_mano = int(Boton._tex_hand_raw.get_width() * (alto_mano / Boton._tex_hand_raw.get_height()))
            self.hand_img = pygame.transform.scale(Boton._tex_hand_raw, (ancho_mano, alto_mano))

    def actualizar(self, pos_mouse):
        self.hover = self.rect.collidepoint(pos_mouse)
        self.color_actual = self.color_hover if self.hover else self.color_base

    def set_resaltado_teclado(self, valor):
        self.resaltado_teclado = valor

    def dibujar(self, superficie):
        seleccionado = self.resaltado_teclado

        if seleccionado and self.tex_selected:
            rect_tex = self.tex_selected.get_rect(center=self.rect.center)
            superficie.blit(self.tex_selected, rect_tex)
        elif self.tex_normal:
            superficie.blit(self.tex_normal, self.rect)
        else:
            pygame.draw.rect(superficie, self.color_actual, self.rect, border_radius=8)
            pygame.draw.rect(superficie, Config.NEGRO, self.rect, width=2, border_radius=8)

        superficie.blit(self.texto_surf, self.texto_rect)

        if seleccionado and self.hand_img:
            bamboleo = int(math.sin(pygame.time.get_ticks() * 0.008) * 4)
            hand_rect = self.hand_img.get_rect(midright=(self.rect.left - 6 + bamboleo, self.rect.centery))
            superficie.blit(self.hand_img, hand_rect)

    def fue_clicado(self, pos_mouse):
        return self.rect.collidepoint(pos_mouse)

    def definir_texto(self, nuevo_texto):
        self.texto = nuevo_texto
        self.texto_surf = self.fuente.render(self.texto, True, Config.NEGRO)
        self.texto_rect = self.texto_surf.get_rect(center=self.rect.center)


class Slider:
    """
    Componente de barra deslizante para ajuste de volumen de Música y SFX
    con soporte de arrastre de mouse y teclado.
    """
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
        self.value = initial_val
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
        
        Slider._cargar_mano()
        self.hand_img = None
        if Slider._tex_hand_raw:
            alto_mano = 32
            ancho_mano = int(Slider._tex_hand_raw.get_width() * (alto_mano / Slider._tex_hand_raw.get_height()))
            self.hand_img = pygame.transform.scale(Slider._tex_hand_raw, (ancho_mano, alto_mano))

    def actualizar(self, pos_mouse):
        zona = pygame.Rect(self.rect.x - 10, self.rect.y - 30, self.rect.width + 20, self.rect.height + 40)
        self.hover = zona.collidepoint(pos_mouse)

    def set_resaltado_teclado(self, valor):
        self.resaltado_teclado = valor

    def modificar_valor(self, delta):
        nuevo_val = max(0.0, min(1.0, self.value + delta))
        if abs(nuevo_val - self.value) > 0.001:
            self.value = round(nuevo_val, 2)
            self.handle_rect.centerx = self.rect.left + int(self.value * self.rect.width)
            return True
        return False

    def handle_event(self, event):
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
        seleccionado = self.resaltado_teclado
        color_texto = Config.AMARILLO if seleccionado else Config.BLANCO
        
        text_surf = font.render(f"{self.label}: {int(self.value * 100)}%", True, color_texto)
        surface.blit(text_surf, (self.rect.x, self.rect.y - 25))
        
        if seleccionado:
            rect_glow = self.rect.inflate(6, 6)
            pygame.draw.rect(surface, Config.AMARILLO, rect_glow, border_radius=6, width=2)
        
        pygame.draw.rect(surface, Config.DARK_GRAY, self.rect, border_radius=4)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, int(self.rect.width * self.value), self.rect.height)
        color_relleno = Config.ACCENT_COLOR if seleccionado else Config.BLUE
        pygame.draw.rect(surface, color_relleno, fill_rect, border_radius=4)
        color_handle = Config.AMARILLO if seleccionado or self.dragging else Config.BLANCO
        pygame.draw.rect(surface, color_handle, self.handle_rect, border_radius=4)

        if seleccionado and self.hand_img:
            bamboleo = int(math.sin(pygame.time.get_ticks() * 0.008) * 4)
            hand_rect = self.hand_img.get_rect(midright=(self.rect.left - 12 + bamboleo, self.rect.centery))
            surface.blit(self.hand_img, hand_rect)
