"""Wavetable synthesis for Chapter 3."""

import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "pyquist")))
import pyquist as pq

ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")
os.makedirs(ASSETS, exist_ok=True)

f_s = 44100
T = 1.5
N = int(T * f_s)

amp = pq.helper.db_to_amplitude(-6)


def build_wavetable(coeffs, M=2048):
    """Build a single-cycle wavetable from Fourier coefficients.

    Args:
        coeffs: List of harmonic amplitudes [a_1, a_2, ..., a_K].
        M: Number of samples in the table.

    Returns:
        NumPy array of shape (M,).
    """
    m = np.arange(M)
    table = np.zeros(M)
    for k in range(1, len(coeffs) + 1):
        table += coeffs[k - 1] * np.sin(2 * np.pi * k * m / M)
    return table


def wavetable_synth(table, f0, f_s, N):
    """Synthesize audio by reading from a wavetable.

    Args:
        table: Single-cycle wavetable, shape (M,).
        f0: Desired fundamental frequency in Hz.
        f_s: Sample rate in Hz.
        N: Number of output samples.

    Returns:
        NumPy array of shape (N,).
    """
    M = len(table)
    phase_inc = f0 * M / f_s
    indices = np.arange(N) * phase_inc
    indices_int = indices.astype(int) % M
    return table[indices_int]


# Build a sawtooth wavetable and synthesize
K = 32
saw_coeffs = [2 * ((-1) ** (k + 1)) / (np.pi * k) for k in range(1, K + 1)]
table = build_wavetable(saw_coeffs)

x = wavetable_synth(table, 220, f_s, N)
x *= amp / np.max(np.abs(x))
pq.Audio(x, sample_rate=f_s).write(os.path.join(ASSETS, "audio-wavetable-saw.wav"))

# Timing comparison: additive vs wavetable
n_arr = np.arange(N)
t_arr = n_arr / f_s

t0 = time.perf_counter()
for _ in range(10):
    x_add = np.zeros(N)
    for k in range(1, K + 1):
        x_add += saw_coeffs[k - 1] * np.sin(2 * np.pi * k * 220 * t_arr)
t_additive = (time.perf_counter() - t0) / 10

t0 = time.perf_counter()
for _ in range(10):
    x_wt = wavetable_synth(table, 220, f_s, N)
t_wavetable = (time.perf_counter() - t0) / 10

print(f"Additive ({K} harmonics): {t_additive:.4f}s")
print(f"Wavetable:                {t_wavetable:.4f}s")
print(f"Speedup:                  {t_additive / t_wavetable:.1f}x")

print("wavetable examples done.")
