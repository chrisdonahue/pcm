"""Extracting and reassembling frames (Chapter 10).

Two tiny, standalone, student-facing building blocks for frame-based
processing: ``iter_frames`` slices audio into frames, and ``overlap_add``
glues frames back into audio. Everything else in the chapter (granular
synthesis, the STFT) is built on top of these.
"""

from typing import Iterator

import numpy as np
import pyquist as pq


def iter_frames(audio: pq.Audio, hop_length: int, frame_length: int) -> Iterator[np.ndarray]:
    """Yields successive frames of ``frame_length`` samples, spaced ``hop_length`` apart.

    We do nothing special at the boundaries: the loop walks the signal in steps
    of ``hop_length`` and stops once fewer than a full frame remains, so every
    yielded frame has exactly ``frame_length`` samples. Each frame keeps its
    channel axis, so a frame has shape ``(frame_length, num_channels)``.
    """
    for start in range(0, len(audio) - frame_length + 1, hop_length):
        yield audio.samples[start:start + frame_length]


def overlap_add(frames: np.ndarray, hop_length: int, sample_rate: int) -> pq.Audio:
    """Reassembles a stack of frames by adding each one back at its hop position.

    ``frames`` is an array of shape ``(num_frames, frame_length, num_channels)``,
    e.g. ``np.array(list(iter_frames(...)))``. Passing a ``hop_length`` different
    from the one used to extract the frames stretches or compresses the result in
    time, which is the basis of the time-stretching examples.
    """
    num_frames, frame_length, num_channels = frames.shape
    length = hop_length * (num_frames - 1) + frame_length
    out = np.zeros((length, num_channels), dtype=frames.dtype)
    for k, frame in enumerate(frames):
        out[k * hop_length: k * hop_length + frame_length] += frame
    return pq.Audio(out, sample_rate)


if __name__ == "__main__":
    # Rectangular windows at 0% overlap (hop == frame) are perfect reconstruction.
    rng = np.random.default_rng(0)
    x = pq.Audio(rng.standard_normal((10 * 1024, 1)).astype(np.float32), 44100)  # whole # of frames
    N_F = 1024
    frames = np.array(list(iter_frames(x, N_F, N_F)))
    y = overlap_add(frames, N_F, 44100)
    n = min(len(x), len(y))
    err = np.max(np.abs(np.asarray(x.samples)[:n] - np.asarray(y.samples)[:n]))
    print(f"rect @ 0% overlap, max reconstruction error: {err:.2e}")
