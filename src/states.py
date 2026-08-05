import pygame
from abc import ABC, abstractmethod
from src.config import Config


class EstadoJuego(ABC):

    def __init__(self, juego):
        self.juego = juego

    @abstractmethod
    def manejar_evento(self, evento):
        #Procesa un evento de Pygame para el estado actual.
        pass

    @abstractmethod
    def actualizar(self, pos_mouse):
        #Actualiza la lógica del estado actual.
        pass

    def dibujar(self, superficie, pos_mouse):
       #Renderiza los elementos visuales invocando el motor de renderizado completo.
        self.juego.renderizar_pantalla_completa(pos_mouse)


class EstadoPantallaTitulo(EstadoJuego):
    #Estado de la pantalla de bienvenida parpadeante.
    def manejar_evento(self, evento):
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                self.juego.reproducir_sonido(self.juego.snd_seleccion)
                self.juego.cambiar_estado("MENU_PRINCIPAL")

    def actualizar(self, pos_mouse):
        pass


class EstadoMenuGenerico(EstadoJuego):
    def __init__(self, juego, nombre_estado):
        super().__init__(juego)
        self.nombre_estado = nombre_estado

    def manejar_evento(self, evento):
        grupo_botones = self.juego.obtener_grupo_botones_actual()

        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self.juego.procesar_click_menu(evento.pos)

        elif evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.juego.procesar_tecla_volver()
                return

            if not grupo_botones:
                return

            if evento.key in (pygame.K_DOWN, pygame.K_s):
                self.juego.indice_boton_seleccionado = (self.juego.indice_boton_seleccionado + 1) % len(grupo_botones)
                self.juego.reproducir_sonido(self.juego.snd_click)
            elif evento.key in (pygame.K_UP, pygame.K_w):
                self.juego.indice_boton_seleccionado = (self.juego.indice_boton_seleccionado - 1) % len(grupo_botones)
                self.juego.reproducir_sonido(self.juego.snd_click)
            elif evento.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                if 0 <= self.juego.indice_boton_seleccionado < len(grupo_botones):
                    btn = grupo_botones[self.juego.indice_boton_seleccionado]
                    self.juego.procesar_click_menu(btn.rect.center)

    def actualizar(self, pos_mouse):
        grupo_botones = self.juego.obtener_grupo_botones_actual()
        if grupo_botones:
            for idx, btn in enumerate(grupo_botones):
                btn.actualizar(pos_mouse)
                btn.set_resaltado_teclado(idx == self.juego.indice_boton_seleccionado)


class EstadoOpciones(EstadoJuego):
    #Estado para el menú de opciones con barras deslizantes de volumen.
    def manejar_evento(self, evento):
        self.juego.slider_musica.handle_event(evento)
        self.juego.slider_sfx.handle_event(evento)

        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self.juego.procesar_click_menu(evento.pos)
        elif evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.juego.procesar_tecla_volver()

    def actualizar(self, pos_mouse):
        self.juego.slider_musica.actualizar(pos_mouse)
        self.juego.slider_sfx.actualizar(pos_mouse)
        Config.volumen_musica = self.juego.slider_musica.value
        Config.volumen_sfx = self.juego.slider_sfx.value
        self.juego.audio.aplicar_volumen_musica()
        self.juego.audio.aplicar_volumen_sfx()


class EstadoPartida(EstadoJuego):
    #Estado activo del juego de pesca (Modo Normal y Duelo).
    def manejar_evento(self, evento):
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.juego.procesar_tecla_volver()
                return

        if getattr(self.juego, 'revelando_dramatico', False) or getattr(self.juego, 'esperando_post_seleccion', False):
            return

        jugadores_vivos = [j for j in self.juego.jugadores if j.vivo]

        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.juego.turno_actual < len(jugadores_vivos):
                j_actual = jugadores_vivos[self.juego.turno_actual]
                if not j_actual.es_cpu:
                    cuerda = self.juego.obtener_cuerda_bajo_mouse(evento.pos)
                    if cuerda and not cuerda.esta_ocupada():
                        idx = self.juego.cuerdas.index(cuerda)
                        self.juego.seleccionar_cuerda_para_jugador(idx, j_actual, jugadores_vivos)

    def actualizar(self, pos_mouse):
        pass


class EstadoPausa(EstadoJuego):
    #Estado de menú de pausa durante una partida.
    def manejar_evento(self, evento):
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.juego.procesar_tecla_volver()
                return

        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self.juego.procesar_click_menu(evento.pos)

    def actualizar(self, pos_mouse):
        grupo = self.juego.obtener_grupo_botones_actual()
        if grupo:
            for idx, btn in enumerate(grupo):
                btn.actualizar(pos_mouse)
                btn.set_resaltado_teclado(idx == self.juego.indice_boton_seleccionado)
