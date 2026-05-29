"""Synthesize a 1-second 440 Hz sine tone and save it as a WAV file.

Run with:  python synthesis.py
"""

import math

import soundfile as sf


f_s = 44100         # samples per second
duration = 1.0      # seconds
f = 440.0           # Hz
N = int(duration * f_s)

samples = [0.0] * N
for i in range(N):
    t = i / f_s
    samples[i] = math.sin(2.0 * math.pi * f * t)

sf.write("sine-440.wav", samples, f_s, subtype="PCM_16")
print(f"Wrote sine-440.wav: {N} samples at f_s = {f_s} Hz")
