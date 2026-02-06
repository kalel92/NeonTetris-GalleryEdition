import pygame
import random
import sys
import json
import os
import math

# --- CONFIGURACIÓN ---
SCREEN_WIDTH = 950
SCREEN_HEIGHT = 850
BLOCK_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
PLAY_WIDTH = GRID_WIDTH * BLOCK_SIZE
PLAY_HEIGHT = GRID_HEIGHT * BLOCK_SIZE
SCORE_FILE = "highscores.json"

# Posición del tablero en la pantalla
TOP_LEFT_X = (
    SCREEN_WIDTH - PLAY_WIDTH
) // 2 - 50  # Movido un poco a la izquierda para balancear con UI
TOP_LEFT_Y = 160  # Mucho más espacio arriba para el título

# --- TEMAS VISUALES ---
THEMES = {
    "CYBERPUNK": {
        "bg": (5, 5, 15),
        "mesh": (25, 25, 65),
        "glow1": (0, 255, 255),
        "glow2": (150, 0, 255),
        "shapes": [
            (0, 160, 180),
            (60, 90, 190),
            (190, 110, 60),
            (180, 160, 40),
            (60, 170, 90),
            (120, 60, 190),
            (180, 60, 85),
        ],
    },
    "MATRIX": {
        "bg": (0, 10, 0),
        "mesh": (0, 40, 0),
        "glow1": (0, 255, 70),
        "glow2": (0, 150, 30),
        "shapes": [
            (0, 100, 0),
            (0, 150, 20),
            (20, 180, 40),
            (0, 255, 60),
            (40, 120, 40),
            (10, 200, 30),
            (0, 80, 10),
        ],
    },
    "LAVA": {
        "bg": (20, 5, 0),
        "mesh": (60, 20, 0),
        "glow1": (255, 80, 0),
        "glow2": (255, 200, 0),
        "shapes": [
            (150, 40, 0),
            (200, 80, 0),
            (255, 120, 40),
            (180, 30, 0),
            (220, 100, 20),
            (255, 160, 60),
            (100, 20, 0),
        ],
    },
    "ICE": {
        "bg": (5, 15, 30),
        "mesh": (100, 150, 255),
        "glow1": (180, 230, 255),
        "glow2": (230, 250, 255),
        "shapes": [
            (100, 180, 255),
            (150, 210, 255),
            (200, 230, 255),
            (180, 190, 240),
            (120, 200, 255),
            (255, 255, 255),
            (80, 150, 200),
        ],
    },
    "CLASSIC": {
        "bg": (10, 10, 10),
        "mesh": (40, 40, 40),
        "glow1": (200, 200, 200),
        "glow2": (100, 100, 100),
        "shapes": [
            (255, 0, 0),
            (0, 255, 0),
            (0, 0, 255),
            (255, 255, 0),
            (255, 165, 0),
            (128, 0, 128),
            (0, 255, 255),
        ],
    },
}

# --- COLORES BASE ---
BLACK = (5, 5, 15)
WHITE = (255, 255, 255)
CYAN_GLOW = (0, 255, 255)
PURPLE_GLOW = (150, 0, 255)

active_theme_name = "CYBERPUNK"
active_theme = THEMES[active_theme_name]


# Colores dinámicos
def get_c():
    return active_theme["bg"]


def get_g1():
    return active_theme["glow1"]


def get_g2():
    return active_theme["glow2"]


def get_m():
    return active_theme["mesh"]


def get_s(idx):
    return active_theme["shapes"][idx % len(active_theme["shapes"])]


# --- FORMAS ---
SHAPE_S = [
    [".....", ".....", "..00.", ".00..", "....."],
    [".....", "..0..", "..00.", "...0.", "....."],
]

SHAPE_Z = [
    [".....", ".....", ".00..", "..00.", "....."],
    [".....", "..0..", ".00..", ".0...", "....."],
]

SHAPE_I = [
    ["..0..", "..0..", "..0..", "..0..", "....."],
    [".....", "0000.", ".....", ".....", "....."],
]

SHAPE_O = [[".....", ".....", ".00..", ".00..", "....."]]

SHAPE_J = [
    [".....", ".0...", ".000.", ".....", "....."],
    [".....", "..0..", "..0..", "..0..", "....."],
    [".....", ".....", ".000.", "...0.", "....."],
    [".....", "..0..", "..0..", ".00..", "....."],
]

SHAPE_L = [
    [".....", "...0.", ".000.", ".....", "....."],
    [".....", "..0..", "..0..", "..00.", "....."],
    [".....", ".....", ".000.", ".0...", "....."],
    [".....", ".00..", "..0..", "..0..", "....."],
]

SHAPE_T = [
    [".....", "..0..", ".000.", ".....", "....."],
    [".....", "..0..", "..00.", "..0..", "....."],
    [".....", ".....", ".000.", "..0..", "....."],
    [".....", "..0..", ".00..", "..0..", "....."],
]

SHAPE_JOKER = [[".....", ".....", "..0..", ".....", "....."]]

SHAPES = [SHAPE_S, SHAPE_Z, SHAPE_I, SHAPE_O, SHAPE_J, SHAPE_L, SHAPE_T, SHAPE_JOKER]


# --- PERSISTENCIA ---
def load_scores():
    if not os.path.exists(SCORE_FILE):
        return []
    try:
        with open(SCORE_FILE, "r") as f:
            return sorted(json.load(f), key=lambda x: x["score"], reverse=True)[:10]
    except:
        return []


def save_scores(scores):
    with open(SCORE_FILE, "w") as f:
        json.dump(scores, f)


# --- CLASES Y LÓGICA ---
class Piece(object):
    def __init__(self, x, y, shape):
        self.x = x
        self.y = y
        self.shape = shape
        self.is_joker = shape == SHAPE_JOKER
        if self.is_joker:
            self.color = (255, 255, 255)
        else:
            self.color = get_s(SHAPES.index(shape))
        self.rotation = 0

    def update_color(self):
        if not self.is_joker:
            self.color = get_s(SHAPES.index(self.shape))


def create_grid(locked_pos={}):
    grid = [[active_theme["bg"] for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if (x, y) in locked_pos:
                grid[y][x] = locked_pos[(x, y)]
    return grid


def convert_shape_format(piece):
    positions = []
    format_shape = piece.shape[piece.rotation % len(piece.shape)]
    for i, line in enumerate(format_shape):
        row = list(line)
        for j, column in enumerate(row):
            if column == "0":
                positions.append((piece.x + j, piece.y + i))
    for i, pos in enumerate(positions):
        positions[i] = (pos[0] - 2, pos[1] - 4)
    return positions


def valid_space(piece, grid):
    # Para piezas normales, lógica estándar
    bg_color = active_theme["bg"]
    if not piece.is_joker:
        accepted_pos = [
            [(j, i) for j in range(GRID_WIDTH) if grid[i][j] == bg_color]
            for i in range(GRID_HEIGHT)
        ]
        accepted_pos = [j for sub in accepted_pos for j in sub]
        formatted = convert_shape_format(piece)
        for pos in formatted:
            if pos not in accepted_pos:
                if pos[1] > -1:
                    return False
        return True

    # Para el Joker: Solo límites de la pantalla
    formatted = convert_shape_format(piece)
    for pos in formatted:
        if pos[0] < 0 or pos[0] >= GRID_WIDTH or pos[1] >= GRID_HEIGHT:
            return False
    return True


def get_ghost_piece(piece, grid):
    bg_color = active_theme["bg"]
    ghost = Piece(piece.x, piece.y, piece.shape)
    ghost.rotation = piece.rotation

    if ghost.is_joker:
        pos = convert_shape_format(ghost)[0]
        bx = pos[0]
        deepest_y = pos[1]
        for ty in range(pos[1], GRID_HEIGHT):
            if grid[ty][bx] == bg_color:
                has_hole_below = False
                for check_y in range(ty + 1, GRID_HEIGHT):
                    if grid[check_y][bx] == bg_color:
                        has_hole_below = True
                        break
                if not has_hole_below:
                    deepest_y = ty
                    break
        ghost.y += deepest_y - pos[1]
    else:
        while valid_space(ghost, grid):
            ghost.y += 1
        ghost.y -= 1
    return ghost


def check_lost(positions):
    for pos in positions:
        x, y = pos
        if y < 1:
            return True
    return False


def get_shape(game_mode="JOKER"):
    """Generate a new random Tetris piece, respecting the selected game mode.

    Args:
        game_mode (str): The current game mode ("CLASSIC" or "JOKER").

    Returns:
        Piece: A newly initialized piece at the starting position.
    """
    if game_mode == "JOKER" and random.random() < 0.10:
        return Piece(4, 0, SHAPE_JOKER)
    return Piece(4, 0, random.choice(SHAPES[:-1]))


# --- VISUALES ---
def draw_text_centered(surface, text, size, y_pos, color, font_name="consolas"):
    font = pygame.font.SysFont(font_name, size, bold=True)
    label = font.render(text, 1, color)
    shadow = font.render(text, 1, (20, 20, 40))
    x_pos = SCREEN_WIDTH // 2 - label.get_width() // 2
    surface.blit(shadow, (x_pos + 3, y_pos + 3))
    surface.blit(label, (x_pos, y_pos))


class MeshBackground:
    def __init__(self):
        self.time = 0

    def draw(self, surface):
        self.time += 0.05
        active_theme["bg"]
        accent_blue = active_theme["mesh"]

        # Efecto de malla en movimiento (Horizonte infinito)
        for i in range(0, 15):
            # Líneas horizontales con perspectiva y movimiento
            offset = (self.time * 20) % 60
            y = 250 + i * 40 + offset
            if y > SCREEN_HEIGHT:
                continue
            alpha = max(0, min(255, (y - 250) * 1.5))
            # Usar color del tema para la malla
            r, g, b = accent_blue
            color = (
                int(r * (alpha / 255)),
                int(g * (alpha / 255)),
                int(b * (alpha / 255)),
            )
            pygame.draw.line(surface, color, (0, y), (SCREEN_WIDTH, y), 1)

        for i in range(-10, 20):
            # Líneas verticales fugadas
            start_x = SCREEN_WIDTH // 2
            start_y = 200
            end_x = i * 100 + (SCREEN_WIDTH // 2 - 500)
            end_y = SCREEN_HEIGHT
            # Añadir movimiento sutil lateral
            end_x += math.sin(self.time * 0.5) * 20
            pygame.draw.line(
                surface, accent_blue, (start_x, start_y), (end_x, end_y), 1
            )


def draw_grid(surface):
    grid_color = (25, 25, 45)
    accent_color = (40, 40, 70)
    for i in range(GRID_HEIGHT + 1):
        y = TOP_LEFT_Y + i * BLOCK_SIZE
        pygame.draw.line(
            surface, grid_color, (TOP_LEFT_X, y), (TOP_LEFT_X + PLAY_WIDTH, y), 1
        )
    for j in range(GRID_WIDTH + 1):
        x = TOP_LEFT_X + j * BLOCK_SIZE
        pygame.draw.line(
            surface, grid_color, (x, TOP_LEFT_Y), (x, TOP_LEFT_Y + PLAY_HEIGHT), 1
        )
    for i in range(1, GRID_HEIGHT):
        for j in range(1, GRID_WIDTH):
            px, py = TOP_LEFT_X + j * BLOCK_SIZE, TOP_LEFT_Y + i * BLOCK_SIZE
            pygame.draw.rect(surface, accent_color, (px - 1, py - 1, 3, 3), 0)


def draw_block(surface, x, y, color, is_ghost=False, is_joker=False):
    rect = (x, y, BLOCK_SIZE, BLOCK_SIZE)
    if is_joker:
        pulse = (math.sin(pygame.time.get_ticks() * 0.02) + 1) / 2
        color = (int(130 + 125 * pulse), int(130 + 125 * pulse), 255)

    if is_ghost:
        # Sombra fantasma más sutil y tecnológica
        pygame.draw.rect(surface, (*color, 40), rect, 1, border_radius=2)
        return

    # --- EFECTO 3D EXTRUIDO ---
    padding = 3
    # 1. Cara Lateral/Inferior (Sombra de profundidad)
    dark_color = [max(0, c - 70) for c in color]
    mid_color = [max(0, c - 30) for c in color]
    light_color = [min(255, c + 50) for c in color]

    # Sombra proyectada detrás del bloque
    pygame.draw.rect(
        surface, (0, 0, 0, 80), (x + 4, y + 4, BLOCK_SIZE, BLOCK_SIZE), border_radius=4
    )

    # Polígonos para las caras del cubo
    # Cara derecha (Sombra media)
    pygame.draw.polygon(
        surface,
        mid_color,
        [
            (x + BLOCK_SIZE, y),
            (x + BLOCK_SIZE, y + BLOCK_SIZE),
            (x + BLOCK_SIZE - padding, y + BLOCK_SIZE - padding),
            (x + BLOCK_SIZE - padding, y + padding),
        ],
    )
    # Cara inferior (Sombra oscura)
    pygame.draw.polygon(
        surface,
        dark_color,
        [
            (x, y + BLOCK_SIZE),
            (x + BLOCK_SIZE, y + BLOCK_SIZE),
            (x + BLOCK_SIZE - padding, y + BLOCK_SIZE - padding),
            (x + padding, y + BLOCK_SIZE - padding),
        ],
    )
    # Cara superior (Brillo)
    pygame.draw.polygon(
        surface,
        light_color,
        [
            (x, y),
            (x + BLOCK_SIZE, y),
            (x + BLOCK_SIZE - padding, y + padding),
            (x + padding, y + padding),
        ],
    )
    # Cara izquierda (Brillo medio)
    pygame.draw.polygon(
        surface,
        mid_color,
        [
            (x, y),
            (x, y + BLOCK_SIZE),
            (x + padding, y + BLOCK_SIZE - padding),
            (x + padding, y + padding),
        ],
    )

    # Cara frontal (Principal)
    inner_rect = (
        x + padding,
        y + padding,
        BLOCK_SIZE - padding * 2,
        BLOCK_SIZE - padding * 2,
    )
    pygame.draw.rect(surface, color, inner_rect, border_radius=1)

    # Brillo en la esquina superior izquierda
    pygame.draw.circle(
        surface, (255, 255, 255, 100), (x + padding + 4, y + padding + 4), 2
    )


def draw_theme_selector(surface, is_open):
    x, y = SCREEN_WIDTH - 210, 20
    w, h = 180, 40

    # Botón Principal
    pygame.draw.rect(surface, active_theme["glow1"], (x, y, w, h), 2, border_radius=10)
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (*active_theme["bg"], 200), (0, 0, w, h), border_radius=10)
    surface.blit(s, (x, y))

    font = pygame.font.SysFont("consolas", 18, bold=True)
    txt = font.render(f"THEME: {active_theme_name}", 1, (255, 255, 255))
    surface.blit(txt, (x + 10, y + 10))

    if is_open:
        # Lista desplegable
        for i, name in enumerate(THEMES.keys()):
            dy = y + h + 5 + (i * 35)
            pygame.draw.rect(
                surface, active_theme["glow1"], (x, dy, w, 30), 1, border_radius=5
            )
            s_opt = pygame.Surface((w, 30), pygame.SRCALPHA)
            pygame.draw.rect(
                s_opt, (*active_theme["bg"], 230), (0, 0, w, 30), border_radius=5
            )
            surface.blit(s_opt, (x, dy))

            color = (
                (255, 255, 255) if name != active_theme_name else active_theme["glow1"]
            )
            opt_txt = font.render(name, 1, color)
            surface.blit(opt_txt, (x + 10, dy + 5))
    return pygame.Rect(x, y, w, h)


def draw_next_pieces(pieces, surface):
    stats_x = TOP_LEFT_X + PLAY_WIDTH + 50
    sy = TOP_LEFT_Y

    # Marco para Next Pieces
    pygame.draw.rect(
        surface, active_theme["bg"], (stats_x, sy, 200, 320), 0, border_radius=15
    )
    pygame.draw.rect(
        surface, active_theme["glow2"], (stats_x, sy, 200, 320), 1, border_radius=15
    )

    font = pygame.font.SysFont("consolas", 22, bold=True)
    surface.blit(
        font.render("NEXT MODULES", 1, active_theme["glow1"]), (stats_x + 20, sy + 20)
    )

    for idx, piece in enumerate(pieces):
        format_shape = piece.shape[piece.rotation % len(piece.shape)]

        # Calcular límites de la pieza para centrado perfecto
        blocks = []
        for i, line in enumerate(format_shape):
            for j, column in enumerate(list(line)):
                if column == "0":
                    blocks.append((j, i))

        if blocks:
            min_x = min(b[0] for b in blocks)
            max_x = max(b[0] for b in blocks)
            min_y = min(b[1] for b in blocks)
            max_y = max(b[1] for b in blocks)

            shape_w = (max_x - min_x + 1) * BLOCK_SIZE
            shape_h = (max_y - min_y + 1) * BLOCK_SIZE

            # Posición base para cada pieza (una debajo de la otra)
            piece_area_y = sy + 50 + (idx * 130)
            start_x = stats_x + (200 - shape_w) // 2 - min_x * BLOCK_SIZE
            start_y = piece_area_y + (130 - shape_h) // 2 - min_y * BLOCK_SIZE

            # La segunda pieza es un poco más pequeña/transparente para jerarquía visual
            for j, i in blocks:
                draw_block(
                    surface,
                    start_x + j * BLOCK_SIZE,
                    start_y + i * BLOCK_SIZE,
                    piece.color,
                    is_joker=piece.is_joker,
                )
                if idx > 0:  # Overlay de transparencia para la segunda pieza
                    s = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
                    s.fill((5, 5, 15, 100))
                    surface.blit(
                        s, (start_x + j * BLOCK_SIZE, start_y + i * BLOCK_SIZE)
                    )


class Particle:
    def __init__(self, x, y, color, is_firework=False):
        self.x = x
        self.y = y
        self.color = color
        self.is_firework = is_firework

        if is_firework:
            # Explosión radial para fuegos artificiales
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 8)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed
            self.lifetime = random.randint(180, 255)
            self.gravity = 0.12
        else:
            self.vx = random.uniform(-2, 2)
            self.vy = random.uniform(-2, 2)
            self.lifetime = 255
            self.gravity = 0.08

        self.size = random.randint(2, 4)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.lifetime -= 5

    def draw(self, surface):
        if self.lifetime > 0:
            alpha = max(0, self.lifetime)
            # Superficie para brillo aditivo
            s = pygame.Surface((self.size * 6, self.size * 6), pygame.SRCALPHA)

            # Núcleo de la partícula
            pygame.draw.circle(
                s, (*self.color, alpha), (self.size * 3, self.size * 3), self.size
            )

            # Resplandor exterior (solo si es fuego artificial)
            if self.is_firework:
                pygame.draw.circle(
                    s,
                    (*self.color, alpha // 3),
                    (self.size * 3, self.size * 3),
                    self.size * 2,
                )

            surface.blit(s, (int(self.x - self.size * 3), int(self.y - self.size * 3)))


def get_player_name(surface, score):
    name = ""
    run = True
    clock = pygame.time.Clock()
    mesh = MeshBackground()

    while run:
        surface.fill(active_theme["bg"])
        mesh.draw(surface)

        # Panel de entrada
        panel_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 150, 500, 300
        )
        s = pygame.Surface((500, 300), pygame.SRCALPHA)
        pygame.draw.rect(
            s, (*active_theme["bg"], 230), (0, 0, 500, 300), border_radius=20
        )
        pygame.draw.rect(
            s, active_theme["glow1"], (0, 0, 500, 300), 2, border_radius=20
        )
        surface.blit(s, (panel_rect.x, panel_rect.y))

        draw_text_centered(
            surface, "NEW HIGH RECORD!", 40, panel_rect.y + 30, active_theme["glow1"]
        )
        draw_text_centered(
            surface, f"FINAL SCORE: {score}", 25, panel_rect.y + 90, WHITE
        )

        # Caja de texto
        box_y = panel_rect.y + 160
        pygame.draw.rect(
            surface, (5, 5, 15), (panel_rect.x + 50, box_y, 400, 50), border_radius=5
        )
        pygame.draw.rect(
            surface,
            active_theme["glow1"],
            (panel_rect.x + 50, box_y, 400, 50),
            1,
            border_radius=5,
        )

        name_surf = pygame.font.SysFont("consolas", 35, bold=True).render(
            name + "_", 1, active_theme["glow2"]
        )
        surface.blit(
            name_surf, (SCREEN_WIDTH // 2 - name_surf.get_width() // 2, box_y + 5)
        )

        draw_text_centered(
            surface,
            "PRESS ENTER TO ACCESS ARCHIVE",
            15,
            panel_rect.y + 250,
            (100, 100, 150),
        )

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if name.strip() == "":
                        name = "NEON_USER"
                    run = False
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                else:
                    if len(name) < 10 and (
                        event.unicode.isalnum() or event.unicode in [" ", "_"]
                    ):
                        name += event.unicode.upper()
        clock.tick(60)
    return name[:10]


def draw_high_scores(surface, scores, x_offset=0):
    panel_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200 + x_offset, 250, 400, 300)
    # Fondo del panel con algo de transparencia
    s = pygame.Surface((400, 300), pygame.SRCALPHA)
    pygame.draw.rect(s, (15, 15, 35, 200), (0, 0, 400, 300), border_radius=15)
    pygame.draw.rect(s, CYAN_GLOW, (0, 0, 400, 300), 2, border_radius=15)
    surface.blit(s, (panel_rect.x, panel_rect.y))

    font_title = pygame.font.SysFont("consolas", 24, bold=True)
    font_entry = pygame.font.SysFont("consolas", 18)

    title = font_title.render("SYSTEM HIGH RECORDS", 1, CYAN_GLOW)
    surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2 + x_offset, 270))

    for i, entry in enumerate(scores):
        color = (200, 200, 255) if i > 0 else (255, 255, 100)
        rank = f"{i + 1:2}."
        name = f"{entry['name']:<10}"
        score = f"{entry['score']:>7}"

        label_rank = font_entry.render(rank, 1, CYAN_GLOW)
        label_name = font_entry.render(name, 1, color)
        label_score = font_entry.render(score, 1, WHITE)

        y_y = 310 + i * 22
        surface.blit(label_rank, (panel_rect.x + 30, y_y))
        surface.blit(label_name, (panel_rect.x + 80, y_y))
        surface.blit(label_score, (panel_rect.x + 280, y_y))


def draw_window(surface, grid, score, total_lines, particles, bg_offset, selector_open):
    surface.fill(active_theme["bg"])

    # Fondo con malla sutil
    mesh_color = active_theme["mesh"]
    for i in range(0, SCREEN_HEIGHT, 50):
        pygame.draw.line(surface, mesh_color, (0, i), (SCREEN_WIDTH, i), 1)
    for i in range(0, SCREEN_WIDTH, 50):
        pygame.draw.line(surface, mesh_color, (i, 0), (i, SCREEN_HEIGHT), 1)

    # Título Neón
    font_main = pygame.font.SysFont("arialblack", 60)
    title_text = "NEON TETRIS"
    title_surf = font_main.render(title_text, 1, active_theme["glow1"])

    # Resplandor suave
    for offset in range(3, 0, -1):
        s = font_main.render(title_text, 1, active_theme["glow2"])
        surface.blit(
            s,
            (
                TOP_LEFT_X + PLAY_WIDTH / 2 - title_surf.get_width() / 2 + offset,
                45 + offset,
            ),
        )
    surface.blit(
        title_surf, (TOP_LEFT_X + PLAY_WIDTH / 2 - title_surf.get_width() / 2, 45)
    )

    stats_x = TOP_LEFT_X + PLAY_WIDTH + 50
    panel_y = TOP_LEFT_Y + 340
    pygame.draw.rect(
        surface, active_theme["bg"], (stats_x, panel_y, 200, 180), 0, border_radius=15
    )
    pygame.draw.rect(
        surface,
        active_theme["glow1"],
        (stats_x, panel_y, 200, 180),
        1,
        border_radius=15,
    )

    label_font = pygame.font.SysFont("consolas", 22, bold=True)
    val_font = pygame.font.SysFont("consolas", 34, bold=True)
    surface.blit(
        label_font.render("PLAYER SCORE", 1, (255, 255, 255)),
        (stats_x + 20, panel_y + 20),
    )
    surface.blit(
        val_font.render(str(score), 1, active_theme["glow1"]),
        (stats_x + 20, panel_y + 45),
    )
    surface.blit(
        label_font.render("LINES CLEARED", 1, (255, 255, 255)),
        (stats_x + 20, panel_y + 100),
    )
    surface.blit(
        val_font.render(str(total_lines), 1, active_theme["glow2"]),
        (stats_x + 20, panel_y + 125),
    )

    pygame.draw.rect(
        surface, (0, 0, 0), (TOP_LEFT_X, TOP_LEFT_Y, PLAY_WIDTH, PLAY_HEIGHT)
    )

    # Paredes 3D del foso
    pygame.draw.polygon(
        surface,
        active_theme["mesh"],
        [
            (TOP_LEFT_X, TOP_LEFT_Y),
            (TOP_LEFT_X - 15, TOP_LEFT_Y - 15),
            (TOP_LEFT_X - 15, TOP_LEFT_Y + PLAY_HEIGHT + 15),
            (TOP_LEFT_X, TOP_LEFT_Y + PLAY_HEIGHT),
        ],
    )
    pygame.draw.polygon(
        surface,
        active_theme["bg"],
        [
            (TOP_LEFT_X + PLAY_WIDTH, TOP_LEFT_Y),
            (TOP_LEFT_X + PLAY_WIDTH + 15, TOP_LEFT_Y - 15),
            (TOP_LEFT_X + PLAY_WIDTH + 15, TOP_LEFT_Y + PLAY_HEIGHT + 15),
            (TOP_LEFT_X + PLAY_WIDTH, TOP_LEFT_Y + PLAY_HEIGHT),
        ],
    )

    draw_grid(surface)

    for i in range(len(grid)):
        for j in range(len(grid[i])):
            if grid[i][j] != active_theme["bg"]:
                draw_block(
                    surface,
                    TOP_LEFT_X + j * BLOCK_SIZE,
                    TOP_LEFT_Y + i * BLOCK_SIZE,
                    grid[i][j],
                )

    for p in particles[:]:
        p.update()
        p.draw(surface)
        if p.lifetime <= 0:
            particles.remove(p)

    for i in range(3):
        color = (*active_theme["glow2"], 150 - i * 40)
        pygame.draw.rect(
            surface,
            color,
            (TOP_LEFT_X - i, TOP_LEFT_Y - i, PLAY_WIDTH + i * 2, PLAY_HEIGHT + i * 2),
            2,
            border_radius=5,
        )

    draw_theme_selector(surface, selector_open)


def main(game_mode="JOKER"):
    """Main game loop for Neon Tetris.

    Args:
        game_mode (str): The selected game mode ("CLASSIC" or "JOKER").
    """
    global active_theme_name, active_theme
    locked_positions = {}
    particles = []
    bg_offset = 0
    change_piece = False
    selector_open = False
    run = True
    current_piece = get_shape(game_mode)
    next_pieces = [get_shape(game_mode), get_shape(game_mode)]
    clock = pygame.time.Clock()
    fall_time = 0
    fall_speed = 0.27
    score = 0
    total_lines = 0
    win = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    while run:
        grid = create_grid(locked_positions)
        fall_time += clock.get_rawtime()
        bg_offset += 1
        clock.tick()

        if fall_time / 1000 > fall_speed:
            fall_time = 0
            current_piece.y += 1

            if current_piece.is_joker:
                pos = convert_shape_format(current_piece)[0]
                bx, by = pos

                # REGLA CUÁNTICA: Solo se queda si es el HUECO MÁS PROFUNDO de la columna
                if by >= 0 and by < GRID_HEIGHT:
                    if grid[by][bx] == active_theme["bg"]:
                        has_hole_below = False
                        for ty in range(by + 1, GRID_HEIGHT):
                            if grid[ty][bx] == active_theme["bg"]:
                                has_hole_below = True
                                break
                        if not has_hole_below:
                            # Ya no hay más huecos abajo, nos bloqueamos aquí
                            change_piece = True
                elif by >= GRID_HEIGHT:
                    current_piece.y -= 1
                    change_piece = True
            else:
                if not (valid_space(current_piece, grid)) and current_piece.y > 0:
                    current_piece.y -= 1
                    change_piece = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    current_piece.x -= 1
                    if not (valid_space(current_piece, grid)):
                        current_piece.x += 1
                if event.key == pygame.K_RIGHT:
                    current_piece.x += 1
                    if not (valid_space(current_piece, grid)):
                        current_piece.x -= 1
                if event.key == pygame.K_DOWN:
                    current_piece.y += 1
                    if not (valid_space(current_piece, grid)):
                        current_piece.y -= 1
                if event.key == pygame.K_UP:
                    if game_mode == "RANDOM":
                        # -- RANDOM MADNESS: Cambiar pieza al rotar --
                        old_shape = current_piece.shape
                        old_rotation = current_piece.rotation
                        old_joker = current_piece.is_joker

                        potential_shapes = SHAPES[:]
                        random.shuffle(potential_shapes)

                        found = False
                        for s in potential_shapes:
                            potential_rotations = list(range(len(s)))
                            random.shuffle(potential_rotations)
                            for r in potential_rotations:
                                current_piece.shape = s
                                current_piece.rotation = r
                                current_piece.is_joker = s == SHAPE_JOKER
                                if valid_space(current_piece, grid):
                                    current_piece.update_color()
                                    found = True
                                    break
                            if found:
                                break

                        if not found:
                            current_piece.shape = old_shape
                            current_piece.rotation = old_rotation
                            current_piece.is_joker = old_joker
                    else:
                        current_piece.rotation += 1
                        if not (valid_space(current_piece, grid)):
                            current_piece.rotation -= 1
                if event.key == pygame.K_SPACE:
                    if current_piece.is_joker:
                        # Saltar al hueco más profundo
                        pos = convert_shape_format(current_piece)[0]
                        bx = pos[0]
                        target_y = pos[1]
                        for ty in range(pos[1], GRID_HEIGHT):
                            if grid[ty][bx] == active_theme["bg"]:
                                # ¿Es el último hueco?
                                has_below = False
                                for cy in range(ty + 1, GRID_HEIGHT):
                                    if grid[cy][bx] == active_theme["bg"]:
                                        has_below = True
                                        break
                                if not has_below:
                                    target_y = ty
                                    break
                        current_piece.y += target_y - pos[1]
                    else:
                        while valid_space(current_piece, grid):
                            current_piece.y += 1
                        current_piece.y -= 1
                    change_piece = True

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                # Zona del botón
                btn_rect = pygame.Rect(SCREEN_WIDTH - 210, 20, 180, 40)
                if btn_rect.collidepoint(mx, my):
                    selector_open = not selector_open
                elif selector_open:
                    for i, name in enumerate(THEMES.keys()):
                        dy = 20 + 40 + 5 + (i * 35)
                        if pygame.Rect(SCREEN_WIDTH - 210, dy, 180, 30).collidepoint(
                            mx, my
                        ):
                            active_theme_name = name
                            active_theme = THEMES[name]
                            selector_open = False
                            # Actualizar colores de piezas existentes
                            current_piece.update_color()
                            for p in next_pieces:
                                p.update_color()
                            for pos, color in locked_positions.items():
                                # Recalcular color según el tema (aproximado por índice original si se guardara,
                                # por ahora lo dejamos o lo cambiamos masivamente)
                                pass
                            break

        if change_piece:
            shape_pos = convert_shape_format(current_piece)
            # Solo bloqueamos la pieza si estamos en una posición válida y VACÍA
            for pos in shape_pos:
                bx, by = pos
                if 0 <= by < GRID_HEIGHT and 0 <= bx < GRID_WIDTH:
                    # El Joker solo se queda si el espacio es negro
                    if current_piece.is_joker:
                        if grid[by][bx] == active_theme["bg"]:
                            locked_positions[(bx, by)] = current_piece.color
                    else:
                        locked_positions[(bx, by)] = current_piece.color

            current_piece = next_pieces.pop(0)
            next_pieces.append(get_shape(game_mode))
            change_piece = False

            # --- LÓGICA DE LIMPIEZA DE LÍNEAS ROBUSTA ---
            temp_grid = create_grid(locked_positions)
            lines_to_clear = []
            bg_c = active_theme["bg"]
            for i in range(GRID_HEIGHT):
                # Una línea está llena si NO tiene celdas con el color de fondo
                is_full = True
                for x in range(GRID_WIDTH):
                    if temp_grid[i][x] == bg_c:
                        is_full = False
                        break
                if is_full:
                    lines_to_clear.append(i)

            if lines_to_clear:
                # Partículas de fuegos artificiales
                for row_idx in lines_to_clear:
                    for px in range(0, GRID_WIDTH, 2):
                        particles.append(
                            Particle(
                                TOP_LEFT_X + px * BLOCK_SIZE + 15,
                                TOP_LEFT_Y + row_idx * BLOCK_SIZE + 15,
                                temp_grid[row_idx][px],
                                is_firework=True,
                            )
                        )

                # Eliminar las posiciones de las líneas borradas
                for row_idx in lines_to_clear:
                    for x in range(GRID_WIDTH):
                        if (x, row_idx) in locked_positions:
                            del locked_positions[(x, row_idx)]

                # GRAVEDAD REAL: Cada bloque cae N espacios (N = cuántas líneas se borraron debajo de él)
                new_locked = {}
                for (x, y), color in locked_positions.items():
                    # Contamos cuántas líneas de 'lines_to_clear' están por debajo de la pieza actual
                    shift = sum(1 for line_y in lines_to_clear if line_y > y)
                    new_locked[(x, y + shift)] = color
                locked_positions = new_locked

                total_lines += len(lines_to_clear)
                score += [0, 100, 300, 500, 800][min(len(lines_to_clear), 4)]
                if total_lines % 20 == 0:
                    fall_speed *= 0.95

        # RE-GENERAR GRID con las posiciones ya actualizadas y limpias
        grid = create_grid(locked_positions)

        draw_window(win, grid, score, total_lines, particles, bg_offset, selector_open)

        ghost = get_ghost_piece(current_piece, grid)
        ghost_pos = convert_shape_format(ghost)
        for pos in ghost_pos:
            if pos[1] > -1:
                draw_block(
                    win,
                    TOP_LEFT_X + pos[0] * BLOCK_SIZE,
                    TOP_LEFT_Y + pos[1] * BLOCK_SIZE,
                    current_piece.color,
                    is_ghost=True,
                )

        shape_pos = convert_shape_format(current_piece)
        for pos in shape_pos:
            if pos[1] > -1:
                draw_block(
                    win,
                    TOP_LEFT_X + pos[0] * BLOCK_SIZE,
                    TOP_LEFT_Y + pos[1] * BLOCK_SIZE,
                    current_piece.color,
                    is_joker=current_piece.is_joker,
                )

        draw_next_pieces(next_pieces, win)
        pygame.display.update()

        if check_lost(locked_positions):
            draw_text_centered(
                win, "GAME OVER", 80, SCREEN_HEIGHT // 2 - 40, WHITE, "arialblack"
            )
            pygame.display.update()
            pygame.time.delay(1500)
            scores = load_scores()
            if len(scores) < 10 or score > scores[-1]["score"]:
                name = get_player_name(win, score)
                scores.append({"name": name, "score": score})
                scores = sorted(scores, key=lambda x: x["score"], reverse=True)[:10]
                save_scores(scores)
            run = False


def main_menu():
    """Main menu display and game initialization."""
    pygame.init()
    win = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("NEON TETRIS CYBERPUNK")

    mesh = MeshBackground()
    clock = pygame.time.Clock()

    modes = ["CLASSIC", "JOKER", "RANDOM"]
    current_mode_idx = 1  # Default to Joker Style
    run = True

    while run:
        win.fill(active_theme["bg"])
        mesh.draw(win)

        # Efecto de partículas de fondo
        for i in range(20):
            x = (i * 150) % SCREEN_WIDTH
            y = (i * 200 + pygame.time.get_ticks() * 0.05) % SCREEN_HEIGHT
            pygame.draw.circle(win, active_theme["mesh"], (int(x), int(y)), 1)

        # Título Moderno
        font_main = pygame.font.SysFont("arialblack", 80)
        title_surf = font_main.render("NEON TETRIS", 1, active_theme["glow1"])

        # Brillo del título
        for offset in range(5, 0, -1):
            s = font_main.render("NEON TETRIS", 1, active_theme["glow2"])
            win.blit(
                s,
                (SCREEN_WIDTH // 2 - title_surf.get_width() // 2 + offset, 80 + offset),
            )

        win.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 80))

        # Subtítulo
        draw_text_centered(win, "MULTIVERSE EDITION v3.0", 20, 180, active_theme["glow2"])

        # Sección de Modo de Juego
        mode_y = 560
        mode_title_font = pygame.font.SysFont("consolas", 25, bold=True)
        mode_text = mode_title_font.render("GAME MODE:", 1, WHITE)
        win.blit(mode_text, (SCREEN_WIDTH // 2 - 180, mode_y))

        for i, mode in enumerate(modes):
            color = active_theme["glow1"] if i == current_mode_idx else (100, 100, 100)
            prefix = ">> " if i == current_mode_idx else "   "
            if mode == "CLASSIC":
                display_name = "CLASSIC"
            elif mode == "JOKER":
                display_name = "JOKER STYLE"
            else:
                display_name = "RANDOM MADNESS"
            mode_surf = mode_title_font.render(f"{prefix}{display_name}", 1, color)
            win.blit(mode_surf, (SCREEN_WIDTH // 2 + 10, mode_y + (i * 30) - 5))

        # High Scores
        scores = load_scores()
        draw_high_scores(win, scores)

        # Texto pulsante de inicio
        pulse = (math.sin(pygame.time.get_ticks() * 0.005) + 1) / 2
        text_color = (
            (int(200 * pulse), 255, int(200 * pulse))
            if active_theme_name == "MATRIX"
            else (255, 255, 255)
        )
        draw_text_centered(win, "PRESS ENTER TO START", 25, 680, text_color)
        draw_text_centered(win, "(USE ARROWS TO CHANGE MODE)", 15, 715, (150, 150, 200))

        pygame.display.update()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                    current_mode_idx = (current_mode_idx + 1) % len(modes)
                if event.key == pygame.K_RETURN:
                    main(modes[current_mode_idx])


if __name__ == "__main__":
    main_menu()
