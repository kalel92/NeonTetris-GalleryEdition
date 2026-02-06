"""
Modelos de Datos y Objetos de Neon Tetris PRO.
Define las entidades básicas: Piezas, Partículas y Fondos animados.
"""

import random
import math
import pygame
import config

class Piece:
    """Representa una pieza de Tetris o un 'módulo' de software en el multiverso."""

    def __init__(self, x, y, shape):
        """Inicializa una pieza en una posición y con una forma específica.
        
        Args:
            x (int): Posición X inicial en bloques.
            y (int): Posición Y inicial en bloques.
            shape (list): Matriz de rotaciones de la pieza.
        """
        self.x = x
        self.y = y
        self.shape = shape
        self.is_joker = shape == config.SHAPE_JOKER
        
        # Asignación de color según el índice de la forma en la lista global
        if self.is_joker:
            self.color = (255, 255, 255) # Blanco para el Joker
        else:
            self.color = config.get_s(config.SHAPES.index(shape))
        self.rotation = 0

    def update_color(self):
        """Actualiza el color de la pieza si el tema global cambia durante el juego."""
        if not self.is_joker:
            self.color = config.get_s(config.SHAPES.index(self.shape))

class Particle:
    """Sistema de partículas simple para efectos de explosión y limpieza de líneas."""

    def __init__(self, x, y, color, is_firework=False):
        """Crea una partícula con velocidad y dirección aleatoria.
        
        Args:
            x, y (float): Coordenadas iniciales.
            color (tuple): Color RGB.
            is_firework (bool): Si es True, tiene mayor velocidad y gravedad (efecto explosivo).
        """
        self.x = x
        self.y = y
        self.color = color
        self.is_firework = is_firework

        if is_firework:
            # Explosión radial aleatoria
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 8)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed
            self.lifetime = random.randint(180, 255)
            self.gravity = 0.12
        else:
            # Dispersión simple
            self.vx = random.uniform(-2, 2)
            self.vy = random.uniform(-2, 2)
            self.lifetime = 255
            self.gravity = 0.08

        self.size = random.randint(2, 4)

    def update(self):
        """Actualiza posición y vida de la partícula."""
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity # Simulación de gravedad
        self.lifetime -= 5      # Desvanecimiento

    def draw(self, surface):
        """Dibuja la partícula con un resplandor luminoso."""
        if self.lifetime > 0:
            alpha = max(0, self.lifetime)
            # Superficie de superficie con transparencia (SRCALPHA)
            s = pygame.Surface((self.size * 6, self.size * 6), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (self.size * 3, self.size * 3), self.size)
            if self.is_firework:
                # Resplandor adicional para fuegos artificiales
                pygame.draw.circle(s, (*self.color, alpha // 3), (self.size * 3, self.size * 3), self.size * 2)
            surface.blit(s, (int(self.x - self.size * 3), int(self.y - self.size * 3)))

class Star:
    """Representa una estrella individual en el fondo de Galaga."""
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.x = random.randint(0, config.SCREEN_WIDTH)
        self.y = random.randint(0, config.SCREEN_HEIGHT)
        self.speed = random.uniform(1, 4)
        self.size = random.randint(1, 3)
        # Colores clásicos de Galaga: Cyan, Rojo, Amarillo, Blanco
        self.color = random.choice([(200, 200, 255), (255, 100, 100), (255, 255, 150), (255, 255, 255)])
        self.brightness = random.randint(100, 255)
        self.twinkle_speed = random.uniform(0.05, 0.2)

    def update(self):
        self.y += self.speed
        if self.y > config.SCREEN_HEIGHT:
            self.y = 0
            self.x = random.randint(0, config.SCREEN_WIDTH)
        
        # Efecto de parpadeo
        self.brightness += math.sin(pygame.time.get_ticks() * self.twinkle_speed) * 10
        self.brightness = max(100, min(255, self.brightness))

    def draw(self, surface):
        c = [int(v * (self.brightness / 255)) for v in self.color]
        pygame.draw.circle(surface, c, (int(self.x), int(self.y)), self.size)

class Starfield:
    """Gestiona una colección de estrellas para el efecto espacial Galaga."""
    def __init__(self, count=100):
        self.stars = [Star() for _ in range(count)]

    def draw(self, surface):
        for star in self.stars:
            star.update()
            star.draw(surface)

class MeshBackground:
    """Fondo animado de malla con perspectiva Cyberpunk."""

    def __init__(self):
        self.time = 0

    def draw(self, surface):
        """Dibuja líneas en movimiento que convergen en el horizonte."""
        self.time += 0.05
        accent_blue = config.active_theme["mesh"]
        
        # Líneas horizontales con perspectiva
        for i in range(0, 15):
            offset = (self.time * 20) % 60
            y = 250 + i * 40 + offset
            if y > config.SCREEN_HEIGHT: continue
            alpha = max(0, min(255, (y - 250) * 1.5))
            r, g, b = accent_blue
            color = (int(r * (alpha / 255)), int(g * (alpha / 255)), int(b * (alpha / 255)))
            pygame.draw.line(surface, color, (0, y), (config.SCREEN_WIDTH, y), 1)

        # Líneas verticales
        for i in range(-10, 20):
            start_x = config.SCREEN_WIDTH // 2
            start_y = 200
            end_x = i * 100 + (config.SCREEN_WIDTH // 2 - 500)
            end_y = config.SCREEN_HEIGHT
            end_x += math.sin(self.time * 0.5) * 20
            pygame.draw.line(surface, accent_blue, (start_x, start_y), (end_x, end_y), 1)
class Lightning:
    """Efecto visual de rayo/trueno generativo."""
    def __init__(self, x_start):
        self.points = []
        self.lifetime = 20 # Frames de duración del parpadeo
        self.alpha = 255
        
        # Generar puntos quebrados del rayo
        curr_x = x_start
        curr_y = 0
        self.points.append((curr_x, curr_y))
        
        while curr_y < config.SCREEN_HEIGHT:
            curr_y += random.randint(20, 50)
            curr_x += random.randint(-40, 40)
            self.points.append((curr_x, curr_y))

    def update(self):
        self.lifetime -= 1
        self.alpha = max(0, self.alpha - 15)

    def draw(self, surface):
        if self.lifetime > 0:
            # Color del rayo: blanco con núcleo cian
            color = (200, 255, 255)
            # Dibujar con un poco de grosor aleatorio para parpadeo
            width = random.randint(2, 6)
            if len(self.points) > 1:
                pygame.draw.lines(surface, color, False, self.points, width)
                # Resplandor exterior
                pygame.draw.lines(surface, (0, 150, 255, self.alpha // 2), False, self.points, width + 4)
