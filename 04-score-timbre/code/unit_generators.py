"""Four Python idioms for implementing a unit generator.

A unit generator must produce successive blocks of a signal while keeping
track of where it left off (here, the oscillator's phase). Python offers
several ways to manage that state. Each idiom below implements the same sine
oscillator, and the driver at the bottom confirms they all agree.

We do not recommend one idiom over the others — each has tradeoffs and suits
different situations. Experiment and see what you prefer.
"""

from typing import Iterator

import numpy as np
import pyquist as pq

F_S = 44100


# (1) As a pure function of the global sample index. The caller is
#     responsible for passing a consistent `n` across blocks.
def osc(f_0: float, N: int, n: int = 0) -> pq.Audio:
    t = (n + np.arange(N)) / F_S
    return pq.Audio(np.sin(2.0 * np.pi * f_0 * t), F_S)


# (2) As a function that passes phase state in and out explicitly.
def osc_stateless(
    f_0: float, N: int, phase: float = 0.0
) -> tuple[pq.Audio, float]:
    d_phase = 2.0 * np.pi * f_0 / F_S
    phases = phase + np.arange(N) * d_phase
    next_phase = phase + N * d_phase
    return pq.Audio(np.sin(phases), F_S), next_phase


# (3) As an iterator that yields successive blocks, hiding the state inside
#     the generator's local scope.
def osc_iter(f_0: float, B: int) -> Iterator[pq.Audio]:
    phase = 0.0
    while True:
        block, phase = osc_stateless(f_0, B, phase)
        yield block


# (4) As a stateful object that remembers its own phase between calls.
class Osc:
    def __init__(self, f_0: float) -> None:
        self.d_phase = 2.0 * np.pi * f_0 / F_S
        self.phase = 0.0

    def __call__(self, N: int) -> pq.Audio:
        phases = self.phase + np.arange(N) * self.d_phase
        self.phase += N * self.d_phase
        return pq.Audio(np.sin(phases), F_S)


if __name__ == "__main__":
    f_0, B = 220.0, 441

    a, b, c, d = [], [], [], []
    b_phase = 0.0
    c_iter = osc_iter(f_0, B)
    d_osc = Osc(f_0)
    for n in range(0, F_S, B):
        a.append(osc(f_0, B, n))
        b_block, b_phase = osc_stateless(f_0, B, b_phase)
        b.append(b_block)
        c.append(next(c_iter))
        d.append(d_osc(B))
    a, b, c, d = (pq.Audio.concatenate(x) for x in (a, b, c, d))

    assert np.allclose(a, b) and np.allclose(b, c) and np.allclose(c, d)
    print("all four unit-generator idioms agree.")
