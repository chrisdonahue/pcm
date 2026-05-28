"""Basic waveform shapes via additive synthesis for Chapter 3."""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "pyquist")))
import pyquist as pq

ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")
os.makedirs(ASSETS, exist_ok=True)

f_s = 44100
T = 1.5
N = int(T * f_s)
n = np.arange(N)
t = n / f_s
K = 32

amp = pq.helper.db_to_amplitude(-6)


def additive_synth(f0, coeffs):
    x = np.zeros(N)
    for k in range(1, K + 1):
        x += coeffs[k - 1] * np.sin(2 * np.pi * k * f0 * t)
    return x


# Sawtooth: a_k = 2(-1)^{k+1} / (pi * k)
saw_coeffs = np.array([2 * ((-1) ** (k + 1)) / (np.pi * k) for k in range(1, K + 1)])
x = additive_synth(220, saw_coeffs)
x *= amp / np.max(np.abs(x))
pq.Audio(x, sample_rate=f_s).write(os.path.join(ASSETS, "audio-sawtooth.wav"))

# Square: a_k = 4/(pi*k) for odd k, 0 for even
sq_coeffs = np.array([4 / (np.pi * k) if k % 2 == 1 else 0.0 for k in range(1, K + 1)])
x = additive_synth(220, sq_coeffs)
x *= amp / np.max(np.abs(x))
pq.Audio(x, sample_rate=f_s).write(os.path.join(ASSETS, "audio-square.wav"))

# Triangle: a_k = 8 (-1)^{(k-1)/2} / (pi^2 k^2) for odd k, 0 for even
tri_coeffs = np.array([
    8 * ((-1) ** ((k - 1) // 2)) / (np.pi ** 2 * k ** 2) if k % 2 == 1 else 0.0
    for k in range(1, K + 1)
])
x = additive_synth(220, tri_coeffs)
x *= amp / np.max(np.abs(x))
pq.Audio(x, sample_rate=f_s).write(os.path.join(ASSETS, "audio-triangle.wav"))

print("waveform examples done.")
