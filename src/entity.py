import pygame
import math
import os
import random
from src.config import Config
from src.ui import Boton, Slider


class Jugador:
    # Colores vivos por personaje para el nombre que flota sobre el sprite
    # (se dibujan sobre el fondo marino oscuro, por eso son tonos brillantes)
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
        self.id = id
        self.es_cpu = es_cpu
        self.vivo = True
        self.sumergido = False  # True apenas su sprite toca el agua (para ocultarlo antes de llegar al fondo)
        self.cuerda_elegida = None
        self.x = 0
        self.y = 0
        self.angulo_actual = 0.0
        
        # Asignar personaje
        self.personaje = personaje if personaje else Config.PERSONAJES[(id - 1) % 8]
        
        # El nombre del jugador dependerá del personaje y si es CPU
        tipo_jugador = "CPU" if es_cpu else f"J{self.id}"
        self.nombre = f"{tipo_jugador} ({self.personaje})"
        
        # --- OPTIMIZACIÓN: Cargar fuentes fijas al inicializar ---
        # Nombre un poco más grande y coloreado según el personaje
        self.fuente_name = pygame.font.Font(Config.FUENTE_PRINCIPAL, 24)
        self.fuente_cuerda = pygame.font.Font(Config.FUENTE_PRINCIPAL, 18)
        color_nombre = self.COLORES_NOMBRE.get(self.personaje, Config.BLANCO)
        self.txt_n = self.fuente_name.render(self.nombre, True, color_nombre)
        self.txt_n_sombra = self.fuente_name.render(self.nombre, True, Config.NEGRO)
        
        # Intentar cargar sprite de personaje si existe en la carpeta (char_{Personaje}_Sprite.png)
        self.sprite_char = None
        filename = f"char_{self.personaje}_Sprite.png"
        path_char = Config.RUTA_IMAGENES / filename
        
        # Búsqueda insensible a mayúsculas
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

    def dibujar(self, superficie):
        if not self.vivo or self.sumergido: return
        
        if self.sprite_char:
            superficie.blit(self.sprite_char, (self.x, self.y))
        else:
            # Dibujo vectorial de fallback detallado para los 8 personajes (60x75 px)
            c_camisa = (200, 0, 0)
            c_overol = (10, 30, 150)
            c_gorra = (200, 0, 0)
            c_pelo = (100, 50, 0)
            es_hongo = False
            es_corona = False
            es_yoshi = False
            
            if self.personaje == "Luigi":
                c_camisa = (0, 180, 0)
                c_overol = (10, 30, 150)
                c_gorra = (0, 180, 0)
            elif self.personaje == "Wario":
                c_camisa = (255, 215, 0)    # Amarillo
                c_overol = (128, 0, 128)    # Morado
                c_gorra = (255, 215, 0)
            elif self.personaje == "Yoshi":
                es_yoshi = True
                c_camisa = (50, 205, 50)    # Verde
                c_overol = (255, 255, 255)  # Blanco
                c_gorra = (255, 100, 0)     # Zapatos naranja
            elif self.personaje == "Peach":
                c_camisa = (255, 182, 193)  # Rosa claro
                c_overol = (255, 105, 180)  # Vestido rosa oscuro
                c_gorra = (255, 215, 0)     # Corona dorada
                c_pelo = (255, 220, 100)    # Rubio
                es_corona = True
            elif self.personaje == "Daisy":
                c_camisa = (255, 215, 0)    # Amarillo
                c_overol = (255, 140, 0)    # Naranja
                c_gorra = (255, 215, 0)     # Corona dorada
                c_pelo = (139, 69, 19)      # Castaño
                es_corona = True
            elif self.personaje == "Waluigi":
                c_camisa = (128, 0, 128)    # Morado
                c_overol = (40, 40, 50)     # Gris/Negro
                c_gorra = (128, 0, 128)
            elif self.personaje == "Toad":
                es_hongo = True
                c_camisa = (255, 255, 255)  # Blanco
                c_overol = (10, 30, 150)    # Chaleco azul
                c_gorra = (220, 20, 60)     # Puntos rojos
                
            if es_yoshi:
                # Yoshi
                # Cola y cuerpo verde
                pygame.draw.circle(superficie, (50, 205, 50), (self.x + 30, self.y + 45), 20)
                # Panza blanca
                pygame.draw.circle(superficie, (255, 255, 255), (self.x + 30, self.y + 45), 13)
                # Zapatos/Botas
                pygame.draw.ellipse(superficie, (255, 100, 0), (self.x + 12, self.y + 60, 16, 12))
                pygame.draw.ellipse(superficie, (255, 100, 0), (self.x + 32, self.y + 60, 16, 12))
                # Montura roja en la espalda
                pygame.draw.circle(superficie, (200, 0, 0), (self.x + 10, self.y + 40), 7)
                # Cabeza verde
                pygame.draw.circle(superficie, (50, 205, 50), (self.x + 30, self.y + 22), 14)
                # Hocico blanco
                pygame.draw.ellipse(superficie, (255, 255, 255), (self.x + 14, self.y + 18, 22, 16))
                # Mejilla verde
                pygame.draw.circle(superficie, (50, 205, 50), (self.x + 30, self.y + 24), 8)
                # Ojos y pupilas
                pygame.draw.ellipse(superficie, Config.BLANCO, (self.x + 24, self.y + 10, 8, 12))
                pygame.draw.ellipse(superficie, Config.BLANCO, (self.x + 32, self.y + 10, 8, 12))
                pygame.draw.ellipse(superficie, (0, 0, 255), (self.x + 26, self.y + 12, 4, 8))
                pygame.draw.ellipse(superficie, (0, 0, 255), (self.x + 34, self.y + 12, 4, 8))
                # Crestas rojas detrás
                pygame.draw.circle(superficie, (200, 0, 0), (self.x + 42, self.y + 14), 5)
                pygame.draw.circle(superficie, (200, 0, 0), (self.x + 42, self.y + 22), 5)
                
                pygame.draw.circle(superficie, Config.NEGRO, (self.x + 30, self.y + 22), 14, 2)
                pygame.draw.circle(superficie, Config.NEGRO, (self.x + 30, self.y + 45), 20, 2)
            elif es_hongo:
                # Toad
                # Pantalones/cuerpo blanco
                pygame.draw.rect(superficie, (255, 255, 255), (self.x + 10, self.y + 35, 40, 30), border_radius=6)
                # Chaleco azul
                pygame.draw.rect(superficie, (10, 30, 150), (self.x + 8, self.y + 35, 44, 18), border_radius=4)
                pygame.draw.rect(superficie, (255, 215, 0), (self.x + 8, self.y + 35, 44, 18), 2, border_radius=4)
                # Cabeza (Piel)
                pygame.draw.circle(superficie, (255, 218, 185), (self.x + 30, self.y + 22), 13)
                # Sombrero de hongo
                pygame.draw.ellipse(superficie, Config.BLANCO, (self.x + 4, self.y - 12, 52, 34))
                pygame.draw.ellipse(superficie, Config.NEGRO, (self.x + 4, self.y - 12, 52, 34), 2)
                # Círculos rojos
                pygame.draw.circle(superficie, (220, 20, 60), (self.x + 30, self.y - 4), 8)
                pygame.draw.circle(superficie, (220, 20, 60), (self.x + 12, self.y + 2), 6)
                pygame.draw.circle(superficie, (220, 20, 60), (self.x + 48, self.y + 2), 6)
                pygame.draw.circle(superficie, (220, 20, 60), (self.x + 30, self.y - 10), 5)
                # Ojos
                pygame.draw.circle(superficie, Config.NEGRO, (self.x + 25, self.y + 22), 2)
                pygame.draw.circle(superficie, Config.NEGRO, (self.x + 35, self.y + 22), 2)
                
                pygame.draw.rect(superficie, Config.NEGRO, (self.x + 10, self.y + 35, 40, 30), 2, border_radius=6)
            else:
                # Mario, Luigi, Wario, Waluigi, Peach, Daisy
                if es_corona:
                    pygame.draw.circle(superficie, c_pelo, (self.x + 18, self.y + 20), 12)
                    pygame.draw.circle(superficie, c_pelo, (self.x + 42, self.y + 20), 12)
                    # Vestido
                    pygame.draw.rect(superficie, c_overol, (self.x + 5, self.y + 30, 50, 36), border_radius=8)
                    pygame.draw.rect(superficie, c_camisa, (self.x + 2, self.y + 24, 56, 12), border_radius=3)
                    # Cabeza
                    pygame.draw.circle(superficie, (255, 218, 185), (self.x + 30, self.y + 18), 13)
                    # Corona
                    puntos = [(self.x + 18, self.y + 6), (self.x + 24, self.y - 4), (self.x + 30, self.y + 6), 
                              (self.x + 36, self.y - 4), (self.x + 42, self.y + 6)]
                    pygame.draw.polygon(superficie, c_gorra, puntos)
                    pygame.draw.polygon(superficie, Config.NEGRO, puntos, 2)
                    pygame.draw.circle(superficie, (0, 0, 255) if self.personaje=="Peach" else (0, 180, 0), (self.x + 24, self.y - 4), 2)
                    pygame.draw.circle(superficie, (220, 20, 60), (self.x + 30, self.y + 4), 2)
                    pygame.draw.circle(superficie, (0, 0, 255) if self.personaje=="Peach" else (0, 180, 0), (self.x + 36, self.y - 4), 2)
                else:
                    # Overol
                    pygame.draw.rect(superficie, c_overol, (self.x + 5, self.y + 30, 50, 36), border_radius=4)
                    pygame.draw.rect(superficie, c_camisa, (self.x + 8, self.y + 22, 44, 12))
                    # Cabeza
                    pygame.draw.circle(superficie, (255, 218, 185), (self.x + 30, self.y + 18), 13)
                    # Gorra
                    pygame.draw.ellipse(superficie, c_gorra, (self.x + 16, self.y - 1, 28, 14))
                    pygame.draw.line(superficie, c_gorra, (self.x + 15, self.y + 6), (self.x + 45, self.y + 6), 4)
                    pygame.draw.ellipse(superficie, Config.NEGRO, (self.x + 16, self.y - 1, 28, 14), 2)
                
                # Ojos
                pygame.draw.circle(superficie, Config.BLANCO, (self.x + 24, self.y + 16), 3)
                pygame.draw.circle(superficie, Config.BLANCO, (self.x + 36, self.y + 16), 3)
                pygame.draw.circle(superficie, Config.NEGRO, (self.x + 24, self.y + 16), 1)
                pygame.draw.circle(superficie, Config.NEGRO, (self.x + 36, self.y + 16), 1)
                
                # Bigote
                if self.personaje in ["Mario", "Luigi", "Wario", "Waluigi"]:
                    c_bigote = Config.NEGRO
                    if self.personaje == "Wario": c_bigote = (90, 50, 0)
                    pygame.draw.rect(superficie, c_bigote, (self.x + 22, self.y + 22, 16, 4), border_radius=1)
                
                pygame.draw.rect(superficie, Config.NEGRO, (self.x + 5, self.y + 30, 50, 36), 2, border_radius=8 if es_corona else 4)

        # Dibujar nombre e indicador de cuerda
        rect_n = self.txt_n.get_rect(center=(self.x + Config.CHAR_ANCHO // 2, self.y - 15))
        rect_n_sombra = self.txt_n_sombra.get_rect(center=(self.x + Config.CHAR_ANCHO // 2 + 1, self.y - 15 + 1))
        superficie.blit(self.txt_n_sombra, rect_n_sombra)
        superficie.blit(self.txt_n, rect_n)
        


    def dibujar_flecha(self, superficie):
        if not self.vivo: return
        desplazamiento = math.sin(pygame.time.get_ticks() * 0.01) * 4
        base_y = self.y - 40 + desplazamiento
        center_x = self.x + Config.CHAR_ANCHO // 2

        puntos = [(int(center_x), int(base_y + 12)), (int(center_x - 8), int(base_y)), (int(center_x + 8), int(base_y))]
        pygame.draw.polygon(superficie, Config.AMARILLO, puntos)
        pygame.draw.polygon(superficie, Config.NEGRO, puntos, width=2)


class Cuerda:
    _cache_sprite_rope = None
    _cache_sprite_fish = None
    _cache_sprite_monster1 = None
    _cache_sprite_monster2 = None

    def __init__(self, id, x, y_inicio):
        self.id = id
        self.x = int(x)
        self.y_inicio = int(y_inicio)
        
        # Altura en reposo inicial bajo el agua
        self.y_fin = Config.NIVEL_AGUA + 60  
        
        self.ocupada_por = None
        self.contenido = "Pez Bueno"
        self.atrapado = False  
        
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

        # Carga de sprites reales pescados ("_fished") manteniendo dimensiones naturales
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

    def _precalcular_segmentos_curvos(self):
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

    def dibujar(self, superficie, revelado_total, en_proceso=False, resaltada=False):
        largo_actual = int(self.y_fin - self.y_inicio)

        # 0. RESALTADO AL PASAR/APUNTAR EL MOUSE (Flecha animada + Viga translúcida sin círculo)
        if resaltada and self.ocupada_por is None:
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

        # 1. DIBUJAR CUERDA CURVEADA EN 3D SOBRE EL SALVAVIDAS (USANDO CACHÉ OPTIMIZADA DE SEGMENTOS)
        if largo_actual > 0:
            if self._cache_segmentos_curvos is None:
                self._precalcular_segmentos_curvos()

            for surf_seg_rot, rect_seg in self._cache_segmentos_curvos:
                superficie.blit(surf_seg_rot, rect_seg)

            # B) Tramo vertical colgante recto (solapado 10px hacia arriba para ELIMINAR la separación en el borde)
            y_start_vert = self.y_inicio - 10
            largo_vert = int(self.y_fin - y_start_vert)
            if largo_vert > 0:
                cuerda_vert = pygame.transform.scale(self.sprite_rope, (32, largo_vert))
                superficie.blit(cuerda_vert, (self.x - 16, y_start_vert))

        # 2. REVELAR RECOMPENSAS PESCADAS (Visibles de forma clara e inmediata al pescar)
        debe_dibujar = False
        if self.contenido == "Pez Bueno":
            if en_proceso or self.atrapado:
                sprite_c = self.sprite_fish
                debe_dibujar = True
        else:
            # Los monstruos SOLO se muestran cuando un jugador los pesca en vivo, NO en la revelación final automática
            if en_proceso or self.atrapado:
                sprite_c = self.sprite_monster2 if self.contenido in ("Monstruo 2", "Monstruo_2") else self.sprite_monster1
                debe_dibujar = True

        if debe_dibujar:
            cw = sprite_c.get_width()
            ch = sprite_c.get_height()
            # Desplazar el Pez Bueno 6px a la derecha para alinearse perfectamente con el nudo y cuerda
            off_x = 12 if self.contenido == "Pez Bueno" else 0
            y_item = max(Config.NIVEL_AGUA + 40, self.y_fin)
            superficie.blit(sprite_c, (self.x - cw // 2 + off_x, y_item - ch // 2))

    def contiene_punto(self, pos_mouse, umbral_x=30):
        """Determina si una posición del mouse cae sobre el área clicable de esta cuerda."""
        mx, my = pos_mouse
        if not (self.y_inicio - 20 <= my <= self.y_fin + 40):
            return False
        return abs(self.x - mx) <= umbral_x


class CriaturaAmbiental:
    """
    Representa una criatura marina del fondo (peces, monstruo 1, monstruo 2, etc.)
    que utiliza los sprites reales manteniendo sus proporciones naturales
    de aspecto y nado autónomo.
    """
    def __init__(self, ruta_izquierda=None, ruta_derecha=None, es_pez=False, escala_factor=1.0):
        self.ruta_izquierda = ruta_izquierda
        self.ruta_derecha = ruta_derecha
        self.es_pez = es_pez
        self.escala_factor = escala_factor
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

        self.sprite = None
        self.reiniciar()
        self.x = random.randint(0, Config.ANCHO)

    def reiniciar(self):
        # 1. Dirección de nado
        self.direccion = random.choice([1, -1])
        
        # 2. Elegir el sprite ya orientado según la dirección real de nado
        if self.direccion == 1:
            sprite_base = self.sprite_der_original or self.sprite_izq_original
        else:
            sprite_base = self.sprite_izq_original or self.sprite_der_original

        if sprite_base:
            w_orig = sprite_base.get_width()
            h_orig = sprite_base.get_height()
            
            # Mantener la proporción de aspecto natural original del sprite
            factor = random.uniform(0.85, 1.15) * self.escala_factor
            self.ancho = int(w_orig * factor)
            self.alto = int(h_orig * factor)

            self.sprite = pygame.transform.scale(sprite_base, (self.ancho, self.alto))

            color_tinte = random.choice([
                (255, 255, 255, 255), # Original
                (255, 130, 130, 255), # Rojo
                (130, 255, 130, 255), # Verde
                (255, 220, 100, 255), # Dorado
                (130, 190, 255, 255), # Celeste
                (230, 130, 255, 255)  # Violeta
            ])
            if self.es_pez and color_tinte != (255, 255, 255, 255):
                tinte_surf = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
                tinte_surf.fill(color_tinte)
                self.sprite.blit(tinte_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        else:
            self.ancho = 50
            self.alto = 30
            self.sprite = None

        # 3. Velocidad
        self.velocidad = random.uniform(0.8, 2.2)
        
        # 4. Posición vertical (siempre bajo el agua)
        self.y = random.randint(Config.NIVEL_AGUA + 20, Config.ALTO - self.alto - 60)
        
        # 5. Posición horizontal inicial fuera de pantalla
        if self.direccion == 1:
            self.x = -self.ancho - random.randint(10, 300)
        else:
            self.x = Config.ANCHO + random.randint(10, 300)

    def actualizar(self):
        self.x += self.direccion * self.velocidad
        
        if self.direccion == 1 and self.x > Config.ANCHO + 100:
            self.reiniciar()
        elif self.direccion == -1 and self.x < -self.ancho - 100:
            self.reiniciar()

    def dibujar(self, superficie):
        if self.sprite:
            superficie.blit(self.sprite, (self.x, self.y))
        else:
            color_reserva = (40, 120, 160)
            pygame.draw.ellipse(superficie, color_reserva, (self.x, self.y, self.ancho, self.alto))