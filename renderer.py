"""
Motor de Renderizado de Neon Tetris PRO.
Gestiona el dibujo de bloques, mallas, texto y efectos especiales como Screen Shake.
"""

import pygame
import math
import random
import config

# --- VARIABLES DE ESTADO PARA EFECTOS VISUALES ---
screen_shake_time = 0      # Duración restante de la sacudida
screen_shake_intensity = 0  # Fuerza de la sacudida en píxeles

def set_screen_shake(duration, intensity):
    """Activa un efecto de sacudida de pantalla.
    
    Args:
        duration (int): Número de frames que durará el efecto.
        intensity (int): Intensidad máxima del desplazamiento.
    """
    global screen_shake_time, screen_shake_intensity
    screen_shake_time = duration
    screen_shake_intensity = intensity

def get_shake_offsets():
    """Calcula el desplazamiento aleatorio actual si hay una sacudida activa."""
    global screen_shake_time
    if screen_shake_time > 0:
        screen_shake_time -= 1
        return random.randint(-screen_shake_intensity, screen_shake_intensity), \
               random.randint(-screen_shake_intensity, screen_shake_intensity)
    return 0, 0

def draw_text_centered(surface, text, size, y_pos, color, font_name="consolas", glow=False):
    """Dibuja texto centrado horizontalmente con efectos de sombra y resplandor."""
    font = pygame.font.SysFont(font_name, size, bold=True)
    
    # Sombra profunda para mayor legibilidad
    shadow = font.render(text, 1, (10, 10, 20))
    x_pos = config.SCREEN_WIDTH // 2 - shadow.get_width() // 2
    surface.blit(shadow, (x_pos + 4, y_pos + 4))
    
    label = font.render(text, 1, color)
    if glow:
        # Efecto de resplandor simple (dibujar el texto varias veces con offset)
        for ox, oy in [(-1,-1), (1,-1), (-1,1), (1,1)]:
            surface.blit(font.render(text, 1, color), (x_pos + ox, y_pos + oy))
    
    surface.blit(label, (x_pos, y_pos))

def draw_arcade_overlay(surface):
    """Añade un efecto de scanlines (CRT) y un ligero viñeteado para estética arcade."""
    # Scanlines
    for y in range(0, config.SCREEN_HEIGHT, 4):
        s = pygame.Surface((config.SCREEN_WIDTH, 2), pygame.SRCALPHA)
        s.fill((0, 0, 0, 40)) # Líneas de barrido negras semitransparentes
        surface.blit(s, (0, y))
    
    # Efecto viñeta (bordes oscuros)
    vignette = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(vignette, (0, 0, 0, 30), vignette.get_rect(), 100, border_radius=150)
    surface.blit(vignette, (0, 0))

def draw_block(surface, x, y, color, is_ghost=False, is_joker=False, shake=(0,0)):
    """Renderiza un bloque individual con estilo 3D extrudido.
    
    Args:
        surface: Superficie de pygame donde dibujar.
        x, y: Coordenadas de píxel.
        color: Color RGB base del bloque.
        is_ghost (bool): Si es True, dibuja solo el contorno (sombra).
        is_joker (bool): Si es True, aplica un efecto de pulso luminoso.
        shake (tuple): Desplazamiento (x, y) por efectos de sacudida o glitch.
    """
    rect = (x + shake[0], y + shake[1], config.BLOCK_SIZE, config.BLOCK_SIZE)
    
    if is_joker:
        # Efecto de pulso blanco/azul para la ficha comodín
        pulse = (math.sin(pygame.time.get_ticks() * 0.02) + 1) / 2
        color = (int(130 + 125 * pulse), int(130 + 125 * pulse), 255)

    if is_ghost:
        # Silueta con mucho mayor contraste: Borde más grueso y Alfa mayor
        s = pygame.Surface((config.BLOCK_SIZE, config.BLOCK_SIZE), pygame.SRCALPHA)
        # Dibujamos un fondo muy tenue pero visible
        pygame.draw.rect(s, (*color, 60), (0, 0, config.BLOCK_SIZE, config.BLOCK_SIZE), border_radius=2)
        # Borde de 2px para que resalte incluso en morado/azul oscuro
        pygame.draw.rect(s, (*color, 180), (0, 0, config.BLOCK_SIZE, config.BLOCK_SIZE), 2, border_radius=2)
        surface.blit(s, (rect[0], rect[1]))
        return

    # --- SIMULACIÓN DE PROFUNDIDAD 3D (Suavizada) ---
    padding = 2 # Sombra más fina
    dark_color = [max(0, c - 40) for c in color] # Menos oscuridad
    mid_color = [max(0, c - 20) for c in color]  # Menos contraste
    light_color = [min(255, c + 40) for c in color]
    
    # Sombra proyectada muy suave
    s = pygame.Surface((config.BLOCK_SIZE, config.BLOCK_SIZE), pygame.SRCALPHA)
    pygame.draw.rect(s, (0, 0, 0, 40), (0, 0, config.BLOCK_SIZE, config.BLOCK_SIZE), border_radius=4)
    surface.blit(s, (rect[0]+3, rect[1]+3))

    # Caras del cubo
    pygame.draw.polygon(surface, mid_color, [(rect[0]+config.BLOCK_SIZE, rect[1]), (rect[0]+config.BLOCK_SIZE, rect[1]+config.BLOCK_SIZE), (rect[0]+config.BLOCK_SIZE-padding, rect[1]+config.BLOCK_SIZE-padding), (rect[0]+config.BLOCK_SIZE-padding, rect[1]+padding)])
    pygame.draw.polygon(surface, dark_color, [(rect[0], rect[1]+config.BLOCK_SIZE), (rect[0]+config.BLOCK_SIZE, rect[1]+config.BLOCK_SIZE), (rect[0]+config.BLOCK_SIZE-padding, rect[1]+config.BLOCK_SIZE-padding), (rect[0]+padding, rect[1]+config.BLOCK_SIZE-padding)])
    pygame.draw.polygon(surface, light_color, [(rect[0], rect[1]), (rect[0]+config.BLOCK_SIZE, rect[1]), (rect[0]+config.BLOCK_SIZE-padding, rect[1]+padding), (rect[0]+padding, rect[1]+padding)])
    pygame.draw.polygon(surface, mid_color, [(rect[0], rect[1]), (rect[0], rect[1]+config.BLOCK_SIZE), (rect[0]+padding, rect[1]+config.BLOCK_SIZE-padding), (rect[0]+padding, rect[1]+padding)])

    # Cara frontal
    pygame.draw.rect(surface, color, (rect[0]+padding, rect[1]+padding, config.BLOCK_SIZE-padding*2, config.BLOCK_SIZE-padding*2), border_radius=1)

def draw_audio_control(surface, volume, muted):
    """Dibuja el icono de volumen interactivo y la barra de nivel."""
    x, y = 880, 20
    color = (0, 255, 255) if not muted else (255, 50, 50)
    
    # Dibujar Icono de Altavoz Simplificado
    pygame.draw.rect(surface, color, (x, y+8, 8, 10))
    pygame.draw.polygon(surface, color, [(x+8, y+8), (x+18, y), (x+18, y+24), (x+8, y+16)])
    
    if muted:
        pygame.draw.line(surface, (255, 50, 50), (x, y), (x+18, y+24), 3)
    else:
        # Ondas de sonido
        if volume > 0.1: pygame.draw.arc(surface, color, (x+12, y+2, 10, 20), -math.pi/3, math.pi/3, 2)
        if volume > 0.5: pygame.draw.arc(surface, color, (x+18, y-4, 15, 32), -math.pi/3, math.pi/3, 2)

    # Barra de volumen
    bar_width = 80
    bar_x = x - bar_width - 10
    pygame.draw.rect(surface, (50, 50, 100), (bar_x, y+10, bar_width, 6), border_radius=3)
    pygame.draw.rect(surface, color, (bar_x, y+10, int(bar_width * volume), 6), border_radius=3)
    
    return pygame.Rect(bar_x, y, bar_width + 40, 30) # Devolvemos el área interactiva

def draw_grid(surface, shake=(0,0)):
    """Dibuja el área de juego con fondo contrastado, bordes marcados y cuadrícula."""
    # 1. Fondo del área de juego para mayor contraste (un poco más claro que el fondo general)
    play_area_rect = (config.TOP_LEFT_X + shake[0], config.TOP_LEFT_Y + shake[1], config.PLAY_WIDTH, config.PLAY_HEIGHT)
    pygame.draw.rect(surface, (15, 15, 35), play_area_rect)
    
    # 2. Bordes del área de juego (Doble borde neón)
    # Dibujamos el primer borde 2px hacia AFUERA para que las fichas no se sobrepongan
    border_rect = (play_area_rect[0] - 2, play_area_rect[1] - 2, play_area_rect[2] + 4, play_area_rect[3] + 4)
    pygame.draw.rect(surface, config.active_theme["glow1"], border_rect, 2, border_radius=2)
    # Segundo borde decorativo un poco más alejado
    pygame.draw.rect(surface, config.active_theme["glow2"], (border_rect[0]-4, border_rect[1]-4, border_rect[2]+8, border_rect[3]+8), 1, border_radius=4)
    
    # 3. Cuadrícula interna
    grid_color = (30, 30, 60)
    for i in range(config.GRID_HEIGHT + 1):
        y = config.TOP_LEFT_Y + i * config.BLOCK_SIZE
        pygame.draw.line(surface, grid_color, (config.TOP_LEFT_X + shake[0], y + shake[1]), (config.TOP_LEFT_X + config.PLAY_WIDTH + shake[0], y + shake[1]), 1)
    for j in range(config.GRID_WIDTH + 1):
        x = config.TOP_LEFT_X + j * config.BLOCK_SIZE
        pygame.draw.line(surface, grid_color, (x + shake[0], config.TOP_LEFT_Y + shake[1]), (x + shake[0], config.TOP_LEFT_Y + config.PLAY_HEIGHT + shake[1]), 1)

def draw_next_pieces(surface, next_pieces, shake=(0,0)):
    """Dibuja las próximas dos piezas en un panel lateral."""
    panel_x = config.TOP_LEFT_X + config.PLAY_WIDTH + 50
    panel_y = config.TOP_LEFT_Y
    
    pygame.draw.rect(surface, (10, 10, 30), (panel_x, panel_y, 150, 250), 0, border_radius=10)
    pygame.draw.rect(surface, config.active_theme["glow1"], (panel_x, panel_y, 150, 250), 2, border_radius=10)
    
    font = pygame.font.SysFont("consolas", 20, bold=True)
    label = font.render(config._("NEXT"), 1, WHITE)
    surface.blit(label, (panel_x + 15, panel_y + 10))
    
    for i, piece in enumerate(next_pieces[:2]):
        format_shape = piece.shape[piece.rotation % len(piece.shape)]
        for r, line in enumerate(format_shape):
            for c, char in enumerate(line):
                if char == "0":
                    color = config.get_s(config.SHAPES.index(piece.shape))
                    px = panel_x + 35 + c * 20
                    py = panel_y + 50 + i * 100 + r * 20
                    pygame.draw.rect(surface, color, (px, py, 18, 18), border_radius=2)

def draw_hold_piece(surface, hold_piece, shake=(0,0)):
    """Dibuja la pieza guardada."""
    panel_x = config.TOP_LEFT_X - 180
    panel_y = config.TOP_LEFT_Y
    
    pygame.draw.rect(surface, (10, 10, 30), (panel_x, panel_y, 150, 150), 0, border_radius=10)
    pygame.draw.rect(surface, config.active_theme["glow2"], (panel_x, panel_y, 150, 150), 2, border_radius=10)
    
    font = pygame.font.SysFont("consolas", 20, bold=True)
    label = font.render(config._("HOLD"), 1, WHITE)
    surface.blit(label, (panel_x + 25, panel_y + 10))
    
    if hold_piece:
        format_shape = hold_piece.shape[hold_piece.rotation % len(hold_piece.shape)]
        for r, line in enumerate(format_shape):
            for c, char in enumerate(line):
                if char == "0":
                    color = config.get_s(config.SHAPES.index(hold_piece.shape))
                    px = panel_x + 35 + c * 20
                    py = panel_y + 50 + r * 20
                    pygame.draw.rect(surface, color, (px, py, 18, 18), border_radius=2)

def draw_hud(surface, score, lines, level, combo, next_pieces, hold_piece, shake=(0,0)):
    """Dibuja la interfaz completa."""
    # Dibujar paneles de Piezas
    draw_next_pieces(surface, next_pieces, shake)
    draw_hold_piece(surface, hold_piece, shake)
    
    # Dibujar Estadísticas
    stats_x = config.TOP_LEFT_X + config.PLAY_WIDTH + 50
    panel_y = config.TOP_LEFT_Y + 270
    
    pygame.draw.rect(surface, (10, 10, 30), (stats_x, panel_y, 200, 240), 0, border_radius=15)
    pygame.draw.rect(surface, config.active_theme["glow1"], (stats_x, panel_y, 200, 240), 2, border_radius=15)
    
    label_font = pygame.font.SysFont("consolas", 20, bold=True)
    val_font = pygame.font.SysFont("consolas", 30, bold=True)
    
    surface.blit(label_font.render(config._("SCORE"), 1, WHITE), (stats_x + 20, panel_y + 15))
    surface.blit(val_font.render(str(score), 1, config.active_theme["glow1"]), (stats_x + 20, panel_y + 35))
    
    surface.blit(label_font.render(config._("LINES"), 1, WHITE), (stats_x + 20, panel_y + 75))
    surface.blit(val_font.render(str(lines), 1, config.active_theme["glow2"]), (stats_x + 20, panel_y + 95))

    surface.blit(label_font.render(config._("LEVEL"), 1, WHITE), (stats_x + 20, panel_y + 135))
    surface.blit(val_font.render(str(level), 1, (255, 255, 100)), (stats_x + 20, panel_y + 155))

    if combo > 1:
        # Efecto de parpadeo arcade para combos
        ticks = pygame.time.get_ticks()
        combo_color = (255, 100, 100) if (ticks // 150) % 2 == 0 else (255, 255, 255)
        surface.blit(label_font.render(f"COMBO X{combo}!", 1, combo_color), (stats_x + 20, panel_y + 200))

def draw_high_scores(surface, scores, y_offset=650):
    """Dibuja la tabla de récords en el menú principal con estética arcade."""
    # Caja para los récords
    box_rect = (config.SCREEN_WIDTH // 2 - 190, y_offset, 380, 160)
    pygame.draw.rect(surface, (0, 0, 20), box_rect)
    pygame.draw.rect(surface, (255, 0, 0), box_rect, 2)
    
    label_font = pygame.font.SysFont("consolas", 18, bold=True)
    score_font = pygame.font.SysFont("consolas", 16)
    
    header = label_font.render(config._("TOP_HEROES"), 1, (255, 255, 0))
    surface.blit(header, (config.SCREEN_WIDTH // 2 - header.get_width() // 2, y_offset + 10))
    
    # Mostrar solo los 5 mejores para que quepa en el diseño Galaga
    for i, entry in enumerate(scores[:5]):
        name_text = score_font.render(f"{i+1}. {entry['name'][:10]}", 1, (255, 255, 255))
        score_val = score_font.render(str(entry["score"]), 1, (0, 255, 255))
        
        y_y = y_offset + 40 + i * 22
        surface.blit(name_text, (config.SCREEN_WIDTH // 2 - 160, y_y))
        surface.blit(score_val, (config.SCREEN_WIDTH // 2 + 60, y_y))

def draw_settings_button(surface):
    """Dibuja un botón de engrane en la parte inferior derecha."""
    x, y = 880, 780
    color = (200, 200, 200)
    # Cuerpo del engrane
    pygame.draw.circle(surface, color, (x+15, y+15), 10)
    pygame.draw.circle(surface, (30,30,30), (x+15, y+15), 4) # Hueco central
    # Dientes
    for i in range(8):
        angle = i * (math.pi / 4)
        dx = math.cos(angle) * 12
        dy = math.sin(angle) * 12
        pygame.draw.line(surface, color, (x+15, y+15), (x+15+dx, y+15+dy), 4)
    return pygame.Rect(x, y, 30, 30)

def draw_pause_menu(surface, selected_idx):
    """Dibuja el overlay del menú de pausa."""
    # Fondo semi-transparente
    overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))
    
    draw_text_centered(surface, config._("PAUSED"), 60, 200, (255, 255, 0))
    
    options = [config._("CONTINUE"), config._("SAVE"), config._("MENU")]
    for i, opt in enumerate(options):
        color = (255, 255, 255) if i == selected_idx else (100, 100, 150)
        prefix = "> " if i == selected_idx else "  "
        draw_text_centered(surface, f"{prefix}{opt}", 35, 350 + i*60, color)

def draw_load_menu(surface, save_info, selected_idx):
    """Dibuja la pantalla de selección de slots para cargar."""
    surface.fill((0, 0, 10))
    draw_text_centered(surface, config._("LOAD"), 60, 100, (0, 255, 255))
    
    for i, slot in enumerate(save_info):
        color = (255, 255, 255) if i == selected_idx else (80, 80, 120)
        box_y = 220 + i * 100
        pygame.draw.rect(surface, color, (150, box_y, 650, 80), 2, border_radius=10)
        
        slot_text = f"{config._('SLOT')} {slot['slot']}: "
        if slot.get('empty'):
            desc = config._("EMPTY")
        else:
            desc = f"{config._('SCORE')}: {slot['score']} | {config._('LEVEL')}: {slot['level']} | {slot['mode']}"
        
        font = pygame.font.SysFont("consolas", 20, bold=True)
        surface.blit(font.render(slot_text + desc, 1, color), (180, box_y + 30))
        
        if i == selected_idx:
            draw_text_centered(surface, config._("PRESS_ENTER_LOAD"), 15, box_y + 85, (255, 255, 0))

def draw_game_over(surface, score):
    """Dibuja la pantalla de fin de juego con el puntaje final."""
    overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((20, 0, 0, 200)) # Tinte rojo oscuro
    surface.blit(overlay, (0, 0))
    
    draw_text_centered(surface, config._("GAME_OVER"), 80, 250, (255, 50, 50), "arialblack")
    draw_text_centered(surface, f"{config._('FINAL_SCORE')} {score}", 40, 360, (255, 255, 255))
    draw_text_centered(surface, config._("PRESS_ANY_KEY"), 20, 500, (150, 150, 150))

def ask_name(surface):
    """Interfaz para que el usuario ingrese su nombre para el ranking."""
    name = ""
    run = True
    while run:
        surface.fill((5, 5, 20))
        draw_text_centered(surface, config._("NEW_RECORD"), 60, 200, (255, 255, 0))
        draw_text_centered(surface, config._("ENTER_NAME"), 25, 300, (255, 255, 255))
        
        # Cursor parpadeante
        cursor = "_" if (pygame.time.get_ticks() // 400) % 2 == 0 else ""
        draw_text_centered(surface, name + cursor, 40, 380, (0, 255, 255))
        
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "???"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN: run = False
                elif event.key == pygame.K_BACKSPACE: name = name[:-1]
                else:
                    if len(name) < 10 and event.unicode.isalnum():
                        name += event.unicode.upper()
    return name if name else "JUGADOR"

WHITE = (255, 255, 255)
