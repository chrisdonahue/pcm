"""Synthesize a 1-second 440 Hz sine tone and save it as a WAV file.

Run with:  python synthesis.py

This is the "hello world" of computer music: generate an array of samples by
evaluating a continuous mathematical function at uniform intervals, then write
those samples to disk as a WAV file.
"""

import math
import struct
import wave


def synthesize_sine(f, duration, f_s):
    """Return a list of float samples in [-1, 1] for a sine wave of frequency f."""
    N = int(duration * f_s)
    samples = [0.0] * N
    for i in range(N):
        t = i / f_s
        samples[i] = math.sin(2.0 * math.pi * f * t)
    return samples


def write_wav(samples, f_s, path):
    """Quantize float samples in [-1, 1] to 16-bit signed PCM and write a WAV file."""
    with wave.open(path, "w") as out:
        out.setnchannels(1)
        out.setsampwidth(2)  # 16 bits per sample
        out.setframerate(f_s)
        for s in samples:
            s_clamped = max(-1.0, min(s, 1.0))
            sample_int = int(round(s_clamped * 32767))
            out.writeframes(struct.pack("<h", sample_int))


if __name__ == "__main__":
    f_s = 44100
    samples = synthesize_sine(f=440.0, duration=1.0, f_s=f_s)
    write_wav(samples, f_s, "sine-440.wav")
    print(f"Wrote sine-440.wav: {len(samples)} samples at f_s = {f_s} Hz")
