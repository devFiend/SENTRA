"""Alert dispatcher, tier routing, and procedural audio feedback."""
import platform
import time
from typing import Optional
import numpy as np
import pygame

from sentra.events.schemas import AlertTier, EventRecord


class AlertManager:
    """
    Routes events to local notifications, synthesized sound chimes, and UI alerts.
    Enforces mute toggles and sound cooldowns.
    """

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.muted = False
        self._initialized = False
        self._last_sound_time = 0.0

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=sample_rate, size=-16, channels=2, buffer=512)
            self._initialized = True
        except Exception:
            self._initialized = False

    def toggle_mute(self) -> bool:
        self.muted = not self.muted
        return self.muted

    def dispatch(self, event: EventRecord) -> None:
        """Route event based on severity tier."""
        now = time.time()

        if event.tier == AlertTier.URGENT_REVIEW:
            self.play_urgent_alarm()
        elif event.tier == AlertTier.REVIEW:
            self.play_review_chime()

    def play_review_chime(self) -> None:
        """Synthesize a dual harmonic notification chime (880 Hz / 1760 Hz)."""
        if not self._initialized or self.muted:
            return
        now = time.time()
        if now - self._last_sound_time < 1.0:
            return
        self._last_sound_time = now

        try:
            dur = 0.35
            t = np.linspace(0.0, dur, int(self.sample_rate * dur), endpoint=False)
            env = np.exp(-t * 10.0)
            tone1 = np.sin(2.0 * np.pi * 880.0 * t)
            tone2 = np.sin(2.0 * np.pi * 1760.0 * t) * 0.4
            wave = ((tone1 + tone2) * env * 0.4 * 32767).astype(np.int16)
            stereo = np.column_stack((wave, wave))
            sound = pygame.sndarray.make_sound(stereo)
            sound.set_volume(0.8)
            sound.play()
        except Exception:
            pass

    def play_urgent_alarm(self) -> None:
        """Synthesize urgent alert pulses (two descending warning bursts)."""
        if not self._initialized or self.muted:
            return
        now = time.time()
        if now - self._last_sound_time < 1.2:
            return
        self._last_sound_time = now

        try:
            dur = 0.40
            t = np.linspace(0.0, dur, int(self.sample_rate * dur), endpoint=False)
            freq = np.linspace(900.0, 450.0, len(t))
            env = np.sin(np.pi * t / dur) ** 0.5
            wave = (np.sin(2.0 * np.pi * freq * t) * env * 0.55 * 32767).astype(np.int16)
            stereo = np.column_stack((wave, wave))
            sound = pygame.sndarray.make_sound(stereo)
            sound.set_volume(0.9)
            sound.play()
        except Exception:
            pass
