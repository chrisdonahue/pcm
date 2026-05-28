"""Basic sinusoid synthesis examples for Chapter 3."""

from pathlib import Path

import numpy as np
import pyquist as pq

ASSETS = Path(__file__).resolve().parent.parent / "assets"
ASSETS.mkdir(exist_ok=True)

f_s = 44100
T = 1.0
N = int(T * f_s)
n = np.arange(N)
t = n / f_s

amp = pq.helper.db_to_amplitude(-6)

# --- Frequency examples: 220, 330, 440 Hz ---
for f in [220, 330, 440]:
    samples = amp * np.sin(2 * np.pi * f * t)
    pq.Audio(samples, sample_rate=f_s).write(str(ASSETS / f"audio-sine-{f}.wav"))

# --- Amplitude examples: 0.5, 0.05, 0.005 (unnormalized) ---
for a in [0.5, 0.05, 0.005]:
    samples = a * np.sin(2 * np.pi * 220 * t)
    label = str(a).replace(".", "p")
    pq.Audio(samples, sample_rate=f_s).write(str(ASSETS / f"audio-sine-amp-{label}.wav"))

# --- Phase examples: 0, pi/2, pi ---
for i, phi in enumerate([0.0, np.pi / 2, np.pi]):
    samples = amp * np.sin(2 * np.pi * 220 * t + phi)
    pq.Audio(samples, sample_rate=f_s).write(str(ASSETS / f"audio-sine-phase-{i}.wav"))

print("sinusoid examples done.")
