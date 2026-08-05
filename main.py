import pygame
import sys
from src.config import *
from src.game import *

def main():
    pygame.init()
    pygame.display.set_caption("Cheep Cheep Chance Remake")
    
    ruta_icono = Config.RUTA_IMAGENES / "icon_Kamek.png"
    if ruta_icono.exists():
        try:
            icono = pygame.image.load(str(ruta_icono))
            pygame.display.set_icon(icono)
        except Exception as e:
            print(f"Error cargando icono de ventana: {e}")
    
    pantalla = pygame.display.set_mode((Config.ANCHO, Config.ALTO))
    
    juego = ManejadorJuego(pantalla)
    juego.ejecutar()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()