"""Envelopes: turning sustained tones into finite sound events.

Defines a sine oscillator and a piecewise-linear attack/decay envelope,
then multiplies them to produce a single enveloped note. Run directly to
render the audio example used in the chapter.
"""

from pathlib import Path

import numpy as np
import pyquist as pq

F_S = 44100


def osc(f_0: float, N: int, n: int = 0) -> pq.Audio:
    """A sine oscillator.

    Synthesizes ``N`` samples of a sinusoid at ``f_0`` Hz, as if starting
    from global sample index ``n`` (so blocks stitched end-to-end stay
    phase-continuous).
    """
    t = (n + np.arange(N)) / F_S
    return pq.Audio(np.sin(2.0 * np.pi * f_0 * t), F_S)


def adenv(a_dur: float, d_dur: float, N: int, n: int = 0) -> np.ndarray:
    """A piecewise-linear attack/decay envelope with unit peak.

    The envelope rises linearly from 0 to 1 over ``[0, a_dur]`` then falls
    back from 1 to 0 over ``[a_dur, a_dur + d_dur]``. ``a_dur`` and ``d_dur``
    are in seconds; ``N`` and ``n`` are in samples.

    Note this returns an ``np.ndarray``, not a :class:`pq.Audio`, because an
    envelope is an amplitude-shaping curve, not something we listen to. Its
    shape ``(N, 1)`` lets it broadcast across the channels of an ``Audio``
    buffer when multiplied.
    """
    t = (n + np.arange(N)) / F_S
    env = np.interp(t, [0.0, a_dur, a_dur + d_dur], [0.0, 1.0, 0.0])
    return env[:, np.newaxis]


if __name__ == "__main__":
    a_dur, d_dur = 0.1, 0.9
    N = int((a_dur + d_dur) * F_S)
    note = osc(220.0, N) * adenv(a_dur, d_dur, N)
    note.normalize(peak_dbfs=-6.0)
    assets = Path(__file__).resolve().parent.parent / "assets"
    assets.mkdir(exist_ok=True)
    note.write(str(assets / "audio-enveloped-note.wav"))
    print("wrote audio-enveloped-note.wav")
