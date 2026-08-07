from pathlib import Path

RUTA_RAIZ = Path(__file__).resolve().parent.parent
RUTA_ASSETS = RUTA_RAIZ / "assets"
RUTA_IMAGENES = RUTA_ASSETS / "sprites"
RUTA_FUENTES = RUTA_ASSETS / "fonts"
RUTA_SONIDOS = RUTA_ASSETS / "sounds"

class Config:
    RUTA_IMAGENES = RUTA_IMAGENES
    RUTA_FUENTES = RUTA_FUENTES
    RUTA_SONIDOS = RUTA_SONIDOS
    RUTA_MUSICA = RUTA_SONIDOS / "music"
    RUTA_SFX = RUTA_SONIDOS / "sfx"

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
    
    FUENTE_PRINCIPAL = RUTA_FUENTES / "sm256.ttf"
    
    # Rutas a los archivos de sprites
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
    SPRITE_FISH2_LEFT = RUTA_IMAGENES / "sprite_fish2_left.png"
    SPRITE_FISH2_RIGHT = RUTA_IMAGENES / "sprite_fish2_right.png"
    SPRITE_FISH2_FISHED = RUTA_IMAGENES / "sprite_fish2_fished.png"
    SPRITE_FISH3_LEFT = RUTA_IMAGENES / "sprite_fish3_left.png"
    SPRITE_FISH3_RIGHT = RUTA_IMAGENES / "sprite_fish3_right.png"
    SPRITE_FISH3_FISHED = RUTA_IMAGENES / "sprite_fish3_fished.png"
    SPRITE_FISH4_LEFT = RUTA_IMAGENES / "sprite_fish4_left.png"
    SPRITE_FISH4_RIGHT = RUTA_IMAGENES / "sprite_fish4_right.png"
    SPRITE_FISH4_FISHED = RUTA_IMAGENES / "sprite_fish4_fished.png"
    SPRITE_MONSTER3_LEFT = RUTA_IMAGENES / "sprite_monster3_left.png"
    SPRITE_MONSTER3_RIGHT = RUTA_IMAGENES / "sprite_monster3_right.png"
    SPRITE_MONSTER3_FISHED = RUTA_IMAGENES / "sprite_monster3_fished.png"
    SPRITE_MONSTER4_LEFT = RUTA_IMAGENES / "sprite_monster4_left.png"
    SPRITE_MONSTER4_RIGHT = RUTA_IMAGENES / "sprite_monster4_right.png"
    SPRITE_MONSTER4_FISHED = RUTA_IMAGENES / "sprite_monster4_fished.png"
    SPRITE_MONSTER5 = RUTA_IMAGENES / "sprite_monster5.png"
    SPRITE_BACKGROUND_TOP = RUTA_IMAGENES / "sea_background_claro.png"
    SPRITE_BACKGROUND_BOTTOM = RUTA_IMAGENES / "sea_background.png"
    SPRITE_BACKGROUND = RUTA_IMAGENES / "menuframe.png"
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
    # opciones.
    volumen_musica = 0.3
    volumen_sfx = 0.5
