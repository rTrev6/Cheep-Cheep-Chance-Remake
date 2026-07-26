import pygame
import math
from src.config import Config

class RenderizadorEscenario:
    """
    Encapsula todas las rutinas de renderizado del escenario 3D:
    - Plataforma circular/elíptica modular (salvavidas).
    - Fondo marino con ondas de arena y algas animadas.
    - Título animado del menú principal.
    - Banner HUD e instrucciones en pantalla.
    """
    def __init__(self, pantalla):
        self.pantalla = pantalla

    def dibujar_plataforma_modular(self, sprite_platform=None, sprite_border_texture=None):
        """Dibuja la plataforma circular/elíptica de 430x175 px con la textura de borde incorporada."""
        if sprite_platform:
            self.pantalla.blit(sprite_platform, (Config.SALV_X, Config.SALV_Y))
            return

        w = Config.SALV_ANCHO
        h = Config.SALV_ALTO
        
        profundidad_3d = 14
        for offset_y in range(profundidad_3d, 0, -2):
            grosor_color = (130, 20, 20) if offset_y > 6 else (170, 30, 30)
            pygame.draw.ellipse(self.pantalla, grosor_color, (Config.SALV_X, Config.SALV_Y + offset_y, w, h))

        rect_ext = pygame.Rect(Config.SALV_X, Config.SALV_Y, w, h)
        pygame.draw.ellipse(self.pantalla, (215, 40, 40), rect_ext)
        pygame.draw.ellipse(self.pantalla, Config.NEGRO, rect_ext, width=3)

        m_x = 24
        m_y = 15
        rect_franja = pygame.Rect(Config.SALV_X + m_x, Config.SALV_Y + m_y, w - m_x * 2, h - m_y * 2)
        pygame.draw.ellipse(self.pantalla, (245, 245, 245), rect_franja, width=12)

        p_x = 36
        p_y = 22
        rect_piso = pygame.Rect(Config.SALV_X + p_x, Config.SALV_Y + p_y, w - p_x * 2, h - p_y * 2)
        pygame.draw.ellipse(self.pantalla, (190, 40, 40), rect_piso)
        pygame.draw.ellipse(self.pantalla, (140, 25, 25), rect_piso, width=2)

        if sprite_border_texture:
            b_w = Config.SALV_ANCHO
            b_h = int(sprite_border_texture.get_height() * (b_w / sprite_border_texture.get_width()))
            tex_escalada = pygame.transform.scale(sprite_border_texture, (b_w, max(25, b_h)))
            
            pos_x = Config.SALV_X
            pos_y = Config.SALV_Y + (h // 2) - 5
            self.pantalla.blit(tex_escalada, (pos_x, pos_y))
            pygame.draw.arc(self.pantalla, Config.NEGRO, (Config.SALV_X, Config.SALV_Y + (h // 2) - 5, b_w, max(25, b_h)), math.pi, 2 * math.pi, 2)

    def dibujar_fondo_marino(self, algas_x):
        """Dibuja el lecho marino de arena dorada y las algas submarinas oscilantes."""
        puntos_arena = [(0, Config.ALTO)]
        for x in range(0, Config.ANCHO + 10, 20):
            y = Config.ALTO - 45 + int(math.sin(x * 0.015) * 8)
            puntos_arena.append((x, y))
        puntos_arena.append((Config.ANCHO, Config.ALTO))
        pygame.draw.polygon(self.pantalla, (218, 165, 32), puntos_arena)
        pygame.draw.polygon(self.pantalla, (139, 90, 0), puntos_arena, width=2)
        
        tiempo = pygame.time.get_ticks() * 0.0015
        for i, ax in enumerate(algas_x):
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

    def dibujar_titulo_animado(self, fuente_titulo, fuente_subtitulo, texto_titulo="CHEEP CHEEP CHANCE", texto_sub="REMAKE", centro_x=None, base_y=110):
        """Renderiza el título tridimensional estilo Mario Party con bamboleo sinusoidal."""
        if centro_x is None:
            centro_x = Config.ANCHO // 2

        tiempo = pygame.time.get_ticks() * 0.003
        bamboleo_y = math.sin(tiempo) * 5

        # Sombra 3D
        rect_shadow = fuente_titulo.render(texto_titulo, True, Config.NEGRO).get_rect(center=(centro_x + 4, base_y + 4 + bamboleo_y))
        self.pantalla.blit(fuente_titulo.render(texto_titulo, True, Config.NEGRO), rect_shadow)

        # Borde exterior grueso
        for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2), (-3, 0), (3, 0), (0, -3), (0, 3)]:
            r_stroke = fuente_titulo.render(texto_titulo, True, Config.NEGRO).get_rect(center=(centro_x + dx, base_y + dy + bamboleo_y))
            self.pantalla.blit(fuente_titulo.render(texto_titulo, True, Config.NEGRO), r_stroke)

        # Texto frontal dorado
        rect_titulo = fuente_titulo.render(texto_titulo, True, Config.AMARILLO).get_rect(center=(centro_x, base_y + bamboleo_y))
        self.pantalla.blit(fuente_titulo.render(texto_titulo, True, Config.AMARILLO), rect_titulo)

        if texto_sub:
            y_sub = base_y + 45 + bamboleo_y * 0.5
            r_sub_shadow = fuente_subtitulo.render(texto_sub, True, Config.NEGRO).get_rect(center=(centro_x + 2, y_sub + 2))
            self.pantalla.blit(fuente_subtitulo.render(texto_sub, True, Config.NEGRO), r_sub_shadow)
            r_sub = fuente_subtitulo.render(texto_sub, True, Config.BLANCO).get_rect(center=(centro_x, y_sub))
            self.pantalla.blit(fuente_subtitulo.render(texto_sub, True, Config.BLANCO), r_sub)
