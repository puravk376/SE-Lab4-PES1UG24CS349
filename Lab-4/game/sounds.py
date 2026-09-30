"""Sound effects generated in code, so no audio files are needed.

If the machine has no audio device, every sound silently becomes a no-op
so the game still runs.
"""
import math
import random
from array import array

import pygame


class _Silent:
    def play(self):
        pass


def _make_sound(samples):
    """Convert a list of floats in [-1, 1] to a pygame Sound."""
    freq, size, channels = pygame.mixer.get_init()
    buf = array("h")
    for s in samples:
        v = int(max(-1.0, min(1.0, s)) * 32767 * 0.5)
        for _ in range(channels):
            buf.append(v)
    return pygame.mixer.Sound(buffer=buf.tobytes())


def _slice_samples(rate):
    # Quick "swish": noise with a fast decay plus a falling tone
    n = int(rate * 0.12)
    out = []
    for i in range(n):
        t = i / rate
        env = (1 - i / n) ** 2
        tone = math.sin(2 * math.pi * (1400 - 6000 * t) * t)
        out.append(env * (0.5 * tone + 0.5 * random.uniform(-1, 1)))
    return out


def _bomb_samples(rate):
    # Low rumbling explosion
    n = int(rate * 0.6)
    out = []
    for i in range(n):
        t = i / rate
        env = math.exp(-5 * t)
        rumble = math.sin(2 * math.pi * 60 * t)
        out.append(env * (0.6 * random.uniform(-1, 1) + 0.4 * rumble))
    return out


def _game_over_samples(rate):
    # Three descending notes
    out = []
    for f in (523, 392, 262):
        n = int(rate * 0.22)
        for i in range(n):
            t = i / rate
            env = 1 - i / n
            out.append(env * math.sin(2 * math.pi * f * t))
    return out


class SoundBank:
    def __init__(self):
        self.slice = self.bomb = self.game_over = _Silent()
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            rate = pygame.mixer.get_init()[0]
            self.slice = _make_sound(_slice_samples(rate))
            self.bomb = _make_sound(_bomb_samples(rate))
            self.game_over = _make_sound(_game_over_samples(rate))
        except Exception as e:  # no audio device, etc.
            print("Sound disabled:", e)
