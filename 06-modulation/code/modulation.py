"""Modulation synthesis: ring/amplitude modulation, a correct time-varying
oscillator, and frequency modulation.

Standalone, student-facing implementations for Chapter 6. Run directly to
render a handful of demonstration tones to WAV files in the current directory.
"""

from pathlib import Path

import numpy as np
import pyquist as pq

F_S = 44100


def ring_mod(f_c: float, f_m: float, dur: float) -> pq.Audio:
    """Ring modulation: the product of a carrier and a modulator sinusoid."""
    t = np.arange(int(dur * F_S)) / F_S
    x = np.sin(2 * np.pi * f_c * t) * np.sin(2 * np.pi * f_m * t)
    return pq.Audio(x.astype(np.float32), F_S)


def amp_mod(f_c: float, f_m: float, dur: float, r: float = 2.0) -> pq.Audio:
    """Amplitude modulation: ring modulation that retains the carrier.

    ``r`` is the ratio of the carrier amplitude to each sideband amplitude.
    """
    t = np.arange(int(dur * F_S)) / F_S
    x = np.sin(2 * np.pi * f_c * t) * (r / 2.0 + np.sin(2 * np.pi * f_m * t))
    return pq.Audio(x.astype(np.float32), F_S)


def osc_naive(freq: np.ndarray) -> pq.Audio:
    """WRONG time-varying oscillator: multiplies the *current* frequency by the
    *total* elapsed time. Sounds badly out of tune when ``freq`` changes."""
    n = np.arange(len(freq))
    x = np.sin(2 * np.pi * freq * n / F_S)
    return pq.Audio(x.astype(np.float32), F_S)


def osc(freq: np.ndarray) -> pq.Audio:
    """A time-varying oscillator driven by a per-sample frequency (in Hz).

    Accumulate (integrate) frequency into phase, one sample at a time, then
    take the sine of the accumulated phase. This is the correct way to handle
    a frequency that changes over time.
    """
    x = np.zeros(len(freq), dtype=np.float32)
    theta = 0.0
    for n in range(len(freq)):
        theta += 2 * np.pi * freq[n] / F_S
        x[n] = np.sin(theta)
    return pq.Audio(x, F_S)


def osc_vectorized(freq: np.ndarray) -> pq.Audio:
    """The same time-varying oscillator, vectorized: ``np.cumsum`` is the
    running total (a discrete integral) of the per-sample phase increments."""
    theta = np.cumsum(2 * np.pi * freq / F_S)
    return pq.Audio(np.sin(theta).astype(np.float32), F_S)


def freq_mod(f_c: float, f_m: float, I: float, dur: float) -> pq.Audio:
    """Classic (integrated) frequency modulation.

    ``I`` is the index of modulation (``I = D / f_m``), which controls the
    number of audible sidebands. The ratio ``f_c / f_m`` sets harmonicity.
    """
    t = np.arange(int(dur * F_S)) / F_S
    x = np.sin(2 * np.pi * f_c * t + I * np.sin(2 * np.pi * f_m * t))
    return pq.Audio(x.astype(np.float32), F_S)


def freq_mod_general(f_c: float, modulation: np.ndarray) -> pq.Audio:
    """General FM: the carrier's frequency is ``f_c`` plus a modulating signal
    that may be *any* sound (in Hz), not just a single sinusoid. Built on the
    time-varying oscillator above."""
    return osc_vectorized(f_c + modulation)


if __name__ == "__main__":
    out = Path(".")
    for name, audio in [
        ("ring_mod", ring_mod(220.0, 4.0, 3.0)),
        ("amp_mod", amp_mod(220.0, 55.0, 3.0)),
        ("fm_harmonic", freq_mod(440.0, 220.0, 3.0, 3.0)),
        ("fm_bell", freq_mod(200.0, 280.0, 3.0, 3.0)),
    ]:
        audio.normalize(peak_dbfs=-6.0)
        audio.write(str(out / f"{name}.wav"))
        print(f"wrote {name}.wav")
