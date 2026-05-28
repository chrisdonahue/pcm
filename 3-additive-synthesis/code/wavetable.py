"""Wavetable synthesis for Chapter 3."""

from pathlib import Path
import time

import numpy as np
import pyquist as pq

ASSETS = Path(__file__).resolve().parent.parent / "assets"
ASSETS.mkdir(exist_ok=True)

f_s = 44100
T = 1.5
N = int(T * f_s)

amp = pq.helper.db_to_amplitude(-6)


def build_wavetable(a: list[float], M: int = 2048) -> np.ndarray:
    """Build a single-cycle wavetable from Fourier coefficients.

    Args:
        a: Harmonic amplitudes [a_1, a_2, ..., a_K].
        M: Number of samples in the table.

    Returns:
        NumPy array of shape (M,).
    """
    K = len(a)
    a = np.array(a)
    k = 1 + np.arange(K)
    m = np.arange(M)
    # Broadcasting: (M, 1) * (K,) -> (M, K)
    table = (a * np.sin(2 * np.pi * k * m[:, np.newaxis] / M)).sum(axis=1)
    return table


def wavetable_naive(
    table: np.ndarray,
    f_0: float,
    f_s: int,
    N: int,
) -> pq.Audio:
    """Synthesize audio from a wavetable using nearest-neighbor lookup.

    Args:
        table: Single-cycle wavetable, shape (M,).
        f_0: Desired fundamental frequency in Hz.
        f_s: Sample rate in Hz.
        N: Number of output samples.

    Returns:
        A pq.Audio object.
    """
    M = len(table)
    phase_inc = f_0 * M / f_s
    phase = np.arange(N) * phase_inc
    indices = phase.astype(int) % M
    return pq.Audio(table[indices], sample_rate=f_s)


def wavetable_interp(
    table: np.ndarray,
    f_0: float,
    f_s: int,
    N: int,
) -> pq.Audio:
    """Synthesize audio from a wavetable using linear interpolation.

    Args:
        table: Single-cycle wavetable, shape (M,).
        f_0: Desired fundamental frequency in Hz.
        f_s: Sample rate in Hz.
        N: Number of output samples.

    Returns:
        A pq.Audio object.
    """
    M = len(table)
    phase_inc = f_0 * M / f_s
    phase = np.arange(N) * phase_inc
    m = phase.astype(int)
    alpha = phase - m
    x = (1 - alpha) * table[m % M] + alpha * table[(m + 1) % M]
    return pq.Audio(x, sample_rate=f_s)


# Build a sawtooth wavetable and synthesize
K = 32
saw_a = [2 * ((-1) ** (k + 1)) / (np.pi * k) for k in range(1, K + 1)]
table = build_wavetable(saw_a)

# Naive (nearest-neighbor) output
audio_naive = wavetable_naive(table, 220, f_s, N)
samples_naive = audio_naive.samples[:, 0]
samples_naive *= amp / np.max(np.abs(samples_naive))
pq.Audio(samples_naive, sample_rate=f_s).write(str(ASSETS / "audio-wavetable-saw.wav"))

# Interpolated output
audio_interp = wavetable_interp(table, 220, f_s, N)
samples_interp = audio_interp.samples[:, 0]
samples_interp *= amp / np.max(np.abs(samples_interp))
pq.Audio(samples_interp, sample_rate=f_s).write(
    str(ASSETS / "audio-wavetable-saw-interp.wav")
)

# Timing comparison: additive vs wavetable
n_arr = np.arange(N)
t_arr = n_arr / f_s

t0 = time.perf_counter()
for _ in range(10):
    k = np.arange(1, K + 1)
    x_add = (np.array(saw_a) * np.sin(2 * np.pi * k * 220 * t_arr[:, np.newaxis])).sum(
        axis=1
    )
t_additive = (time.perf_counter() - t0) / 10

t0 = time.perf_counter()
for _ in range(10):
    _ = wavetable_interp(table, 220, f_s, N)
t_wavetable = (time.perf_counter() - t0) / 10

print(f"Additive ({K} harmonics): {t_additive:.4f}s")
print(f"Wavetable (interp):       {t_wavetable:.4f}s")
print(f"Speedup:                  {t_additive / t_wavetable:.1f}x")

print("wavetable examples done.")
