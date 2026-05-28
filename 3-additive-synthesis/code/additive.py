"""Additive synthesis examples for Chapter 3."""

from pathlib import Path

import numpy as np
import pyquist as pq

ASSETS = Path(__file__).resolve().parent.parent / "assets"
ASSETS.mkdir(exist_ok=True)

f_s = 44100
T = 1.5
N = int(T * f_s)
n = np.arange(N)
t = n / f_s

amp = pq.helper.db_to_amplitude(-6)


def additive_synth(
    f_0: float,
    a: list[float],
    phi: list[float] | None = None,
) -> np.ndarray:
    """Synthesize a tone via additive synthesis.

    Args:
        f_0: Fundamental frequency in Hz.
        a: Harmonic amplitudes [a_1, a_2, ..., a_K].
        phi: Initial phases [phi_1, ..., phi_K]. Defaults to all zeros.

    Returns:
        NumPy array of samples.
    """
    K = len(a)
    if phi is None:
        phi = [0.0] * K
    a_arr = np.array(a)  # shape (K,)
    phi_arr = np.array(phi)  # shape (K,)
    k = np.arange(1, K + 1)  # shape (K,)
    # Broadcasting: (N, 1) * (K,) -> (N, K), then sum over harmonics
    harmonics = a_arr * np.sin(2 * np.pi * k * f_0 * t[:, np.newaxis] + phi_arr)
    return harmonics.sum(axis=1)


# --- Default: K=4, f0=220, geometric amplitudes ---
default_a = [1, 1 / 2, 1 / 4, 1 / 8]
x = additive_synth(220, default_a)
x *= amp / np.max(np.abs(x))
pq.Audio(x, sample_rate=f_s).write(str(ASSETS / "audio-additive-default.wav"))

# --- Varying f0 (random between 220 and 440 Hz) ---
rng_f0 = np.random.default_rng(99)
for i in range(4):
    f_0_rand = rng_f0.uniform(220, 440)
    x = additive_synth(f_0_rand, default_a)
    x *= amp / np.max(np.abs(x))
    pq.Audio(x, sample_rate=f_s).write(str(ASSETS / f"audio-additive-f0-{i}.wav"))

# --- Varying K: 1, 2, 4, 8 ---
for K in [1, 2, 4, 8]:
    a_k = [1.0 / (2 ** (k - 1)) for k in range(1, K + 1)]
    x = additive_synth(220, a_k)
    x *= amp / np.max(np.abs(x))
    pq.Audio(x, sample_rate=f_s).write(str(ASSETS / f"audio-additive-K{K}.wav"))

# --- Varying amplitudes (random) ---
rng = np.random.default_rng(42)
for i in range(4):
    rand_a = rng.uniform(0, 1, size=4).tolist()
    x = additive_synth(220, rand_a)
    x *= amp / np.max(np.abs(x))
    pq.Audio(x, sample_rate=f_s).write(str(ASSETS / f"audio-additive-timbre-{i}.wav"))

# --- Varying phase (random) ---
for i in range(4):
    rand_phi = rng.uniform(0, 2 * np.pi, size=4).tolist()
    x = additive_synth(220, default_a, rand_phi)
    x *= amp / np.max(np.abs(x))
    pq.Audio(x, sample_rate=f_s).write(str(ASSETS / f"audio-additive-phase-{i}.wav"))

print("additive examples done.")
