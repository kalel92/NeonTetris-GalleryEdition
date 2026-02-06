"""
Lógica central y cálculos de Neon Tetris.
Contiene la gestión del tablero, detección de colisiones y persistencia de datos.
"""

import os
import json
import random
import config
from models import Piece

def load_scores():
    """Carga las puntuaciones más altas desde el archivo JSON.
    
    Returns:
        list: Lista ordenada de diccionarios con nombre y puntaje.
    """
    if not os.path.exists(config.SCORE_FILE):
        return []
    try:
        with open(config.SCORE_FILE, "r") as f:
            return sorted(json.load(f), key=lambda x: x["score"], reverse=True)[:10]
    except (json.JSONDecodeError, IOError, KeyError):
        return []

def save_scores(scores):
    """Guarda las puntuaciones en el archivo JSON."""
    with open(config.SCORE_FILE, "w") as f:
        json.dump(scores, f)

def create_grid(locked_pos={}):
    """Representa el estado actual del tablero de juego.
    
    Args:
        locked_pos (dict): Diccionario de (x,y) -> Color de bloques fijos.
        
    Returns:
        list: Matriz de colores que representa el tablero.
    """
    grid = [[config.active_theme["bg"] for _ in range(config.GRID_WIDTH)] for _ in range(config.GRID_HEIGHT)]
    for y in range(config.GRID_HEIGHT):
        for x in range(config.GRID_WIDTH):
            if (x, y) in locked_pos:
                grid[y][x] = locked_pos[(x, y)]
    return grid

def convert_shape_format(piece):
    """Convierte el formato de 'lista de hileras' de una pieza a coordenadas reales en el tablero.
    
    Args:
        piece (Piece): La pieza cuya posición se desea calcular.
        
    Returns:
        list: Lista de tuplas (x, y) con las posiciones de los bloques.
    """
    positions = []
    format_shape = piece.shape[piece.rotation % len(piece.shape)]
    for i, line in enumerate(format_shape):
        row = list(line)
        for j, column in enumerate(row):
            if column == "0":
                positions.append((piece.x + j, piece.y + i))
    
    # Ajuste de offset para centrar la pieza correctamente según el sistema de formas 5x5
    for i, pos in enumerate(positions):
        positions[i] = (pos[0] - 2, pos[1] - 4)
    return positions

def valid_space(piece, grid):
    """Comprueba si una pieza puede ocupar su posición actual sin colisionar.
    
    Args:
        piece (Piece): La pieza a validar.
        grid (list): El tablero actual.
        
    Returns:
        bool: True si la posición es válida, False en caso contrario.
    """
    bg_color = config.active_theme["bg"]
    if not piece.is_joker:
        # Lista de todas las posiciones vacías en el tablero
        accepted_pos = [[(j, i) for j in range(config.GRID_WIDTH) if grid[i][j] == bg_color] for i in range(config.GRID_HEIGHT)]
        accepted_pos = [j for sub in accepted_pos for j in sub]
        
        formatted = convert_shape_format(piece)
        for pos in formatted:
            if pos not in accepted_pos:
                # Si está por encima del tablero (y < 0), es válido a menos que esté fuera de X
                if pos[1] > -1:
                    return False
        return True
    
    if piece.is_joker:
        # Lógica especial para el JOKER: Atraviesa bloques para rellenar huecos internos
        formatted = convert_shape_format(piece)
        for pos in formatted:
            x, y = pos
            if x < 0 or x >= config.GRID_WIDTH or y >= config.GRID_HEIGHT:
                return False
            # Si hay un bloque en la posición actual
            if y >= 0 and grid[y][x] != config.active_theme["bg"]:
                # Comprobar si hay algún hueco más abajo en esta columna para seguir bajando
                has_hole_below = False
                for ty in range(y + 1, config.GRID_HEIGHT):
                    if grid[ty][x] == config.active_theme["bg"]:
                        has_hole_below = True
                        break
                return has_hole_below
        return True

def get_ghost_piece(piece, grid):
    """Calcula la posición donde caería la pieza actual (sombra)."""
    bg_color = config.active_theme["bg"]
    ghost = Piece(piece.x, piece.y, piece.shape)
    ghost.rotation = piece.rotation
    
    if ghost.is_joker:
        # El joker cae hasta el hueco más profundo disponible
        pos = convert_shape_format(ghost)[0]
        bx = pos[0]
        deepest_y = pos[1]
        for ty in range(pos[1], config.GRID_HEIGHT):
            if grid[ty][bx] == bg_color:
                has_hole_below = False
                for check_y in range(ty + 1, config.GRID_HEIGHT):
                    if grid[check_y][bx] == bg_color:
                        has_hole_below = True
                        break
                if not has_hole_below:
                    deepest_y = ty
                    break
        ghost.y += deepest_y - pos[1]
    else:
        # Pieza normal cae hasta colisionar
        while valid_space(ghost, grid):
            ghost.y += 1
        ghost.y -= 1
    return ghost

def check_lost(positions):
    """Detección de Game Over: si algún bloque fijo llega al tope superior."""
    for pos in positions:
        x, y = pos
        if y < 1:
            return True
    return False

def get_shape(game_mode="JOKER"):
    """Fábrica de piezas aleatorias."""
    if game_mode == "JOKER" and random.random() < 0.10:
        return Piece(4, 0, config.SHAPE_JOKER) # 10% de probabilidad de Joker
    return Piece(4, 0, random.choice(config.SHAPES[:-1]))

def save_game(slot, game_data):
    """Guarda el estado completo del juego en uno de los 5 slots."""
    if not (1 <= slot <= 5): return False
    filename = f"save_slot_{slot}.json"
    try:
        # Serializar locked_positions (tuplas a strings)
        serializable_locked = {f"{k[0]},{k[1]}": list(v) for k, v in game_data['locked'].items()}
        
        save_obj = {
            "mode": game_data['mode'],
            "score": game_data['score'],
            "lines": game_data['lines'],
            "level": game_data['level'],
            "combo": game_data['combo'],
            "locked": serializable_locked,
            "current_idx": game_data['current_idx'],
            "next_indices": game_data['next_indices'],
            "hold_idx": game_data['hold_idx'],
            "theme": config.active_theme_name
        }
        with open(filename, "w") as f:
            json.dump(save_obj, f)
        return True
    except Exception as e:
        print(f"Error Save: {e}"); return False

def load_game(slot):
    """Carga el estado del juego desde un slot."""
    filename = f"save_slot_{slot}.json"
    if not os.path.exists(filename): return None
    try:
        with open(filename, "r") as f:
            data = json.load(f)
        locked = {}
        for k, v in data['locked'].items():
            x, y = map(int, k.split(','))
            locked[(x,y)] = tuple(v)
        return {
            "mode": data['mode'], "score": data['score'], "lines": data['lines'],
            "level": data['level'], "combo": data['combo'], "locked": locked,
            "current": Piece(4, 0, config.SHAPES[data['current_idx']]),
            "nexts": [Piece(4, 0, config.SHAPES[idx]) for idx in data['next_indices']],
            "hold": Piece(4, 0, config.SHAPES[data['hold_idx']]) if data['hold_idx'] is not None else None,
            "theme": data.get('theme', 'CYBERPUNK')
        }
    except Exception as e:
        print(f"Error Load: {e}"); return None

def get_save_info():
    """Retorna los datos resumen de los 5 slots."""
    info = []
    for i in range(1, 6):
        path = f"save_slot_{i}.json"
        if os.path.exists(path):
            with open(path, "r") as f:
                d = json.load(f)
                info.append({"slot": i, "score": d['score'], "level": d['level'], "mode": d['mode']})
        else: info.append({"slot": i, "empty": True})
    return info
