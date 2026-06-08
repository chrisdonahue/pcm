"""Block-based computing: three ways to run a unit-generator network.

Synthesizes the same enveloped 220 Hz tone three ways and verifies that all
three produce identical output:

1. Sample-by-sample: one sample per call. Minimal memory, maximal call
   overhead.
2. Ugen-by-ugen: each unit generator synthesizes the whole signal at once.
   Maximal memory, minimal call overhead.
3. Block-by-block: process fixed-size blocks. A practical tradeoff, and the
   approach used by most computer music software.
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
    env = np.interp(
        t, [0.0, a_dur, a_dur + d_dur], [0.0, 1.0, 0.0], left=0.0, right=0.0
    )
    return env[:, np.newaxis]


N = F_S  # total duration in samples (1.0 s)

# 1. Sample-by-sample: minimal memory, maximal function-call overhead.
sample_by_sample = []
for n in range(N):
    sample_by_sample.append(osc(220.0, 1, n) * adenv(0.1, 0.9, 1, n))
sample_by_sample = pq.Audio.concatenate(sample_by_sample)

# 2. Ugen-by-ugen: maximal memory, minimal function-call overhead.
ugen_by_ugen = osc(220.0, N) * adenv(0.1, 0.9, N)

# 3. Block-by-block: manageable memory, manageable function-call overhead.
B = 441  # block size in samples (0.01 s)
block_by_block = []
for n in range(0, N, B):
    block_by_block.append(osc(220.0, B, n) * adenv(0.1, 0.9, B, n))
block_by_block = pq.Audio.concatenate(block_by_block)

# All three strategies produce exactly the same signal.
assert np.allclose(sample_by_sample, ugen_by_ugen)
assert np.allclose(block_by_block, ugen_by_ugen)

if __name__ == "__main__":
    print("sample-by-sample, ugen-by-ugen, and block-by-block all agree.")
