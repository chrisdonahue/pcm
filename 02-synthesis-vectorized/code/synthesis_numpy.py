"""Same 1-second 440 Hz sine, vectorized with NumPy.

Run with:  python synthesis_numpy.py
"""

import numpy as np
import soundfile as sf


f_s = 44100            # samples per second
T = 1.0                # duration in seconds
f = 440.0              # Hz, synthesis parameter
N = int(T * f_s)

n = np.arange(N)       # array of sample indices: 0, 1, ..., N-1
samples = np.sin(2 * np.pi * f * (n / f_s))

sf.write("sine-440.wav", samples, f_s, subtype="PCM_16")
print(f"Wrote sine-440.wav: {N} samples at f_s = {f_s} Hz")
