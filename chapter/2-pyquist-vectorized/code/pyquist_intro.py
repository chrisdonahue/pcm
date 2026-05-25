"""Pyquist Audio: construction, mixing, and time-based slicing.

Builds a C major triad (C4, E4, G4) by summing three sine ``Audio`` objects,
then writes both the full chord and the middle 0.5 s segment to disk.

Run with:  python pyquist_intro.py
"""

import numpy as np
import pyquist as pq


f_s = 44100
duration = 2.0
N = int(duration * f_s)
n = np.arange(N)
t = n / f_s

# Build three sine Audio objects (each ≈ −10 dBFS so the sum stays in [-1, 1])
sine_c = pq.Audio(0.3 * np.sin(2 * np.pi * 261.63 * t), sample_rate=f_s)
sine_e = pq.Audio(0.3 * np.sin(2 * np.pi * 329.63 * t), sample_rate=f_s)
sine_g = pq.Audio(0.3 * np.sin(2 * np.pi * 392.00 * t), sample_rate=f_s)

# Mix by adding Audio objects together
chord = sine_c + sine_e + sine_g

# Pull out the middle 0.5 s as a fresh Audio (carrying the same sample rate)
middle = chord.segment(offset=0.25, duration=0.5)

chord.write("c-major-chord.wav")
middle.write("c-major-chord-segment.wav")

print(f"Wrote c-major-chord.wav: {chord}")
print(f"Wrote c-major-chord-segment.wav: {middle}")
