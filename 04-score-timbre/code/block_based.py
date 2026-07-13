"""Block-based computing: three ways to run a unit-generator network.

Synthesizes the same enveloped 220 Hz tone three ways and verifies that all
three produce identical output:

1. Ugen-by-ugen: each unit generator synthesizes the whole signal at once.
   Minimal call overhead, but every full-length buffer is held in memory.
2. Sample-by-sample: one sample per call. Minimal memory, but an enormous
   number of calls.
3. Block-by-block: process fixed-size blocks. A practical tradeoff, and the
   approach used by most computer music software.

The network here is `mul(adenv(0.1, 0.9), osc(220))`, three unit generators
in all: the envelope, the oscillator, and the multiply that combines them.
"""

import numpy as np
import pyquist as pq

F_S = 44100


def osc(f_0: float, N: int, n: int = 0) -> pq.Audio:
    """A sine oscillator (see envelope.py)."""
    t = (n + np.arange(N)) / F_S
    return pq.Audio(np.sin(2.0 * np.pi * f_0 * t), F_S)


def adenv(a_dur: float, d_dur: float, N: int, n: int = 0) -> np.ndarray:
    """A piecewise-linear attack/decay envelope (see envelope.py)."""
    t = (n + np.arange(N)) / F_S
    env = np.interp(t, [0.0, a_dur, a_dur + d_dur], [0.0, 1.0, 0.0])
    return env[:, np.newaxis]


def mul(a, b) -> pq.Audio:
    """Multiply two signals (a unit generator), returning Audio."""
    return pq.Audio(np.asarray(a) * np.asarray(b), F_S)


def add(a, b) -> pq.Audio:
    """Sum two signals (a unit generator), returning Audio."""
    return pq.Audio(np.asarray(a) + np.asarray(b), F_S)


N = F_S  # total duration in samples (1.0 s)

# 1. Ugen-by-ugen: minimal call overhead, maximal memory. Each unit generator
#    allocates a full N-sample buffer, and all are alive at once.
ugen_a = adenv(0.1, 0.9, N)       # a full N-sample envelope buffer
ugen_b = osc(220.0, N)            # a full N-sample oscillator buffer
ugen_by_ugen = mul(ugen_a, ugen_b)  # ...and a third for the product

# 2. Sample-by-sample: minimal memory, maximal number of function calls.
sample_by_sample = []
for n in range(N):
    sample_by_sample.append(mul(adenv(0.1, 0.9, 1, n), osc(220.0, 1, n)))
sample_by_sample = pq.Audio.concatenate(sample_by_sample)

# 3. Block-by-block: manageable memory, manageable number of calls.
B = 441  # block size in samples (0.01 s)
block_by_block = []
for n in range(0, N, B):
    block_by_block.append(mul(adenv(0.1, 0.9, B, n), osc(220.0, B, n)))
block_by_block = pq.Audio.concatenate(block_by_block)

# All three strategies produce exactly the same signal.
assert np.allclose(sample_by_sample, ugen_by_ugen)
assert np.allclose(block_by_block, ugen_by_ugen)

if __name__ == "__main__":
    print("ugen-by-ugen, sample-by-sample, and block-by-block all agree.")
