"""Basic waveform shapes via additive synthesis for Chapter 3."""

from pathlib import Path

import numpy as np
import pyquist as pq

ASSETS = Path(__file__).resolve().parent.parent / "assets"
ASSETS.mkdir(exist_ok=True)

f_s = 44100
T = 1.5
N = int(T * f_s)
n = np.arange(N)
t = n / f_s
K = 32

amp = pq.helper.db_to_amplitude(-6)


def additive_synth(f_0: float, a: np.ndarray) -> np.ndarray:
    """Synthesize via additive synthesis using broadcasting."""
    k = np.arange(1, len(a) + 1)
    harmonics = a * np.sin(2 * np.pi * k * f_0 * t[:, np.newaxis])
    return harmonics.sum(axis=1)


# Sawtooth: a_k = 2(-1)^{k+1} / (pi * k)
k_arr = np.arange(1, K + 1)
saw_a = 2 * ((-1) ** (k_arr + 1)) / (np.pi * k_arr)
x = additive_synth(220, saw_a)
x *= amp / np.max(np.abs(x))
pq.Audio(x, sample_rate=f_s).write(str(ASSETS / "audio-sawtooth.wav"))

# Square: a_k = 4/(pi*k) for odd k, 0 for even
sq_a = np.where(k_arr % 2 == 1, 4 / (np.pi * k_arr), 0.0)
x = additive_synth(220, sq_a)
x *= amp / np.max(np.abs(x))
pq.Audio(x, sample_rate=f_s).write(str(ASSETS / "audio-square.wav"))

# Triangle: a_k = 8 (-1)^{(k-1)/2} / (pi^2 k^2) for odd k, 0 for even
tri_a = np.where(
    k_arr % 2 == 1,
    8 * ((-1) ** ((k_arr - 1) // 2)) / (np.pi ** 2 * k_arr ** 2),
    0.0,
)
x = additive_synth(220, tri_a)
x *= amp / np.max(np.abs(x))
pq.Audio(x, sample_rate=f_s).write(str(ASSETS / "audio-triangle.wav"))

print("waveform examples done.")
