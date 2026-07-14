"""Rendering a score with an instrument.

Encodes "Twinkle, Twinkle, Little Star" as a :class:`pq.Score`, defines a
simple sine-wave instrument, and renders the score to audio via
:meth:`pq.Score.render`. Also demonstrates contemporaneous (simultaneous)
events by layering a bass line under the melody.

Times are in seconds at 120 BPM, so each quarter note is 0.5 s.
"""

from pathlib import Path

import numpy as np
import pyquist as pq
from pyquist.helper import pitch_name_to_pitch, pitch_to_frequency

F_S = 44100


def sine_instrument(pitch: str, duration: float, **kwargs) -> pq.Audio:
    """A basic sine-wave instrument: one pure tone per event.

    A short attack/decay envelope is applied so that each note's onset is
    audibly distinct (envelopes are covered in the next section).

    Args:
        pitch: A scientific pitch name (e.g. ``"C4"``).
        duration: Note duration in seconds.

    Returns:
        The rendered note as :class:`pq.Audio`.
    """
    f_0 = pitch_to_frequency(pitch_name_to_pitch(pitch))
    N = int(duration * F_S)
    t = np.arange(N) / F_S
    tone = np.sin(2 * np.pi * f_0 * t)
    env = np.interp(t, [0.0, 0.01, duration], [0.0, 1.0, 0.0])
    return pq.Audio(tone * env, F_S)


# The melody "Twinkle, Twinkle, Little Star": C C G G A A G.
# Each (time, kwargs) tuple is coerced to a pq.Event by pq.Score.
melody = pq.Score(
    [
        (0.0, {"pitch": "C4", "duration": 0.5}),
        (0.5, {"pitch": "C4", "duration": 0.5}),
        (1.0, {"pitch": "G4", "duration": 0.5}),
        (1.5, {"pitch": "G4", "duration": 0.5}),
        (2.0, {"pitch": "A4", "duration": 0.5}),
        (2.5, {"pitch": "A4", "duration": 0.5}),
        (3.0, {"pitch": "G4", "duration": 1.0}),
    ]
)

# A bass line. Its events share onset times with the melody (e.g. both a
# melody C4 and a bass C3 begin at t = 0), so they sound simultaneously.
bass = pq.Score(
    [
        (0.0, {"pitch": "C3", "duration": 2.0}),
        (2.0, {"pitch": "F2", "duration": 1.0}),
        (3.0, {"pitch": "C3", "duration": 1.0}),
    ]
)

# A Score is just a list of events, so harmonizing is list concatenation.
# Adding two Scores yields a new Score.
harmonized = melody + bass


if __name__ == "__main__":
    assets = Path(__file__).resolve().parent.parent / "assets"
    assets.mkdir(exist_ok=True)

    melody_audio = melody.render(sine_instrument)
    melody_audio.normalize(peak_dbfs=-6.0)
    melody_audio.write(str(assets / "audio-twinkle-melody.wav"))

    harmonized_audio = harmonized.render(sine_instrument)
    harmonized_audio.normalize(peak_dbfs=-6.0)
    harmonized_audio.write(str(assets / "audio-twinkle-harmonized.wav"))

    print("wrote audio-twinkle-melody.wav and audio-twinkle-harmonized.wav")
