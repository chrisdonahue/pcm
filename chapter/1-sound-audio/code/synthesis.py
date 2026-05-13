"""Synthesize a 1-second 440 Hz sine tone and save it as a WAV file.

Run with:  python synthesis.py

This is the "hello world" of computer music: build an array of samples by
evaluating a continuous mathematical function at uniform intervals, then write
those samples to disk as a WAV file.
"""

import numpy as np
import soundfile as sf


def synthesize_sine(f, duration, f_s):
    """Return float samples in [-1, 1] for a sine wave of frequency f."""
    N = int(duration * f_s)
    n = np.arange(N)  # [0, 1, 2, ..., N-1]
    t = n / f_s  # sample times in seconds
    return np.sin(2.0 * np.pi * f * t)


if __name__ == "__main__":
    f_s = 44100
    samples = synthesize_sine(f=440.0, duration=1.0, f_s=f_s)
    sf.write("sine-440.wav", samples, f_s, subtype="PCM_16")
    print(f"Wrote sine-440.wav: {len(samples)} samples at f_s = {f_s} Hz")
