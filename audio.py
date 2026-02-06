"""
Motor de Audio de Neon Tetris PRO - Edición Galaga.
Sintetizador Chiptune Multicananal Procedural con SFX y BPM Dinámico.
"""

import pygame
import numpy as np
import time
import threading
import math
import random

class ChiptuneAudio:
    """Motor de audio avanzado que genera música y efectos mediante síntesis matemática."""

    def __init__(self):
        # 44.1kHz, 16-bit, Stereo (2 canales para panning)
        pygame.mixer.init(frequency=44100, size=-16, channels=2)
        self.sample_rate = 44100
        
        # --- PARTITURA MEJORADA (Nota, Duración) ---
        self.melody = [
            ("E5", 4), ("B4", 8), ("C5", 8), ("D5", 4), ("C5", 8), ("B4", 8),
            ("A4", 4), ("A4", 8), ("C5", 8), ("E5", 4), ("D5", 8), ("C5", 8),
            ("B4", 4), ("B4", 8), ("C5", 8), ("D5", 4), ("E5", 4),
            ("C5", 4), ("A4", 4), ("A4", 4), (None, 4),
            ("D5", 3), ("F5", 8), ("A5", 4), ("G5", 8), ("F5", 8),
            ("E5", 3), ("C5", 8), ("E5", 4), ("D5", 8), ("C5", 8),
            ("B4", 4), ("B4", 8), ("C5", 8), ("D5", 4), ("E5", 4),
            ("C5", 4), ("A4", 4), ("A4", 4)
        ]

        self.bass_line = [
            ("E3", 4), ("E3", 4), ("B2", 4), ("B2", 4),
            ("A2", 4), ("A2", 4), ("E2", 4), ("E2", 4),
            ("G2", 4), ("G2", 4), ("C3", 4), ("C3", 4),
            ("E2", 4), ("E2", 4), ("A2", 4), ("A2", 4)
        ]
        
        self.frequencies = {
            "E2": 82.41, "G2": 98.00, "A2": 110.00, "B2": 123.47,
            "C3": 130.81, "E3": 164.81,
            "A4": 440.00, "B4": 493.88, "C5": 523.25, "D5": 587.33, "E5": 659.25, "F5": 698.46, "G5": 783.99, "A5": 880.00
        }
        
        self.base_bpm = 150
        self.current_bpm = 150
        self.volume = 0.2
        self.running = False
        self.paused = False
        self.thread = None

    def set_volume(self, vol):
        self.volume = max(0.0, min(1.0, vol))

    def set_level(self, level):
        """Aumenta el BPM según el nivel para crear tensión."""
        self.current_bpm = self.base_bpm + (level - 1) * 8

    def generate_wave(self, freq, duration, wave_type="square", volume_mult=1.0, pan=0.0):
        """Genera datos de audio para diferentes tipos de ondas con paneo."""
        if not freq: return None
        
        n_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        
        if wave_type == "square":
            wave = np.sign(np.sin(2 * np.pi * freq * t))
        elif wave_type == "triangle":
            wave = 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1
        elif wave_type == "noise":
            wave = np.random.uniform(-1, 1, n_samples)
        else: # Sine
            wave = np.sin(2 * np.pi * freq * t)

        # Aplicar Envolvente (Attack-Decay) para evitar clicks
        envelope = np.ones(n_samples)
        fade_len = int(self.sample_rate * 0.01)
        if n_samples > fade_len * 2:
            envelope[:fade_len] = np.linspace(0, 1, fade_len)
            envelope[-fade_len:] = np.linspace(1, 0, fade_len)
        
        # Convertir a Stereo y aplicar Paneo
        # pan: -1 (izq), 0 (centro), 1 (der)
        left_mult = 1.0 - max(0, pan)
        right_mult = 1.0 + min(0, pan)
        
        audio = (wave * envelope * self.volume * volume_mult * 32767).astype(np.int16)
        stereo_audio = np.zeros((n_samples, 2), dtype=np.int16)
        stereo_audio[:, 0] = (audio * left_mult).astype(np.int16)
        stereo_audio[:, 1] = (audio * right_mult).astype(np.int16)
        
        return pygame.mixer.Sound(stereo_audio)

    # --- GENERADORES DE SFX ---
    def play_sfx(self, name, pan=0.0):
        """Genera e reproduce efectos de sonido procedurales."""
        if self.volume <= 0: return

        if name == "move":
            # Blip corto descendente
            s = self.generate_wave(600, 0.05, "square", 0.5, pan)
            if s: s.play()
        elif name == "rotate":
            # Chirp ascendente (Láser)
            duration = 0.1
            samples = int(self.sample_rate * duration)
            t = np.linspace(0, duration, samples)
            freqs = np.linspace(400, 800, samples) # Barrido de frecuencia
            wave = np.sin(2 * np.pi * np.cumsum(freqs) / self.sample_rate)
            audio = (wave * self.volume * 0.4 * 32767).astype(np.int16)
            stereo = np.column_stack((audio, audio))
            pygame.mixer.Sound(stereo).play()
        elif name == "drop":
            # Ruido percusivo
            s = self.generate_wave(100, 0.15, "noise", 0.6, pan)
            if s: s.play()
        elif name == "clear":
            # Arpegio triunfal
            notes = [523, 659, 783, 1046] # C-E-G-C (C Major)
            for i, f in enumerate(notes):
                threading.Timer(i * 0.05, lambda freq=f: self.generate_wave(freq, 0.1, "square", 0.7).play()).start()

    def play_loop(self):
        melody_step = 0
        bass_step = 0
        
        while self.running:
            if self.paused:
                time.sleep(0.1)
                continue

            # Duración de una corchea (8th note)
            step_duration = 60 / (self.current_bpm * 2) 

            # Canal 1: Melodía
            note, length = self.melody[melody_step]
            # Solo toca en los tiempos que le corresponden
            if (melody_step % int(length / 2)) == 0:
                if note:
                    f = self.frequencies.get(note)
                    s = self.generate_wave(f, step_duration * 0.8, "square", 0.8, 0.2)
                    if s: s.play()
            
            # Canal 2: Bajo (Onda triangular más suave)
            if melody_step % 4 == 0: # Cada negra
                bnote, blen = self.bass_line[bass_step]
                bf = self.frequencies.get(bnote)
                s = self.generate_wave(bf, step_duration * 1.8, "triangle", 1.2, -0.4)
                if s: s.play()
                bass_step = (bass_step + 1) % len(self.bass_line)

            melody_step = (melody_step + 1) % len(self.melody)
            time.sleep(step_duration)

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.play_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False

audio_engine = ChiptuneAudio()
