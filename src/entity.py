import pygame
import math
import os
import random
from abc import ABC, abstractmethod
from src.config import Config


class EntidadJuego(ABC):
    """
    Clase base abstracta para todas las entidades del juego (Jugador, Cuerda, CriaturaAmbiental).
    Aplica los pilares POO de Herencia, Abstracción y Polimorfismo.
    """
    def __init__(self, x=0, y=0, visible=True):
        self._x = x
        self._y = y
        self._visible = visible

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, valor):
        self._x = valor

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, valor):
        self._y = valor

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, valor):
        self._visible = valor

    @abstractmethod
    def actualizar(self, *args, **kwargs):
        """Actualiza el estado interno de la entidad."""
        pass

    @abstractmethod
    def dibujar(self, superficie, *args, **kwargs):
        """Dibuja la entidad sobre la superficie de Pygame especificada."""
        pass


class Jugador(EntidadJuego):
    """
    Representa a un jugador (Humano o CPU) en la partida.
    Hereda de EntidadJuego aplicando Herencia y Encapsulamiento.
    """
    COLORES_NOMBRE = {
        "Mario": (255, 70, 70),
        "Luigi": (80, 230, 80),
        "Wario": (255, 220, 40),
        "Yoshi": (140, 255, 140),
        "Peach": (255, 150, 205),
        "Daisy": (255, 170, 60),
        "Waluigi": (195, 100, 255),
        "Toad": (150, 200, 255),
    }

    def __init__(self, id, es_cpu=False, personaje=None):
        super().__init__(x=0, y=0, visible=True)
        self.id = id
        self.es_cpu = es_cpu
        self._vivo = True
        self._sumergido = False  # True apenas su sprite toca el agua
        self.cuerda_elegida = None
        self.angulo_actual = 0.0

        # Asignar personaje
        self.personaje = personaje if personaje else Config.PERSONAJES[(id - 1) % 8]

        # El nombre del jugador dependerá del personaje y si es CPU
        tipo_jugador = "CPU" if es_cpu else f"J{self.id}"
        self.nombre = f"{tipo_jugador} ({self.personaje})"

        # --- OPTIMIZACIÓN: Cargar fuentes fijas al inicializar ---
        self.fuente_name = pygame.font.Font(Config.FUENTE_PRINCIPAL, 24)
        self.fuente_cuerda = pygame.font.Font(Config.FUENTE_PRINCIPAL, 18)
        color_nombre = self.COLORES_NOMBRE.get(self.personaje, Config.BLANCO)
        self.txt_n = self.fuente_name.render(self.nombre, True, color_nombre)
        self.txt_n_sombra = self.fuente_name.render(self.nombre, True, Config.NEGRO)

        # Intentar cargar sprite de personaje si existe
        self.sprite_char = None
        filename = f"char_{self.personaje}_Sprite.png"
        path_char = Config.RUTA_IMAGENES / filename

        if not path_char.exists() and Config.RUTA_IMAGENES.exists():
            for f in Config.RUTA_IMAGENES.iterdir():
                if f.is_file() and f.name.lower() == filename.lower():
                    path_char = f
                    break

        if path_char.exists():
            try:
                self.sprite_char = pygame.image.load(str(path_char)).convert_alpha()
                self.sprite_char = pygame.transform.scale(self.sprite_char, (Config.CHAR_ANCHO, Config.CHAR_ALTO))
            except Exception as e:
                print(f"Error cargando sprite de personaje {self.personaje}: {e}")

    @property
    def vivo(self):
        return self._vivo

    @vivo.setter
    def vivo(self, valor):
        self._vivo = valor

    @property
    def sumergido(self):
        return self._sumergido

    @sumergido.setter
    def sumergido(self, valor):
        self._sumergido = valor

    def esta_activo(self):
        """Retorna True si el jugador está vivo y no sumergido."""
        return self._vivo and not self._sumergido

    def actualizar(self, *args, **kwargs):
        """Método de actualización heredado de EntidadJuego."""
        pass

    def dibujar(self, superficie):
        if not self._vivo or self._sumergido or not self.visible:
            return

        if self.sprite_char:
            superficie.blit(self.sprite_char, (self.x, self.y))

        # Dibujar nombre e indicador
        rect_n = self.txt_n.get_rect(center=(self.x + Config.CHAR_ANCHO // 2, self.y - 15))
        rect_n_sombra = self.txt_n_sombra.get_rect(center=(self.x + Config.CHAR_ANCHO // 2 + 1, self.y - 15 + 1))
        superficie.blit(self.txt_n_sombra, rect_n_sombra)
        superficie.blit(self.txt_n, rect_n)


    def dibujar_flecha(self, superficie):
        if not self._vivo or not self.visible:
            return
        desplazamiento = math.sin(pygame.time.get_ticks() * 0.01) * 4
        base_y = self.y - 40 + desplazamiento
        center_x = self.x + Config.CHAR_ANCHO // 2

        puntos = [(int(center_x), int(base_y + 12)), (int(center_x - 8), int(base_y)), (int(center_x + 8), int(base_y))]
        pygame.draw.polygon(superficie, Config.AMARILLO, puntos)
        pygame.draw.polygon(superficie, Config.NEGRO, puntos, width=2)


class Cuerda(EntidadJuego):
    """
    Representa una cuerda de pescar en el escenario.
    Hereda de EntidadJuego aplicando Herencia y Encapsulamiento.
    """
    _cache_sprite_rope = None
    _cache_sprite_fish = None
    _cache_sprite_monster1 = None
    _cache_sprite_monster2 = None

    def __init__(self, id, x, y_inicio):
        super().__init__(x=int(x), y=int(y_inicio), visible=True)
        self.id = id
        self.y_inicio = int(y_inicio)
        self.y_fin = Config.NIVEL_AGUA + 60  # Altura en reposo inicial bajo el agua

        self._ocupada_por = None
        self._contenido = "Pez Bueno"
        self._atrapado = False

        # --- OPTIMIZACIÓN: Cargar fuentes una sola vez ---
        self.fuente_n = pygame.font.Font(Config.FUENTE_PRINCIPAL, 22)
        self.txt_id = self.fuente_n.render(str(self.id), True, Config.BLANCO)

        if Cuerda._cache_sprite_rope is None:
            try:
                Cuerda._cache_sprite_rope = pygame.image.load(str(Config.SPRITE_ROPE)).convert_alpha()
            except Exception as e:
                print(f"Error cargando sprite de cuerda: {e}")
                Cuerda._cache_sprite_rope = pygame.Surface((10, 10), pygame.SRCALPHA)
                Cuerda._cache_sprite_rope.fill(Config.MADERA_CUERDA)
        self.sprite_rope = Cuerda._cache_sprite_rope
        self.ancho_sprite = self.sprite_rope.get_width()

        if Cuerda._cache_sprite_fish is None:
            try:
                Cuerda._cache_sprite_fish = pygame.image.load(str(Config.SPRITE_FISH_FISHED)).convert_alpha()
            except Exception as e:
                print(f"Error cargando sprite de pez: {e}")
                Cuerda._cache_sprite_fish = pygame.Surface((64, 64), pygame.SRCALPHA)

        if Cuerda._cache_sprite_monster1 is None:
            try:
                raw_m1 = pygame.image.load(str(Config.SPRITE_MONSTER_FISHED)).convert_alpha()
                w1, h1 = raw_m1.get_size()
                Cuerda._cache_sprite_monster1 = pygame.transform.smoothscale(raw_m1, (int(w1 * 1.35), int(h1 * 1.0)))
            except Exception as e:
                print(f"Error cargando sprite de monstruo 1: {e}")
                Cuerda._cache_sprite_monster1 = pygame.Surface((48, 140), pygame.SRCALPHA)

        if Cuerda._cache_sprite_monster2 is None:
            try:
                raw_m2 = pygame.image.load(str(Config.SPRITE_MONSTER2_FISHED)).convert_alpha()
                w2, h2 = raw_m2.get_size()
                Cuerda._cache_sprite_monster2 = pygame.transform.smoothscale(raw_m2, (int(w2 * 1.20), int(h2 * 0.85)))
            except Exception as e:
                print(f"Error cargando sprite de monstruo 2: {e}")
                Cuerda._cache_sprite_monster2 = pygame.Surface((70, 96), pygame.SRCALPHA)

        self.sprite_fish = Cuerda._cache_sprite_fish
        self.sprite_monster1 = Cuerda._cache_sprite_monster1
        self.sprite_monster2 = Cuerda._cache_sprite_monster2

        self._cache_segmentos_curvos = None
        self._precalcular_segmentos_curvos()

    @property
    def ocupada_por(self):
        return self._ocupada_por

    @ocupada_por.setter
    def ocupada_por(self, jugador):
        self._ocupada_por = jugador

    @property
    def contenido(self):
        return self._contenido

    @contenido.setter
    def contenido(self, valor):
        self._contenido = valor

    @property
    def atrapado(self):
        return self._atrapado

    @atrapado.setter
    def atrapado(self, valor):
        self._atrapado = valor

    def esta_ocupada(self):
        return self._ocupada_por is not None

    def _precalcular_segmentos_curvos(self):
        """Precalcula los segmentos 3D curvos de la cuerda para acelerar el renderizado a 60 FPS."""
        grosor = 32
        cx = Config.SALV_X + Config.SALV_ANCHO // 2
        x_in = int(cx + (self.x - cx) * 0.44)
        y_in = Config.SALV_Y + int(Config.SALV_ALTO * 0.50)
        x_out = self.x
        y_out = self.y_inicio
        x_ctrl = (x_in + x_out) // 2
        y_ctrl = y_in - 10

        num_pasos = 25
        puntos_curva = []
        for i in range(num_pasos + 1):
            t = i / num_pasos
            inv_t = 1.0 - t
            px = inv_t * inv_t * x_in + 2 * inv_t * t * x_ctrl + t * t * x_out
            py = inv_t * inv_t * y_in + 2 * inv_t * t * y_ctrl + t * t * y_out
            puntos_curva.append((px, py))

        w_cr, h_cr = self.sprite_rope.get_size()
        rope_clean = self.sprite_rope.subsurface((0, 4, w_cr, max(1, h_cr - 8)))

        self._cache_segmentos_curvos = []
        for i in range(len(puntos_curva) - 1):
            p1 = puntos_curva[i]
            p2 = puntos_curva[i + 1]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            dist = max(1, int(math.hypot(dx, dy)))
            ang = math.degrees(math.atan2(dy, dx)) - 90
            surf_seg = pygame.transform.scale(rope_clean, (grosor, dist + 4))
            surf_seg_rot = pygame.transform.rotate(surf_seg, -ang)
            rect_seg = surf_seg_rot.get_rect(center=((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2))
            self._cache_segmentos_curvos.append((surf_seg_rot, rect_seg))

    def actualizar(self, *args, **kwargs):
        """Método de actualización heredado de EntidadJuego."""
        pass

    def dibujar(self, superficie, revelado_total=False, en_proceso=False, resaltada=False):
        if not self.visible:
            return

        largo_actual = int(self.y_fin - self.y_inicio)

        # 0. RESALTADO AL PASAR/APUNTAR EL MOUSE
        if resaltada and self._ocupada_por is None:
            if not hasattr(self, '_glow_surf') or self._glow_surf.get_height() != max(1, largo_actual + 16):
                self._glow_surf = pygame.Surface((32, max(1, largo_actual + 16)), pygame.SRCALPHA)
                pygame.draw.rect(self._glow_surf, (255, 215, 0, 110), (0, 0, 32, max(1, largo_actual + 16)), border_radius=6)
            superficie.blit(self._glow_surf, (self.x - 16, self.y_inicio - 8))

            bamboleo_arrow = math.sin(pygame.time.get_ticks() * 0.01) * 4
            y_base_arrow = self.y_inicio - 16 + bamboleo_arrow
            puntos_flecha = [
                (self.x, int(y_base_arrow + 12)),
                (self.x - 9, int(y_base_arrow)),
                (self.x + 9, int(y_base_arrow))
            ]
            pygame.draw.polygon(superficie, Config.AMARILLO, puntos_flecha)
            pygame.draw.polygon(superficie, Config.NEGRO, puntos_flecha, width=2)

        # 1. DIBUJAR CUERDA CURVEADA EN 3D SOBRE EL SALVAVIDAS
        if largo_actual > 0:
            if self._cache_segmentos_curvos is None:
                self._precalcular_segmentos_curvos()

            for surf_seg_rot, rect_seg in self._cache_segmentos_curvos:
                superficie.blit(surf_seg_rot, rect_seg)

            y_start_vert = self.y_inicio - 10
            largo_vert = int(self.y_fin - y_start_vert)
            if largo_vert > 0:
                cuerda_vert = pygame.transform.scale(self.sprite_rope, (32, largo_vert))
                superficie.blit(cuerda_vert, (self.x - 16, y_start_vert))

        # 2. REVELAR RECOMPENSAS PESCADAS
        debe_dibujar = False
        if self._contenido == "Pez Bueno":
            if en_proceso or self._atrapado:
                sprite_c = self.sprite_fish
                debe_dibujar = True
        else:
            if en_proceso or self._atrapado:
                sprite_c = self.sprite_monster2 if self._contenido in ("Monstruo 2", "Monstruo_2") else self.sprite_monster1
                debe_dibujar = True

        if debe_dibujar:
            cw = sprite_c.get_width()
            ch = sprite_c.get_height()
            off_x = 12 if self._contenido == "Pez Bueno" else 0
            y_item = max(Config.NIVEL_AGUA + 40, self.y_fin)
            superficie.blit(sprite_c, (self.x - cw // 2 + off_x, y_item - ch // 2))

    def contiene_punto(self, pos_mouse, umbral_x=30):
        """Determina si una posición del mouse cae sobre el área clicable de esta cuerda."""
        mx, my = pos_mouse
        if not (self.y_inicio - 20 <= my <= self.y_fin + 40):
            return False
        return abs(self.x - mx) <= umbral_x


class CriaturaAmbiental(EntidadJuego):
    """
    Representa una criatura marina del fondo (peces, monstruos) que nada autónomamente.
    Hereda de EntidadJuego aplicando Herencia y Polimorfismo.
    """
    def __init__(self, ruta_izquierda=None, ruta_derecha=None, es_pez=False, escala_factor=1.0, es_zigzag=False):
        super().__init__(x=0, y=0, visible=True)
        self.ruta_izquierda = ruta_izquierda
        self.ruta_derecha = ruta_derecha
        self.es_pez = es_pez
        self.escala_factor = escala_factor
        self.es_zigzag = es_zigzag
        self.sprite_izq_original = None
        self.sprite_der_original = None

        if ruta_izquierda and os.path.exists(ruta_izquierda):
            try:
                self.sprite_izq_original = pygame.image.load(str(ruta_izquierda)).convert_alpha()
            except Exception as e:
                print(f"Error cargando sprite ambiental {ruta_izquierda}: {e}")

        if ruta_derecha and os.path.exists(ruta_derecha):
            try:
                self.sprite_der_original = pygame.image.load(str(ruta_derecha)).convert_alpha()
            except Exception as e:
                print(f"Error cargando sprite ambiental {ruta_derecha}: {e}")

        if self.sprite_izq_original and not self.sprite_der_original:
            self.sprite_der_original = pygame.transform.flip(self.sprite_izq_original, True, False)
        elif self.sprite_der_original and not self.sprite_izq_original:
            self.sprite_izq_original = pygame.transform.flip(self.sprite_der_original, True, False)

        self.sprite = None
        self.y_base = 0
        self.fase_zigzag = random.uniform(0, 6.28)
        self.amplitud_zigzag = 40.0
        self.frecuencia_zigzag = 0.03
        self.reiniciar()
        self.x = random.randint(0, Config.ANCHO)

    def reiniciar(self):
        self.direccion = random.choice([1, -1])

        if self.direccion == 1:
            sprite_base = self.sprite_der_original or self.sprite_izq_original
        else:
            sprite_base = self.sprite_izq_original or self.sprite_der_original

        if sprite_base:
            w_orig = sprite_base.get_width()
            h_orig = sprite_base.get_height()
            factor = random.uniform(0.85, 1.15) * self.escala_factor
            self.ancho = int(w_orig * factor)
            self.alto = int(h_orig * factor)
            self.sprite = pygame.transform.scale(sprite_base, (self.ancho, self.alto))

            color_tinte = random.choice([
                (255, 255, 255, 255),
                (255, 130, 130, 255),
                (130, 255, 130, 255),
                (255, 220, 100, 255),
                (130, 190, 255, 255),
                (230, 130, 255, 255)
            ])
            if self.es_pez and color_tinte != (255, 255, 255, 255):
                tinte_surf = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
                tinte_surf.fill(color_tinte)
                self.sprite.blit(tinte_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        else:
            self.ancho = 50
            self.alto = 30
            self.sprite = None

        self.velocidad = random.uniform(0.8, 2.2)
        self.y_base = random.randint(Config.NIVEL_AGUA + 50, Config.ALTO - self.alto - 60)
        self.y = self.y_base
        self.fase_zigzag = random.uniform(0.0, 6.28)
        self.amplitud_zigzag = random.uniform(30.0, 50.0)
        self.frecuencia_zigzag = random.uniform(0.02, 0.04)

        if self.direccion == 1:
            self.x = -self.ancho - random.randint(10, 300)
        else:
            self.x = Config.ANCHO + random.randint(10, 300)

    def actualizar(self, *args, **kwargs):
        self.x += self.direccion * self.velocidad

        if self.es_zigzag:
            self.y = self.y_base + math.sin(self.x * self.frecuencia_zigzag + self.fase_zigzag) * self.amplitud_zigzag
            self.y = max(Config.NIVEL_AGUA + 20, min(Config.ALTO - self.alto - 20, self.y))

        if self.direccion == 1 and self.x > Config.ANCHO + 100:
            self.reiniciar()
        elif self.direccion == -1 and self.x < -self.ancho - 100:
            self.reiniciar()

    def dibujar(self, superficie):
        if not self.visible:
            return
        if self.sprite:
            superficie.blit(self.sprite, (self.x, self.y))
        else:
            color_reserva = (40, 120, 160)
            pygame.draw.ellipse(superficie, color_reserva, (self.x, self.y, self.ancho, self.alto))