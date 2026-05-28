"""Basic sinusoid synthesis examples for Chapter 3."""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "pyquist")))
import pyquist as pq

ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")
os.makedirs(ASSETS, exist_ok=True)

f_s = 44100
T = 1.0
N = int(T * f_s)
n = np.arange(N)
t = n / f_s

amp = pq.helper.db_to_amplitude(-6)

# --- Frequency examples: 220, 330, 440 Hz ---
for f in [220, 330, 440]:
    samples = amp * np.sin(2 * np.pi * f * t)
    audio = pq.Audio(samples, sample_rate=f_s)
    audio.write(os.path.join(ASSETS, f"audio-sine-{f}.wav"))

# --- Amplitude examples: 0.5, 0.05, 0.005 (unnormalized) ---
for a in [0.5, 0.05, 0.005]:
    samples = a * np.sin(2 * np.pi * 220 * t)
    audio = pq.Audio(samples, sample_rate=f_s)
    label = str(a).replace(".", "p")
    audio.write(os.path.join(ASSETS, f"audio-sine-amp-{label}.wav"))

# --- Phase examples: 0, pi/2, pi ---
for i, phi in enumerate([0.0, np.pi / 2, np.pi]):
    samples = amp * np.sin(2 * np.pi * 220 * t + phi)
    audio = pq.Audio(samples, sample_rate=f_s)
    audio.write(os.path.join(ASSETS, f"audio-sine-phase-{i}.wav"))

print("sinusoid examples done.")
