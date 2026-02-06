"""
Motor de Audio de Neon Tetris PRO - Edición Galaga.
Sintetizador Chiptune Multicanal Procedural con SFX, BPM Dinámico y Caché de Sonido.
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
        # 44.1kHz, 16-bit, Stereo
        pygame.mixer.init(frequency=44100, size=-16, channels=2)
        self.sample_rate = 44100
        
        # --- PARTITURA (Nota, Ticks) 1 Tick = 1/16 note ---
        # Korobeiniki Melody
        self.melody_data = [
            ("E5", 4), ("B4", 2), ("C5", 2), ("D5", 4), ("C5", 2), ("B4", 2),
            ("A4", 4), ("A4", 2), ("C5", 2), ("E5", 4), ("D5", 2), ("C5", 2),
            ("B4", 6), ("C5", 2), ("D5", 4), ("E5", 4),
            ("C5", 4), ("A4", 4), ("A4", 4), (None, 4),
            
            ("D5", 6), ("F5", 2), ("A5", 4), ("G5", 2), ("F5", 2),
            ("E5", 6), ("C5", 2), ("E5", 4), ("D5", 2), ("C5", 2),
            ("B4", 4), ("B4", 2), ("C5", 2), ("D5", 4), ("E5", 4),
            ("C5", 4), ("A4", 4), ("A4", 4), (None, 4)
        ]

        self.bass_data = [
            ("E2", 4), ("E3", 4), ("B2", 4), ("B3", 4),
            ("A2", 4), ("A3", 4), ("E2", 4), ("E3", 4),
            ("G2", 4), ("G3", 4), ("C3", 4), ("C4", 4),
            ("B2", 4), ("B3", 4), ("A2", 4), ("E3", 4)
        ]
        
        self.frequencies = {
            "E2": 82.41, "G2": 98.00, "A2": 110.00, "B2": 123.47,
            "C3": 130.81, "E3": 164.81, "G3": 196.00, "B3": 246.94, "C4": 261.63,
            "A4": 440.00, "B4": 493.88, "C5": 523.25, "D5": 587.33, "E5": 659.25, "F5": 698.46, "G5": 783.99, "A5": 880.00
        }
        
        self.base_bpm = 150
        self.current_bpm = 150
        self.volume = 0.2
        self.running = False
        self.paused = False
        self.thread = None
        
        # Caché de sonidos para evitar regeneración constante
        self.sound_cache = {}

    def set_volume(self, vol):
        self.volume = max(0.0, min(1.0, vol))
        # Actualizamos volumen de sonidos en caché si es posible
        # (Aunque es mejor aplicarlo al momento de generar si el volumen cambia poco)

    def set_level(self, level):
        """Aumenta el BPM según el nivel."""
        self.current_bpm = self.base_bpm + (level - 1) * 5

    def get_wave(self, freq, duration, wave_type="pulse", volume_mult=1.0, pan=0.0):
        """Genera o recupera un sonido de la caché."""
        if not freq: return None
        
        # Redondear duración para mejorar hit-rate de caché
        duration = round(duration, 3)
        cache_key = (freq, duration, wave_type, pan)
        
        if cache_key in self.sound_cache:
            s = self.sound_cache[cache_key]
            s.set_volume(self.volume * volume_mult)
            return s
            
        n_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        
        if wave_type == "pulse":
            # Onda de pulso (Duty cycle 25%) para sonido más NES/Arcade
            wave = np.where(np.sin(2 * np.pi * freq * t) > 0.5, 1.0, -1.0)
        elif wave_type == "triangle":
            wave = 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1
        elif wave_type == "noise":
            wave = np.random.uniform(-1, 1, n_samples)
        else: # Square 50%
            wave = np.sign(np.sin(2 * np.pi * freq * t))

        # Envolvente suave (ASR)
        envelope = np.ones(n_samples)
        attack = int(self.sample_rate * 0.005)
        decay = int(self.sample_rate * 0.02)
        if n_samples > attack + decay:
            envelope[:attack] = np.linspace(0, 1, attack)
            envelope[-decay:] = np.linspace(1, 0, decay)
        
        audio = (wave * envelope * 32767).astype(np.int16)
        
        # Paneo estéreo
        left_mult = 1.0 - max(0, pan)
        right_mult = 1.0 + min(0, pan)
        stereo_audio = np.zeros((n_samples, 2), dtype=np.int16)
        stereo_audio[:, 0] = (audio * left_mult).astype(np.int16)
        stereo_audio[:, 1] = (audio * right_mult).astype(np.int16)
        
        sound = pygame.mixer.Sound(stereo_audio)
        sound.set_volume(self.volume * volume_mult)
        
        # Limitar tamaño de caché
        if len(self.sound_cache) > 200: self.sound_cache.clear()
        self.sound_cache[cache_key] = sound
        return sound

    def play_sfx(self, name, pan=0.0):
        if self.volume <= 0: return
        
        if name == "move":
            s = self.get_wave(800, 0.04, "pulse", 0.4, pan)
            if s: s.play()
        elif name == "rotate":
            s = self.get_wave(1200, 0.06, "pulse", 0.5, pan)
            if s: s.play()
        elif name == "drop":
            s = self.get_wave(100, 0.1, "noise", 0.5, pan)
            if s: s.play()
        elif name == "clear":
            # Arpegio rápido
            for i, f in enumerate([523, 659, 783, 1046]):
                threading.Timer(i * 0.04, lambda freq=f: self.get_wave(freq, 0.1, "pulse", 0.6).play()).start()

    def play_loop(self):
        melody_idx = 0
        bass_idx = 0
        
        melody_ticks = 0
        bass_ticks = 0
        
        while self.running:
            if self.paused:
                time.sleep(0.1)
                continue

            # 1 tick = 1/16 note
            tick_duration = 60 / (self.current_bpm * 4) 

            # --- PROCESS MELODY ---
            if melody_ticks <= 0:
                note, ticks = self.melody_data[melody_idx]
                melody_ticks = ticks
                if note:
                    f = self.frequencies.get(note)
                    s = self.get_wave(f, tick_duration * ticks * 0.8, "pulse", 0.7, 0.1)
                    if s: s.play()
                melody_idx = (melody_idx + 1) % len(self.melody_data)

            # --- PROCESS BASS ---
            if bass_ticks <= 0:
                bnote, bticks = self.bass_data[bass_idx]
                bass_ticks = bticks
                if bnote:
                    bf = self.frequencies.get(bnote)
                    s = self.get_wave(bf, tick_duration * bticks * 0.9, "triangle", 0.9, -0.3)
                    if s: s.play()
                bass_idx = (bass_idx + 1) % len(self.bass_data)

            melody_ticks -= 1
            bass_ticks -= 1
            
            time.sleep(tick_duration)

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.play_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False

audio_engine = ChiptuneAudio()
