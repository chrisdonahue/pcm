"""Synthesize a 1-second 440 Hz sine tone with a plain Python for-loop.

Run with:  python synthesis.py
"""

import math

import soundfile as sf


f_s = 44100            # samples per second
T = 1.0                # duration in seconds
f = 440.0              # Hz, synthesis parameter
N = int(T * f_s)

samples = [0.0] * N    # sample "buffer" (memory)
for n in range(N):
    samples[n] = math.sin(2.0 * math.pi * f * (n / f_s))

sf.write("sine-440.wav", samples, f_s, subtype="PCM_16")
print(f"Wrote sine-440.wav: {N} samples at f_s = {f_s} Hz")
