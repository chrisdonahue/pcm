"""Sampling-theory utilities: aliasing, quantization, and linear resampling.

Standalone, student-facing implementations for Chapter 7.
"""

import numpy as np
import pyquist as pq


def alias_freq(f: float, f_s: float) -> float:
    """The apparent frequency of a tone at f Hz after sampling at rate f_s.

    Returns a value in [0, f_s / 2]. If f already lies in that band, it is
    returned unchanged (no aliasing); otherwise it folds back across Nyquist.
    """
    m = f % f_s
    return min(m, f_s - m)


def quantize(x: np.ndarray, b: int) -> np.ndarray:
    """Quantize amplitudes in [-1, 1] to b-bit signed PCM integers."""
    levels = 2 ** (b - 1) - 1
    return np.floor(x * levels).astype(np.int64)


def dequantize(q: np.ndarray, b: int) -> np.ndarray:
    """Convert b-bit signed PCM integers back to amplitudes in [-1, 1]."""
    levels = 2 ** (b - 1) - 1
    return q.astype(np.float64) / levels


def resample_linear(audio: pq.Audio, new_sample_rate: int) -> pq.Audio:
    """Resample by linear interpolation (see wavetable synthesis, Chapter 3).

    Note: this does NOT anti-alias, so it is only safe for *upsampling*. To
    lower the sample rate correctly, filter above the new Nyquist first (or
    use ``pq.Audio.resample``, which is bandlimited).
    """
    x = np.asarray(audio.samples)
    mono = x.reshape(len(x), -1).mean(axis=1)
    n = len(mono)
    m = int(round(n * new_sample_rate / audio.sample_rate))
    p = np.arange(m) * (audio.sample_rate / new_sample_rate)
    lo = np.floor(p).astype(int)
    alpha = p - lo
    hi = np.minimum(lo + 1, n - 1)
    y = (1 - alpha) * mono[lo] + alpha * mono[hi]
    return pq.Audio(y.astype(np.float32), new_sample_rate)


if __name__ == "__main__":
    # A 3 kHz tone sampled at 8 kHz is fine; a 6 kHz tone aliases to 2 kHz.
    for f in (3000, 6000, 9000):
        print(f"{f} Hz sampled at 8 kHz -> heard as {alias_freq(f, 8000):.0f} Hz")

    # Each bit of depth is worth ~6 dB: quantize a sine at a few bit depths.
    t = np.arange(8000) / 8000
    x = 0.9 * np.sin(2 * np.pi * 220 * t)
    for b in (4, 8, 16):
        err = dequantize(quantize(x, b), b) - x
        rms = float(np.sqrt(np.mean(err ** 2)))
        print(f"b = {b:2d} bits -> quantization noise RMS {pq.helper.amplitude_to_db(rms):.1f} dBFS")
