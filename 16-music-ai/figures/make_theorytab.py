"""Simplify the Hooktheory dataset into ../assets/TheorytabSimple.json.gz.

This file is *not* student-facing. It reads the Hooktheory dataset released with
Sheet Sage (Donahue, Thickstun, and Liang, ISMIR 2022), 26,175 crowdsourced
melody and chord transcriptions of pop song excerpts, from
../raw/Materials for Symbolic Gen Code Examples/Hooktheory (4).json.gz, and writes a
dead-simple version for the lead sheet notebook:

    {"<hooktheory_id>": {
        "split": "TRAIN" | "VALID" | "TEST",
        "youtube_url": "https://www.youtube.com/embed/<id>?start=<s>&end=<e>" | null,
        "melody": [[beat, pitch], ...],
        "chords": [[beat, "C:maj"], ...]}}

Everything is absolute. `beat` is an onset in beats (quarter notes) from the start
of the annotated excerpt, rounded to 3 decimals (99.95% of onsets lie on a
sixteenth-note grid). `pitch` is a MIDI pitch. A chord label is a root (spelled
with sharps) and one of five families: maj, min, 7, maj7, min7 (60 labels).
Offsets (note and chord durations) and chord inversions are dropped.

Absolute pitch. The dataset stores each melody note as an absolute `pitch_class`
(0 = C) and an `octave`, which we map to MIDI as 12 * (octave + 5) + pitch_class,
so octave 0 is C4-B4 (MIDI 60-71), as in the author's earlier Colab notebook.
Checks that support this:
  - Pitch classes are absolute, not relative to the key: in major keys, the
    melody's pitch classes relative to the `keys` tonic are dominated by the
    major scale (0, 4, 7, 2, 9, 5, 11), and chord roots relative to the tonic by
    I, V, IV, vi (0, 7, 5, 9).
  - The octave is absolute, not relative to the tonic: with this mapping, only
    2.8% of melodic intervals are an octave or more (the mean |interval| is 2.7
    semitones), versus 14% (and 4.7) if the octave counted up from the tonic.
  - Spot checks: the Beatles - Yesterday (F major) has "all my troubles seemed so
    far away" as A3 B3 C#4 D4 E4 F4, and Let It Be (C major) has "when I find
    myself in times of trouble" as G3 G3 G3 A3 E3 G3 ... C4 D4, both in the
    register Paul McCartney sings.
  Caveat: the octave is whatever the annotator notated, so different annotations
  of the same song are sometimes an octave apart (the median pitch is G#4).

Chord roots are absolute pitch classes too (`root_pitch_class`), and
`root_position_intervals` gives the chord family: [4, 3] maj, [3, 4] min,
[4, 3, 3] 7, [4, 3, 4] maj7, [3, 4, 3] min7.

Filtering. We keep an example only if:
  - it is tagged with both MELODY and HARMONY (and both lists are non-empty),
  - it has a single meter, 4/4 (beats_per_bar == 4, beat_unit == 4),
  - it has no SWING_CHANGES tag (swing is a property of the audio alignment, not
    of the notated beats, so constant swing is kept),
  - every chord is in one of the five families above (no sus, dim, aug, 9, ...).
Key and tempo changes are kept, since pitches and beats are absolute.

`youtube_url` points at the annotated excerpt of the original recording, from
the user alignment of beat 0 and the last beat (rounded down and up to whole
seconds). It is null when the example has no audio alignment.

Run with the project virtualenv:
    python make_theorytab.py
"""

import gzip
import json
import math
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHAPTER = HERE.parent
RAW = CHAPTER / "raw" / "Materials for Symbolic Gen Code Examples" / "Hooktheory (4).json.gz"
OUTPUT = CHAPTER / "assets" / "TheorytabSimple.json.gz"

PITCH_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
FAMILIES = {(4, 3): "maj", (3, 4): "min", (4, 3, 3): "7", (4, 3, 4): "maj7", (3, 4, 3): "min7"}


def number(x: float) -> int | float:
    """A beat or time, rounded to 3 decimals, as an int when it is whole (smaller JSON)."""
    x = round(float(x), 3)
    return int(x) if x == int(x) else x


def beat_to_seconds(beats: list[float], times: list[float], beat: float) -> float:
    """Linearly interpolate (or extrapolate) an alignment from beats to seconds."""
    i = max(1, min(len(beats) - 1, sum(b <= beat for b in beats)))
    (b0, b1), (t0, t1) = beats[i - 1:i + 1], times[i - 1:i + 1]
    return t0 + (beat - b0) * (t1 - t0) / (b1 - b0)


def youtube_url(example: dict) -> str | None:
    """An embeddable YouTube URL for the annotated excerpt, or None without audio."""
    alignment = (example.get("alignment") or {}).get("user")
    if "AUDIO_AVAILABLE" not in example["tags"] or not alignment or len(alignment["beats"]) < 2:
        return None
    beats, times = alignment["beats"], alignment["times"]
    start = beat_to_seconds(beats, times, 0)
    end = beat_to_seconds(beats, times, example["annotations"]["num_beats"])
    start, end = max(0, math.floor(start)), math.ceil(end)
    return f"https://www.youtube.com/embed/{example['youtube']['id']}?start={start}&end={end}"


def simplify(example: dict) -> tuple[dict | None, str]:
    """The simplified example (or None), and the reason it was kept or dropped."""
    annotations, tags = example["annotations"], example["tags"]
    if "MELODY" not in tags or "HARMONY" not in tags:
        return None, "no melody or no chords"
    if not annotations["melody"] or not annotations["harmony"]:
        return None, "no melody or no chords"
    meters = annotations["meters"]
    if len(meters) != 1 or (meters[0]["beats_per_bar"], meters[0]["beat_unit"]) != (4, 4):
        return None, "not 4/4 throughout"
    if "SWING_CHANGES" in tags:
        return None, "swing changes"
    chords = []
    for chord in annotations["harmony"]:
        family = FAMILIES.get(tuple(chord["root_position_intervals"]))
        if family is None:
            return None, "other chord types"
        chords.append([number(chord["onset"]), f"{PITCH_NAMES[chord['root_pitch_class']]}:{family}"])
    melody = [[number(note["onset"]), 12 * (note["octave"] + 5) + note["pitch_class"]]
              for note in annotations["melody"]]
    return {
        "split": example["split"],
        "youtube_url": youtube_url(example),
        "melody": sorted(melody),
        "chords": sorted(chords, key=lambda chord: chord[0]),
    }, "kept"


def main() -> None:
    with gzip.open(RAW, "rt") as f:
        dataset = json.load(f)
    simple, reasons = {}, Counter()
    for hooktheory_id, example in dataset.items():
        result, reason = simplify(example)
        reasons[reason] += 1
        if result is not None:
            simple[hooktheory_id] = result
    with gzip.open(OUTPUT, "wt", compresslevel=9) as f:
        json.dump(simple, f, separators=(",", ":"))

    print(f"{len(dataset)} examples in, {len(simple)} kept")
    for reason, count in reasons.most_common():
        print(f"  {reason}: {count}")
    splits = Counter(example["split"] for example in simple.values())
    print("  per split:", dict(sorted(splits.items())))
    print(f"  with YouTube URL: {sum(e['youtube_url'] is not None for e in simple.values())}")
    print(f"  melody notes: {sum(len(e['melody']) for e in simple.values())}, "
          f"chords: {sum(len(e['chords']) for e in simple.values())}")
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
