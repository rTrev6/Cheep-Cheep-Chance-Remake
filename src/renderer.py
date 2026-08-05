import pygame
import math
from src.config import Config


class RenderizadorEscenario:
    """
    Encapsula todas las rutinas de renderizado del escenario:
    - Plataforma circular/elíptica modular (salvavidas).
    - Fondo marino con ondas de arena y algas animadas.
    - Título animado tridimensional estilo Mario Party.
    - Sistema de caché de fuentes para evitar re-instanciaciones a 60 FPS.
    """
    def __init__(self, pantalla):
        self.pantalla = pantalla
        self._cache_fuentes = {}

    def obtener_fuente(self, tamano):
        """Retorna una fuente de la memoria caché según su tamaño, instanciándola solo una vez."""
        if tamano not in self._cache_fuentes:
            try:
                self._cache_fuentes[tamano] = pygame.font.Font(Config.FUENTE_PRINCIPAL, tamano)
            except Exception as e:
                print(f"Error cargando fuente tamaño {tamano}: {e}")
                self._cache_fuentes[tamano] = pygame.font.SysFont("arial", tamano, bold=True)
        return self._cache_fuentes[tamano]

    def dibujar_plataforma_modular(self, sprite_platform=None, sprite_border_texture=None):
        """Dibuja la plataforma circular/elíptica con la textura de borde incorporada."""
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

    def dibujar_titulo_animado(self, texto_titulo="CHEEP CHEEP CHANCE", texto_sub="REMAKE", centro_x=None, base_y=110, tamano_titulo=56, tamano_sub=32):
        """
        Renderiza el título tridimensional multicolor con animación de olas por letra estilo Mario Party,
        utilizando la caché de fuentes optimizada.
        """
        if centro_x is None:
            centro_x = Config.ANCHO // 2

        t = pygame.time.get_ticks()
        fuente_grande = self.obtener_fuente(tamano_titulo)

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
            fuente_sub = self.obtener_fuente(tamano_sub)
            color_sub = Config.AMARILLO if (t // 300) % 2 == 0 else Config.BLANCO

            txt_sub = fuente_sub.render(texto_sub, True, color_sub)
            rect_sub = txt_sub.get_rect(center=(centro_x, base_y + 64))

            shadow_sub = fuente_sub.render(texto_sub, True, Config.NEGRO)
            rect_shadow_sub = shadow_sub.get_rect(center=(centro_x + 2, base_y + 64))

            self.pantalla.blit(shadow_sub, rect_shadow_sub)
            self.pantalla.blit(txt_sub, rect_sub)
