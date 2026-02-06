"""
Punto de entrada principal para Neon Tetris PRO.
Gestiona el bucle de juego, la entrada del usuario, los estados de los niveles,
mecánicas de Hold, Combos y efectos especiales.
"""

import pygame
import sys
import random
import config
import logic
import renderer
import models
from audio import audio_engine

class Game:
    """Clase maestra que controla una sesión de juego."""

    def __init__(self, mode="JOKER"):
        """Inicializa el estado del juego.
        
        Args:
            mode (str): Modo de juego activo (CLASSIC, JOKER, RANDOM, ZEN).
        """
        self.mode = mode
        self.locked_positions = {}  # Bloques que ya han caído y están fijos: (x,y) -> Color
        self.grid = logic.create_grid()
        self.change_piece = False   # Flag para indicar que la pieza actual ha aterrizado
        self.run = True
        
        # Gestión de piezas (Sistema 7-Bag para equilibrio profesional)
        self.bag = []
        self.current_piece = self.get_bag_shape()
        self.next_pieces = [self.get_bag_shape(), self.get_bag_shape()]
        self.hold_piece = None      # Pieza guardada con 'C'
        self.can_hold = True        # Solo permite un cambio por turno
        
        # Estadísticas y progresión
        self.score = 0
        self.total_lines = 0
        self.level = 1
        self.combo = 0              # Multiplicador por limpiezas consecutivas
        self.fall_speed = 0.27      # Velocidad base de caída
        self.fall_time = 0
        self.particles = []         # Efectos visuales activos
        
        # --- NUEVA MECÁNICA: LOCK DELAY (Tiempo de Gracia) ---
        self.lock_timer = 0         # Tiempo que la pieza lleva en el suelo
        self.lock_delay_max = 500   # 500ms de gracia antes de fijarse
        self.lock_move_count = 0    # Contador de movimientos/rotaciones en el suelo
        self.lock_move_limit = 15   # Límite para evitar stall infinito
        self.is_on_ground = False   # Flag para activar el timer
        self.lightnings = []        # Efectos de truenos activos
        
        # --- MECÁNICAS PROFESIONALES (Tetris Guideline) ---
        self.key_timers = {pygame.K_LEFT: 0, pygame.K_RIGHT: 0, pygame.K_DOWN: 0}
        self.das_delay = 170  # ms antes de empezar a repetir
        self.arr_delay = 35   # ms entre cada paso de repetición
        self.back_to_back = False # Flag para bonus de Tetrises consecutivos
        self.last_raw_time = 0

        # Efectos de 'Madness'
        self.is_glitched = False
        self.glitch_timer = 0
        self.glitch_offset = (0,0)

    def update(self, clock):
        """Actualiza la lógica del juego en cada frame."""
        raw_time = clock.get_rawtime()
        self.last_raw_time = raw_time
        self.grid = logic.create_grid(self.locked_positions)
        self.fall_time += raw_time
        
        # --- CÁLCULO DE DIFICULTAD ---
        self.level = 1 + (self.total_lines // 10)
        # La pieza cae 10% más rápido por cada nivel aumentado
        actual_speed = self.fall_speed * (0.9 ** (self.level - 1))
        if self.mode == "ZEN": actual_speed = 0.4 # Velocidad constante para relax

        # --- MANEJO DE DAS / ARR (Movimiento Continuo) ---
        keys = pygame.key.get_pressed()
        for key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_DOWN]:
            if keys[key]:
                if self.key_timers[key] == 0:
                    # Primer movimiento instantáneo
                    self.move_piece(key)
                    self.key_timers[key] = 1 # Iniciamos espera DAS
                else:
                    self.key_timers[key] += raw_time
                    delay = self.das_delay if self.key_timers[key] <= self.das_delay + 1 else self.arr_delay
                    if self.key_timers[key] > self.das_delay:
                        # Estamos en fase ARR
                        if (self.key_timers[key] - self.das_delay) >= self.arr_delay:
                            self.move_piece(key)
                            self.key_timers[key] = self.das_delay + 1 # Reset ARR timer
            else:
                self.key_timers[key] = 0

        # --- LÓGICA DE GLITCH (Modo RANDOM MADNESS) ---
        if self.mode == "RANDOM" and random.random() < 0.005:
            self.is_glitched = True
            self.glitch_timer = 30 # Dura medio segundo aprox a 60fps
        
        if self.is_glitched:
            self.glitch_timer -= 1
            self.glitch_offset = (random.randint(-5, 5), random.randint(-5, 5))
            if self.glitch_timer <= 0:
                self.is_glitched = False
                self.glitch_offset = (0,0)

        # --- DETECCIÓN DE SUELO PARA LOCK DELAY ---
        # Si al bajar una posición hay colisión, estamos en el suelo
        p_down = models.Piece(self.current_piece.x, self.current_piece.y + 1, self.current_piece.shape)
        p_down.rotation = self.current_piece.rotation
        if not logic.valid_space(p_down, self.grid):
            self.is_on_ground = True
            # Acumulamos tiempo en el suelo si no estamos en pausa
            self.lock_timer += clock.get_rawtime()
        else:
            # Si hay espacio abajo, volvemos a aire (no locking)
            self.is_on_ground = False
            self.lock_timer = 0
            self.lock_move_count = 0

        # --- MOVIMIENTO AUTOMÁTICO HACIA ABAJO ---
        if self.fall_time / 1000 > actual_speed:
            self.fall_time = 0
            if not self.is_on_ground:
                self.current_piece.y += 1
        
        # --- ACTUALIZAR TRUENOS ---
        for l in self.lightnings[:]:
            l.update()
            if l.lifetime <= 0: self.lightnings.remove(l)
        
        # --- FIJAR PIEZA SI SE ACABA EL TIEMPO DE GRACIA ---
        if self.is_on_ground and self.lock_timer >= self.lock_delay_max:
            self.change_piece = True

    def handle_events(self):
        """Gestiona la entrada por teclado del jugador."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.run = False
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.current_piece.x -= 1
                    if not logic.valid_space(self.current_piece, self.grid): self.current_piece.x += 1
                elif event.key == pygame.K_RIGHT:
                    self.current_piece.x += 1
                    if not logic.valid_space(self.current_piece, self.grid): self.current_piece.x -= 1
                elif event.key == pygame.K_DOWN:
                    self.current_piece.y += 1
                    if not logic.valid_space(self.current_piece, self.grid): self.current_piece.y -= 1
                elif event.key == pygame.K_UP:
                    self.rotate_piece()
                elif event.key == pygame.K_SPACE:
                    self.hard_drop()
                elif event.key == pygame.K_c or event.key == pygame.K_LSHIFT:
                    self.handle_hold()

    def move_piece(self, key):
        """Mueve la pieza y gestiona colisiones y lock delay."""
        if key == pygame.K_LEFT:
            self.current_piece.x -= 1
            if not logic.valid_space(self.current_piece, self.grid): self.current_piece.x += 1
            else: self.reset_lock_delay()
        elif key == pygame.K_RIGHT:
            self.current_piece.x += 1
            if not logic.valid_space(self.current_piece, self.grid): self.current_piece.x -= 1
            else: self.reset_lock_delay()
        elif key == pygame.K_DOWN:
            self.current_piece.y += 1
            if not logic.valid_space(self.current_piece, self.grid): self.current_piece.y -= 1

    def get_bag_shape(self):
        """Implementa el sistema 7-Bag: una bolsa con las 7 piezas clásicas que se baraja al vaciarse."""
        # Probabilidad especial de Joker (fuera de la bolsa)
        if self.mode == "JOKER" and random.random() < 0.10:
            return models.Piece(4, 0, config.SHAPE_JOKER)
        
        # Si la bolsa está vacía, la rellenamos con las 7 clásicas y barajamos
        if not self.bag:
            self.bag = list(range(len(config.SHAPES) - 1)) # Excluye el Joker
            random.shuffle(self.bag)
        
        idx = self.bag.pop()
        return models.Piece(4, 0, config.SHAPES[idx])

    def handle_hold(self):
        """Mecánica de guardar pieza (Hold)."""
        if not self.can_hold: return
        if self.hold_piece is None:
            # Si no hay nada guardado, guardamos la actual y sacamos la siguiente
            self.hold_piece = models.Piece(4, 0, self.current_piece.shape)
            self.current_piece = self.next_pieces.pop(0)
            self.next_pieces.append(self.get_bag_shape())
        else:
            # Intercambio de piezas
            temp = self.current_piece.shape
            self.current_piece = models.Piece(4, 0, self.hold_piece.shape)
            self.hold_piece = models.Piece(4, 0, temp)
        
        self.can_hold = False # Bloqueamos más cambios hasta que aterrice esta pieza
        self.current_piece.y = 0

    def reset_lock_delay(self):
        """Reinicia el tiempo de gracia si el jugador interactúa con la pieza en el suelo."""
        if self.is_on_ground and self.lock_move_count < self.lock_move_limit:
            self.lock_timer = 0
            self.lock_move_count += 1

    def rotate_piece(self):
        """Gira la pieza con sistema de Wall Kicks (SRS simplificado)."""
        if self.mode == "RANDOM":
            # RANDOM MADNESS: sigue siendo puro caos
            old_s, old_r = self.current_piece.shape, self.current_piece.rotation
            new_s = random.choice(config.SHAPES)
            self.current_piece.shape = new_s
            self.current_piece.rotation = random.randint(0, 3)
            if not logic.valid_space(self.current_piece, self.grid):
                self.current_piece.shape, self.current_piece.rotation = old_s, old_r
            else:
                self.reset_lock_delay()
            self.current_piece.update_color()
        else:
            old_rot = self.current_piece.rotation
            self.current_piece.rotation = (self.current_piece.rotation + 1) % len(self.current_piece.shape)
            
            if not logic.valid_space(self.current_piece, self.grid):
                # Wall Kick: Intentar mover la pieza para que encaje (SRS simplificado)
                # Kicks: izquierda, derecha, arriba, esquinas superiores
                kicks = [(-1, 0), (1, 0), (0, -1), (-1, -1), (1, -1)]
                found = False
                for dx, dy in kicks:
                    self.current_piece.x += dx
                    self.current_piece.y += dy
                    if logic.valid_space(self.current_piece, self.grid):
                        found = True
                        self.reset_lock_delay()
                        break
                    self.current_piece.x -= dx
                    self.current_piece.y -= dy
                
                if not found:
                    self.current_piece.rotation = old_rot
            else:
                self.reset_lock_delay()

    def hard_drop(self):
        """Envía la pieza directamente al fondo y activa sacudida de pantalla."""
        while logic.valid_space(self.current_piece, self.grid):
            self.current_piece.y += 1
        self.current_piece.y -= 1
        self.change_piece = True
        renderer.set_screen_shake(5, 4) # Sacudida pequeña por impacto

    def clear_lines(self):
        """Escanea, elimina líneas llenas y recalcula gravedad y puntuación."""
        temp_grid = logic.create_grid(self.locked_positions)
        lines_to_clear = []
        for i in range(config.GRID_HEIGHT):
            # Comprobamos si la fila NO tiene colores de fondo disponibles (está llena)
            if all(temp_grid[i][x] != config.active_theme["bg"] for x in range(config.GRID_WIDTH)):
                lines_to_clear.append(i)
        
        if lines_to_clear:
            renderer.set_screen_shake(10, 8) # Sacudida fuerte por limpieza de líneas
            num_lines = len(lines_to_clear)
            self.total_lines += num_lines
            self.combo += 1
            
            # --- SISTEMA DE PUNTUACIÓN PROFESIONAL ---
            points_base = [0, 100, 300, 500, 800][min(num_lines, 4)]
            
            # Bonus Back-to-Back (Tetrises seguidos)
            if num_lines == 4:
                if self.back_to_back: points_base = int(points_base * 1.5)
                self.back_to_back = True
            else:
                self.back_to_back = False
                
            self.score += points_base * self.level * self.combo
            
            # Generar partículas visuales
            if num_lines == 4 or self.combo >= 4:
                # ¡TRUENOS PARA TETRIS O COMBOS ALTOS!
                renderer.set_screen_shake(25, 20) # Sacudida épica
                for _ in range(3):
                    self.lightnings.append(models.Lightning(random.randint(0, config.SCREEN_WIDTH)))
            for r in lines_to_clear:
                for x in range(config.GRID_WIDTH):
                    self.particles.append(models.Particle(config.TOP_LEFT_X + x*config.BLOCK_SIZE + 15, config.TOP_LEFT_Y + r*config.BLOCK_SIZE + 15, temp_grid[r][x], True))

            # Eliminar bloques fijos de las líneas y bajar los superiores
            for r in sorted(lines_to_clear):
                # Borramos la línea de la memoria
                for x in range(config.GRID_WIDTH):
                    if (x, r) in self.locked_positions: del self.locked_positions[(x,r)]
                
                # Desplazamos hacia abajo todo lo que esté por encima de la línea borrada
                new_locked = {}
                for (lx, ly), color in self.locked_positions.items():
                    if ly < r: new_locked[(lx, ly + 1)] = color
                    else: new_locked[(lx, ly)] = color
                self.locked_positions = new_locked
        else:
            self.combo = 0 # El combo se rompe si colocas una pieza sin limpiar nada

    def draw(self, win):
        """Renderizado completo del frame de juego."""
        shake = renderer.get_shake_offsets()
        if self.is_glitched: 
            shake = (shake[0] + self.glitch_offset[0], shake[1] + self.glitch_offset[1])
        
        win.fill(config.active_theme["bg"])
        m = models.MeshBackground(); m.draw(win)
        renderer.draw_grid(win, shake)
        
        play_surface = pygame.Surface((config.PLAY_WIDTH, config.PLAY_HEIGHT), pygame.SRCALPHA)
        for (x, y), color in self.locked_positions.items():
            if y >= 0: renderer.draw_block(play_surface, x*config.BLOCK_SIZE, y*config.BLOCK_SIZE, color)
        
        ghost = logic.get_ghost_piece(self.current_piece, self.grid)
        for x, y in logic.convert_shape_format(ghost):
            if y >= 0: renderer.draw_block(play_surface, x*config.BLOCK_SIZE, y*config.BLOCK_SIZE, self.current_piece.color, is_ghost=True)
            
        for x, y in logic.convert_shape_format(self.current_piece):
            if y >= 0: renderer.draw_block(play_surface, x*config.BLOCK_SIZE, y*config.BLOCK_SIZE, self.current_piece.color, is_joker=self.current_piece.is_joker)

        win.blit(play_surface, (config.TOP_LEFT_X + shake[0], config.TOP_LEFT_Y + shake[1]))

        for p in self.particles[:]:
            p.update(); p.draw(win)
            if p.lifetime <= 0: self.particles.remove(p)

        renderer.draw_hud(win, self.score, self.total_lines, self.level, self.combo, self.next_pieces, self.hold_piece, shake)
        
        # Dibujar truenos
        for l in self.lightnings:
            l.draw(win)

        # Botón de engrane
        return renderer.draw_settings_button(win)

def handle_save_flow(win, g):
    """Menú secundario para elegir slot de guardado."""
    save_info = logic.get_save_info()
    sel = 0
    while True:
        renderer.draw_load_menu(win, save_info, sel) # Reusamos la estética de carga
        renderer.draw_text_centered(win, config._("SELECT_SAVE"), 30, 50, (255, 255, 0))
        pygame.display.update()
        for e in pygame.event.get():
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_UP: sel = (sel - 1) % 5
                if e.key == pygame.K_DOWN: sel = (sel + 1) % 5
                if e.key == pygame.K_ESCAPE: return
                if e.key == pygame.K_RETURN:
                    # Preparar datos para guardar
                    data = {
                        "mode": g.mode, "score": g.score, "lines": g.total_lines,
                        "level": g.level, "combo": g.combo, "locked": g.locked_positions,
                        "current_idx": config.SHAPES.index(g.current_piece.shape),
                        "next_indices": [config.SHAPES.index(p.shape) for p in g.next_pieces],
                        "hold_idx": config.SHAPES.index(g.hold_piece.shape) if g.hold_piece else None
                    }
                    if logic.save_game(sel + 1, data): return
        pygame.time.Clock().tick(60)

def main_menu():
    """Lógica del Menú Principal con botones de Carga y Galaga Style."""
    pygame.init()
    win = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("NEON TETRIS PRO - GALAGA EDITION")
    clock = pygame.time.Clock()
    audio_engine.start()
    starfield = models.Starfield(150)
    
    modes_keys = ["CLASSIC", "JOKER", "RANDOM", "ZEN", "LOAD", "EXIT"]
    theme_keys = list(config.THEMES.keys())
    cur_idx = 0; theme_idx = 0
    volume = 0.5; muted = False; audio_engine.set_volume(volume)
    
    while True:
        win.fill((0, 0, 5)); starfield.draw(win)
        config.active_theme = config.THEMES[theme_keys[theme_idx]]; config.active_theme_name = theme_keys[theme_idx]
        ticks = pygame.time.get_ticks()
        title_color = (255, 255, 255) if (ticks // 500) % 2 == 0 else (255, 200, 0)
        renderer.draw_text_centered(win, "NEON TETRIS", 100, 40, title_color, "arialblack", glow=True)
        renderer.draw_text_centered(win, "GALLERY EDITION", 22, 145, (255, 50, 50), "consolas")
        audio_rect = renderer.draw_audio_control(win, volume, muted)
        
        # Naves decorativas Galaga (Posiciones ajustadas)
        ship_color = (255, 0, 0)
        renderer.draw_block(win, 70, 60, ship_color); renderer.draw_block(win, 70, 90, ship_color)
        renderer.draw_block(win, 40, 90, ship_color); renderer.draw_block(win, 100, 90, ship_color)
        renderer.draw_block(win, 850, 60, (0, 255, 255)); renderer.draw_block(win, 850, 90, (0, 255, 255))
        renderer.draw_block(win, 820, 90, (0, 255, 255)); renderer.draw_block(win, 880, 90, (0, 255, 255))

        # Selectores de Tema e Idioma (Más abajo para no chocar con el subtítulo)
        renderer.draw_text_centered(win, f"< {config._('LANGUAGE')}: {config.LANGS[config.current_lang]} >", 20, 190, (255, 255, 0))
        renderer.draw_text_centered(win, f"< {config._('THEME')}: {theme_keys[theme_idx]} >", 20, 215, (0, 255, 255))
        
        # Caja de Opciones (Más grande y centrada)
        pygame.draw.rect(win, (255, 255, 255), (config.SCREEN_WIDTH//2 - 180, 250, 360, 360), 2, border_radius=5)
        renderer.draw_text_centered(win, config._("SELECT_OPT"), 20, 270, (255, 255, 0))
        
        for i, m_key in enumerate(modes_keys):
            color = (255, 255, 255) if i == cur_idx else (80, 80, 160)
            prefix = " > " if i == cur_idx else "   "
            suffix = " < " if i == cur_idx else "   "
            if i == cur_idx and (ticks // 200) % 2 == 0: color = (255, 50, 50)
            opt_text = config._(m_key)
            # Mayor espaciado vertical (i*50 en lugar de i*45) y centrado
            renderer.draw_text_centered(win, f"{prefix}{opt_text}{suffix}", 32, 315 + i*48, color)
        
        if (ticks // 800) % 2 == 0: renderer.draw_text_centered(win, config._("PRESS_START"), 25, 625, (0, 255, 0))
        renderer.draw_high_scores(win, logic.load_scores(), y_offset=670)
        renderer.draw_text_centered(win, "CREDIT  01", 18, 810, (255, 255, 255))
        renderer.draw_text_centered(win, "© 2026 ANTIGRAVITY ARCADE", 14, 830, (120, 120, 120))

        # Filtro Arcade
        renderer.draw_arcade_overlay(win)

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return
            if event.type == pygame.MOUSEBUTTONDOWN:
                if audio_rect.collidepoint(event.pos):
                    if event.pos[0] > audio_rect.x + audio_rect.width - 40: muted = not muted
                    else:
                        rel_x = event.pos[0] - audio_rect.x
                        volume = max(0.0, min(1.0, rel_x / (audio_rect.width - 40))); muted = False
                    audio_engine.set_volume(0 if muted else volume)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP: cur_idx = (cur_idx - 1) % len(modes_keys)
                if event.key == pygame.K_DOWN: cur_idx = (cur_idx + 1) % len(modes_keys)
                if event.key == pygame.K_LEFT: theme_idx = (theme_idx - 1) % len(theme_keys)
                if event.key == pygame.K_RIGHT: theme_idx = (theme_idx + 1) % len(theme_keys)
                
                # Nuevas teclas para idioma: A y S (o usar otra lógica)
                if event.key == pygame.K_a: config.current_lang = (config.current_lang - 1) % len(config.LANGS)
                if event.key == pygame.K_d: config.current_lang = (config.current_lang + 1) % len(config.LANGS)
                
                if event.key == pygame.K_RETURN:
                    g = None
                    selected_mode_key = modes_keys[cur_idx]
                    if selected_mode_key == "EXIT":
                        pygame.quit()
                        sys.exit()
                    elif selected_mode_key == "LOAD":
                        # Pantalla de carga
                        load_sel = 0
                        loading = True
                        while loading:
                            info = logic.get_save_info()
                            renderer.draw_load_menu(win, info, load_sel)
                            pygame.display.update()
                            for le in pygame.event.get():
                                if le.type == pygame.KEYDOWN:
                                    if le.key == pygame.K_UP: load_sel = (load_sel - 1) % 5
                                    if le.key == pygame.K_DOWN: load_sel = (load_sel + 1) % 5
                                    if le.key == pygame.K_ESCAPE: loading = False
                                    if le.key == pygame.K_RETURN:
                                        save_data = logic.load_game(load_sel + 1)
                                        if save_data:
                                            g = Game(save_data['mode'])
                                            g.score = save_data['score']; g.total_lines = save_data['lines']; g.level = save_data['level']; g.combo = save_data['combo']
                                            g.locked_positions = save_data['locked']
                                            g.current_piece = save_data['current'] # Llave corregida
                                            g.next_pieces = save_data['nexts']     # Llave corregida
                                            g.hold_piece = save_data['hold']       # Llave corregida
                                            # Aplicar tema
                                            if save_data['theme'] in config.THEMES:
                                                theme_idx = list(config.THEMES.keys()).index(save_data['theme'])
                                            loading = False
                            clock.tick(60)
                        if not g: continue # Si no cargó nada, vuelve al menú
                    else:
                        g = Game(selected_mode_key)

                    # --- BUCLE DE JUEGO ---
                    is_paused = False
                    pause_idx = 0
                    while g.run:
                        if not is_paused:
                            g.update(clock)
                        
                        for game_event in pygame.event.get():
                            if game_event.type == pygame.QUIT: pygame.quit(); sys.exit()
                            
                            if game_event.type == pygame.MOUSEBUTTONDOWN:
                                if audio_rect.collidepoint(game_event.pos):
                                    if game_event.pos[0] > audio_rect.x + audio_rect.width - 40: muted = not muted
                                    else:
                                        rel_x = game_event.pos[0] - audio_rect.x
                                        volume = max(0.0, min(1.0, rel_x / (audio_rect.width - 40))); muted = False
                                    audio_engine.set_volume(0 if muted else volume)
                                
                                if not is_paused and g.settings_rect.collidepoint(game_event.pos):
                                    is_paused = True
                            
                            if game_event.type == pygame.KEYDOWN:
                                if game_event.key == pygame.K_ESCAPE: is_paused = not is_paused
                                if not is_paused:
                                    if game_event.key == pygame.K_UP: g.rotate_piece()
                                    elif game_event.key == pygame.K_SPACE: g.hard_drop()
                                    elif game_event.key == pygame.K_c or game_event.key == pygame.K_LSHIFT: g.handle_hold()
                                else:
                                    # Navegación Menú Pausa
                                    if game_event.key == pygame.K_UP: pause_idx = (pause_idx - 1) % 3
                                    if game_event.key == pygame.K_DOWN: pause_idx = (pause_idx + 1) % 3
                                    if game_event.key == pygame.K_RETURN:
                                        if pause_idx == 0: is_paused = False
                                        elif pause_idx == 1: handle_save_flow(win, g)
                                        elif pause_idx == 2: g.run = False

                        if not is_paused and g.change_piece:
                            for x, y in logic.convert_shape_format(g.current_piece): g.locked_positions[(x, y)] = g.current_piece.color
                            g.clear_lines(); g.current_piece = g.next_pieces.pop(0); g.next_pieces.append(g.get_bag_shape())
                            g.change_piece = False; g.can_hold = True
                            if logic.check_lost(g.locked_positions): g.run = False
                        
                        g.settings_rect = g.draw(win)
                        if is_paused: renderer.draw_pause_menu(win, pause_idx)
                        renderer.draw_audio_control(win, volume, muted)
                        pygame.display.update(); clock.tick(60)

                    # --- FIN DE PARTIDA / GAME OVER ---
                    renderer.draw_game_over(win, g.score)
                    pygame.display.update()
                    pygame.time.delay(1500)
                    
                    # Comprobar si es record
                    high_scores = logic.load_scores()
                    if not high_scores or g.score > high_scores[-1]["score"] or len(high_scores) < 10:
                        name = renderer.ask_name(win)
                        high_scores.append({"name": name, "score": g.score})
                        logic.save_scores(high_scores)

if __name__ == "__main__":
    main_menu()
