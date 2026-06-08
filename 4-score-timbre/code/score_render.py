"""Rendering a score with an instrument.

Encodes "Twinkle, Twinkle, Little Star" as a :class:`pq.Score`, defines a
simple additive-synthesis instrument, and renders the score to audio via
:meth:`pq.Score.render`. Also demonstrates contemporaneous (simultaneous)
events by layering a bass line under the melody.
"""

from pathlib import Path

import numpy as np
import pyquist as pq
from pyquist.helper import pitch_name_to_pitch, pitch_to_frequency

F_S = 44100


def additive_instrument(pitch: str, duration: float, **kwargs) -> pq.Audio:
    """A four-harmonic additive instrument with an attack/decay envelope.

    Args:
        pitch: A scientific pitch name (e.g. ``"C4"``).
        duration: Note duration in seconds.

    Returns:
        The rendered note as :class:`pq.Audio`.
    """
    f_0 = pitch_to_frequency(pitch_name_to_pitch(pitch))
    N = int(duration * F_S)
    t = np.arange(N) / F_S

    # Four harmonics with 1/k amplitude decay (a sawtooth-ish recipe).
    k = np.arange(1, 5)
    a = 1.0 / k
    samples = (a * np.sin(2 * np.pi * k * f_0 * t[:, np.newaxis])).sum(axis=1)

    # Short attack, decay to silence over the rest of the note.
    env = np.interp(t, [0.0, 0.02, duration], [0.0, 1.0, 0.0], left=0.0, right=0.0)
    return pq.Audio(samples * env, F_S)


# The melody "Twinkle, Twinkle, Little Star": C C G G A A G.
# time is in seconds; each event's kwargs are passed to the instrument.
melody = pq.Score(
    [
        pq.Event(0.0, {"pitch": "C4", "duration": 1.0}),
        pq.Event(1.0, {"pitch": "C4", "duration": 1.0}),
        pq.Event(2.0, {"pitch": "G4", "duration": 1.0}),
        pq.Event(3.0, {"pitch": "G4", "duration": 1.0}),
        pq.Event(4.0, {"pitch": "A4", "duration": 1.0}),
        pq.Event(5.0, {"pitch": "A4", "duration": 1.0}),
        pq.Event(6.0, {"pitch": "G4", "duration": 2.0}),
    ]
)

# A bass line. Its events share onset times with the melody (e.g. both a
# melody C4 and a bass C3 begin at t = 0), so they sound simultaneously.
bass = pq.Score(
    [
        pq.Event(0.0, {"pitch": "C3", "duration": 4.0}),
        pq.Event(4.0, {"pitch": "F2", "duration": 2.0}),
        pq.Event(6.0, {"pitch": "C3", "duration": 2.0}),
    ]
)

# A Score is just a list of events, so harmonizing is list concatenation.
harmonized = pq.Score(melody + bass)


if __name__ == "__main__":
    assets = Path(__file__).resolve().parent.parent / "assets"
    assets.mkdir(exist_ok=True)

    melody_audio = melody.render(additive_instrument)
    melody_audio.normalize(peak_dbfs=-6.0)
    melody_audio.write(str(assets / "audio-twinkle-melody.wav"))

    harmonized_audio = harmonized.render(additive_instrument)
    harmonized_audio.normalize(peak_dbfs=-6.0)
    harmonized_audio.write(str(assets / "audio-twinkle-harmonized.wav"))

    print("wrote audio-twinkle-melody.wav and audio-twinkle-harmonized.wav")
