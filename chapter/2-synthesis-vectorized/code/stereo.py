"""Stereo synthesis via NumPy broadcasting, plus mono downmix.

Generates a 1-second stereo signal with a 220 Hz tone on the left channel
and a 330 Hz tone on the right, then writes both the stereo file and the
mono (mean-of-channels) downmix to disk.

Run with:  python stereo.py
"""

import numpy as np
import soundfile as sf


f_s = 44100
T = 1.0
N = int(T * f_s)

t = np.arange(N) / f_s                     # shape (N,)
freqs = np.array([220.0, 330.0])           # left, right

# t[:, np.newaxis] has shape (N, 1)
# freqs            has shape (2,)
# Their product broadcasts to shape (N, 2)
stereo = 0.5 * np.sin(2 * np.pi * freqs * t[:, np.newaxis])

# Mono downmix: average across the channel axis.
mono = stereo.mean(axis=1)

sf.write("stereo-220-330.wav", stereo, f_s, subtype="PCM_16")
sf.write("mono-220-330-mix.wav", mono, f_s, subtype="PCM_16")
print(f"Wrote stereo-220-330.wav (shape {stereo.shape}) and mono-220-330-mix.wav (shape {mono.shape}).")
