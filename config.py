"""
Configuración global para Neon Tetris PRO.
Contiene dimensiones, temas visuales, colores base y las definiciones de las piezas.
"""

import json
import os

# --- DIMENSIONES DE LA PANTALLA Y EL JUEGO ---
SCREEN_WIDTH = 950
SCREEN_HEIGHT = 850
BLOCK_SIZE = 30      # Tamaño en píxeles de cada bloque cuadrado
GRID_WIDTH = 10      # Ancho del tablero en bloques
GRID_HEIGHT = 20     # Alto del tablero en bloques

# Dimensiones del área de juego
PLAY_WIDTH = GRID_WIDTH * BLOCK_SIZE
PLAY_HEIGHT = GRID_HEIGHT * BLOCK_SIZE

# Posicionamiento del tablero en la pantalla
TOP_LEFT_X = (SCREEN_WIDTH - PLAY_WIDTH) // 2 - 50
TOP_LEFT_Y = 160

# Archivo de persistencia para mejores puntuaciones
SCORE_FILE = "highscores.json"

# --- DISEÑO DEL SISTEMA DE TEMAS ---
# Cada tema define colores de fondo, malla, resplandores y los colores de las 7 piezas
THEMES = {
    "CYBERPUNK": {
        "bg": (5, 5, 15),
        "mesh": (25, 25, 65),
        "glow1": (0, 255, 255),
        "glow2": (150, 0, 255),
        "shapes": [
            (0, 255, 255),   # Cian eléctrico
            (255, 0, 255),   # Magenta neón
            (255, 255, 0),   # Amarillo vibrante
            (0, 255, 0),     # Verde ácido
            (255, 100, 0),   # Naranja fuego
            (100, 100, 255), # Azul profundo
            (255, 50, 50),   # Rojo brillante
        ],
    },
    "MATRIX": {
        "bg": (0, 10, 0),
        "mesh": (0, 40, 0),
        "glow1": (0, 255, 70),
        "glow2": (0, 150, 30),
        "shapes": [
            (0, 255, 0),     # Verde puro
            (50, 200, 50),   # Verde esmeralda
            (150, 255, 150), # Verde fantasmal
            (0, 100, 0),     # Verde oscuro
            (100, 255, 0),   # Lima
            (0, 150, 150),   # Verde azulado
            (255, 255, 255), # Blanco (Código puro)
        ],
    },
    "LAVA": {
        "bg": (20, 5, 0),
        "mesh": (60, 20, 0),
        "glow1": (255, 80, 0),
        "glow2": (255, 200, 0),
        "shapes": [
            (255, 0, 0),     # Rojo lava
            (255, 100, 0),   # Naranja lava
            (255, 255, 0),   # Amarillo sol
            (150, 50, 0),    # Tierra quemada
            (255, 150, 50),  # Ámbar
            (100, 0, 0),     # Carmesí oscuro
            (255, 200, 100), # Oro fundido
        ],
    },
    "ICE": {
        "bg": (5, 15, 30),
        "mesh": (100, 150, 255),
        "glow1": (180, 230, 255),
        "glow2": (230, 250, 255),
        "shapes": [
            (0, 150, 255),   # Azul ártico
            (150, 255, 255), # Cian hielo
            (255, 255, 255), # Blanco nieve
            (80, 80, 200),   # Azul profundo glacial
            (180, 200, 255), # Celeste pálido
            (100, 255, 200), # Menta fría
            (200, 220, 255), # Cristalino
        ],
    },
    "CLASSIC": {
        "bg": (10, 10, 10),
        "mesh": (40, 40, 40),
        "glow1": (200, 200, 200),
        "glow2": (100, 100, 100),
        "shapes": [
            (255, 0, 0),     # Rojo
            (0, 255, 0),     # Verde
            (0, 0, 255),     # Azul
            (255, 255, 0),   # Amarillo
            (255, 165, 0),   # Naranja
            (128, 0, 128),   # Púrpura
            (0, 255, 255),   # Cian
        ],
    },
}

# --- COLORES BASE ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# --- ESTADO DE TEMA ACTIVO ---
active_theme_name = "CYBERPUNK"
active_theme = THEMES[active_theme_name]

# Funciones de utilidad para obtener colores dinámicos según el tema
def get_c(): return active_theme["bg"]
def get_g1(): return active_theme["glow1"]
def get_g2(): return active_theme["glow2"]
def get_m(): return active_theme["mesh"]
def get_s(idx): return active_theme["shapes"][idx % len(active_theme["shapes"])]

# --- DEFINICIÓN DE PIEZAS (FORMA Y ROTACIONES) ---
# Matriz de 5x5 donde '0' representa un bloque ocupado
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
    [".....", "..00.", "..0..", "..0..", "....."],
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

# --- SISTEMA DE TRADUCCIÓN (i18n) ---
LANGS = ["ESPAÑOL", "ENGLISH", "DEUTSCH"]
current_lang = 0

TRANSLATIONS = {
    "ESPAÑOL": {
        "HOLD": "GUARDADA", "NEXT": "SIGUIENTES", "SCORE": "PUNTAJE", "LINES": "LÍNEAS",
        "LEVEL": "NIVEL", "TOP_HEROES": "--- MEJORES PUNTAJES ---", "PAUSED": "JUEGO PAUSADO",
        "CONTINUE": "CONTINUAR", "SAVE": "GUARDAR PARTIDA", "MENU": "VOLVER AL MENÚ",
        "LOAD": "CARGAR PARTIDA", "EMPTY": "VACÍO", "SLOT": "SLOT", "PRESS_ENTER_LOAD": "Presiona ENTER para cargar",
        "GAME_OVER": "FIN DEL JUEGO", "FINAL_SCORE": "PUNTAJE FINAL:", "PRESS_ANY_KEY": "PRESIONA CUALQUIER TECLA",
        "NEW_RECORD": "¡NUEVO RÉCORD!", "ENTER_NAME": "INTRODUCE TU NOMBRE:", "PLAYER": "JUGADOR",
        "SELECT_OPT": "SELECCIONA OPCIÓN", "PRESS_START": "ENTER PARA EMPEZAR", "EXIT": "SALIR DEL JUEGO",
        "SELECT_SAVE": "SELECCIONA SLOT PARA GUARDAR", "THEME": "TEMA", "LANGUAGE": "IDIOMA",
        "CLASSIC": "CLÁSICO", "JOKER": "COMODÍN", "RANDOM": "ALEATORIO", "ZEN": "RELAX"
    },
    "ENGLISH": {
        "HOLD": "HOLD", "NEXT": "NEXT", "SCORE": "SCORE", "LINES": "LINES",
        "LEVEL": "LEVEL", "TOP_HEROES": "--- TOP HEROES ---", "PAUSED": "GAME PAUSED",
        "CONTINUE": "CONTINUE", "SAVE": "SAVE GAME", "MENU": "BACK TO MENU",
        "LOAD": "LOAD GAME", "EMPTY": "EMPTY", "SLOT": "SLOT", "PRESS_ENTER_LOAD": "Press ENTER to load",
        "GAME_OVER": "GAME OVER", "FINAL_SCORE": "FINAL SCORE:", "PRESS_ANY_KEY": "PRESS ANY KEY TO CONTINUE",
        "NEW_RECORD": "NEW RECORD!", "ENTER_NAME": "ENTER YOUR NAME:", "PLAYER": "PLAYER",
        "SELECT_OPT": "SELECT OPTION", "PRESS_START": "ENTER TO START", "EXIT": "EXIT GAME",
        "SELECT_SAVE": "SELECT SLOT TO SAVE", "THEME": "THEME", "LANGUAGE": "LANGUAGE",
        "CLASSIC": "CLASSIC", "JOKER": "JOKER", "RANDOM": "RANDOM", "ZEN": "ZEN"
    },
    "DEUTSCH": {
        "HOLD": "GEHALTEN", "NEXT": "NÄCHSTE", "SCORE": "PUNKTE", "LINES": "REIHEN",
        "LEVEL": "LEVEL", "TOP_HEROES": "--- TOP HELDEN ---", "PAUSED": "PAUSE",
        "CONTINUE": "WEITER", "SAVE": "SPEICHERN", "MENU": "HAUPTMENÜ",
        "LOAD": "LADEN", "EMPTY": "LEER", "SLOT": "SLOT", "PRESS_ENTER_LOAD": "Drücke ENTER zum Laden",
        "GAME_OVER": "SPIEL VORBEI", "FINAL_SCORE": "ENDPUNKTZAHL:", "PRESS_ANY_KEY": "TASTE DRÜCKEN",
        "NEW_RECORD": "NEUER REKORD!", "ENTER_NAME": "NAME EINGEBEN:", "PLAYER": "SPIELER",
        "SELECT_OPT": "OPTION WÄHLEN", "PRESS_START": "ENTER ZUM STARTEN", "EXIT": "BEENDEN",
        "SELECT_SAVE": "SPEICHERPLATZ WÄHLEN", "THEME": "THEMA", "LANGUAGE": "SPRACHE",
        "CLASSIC": "KLASSIK", "JOKER": "JOKER", "RANDOM": "ZUFALL", "ZEN": "ZEN"
    }
}

def _(key):
    """Función de traducción rápida."""
    lang = LANGS[current_lang]
    return TRANSLATIONS[lang].get(key, key)

# Pieza especial: ficha única del modo JOKER
SHAPE_JOKER = [[".....", ".....", "..0..", ".....", "....."]]

# Lista maestra de todas las formas disponibles
SHAPES = [SHAPE_S, SHAPE_Z, SHAPE_I, SHAPE_O, SHAPE_J, SHAPE_L, SHAPE_T, SHAPE_JOKER]
