"""Stereo synthesis via NumPy broadcasting, plus mono downmix.

Generates a 1-second stereo signal with a 220 Hz tone on the left channel
and a 330 Hz tone on the right, then writes both the stereo file and the
mono (mean-of-channels) downmix to disk.

Run with:  python stereo.py
"""

import numpy as np
import soundfile as sf


f_s = 44100
duration = 1.0
N = int(duration * f_s)

n = np.arange(N)
t = n / f_s                                # shape (N,)
freqs = np.array([220.0, 330.0])           # left, right

# t[:, np.newaxis] is (N, 1); freqs is (2,); their product broadcasts to (N, 2).
stereo = 0.5 * np.sin(2 * np.pi * freqs * t[:, np.newaxis])

# Mono downmix: average across the channel axis.
mono = stereo.mean(axis=1)

sf.write("stereo-220-330.wav", stereo, f_s, subtype="PCM_16")
sf.write("mono-220-330-mix.wav", mono, f_s, subtype="PCM_16")
print(f"Wrote stereo-220-330.wav (shape {stereo.shape}) and mono-220-330-mix.wav (shape {mono.shape}).")
