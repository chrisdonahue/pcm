"""The short-time Fourier transform and its inverse (Chapter 10).

Standalone, student-facing implementations. The STFT is just "the DFT of each
frame"; the inverse STFT is "the inverse DFT of each frame, overlap-added back
together". Run directly to check that the round trip reconstructs a signal.
"""

import numpy as np


def stft(x: np.ndarray, hop_length: int, frame_length: int,
         window: np.ndarray = None) -> np.ndarray:
    """Short-time Fourier transform: window each frame and take its DFT.

    Returns a complex matrix of shape ``(num_frames, frame_length // 2 + 1)``,
    one row per frame and one column per (non-redundant) frequency bin. We use
    the real FFT ``np.fft.rfft`` since audio is real-valued.
    """
    if window is None:
        window = np.ones(frame_length)
    frames = []
    for start in range(0, len(x) - frame_length + 1, hop_length):
        frames.append(np.fft.rfft(x[start:start + frame_length] * window))
    return np.array(frames)


def istft(S: np.ndarray, hop_length: int, frame_length: int,
          window: np.ndarray = None) -> np.ndarray:
    """Inverse STFT: inverse-DFT each frame and overlap-add the results.

    Each frame is windowed again on the way out and the running sum of squared
    windows is divided out at the end. This "weighted overlap-add" gives perfect
    reconstruction whenever the windows satisfy the constant-overlap-add
    property (e.g. a rectangular window at 0% overlap, or a Hann window at 50%).
    """
    if window is None:
        window = np.ones(frame_length)
    num_frames = S.shape[0]
    length = hop_length * (num_frames - 1) + frame_length
    out = np.zeros(length)
    window_sum = np.zeros(length)
    for k in range(num_frames):
        frame = np.fft.irfft(S[k], frame_length) * window
        out[k * hop_length: k * hop_length + frame_length] += frame
        window_sum[k * hop_length: k * hop_length + frame_length] += window ** 2
    return out / np.maximum(window_sum, 1e-8)


def hann(frame_length: int) -> np.ndarray:
    """A Hann window of length ``frame_length``."""
    n = np.arange(frame_length)
    return 0.5 * (1 - np.cos(2 * np.pi * n / frame_length))


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    x = rng.standard_normal(20000)
    N_F, N_H = 1024, 256                    # Hann window at 75% overlap
    w = hann(N_F)
    y = istft(stft(x, N_H, N_F, w), N_H, N_F, w)
    n = min(len(x), len(y))
    # Skip the warm-up region at the very edges, where fewer windows overlap.
    err = np.max(np.abs(x[N_F:n - N_F] - y[N_F:n - N_F]))
    print(f"STFT round-trip max error (interior): {err:.2e}")
