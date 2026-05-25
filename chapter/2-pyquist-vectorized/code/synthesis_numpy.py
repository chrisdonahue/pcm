"""Same 1-second 440 Hz sine, vectorized with NumPy.

Run with:  python synthesis_numpy.py
"""

import numpy as np
import soundfile as sf


f_s = 44100
duration = 1.0
f = 440.0
N = int(duration * f_s)

n = np.arange(N)                          # array of sample indices: 0, 1, ..., N-1
t = n / f_s                               # corresponding times in seconds
samples = np.sin(2 * np.pi * f * t)       # one sine value per timestamp, all at once

sf.write("sine-440.wav", samples, f_s, subtype="PCM_16")
print(f"Wrote sine-440.wav: {N} samples at f_s = {f_s} Hz")
