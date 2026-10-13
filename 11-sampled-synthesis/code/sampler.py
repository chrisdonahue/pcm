"""A tiny sample-based synthesizer.

A single recording of one soprano saxophone note (C5) becomes a playable
instrument with independent control over three musical properties:

- pitch:    resampling by a factor of 2^(k/12) shifts the pitch by k steps
- duration: looping a region of the sustain lengthens a note without
            changing its pitch
- dynamics: scaling the amplitude, and low-pass filtering softer notes so
            they sound mellower, like a real instrument played softly

Run directly to render and play a short phrase that uses all three.
"""

from pathlib import Path

import numpy as np
import pyquist as pq
from pyquist.helper import pitch_name_to_pitch
from scipy.signal import lfilter

ASSETS = Path(__file__).resolve().parent.parent / "assets"


# ---------------------------------------------------------------------------
# Pitch: resampling
# ---------------------------------------------------------------------------


def resample(x: pq.Audio, ratio: float) -> pq.Audio:
    """Read x at `ratio` times its original speed, with linear interpolation.

    A ratio above 1 plays faster (shorter and higher), and a ratio below 1
    plays slower (longer and lower). The sample rate stays the same.
    """
    samples = np.asarray(x.samples)
    N = len(samples)
    M = int(N / ratio)                       # the duration scales by 1 / ratio
    p = np.arange(M) * ratio                 # fractional read positions in x
    p_floor = np.floor(p).astype(int)
    alpha = (p - p_floor)[:, np.newaxis]
    p_next = np.minimum(p_floor + 1, N - 1)
    y = (1 - alpha) * samples[p_floor] + alpha * samples[p_next]
    return pq.Audio(y, x.sample_rate)


def repitch(x: pq.Audio, k: float) -> pq.Audio:
    """Shift the pitch of x by k steps, which also scales its duration by 2^(-k/12)."""
    return resample(x, 2 ** (k / 12))


# ---------------------------------------------------------------------------
# Duration: looping the sustain
# ---------------------------------------------------------------------------


def loop_note(x: pq.Audio, t_s: float, t_e: float, duration: float,
              xfade: float = 0.03) -> pq.Audio:
    """Lengthen a note to roughly `duration` seconds by looping [t_s, t_e).

    Everything before the loop plays once, the loop repeats, and everything
    after the loop (the release) plays once. Each time the loop wraps around,
    its last `xfade` seconds are crossfaded into the audio just *before* t_s,
    which flows continuously into the next pass. Requires t_s >= xfade.
    """
    samples = np.asarray(x.samples)
    f_s = x.sample_rate
    s, e = int(round(t_s * f_s)), int(round(t_e * f_s))
    L = int(round(xfade * f_s))
    d_A, d_S, d_R = s, e - s, len(samples) - e          # all in samples
    n_loops = max(1, round((duration * f_s - d_A - d_R) / d_S))
    body = samples[s:e].copy()
    if L > 0:
        w = np.linspace(0.0, 1.0, L)[:, np.newaxis]     # fade-in weights
        body[-L:] = (1 - w) * samples[e - L:e] + w * samples[s - L:s]
    # The final pass is not crossfaded: it flows straight into the release.
    parts = [samples[:s]] + [body] * (n_loops - 1) + [samples[s:e], samples[e:]]
    return pq.Audio(np.concatenate(parts), f_s)


def cut_off(x: pq.Audio, duration: float, r_dur: float = 0.1) -> pq.Audio:
    """End a note early: keep `duration` seconds, fading out over the last r_dur."""
    y = np.asarray(x.samples)[:int(duration * x.sample_rate)].copy()
    n_r = min(len(y), int(r_dur * x.sample_rate))
    y[len(y) - n_r:] *= np.linspace(1.0, 0.0, n_r)[:, np.newaxis]
    return pq.Audio(y, x.sample_rate)


# ---------------------------------------------------------------------------
# Dynamics: gain plus a velocity-dependent low-pass filter
# ---------------------------------------------------------------------------


def lpf(f_c: float, Q: float, f_s: int) -> tuple[np.ndarray, np.ndarray]:
    """A low-pass biquad from the Audio EQ Cookbook (as in Chapter 9's rbj.py)."""
    w0 = 2 * np.pi * f_c / f_s
    c, alpha = np.cos(w0), np.sin(w0) / (2 * Q)
    b = np.array([(1 - c) / 2, 1 - c, (1 - c) / 2])
    a = np.array([1 + alpha, -2 * c, 1 - alpha])
    return b / a[0], a / a[0]


def dynamics(x: pq.Audio, velocity: float, f_lo: float = 1000.0,
             f_hi: float = 12000.0) -> pq.Audio:
    """Play x at a `velocity` in (0, 1]: scale its amplitude by the velocity,
    and low-pass it with a cutoff that rises exponentially from f_lo (soft)
    to f_hi (loud), since louder notes have stronger upper harmonics."""
    f_c = f_lo * (f_hi / f_lo) ** velocity
    b, a = lpf(f_c, 0.707, x.sample_rate)
    y = lfilter(b, a, velocity * np.asarray(x.samples), axis=0)
    return pq.Audio(y, x.sample_rate)


# ---------------------------------------------------------------------------
# The instrument
# ---------------------------------------------------------------------------

SAX = pq.Audio.from_file(str(ASSETS / "sax-C5.wav"))
SAX_PITCH = pitch_name_to_pitch("C5")
# A loop that spans a whole number of cycles (131) of C5, ending just before
# the recording's release begins.
LOOP = (3.0496, 3.3000)


def sax(pitch: str, duration: float, velocity: float = 1.0, **kwargs) -> pq.Audio:
    """A sampled soprano saxophone with independent pitch, duration, and dynamics."""
    k = pitch_name_to_pitch(pitch) - SAX_PITCH
    note = repitch(SAX, k)                                    # pitch
    ratio = 2 ** (k / 12)
    t_s, t_e = LOOP[0] / ratio, LOOP[1] / ratio               # loop points move with resampling
    if duration < note.duration:                              # duration
        note = cut_off(note, duration)                        #   shorter: end the note early
    else:
        note = loop_note(note, t_s, t_e, duration)            #   longer: loop the sustain
    return dynamics(note, velocity)                           # dynamics


if __name__ == "__main__":
    phrase = pq.Score([
        (0.0, {"pitch": "G4", "duration": 0.4, "velocity": 0.4}),
        (0.5, {"pitch": "C5", "duration": 0.4, "velocity": 0.6}),
        (1.0, {"pitch": "E5", "duration": 0.4, "velocity": 0.8}),
        (1.5, {"pitch": "G5", "duration": 6.0, "velocity": 1.0}),   # held: loops the sustain
    ])
    audio = phrase.render(sax)
    audio.normalize(peak_dbfs=-6.0)
    pq.play(audio)
