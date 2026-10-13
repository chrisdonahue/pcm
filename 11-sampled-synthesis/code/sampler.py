"""A tiny sample-based synthesizer.

A single recording of one clarinet note (A#5) becomes a playable instrument
with independent control over three expressive parameters:

- pitch:    resampling by a factor of 2^(k/12) shifts the pitch by k steps
- duration: repeating a loop from the sustain, then jumping to the release,
            changes the duration without changing the pitch
- loudness: a loudness in [0, 1] maps linearly to a gain from -80 to 0 dB
            (and 0 to silence)

Run directly to render and play a short phrase that uses all three.
"""

from pathlib import Path

import numpy as np
import pyquist as pq
from pyquist.helper import pitch_name_to_pitch

ASSETS = Path(__file__).resolve().parent.parent / "assets"
RECORDING = pq.Audio.from_file(str(ASSETS / "clarinet.wav"))   # A#5
RECORDING_PITCH = pitch_name_to_pitch("A#5")
LOOP_START, LOOP_END = 0.5, 0.72095   # seconds: 206 periods of A#5, about 9744 audio samples
RELEASE = 3.84968                     # seconds: where the release begins


def resample(x: pq.Audio, ratio: float) -> pq.Audio:
    """Read x at `ratio` times its original speed, with linear interpolation.

    A ratio above 1 plays faster (shorter and higher), and a ratio below 1
    plays slower (longer and lower). The sample rate stays the same.
    """
    samples = np.asarray(x.samples)
    N = len(samples)
    M = int(N / ratio)                        # the duration scales by 1 / ratio
    p = np.arange(M) * ratio                  # fractional read positions in x
    p_floor = np.floor(p).astype(int)
    alpha = (p - p_floor)[:, np.newaxis]
    p_next = np.minimum(p_floor + 1, N - 1)
    y = (1 - alpha) * samples[p_floor] + alpha * samples[p_next]
    return pq.Audio(y, x.sample_rate)


def repitch(x: pq.Audio, k: float) -> pq.Audio:
    """Shift the pitch of x by k steps, which also scales its duration by 2^(-k/12)."""
    return resample(x, 2 ** (k / 12))


def clarinet(pitch: str, duration: float, loudness: float) -> pq.Audio:
    """A sampled clarinet with independent control over pitch, duration, and loudness."""
    k = pitch_name_to_pitch(pitch) - RECORDING_PITCH
    x = np.asarray(repitch(RECORDING, k).samples)                          # pitch
    # Reading the recording 2^(k/12) times faster also moves the loop points
    to_samples = RECORDING.sample_rate / 2 ** (k / 12)
    s, e, r = (round(t * to_samples) for t in (LOOP_START, LOOP_END, RELEASE))
    # Play up to the loop, repeat the loop to fill out the duration, then play the release
    n = max(0, round((duration * RECORDING.sample_rate - s - (len(x) - r)) / (e - s)))
    x = np.concatenate([x[:s]] + [x[s:e]] * n + [x[r:]])                   # duration
    gain = 0.0 if loudness == 0 else 10 ** (80 * (loudness - 1) / 20)      # loudness
    return pq.Audio(gain * x, RECORDING.sample_rate)


if __name__ == "__main__":
    phrase = pq.Score([
        (0.0, {"pitch": "D5", "duration": 2.5, "loudness": 0.7}),
        (2.0, {"pitch": "F5", "duration": 2.5, "loudness": 0.8}),
        (4.0, {"pitch": "A#5", "duration": 2.5, "loudness": 0.9}),
        (6.0, {"pitch": "D6", "duration": 6.0, "loudness": 1.0}),   # held: loops the sustain
    ])
    audio = phrase.render(clarinet)
    audio.normalize(peak_dbfs=-6.0)
    pq.play(audio)
