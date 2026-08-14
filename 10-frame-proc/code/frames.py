"""Extracting and reassembling frames (Chapter 10).

Two tiny, standalone, student-facing building blocks for frame-based
processing: ``iter_frames`` slices audio into frames, and ``overlap_add``
glues frames back into audio. Everything else in the chapter (granular
synthesis, the STFT) is built on top of these.
"""

from typing import Iterable, Iterator

import numpy as np
import pyquist as pq


def iter_frames(audio: pq.Audio, hop_length: int, frame_length: int) -> Iterator[np.ndarray]:
    """Yields successive frames of ``frame_length`` samples, spaced ``hop_length`` apart.

    We do nothing special at the boundaries: the loop simply walks the signal
    in steps of ``hop_length``, so the final frame or two may be _incomplete_
    (shorter than ``frame_length``) where the signal runs out.
    """
    x = np.asarray(audio.samples).reshape(-1)
    for start in range(0, len(x), hop_length):
        yield x[start:start + frame_length]


def overlap_add(frames: Iterable[np.ndarray], hop_length: int,
                sample_rate: int) -> pq.Audio:
    """Reassembles frames by adding each one back at its hop position.

    Any incomplete frames (shorter than the first, full frame) are dropped, so
    that the output is built only from complete frames. Passing a ``hop_length``
    different from the one used to extract the frames stretches or compresses
    the result in time, which is the basis of the time-stretching examples.
    """
    frames = [f for f in frames]
    frame_length = len(frames[0])
    length = hop_length * (len(frames) - 1) + frame_length
    out = np.zeros(length)
    for k, frame in enumerate(frames):
        if len(frame) < frame_length:          # drop incomplete frames
            continue
        out[k * hop_length: k * hop_length + frame_length] += frame
    return pq.Audio(out.astype(np.float32), sample_rate)


if __name__ == "__main__":
    # Rectangular windows at 0% overlap (hop == frame) are perfect reconstruction.
    rng = np.random.default_rng(0)
    x = pq.Audio(rng.standard_normal(10 * 1024).astype(np.float32), 44100)  # whole # of frames
    N_F = 1024
    y = overlap_add(iter_frames(x, N_F, N_F), N_F, 44100)
    n = min(len(np.asarray(x.samples).reshape(-1)), len(np.asarray(y.samples).reshape(-1)))
    err = np.max(np.abs(np.asarray(x.samples).reshape(-1)[:n] - np.asarray(y.samples).reshape(-1)[:n]))
    print(f"rect @ 0% overlap, max reconstruction error: {err:.2e}")
