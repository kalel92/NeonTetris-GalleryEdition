"""
Motor de Audio de Neon Tetris.
Sintetiza la melodía de Korobeiniki en tiempo real usando ondas cuadradas
para lograr un estilo retro 'chiptune' de 64 bits.
"""

import pygame
import numpy as np
import time
import threading

class ChiptuneAudio:
    """Clase para la generación y reproducción de música chiptune."""

    def __init__(self):
        """Inicializa el mixer de pygame y define la melodía."""
        # Configuración del mixer: 44.1kHz, 16-bit por muestra, mono
        pygame.mixer.init(frequency=44100, size=-16, channels=1)
        self.sample_rate = 44100
        
        # Partitura simplificada de Korobeiniki (Nota, Duración)
        self.melody_notes = [
            ("E5", 4), ("B4", 8), ("C5", 8), ("D5", 4), ("C5", 8), ("B4", 8),
            ("A4", 4), ("A4", 8), ("C5", 8), ("E5", 4), ("D5", 8), ("C5", 8),
            ("B4", 4), ("B4", 8), ("C5", 8), ("D5", 4), ("E5", 4),
            ("C5", 4), ("A4", 4), ("A4", 4), (None, 4),
            ("D5", 3), ("F5", 8), ("A5", 4), ("G5", 8), ("F5", 8),
            ("E5", 3), ("C5", 8), ("E5", 4), ("D5", 8), ("C5", 8),
            ("B4", 4), ("B4", 8), ("C5", 8), ("D5", 4), ("E5", 4),
            ("C5", 4), ("A4", 4), ("A4", 4)
        ]
        
        # Mapeo de frecuencias para las notas musicales utilizadas
        self.frequencies = {
            "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23, "G4": 392.00, "A4": 440.00, "B4": 493.88,
            "C5": 523.25, "D5": 587.33, "E5": 659.25, "F5": 698.46, "G5": 783.99, "A5": 880.00, "B5": 987.77
        }
        
        self.bpm = 150 # Pulsos por minuto
        self.running = False
        self.thread = None
        self.volume = 0.1 # Volumen por defecto (redimensionado)

    def set_volume(self, vol):
        """Ajusta el volumen (0.0 a 1.0)."""
        self.volume = max(0.0, min(1.0, vol))

    def generate_square_wave(self, freq, duration):
        """Genera un sonido de onda cuadrada para una frecuencia dada.
        
        Args:
            freq (float): Frecuencia en Hz.
            duration (float): Duración en segundos.
            
        Returns:
            pygame.mixer.Sound: El objeto de sonido listo para ser reproducido.
        """
        n_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        # Una onda cuadrada es simplemente el signo de una onda senoidal
        wave = np.sign(np.sin(2 * np.pi * freq * t))
        # Convertimos a formato de 16 bits (rango -32768 a 32767)
        audio = (wave * self.volume * 32767).astype(np.int16)
        return pygame.mixer.Sound(audio)

    def play_melody(self):
        """Bucle de reproducción que recorre la partitura."""
        while self.running:
            for note, length in self.melody_notes:
                if not self.running: break
                # Calculamos duración según el tempo (BPM)
                duration = (60 / self.bpm) * (4 / length)
                if note:
                    freq = self.frequencies.get(note, 440)
                    sound = self.generate_square_wave(freq, duration * 0.9)
                    sound.play()
                time.sleep(duration) # Esperamos a que termine la nota

    def start(self):
        """Inicia la reproducción en un hilo separado por detrás."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.play_melody, daemon=True)
            self.thread.start()

    def stop(self):
        """Detiene el hilo de reproducción."""
        self.running = False

# Instancia global para ser usada en todo el juego
audio_engine = ChiptuneAudio()
