import pygame
import sys
from src.config import Config
from src.game import ManejadorJuego

def main():
    # Inicialización propia obligatoria desde cero
    pygame.init()
    pygame.display.set_caption("Cheep Cheep Chance Remake")
    
    # Ventana con la resolución idéntica al Launcher
    pantalla = pygame.display.set_mode((Config.ANCHO, Config.ALTO))
    
    # Instancia y ejecuta el juego (Encapsulamiento total sin globales)
    juego = ManejadorJuego(pantalla)
    juego.ejecutar()
    
    # REQUISITO CÁTEDRA: Cierre seguro y limpio al terminar
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
