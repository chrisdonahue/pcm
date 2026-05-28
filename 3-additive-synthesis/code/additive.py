"""Additive synthesis examples for Chapter 3."""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "pyquist")))
import pyquist as pq

ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")
os.makedirs(ASSETS, exist_ok=True)

f_s = 44100
T = 1.5
N = int(T * f_s)
n = np.arange(N)
t = n / f_s

amp = pq.helper.db_to_amplitude(-6)


def additive_synth(f0, amplitudes, phases=None):
    """Synthesize a tone via additive synthesis.

    Args:
        f0: Fundamental frequency in Hz.
        amplitudes: List of harmonic amplitudes [a_1, a_2, ..., a_K].
        phases: List of initial phases [phi_1, ..., phi_K]. Defaults to all zeros.

    Returns:
        NumPy array of samples.
    """
    K = len(amplitudes)
    if phases is None:
        phases = [0.0] * K
    x = np.zeros(N)
    for k in range(1, K + 1):
        x += amplitudes[k - 1] * np.sin(2 * np.pi * k * f0 * t + phases[k - 1])
    return x


# --- Default: K=4, f0=220, geometric amplitudes ---
default_amps = [1, 1/2, 1/4, 1/8]
x = additive_synth(220, default_amps)
x *= amp / np.max(np.abs(x))
pq.Audio(x, sample_rate=f_s).write(os.path.join(ASSETS, "audio-additive-default.wav"))

# --- Varying f0 (random between 220 and 440 Hz) ---
rng_f0 = np.random.default_rng(99)
for i in range(4):
    f0_rand = rng_f0.uniform(220, 440)
    x = additive_synth(f0_rand, default_amps)
    x *= amp / np.max(np.abs(x))
    pq.Audio(x, sample_rate=f_s).write(os.path.join(ASSETS, f"audio-additive-f0-{i}.wav"))

# --- Varying K: 1, 2, 4, 8 ---
for K in [1, 2, 4, 8]:
    amps_k = [1.0 / (2 ** (k - 1)) for k in range(1, K + 1)]
    x = additive_synth(220, amps_k)
    x *= amp / np.max(np.abs(x))
    pq.Audio(x, sample_rate=f_s).write(os.path.join(ASSETS, f"audio-additive-K{K}.wav"))

# --- Varying amplitudes (random) ---
rng = np.random.default_rng(42)
for i in range(4):
    rand_amps = rng.uniform(0, 1, size=4).tolist()
    x = additive_synth(220, rand_amps)
    x *= amp / np.max(np.abs(x))
    pq.Audio(x, sample_rate=f_s).write(os.path.join(ASSETS, f"audio-additive-timbre-{i}.wav"))

# --- Varying phase (random) ---
for i in range(4):
    rand_phases = rng.uniform(0, 2 * np.pi, size=4).tolist()
    x = additive_synth(220, default_amps, rand_phases)
    x *= amp / np.max(np.abs(x))
    pq.Audio(x, sample_rate=f_s).write(os.path.join(ASSETS, f"audio-additive-phase-{i}.wav"))

print("additive examples done.")
