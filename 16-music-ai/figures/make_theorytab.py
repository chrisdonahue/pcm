"""Simplify the Hooktheory dataset into ../assets/TheorytabSimple.json.gz.

This file is *not* student-facing. It reads the Hooktheory dataset released with
Sheet Sage (Donahue, Thickstun, and Liang, ISMIR 2022), 26,175 crowdsourced
melody and chord transcriptions of pop song excerpts, from
../raw/Materials for Symbolic Gen Code Examples/Hooktheory (4).json.gz, and writes a
dead-simple version for the lead sheet notebook:

    {"<hooktheory_id>": {
        "split": "TRAIN" | "VALID" | "TEST",
        "hookpad_url": "https://hookpad.hooktheory.com/?idOfSong=<id>&enableYouTube=true",
        "youtube_url": "https://www.youtube.com/watch?v=<id>&t=<start>" | null,
        "youtube_segment": [<start>, <end>] | null,
        "tempo": <beats per minute> | null,
        "melody": [[beat, pitch], ...],
        "chords": [[beat, "C:maj"], ...]}}

Everything is absolute. `beat` is an onset in beats (quarter notes) from the start
of the annotated excerpt, counting from 0 (beat 0 is the first downbeat, so bars
start at beats 0, 4, 8, ..., and a song whose melody starts with a rest under the
first chord has its first melody note after beat 0). Beats are rounded to 3 decimals (99.95% of onsets lie on a
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
  - it has no TEMPO_CHANGES tag, so that a single `tempo` describes it,
  - it has no incomplete measures: something (a note or a chord) starts at beat 0,
    and its length is a whole number of bars (num_beats is a multiple of 4), so
    songs that start with a pickup or end mid-bar are dropped,
  - every chord is in one of the five families above (no sus, dim, aug, 9, ...).
Key changes are kept, since pitches are absolute.

`youtube_url` is a standard YouTube link to the original recording, starting at the
annotated excerpt (`&t=<start>`, rounded down to whole seconds, since watch links
can't specify an end). `youtube_segment` is the excerpt's [start, end] in seconds,
from the user alignment of beat 0 and the last beat. `tempo` (unused by the notebook)
is the average tempo of that alignment, in beats per minute. A few alignments are
broken (e.g. the whole excerpt squeezed into 0.27 s), so if the implied tempo is
outside 30-400 BPM, the segment and tempo are null and the link has no start time.
All three are null when the example has no audio.

Run with the project virtualenv:
    python make_theorytab.py
"""

import gzip
import json
import math
import re
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


HOOKPAD = "https://hookpad.hooktheory.com/"   # Hooktheory's editor, to view an annotation
MIN_TEMPO, MAX_TEMPO = 30, 400   # an alignment implying a tempo outside this is broken


def audio_fields(example: dict) -> dict:
    """The YouTube URL of the original recording (starting at the annotated excerpt),
    the excerpt's [start, end] in seconds, and its average tempo in BPM, all from the
    user alignment of the annotation to the audio. Fields are None when unknown."""
    if "AUDIO_AVAILABLE" not in example["tags"] or not example.get("youtube"):
        return {"youtube_url": None, "youtube_segment": None, "tempo": None}
    url = f"https://www.youtube.com/watch?v={example['youtube']['id']}"
    alignments = example.get("alignment") or {}
    alignment = alignments.get("user") or alignments.get("refined")
    if not alignment or len(alignment["beats"]) < 2:
        return {"youtube_url": url, "youtube_segment": None, "tempo": None}
    beats, times = alignment["beats"], alignment["times"]
    tempo = 60 * (beats[-1] - beats[0]) / (times[-1] - times[0])
    if not MIN_TEMPO <= tempo <= MAX_TEMPO:
        return {"youtube_url": url, "youtube_segment": None, "tempo": None}
    start = max(0.0, beat_to_seconds(beats, times, 0))
    end = beat_to_seconds(beats, times, example["annotations"]["num_beats"])
    return {"youtube_url": f"{url}&t={math.floor(start)}",
            "youtube_segment": [round(start, 2), round(end, 2)],
            "tempo": round(tempo, 1)}


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
    if "TEMPO_CHANGES" in tags:
        return None, "tempo changes"
    onsets = [e["onset"] for e in annotations["melody"] + annotations["harmony"]]
    if min(onsets) > 0:
        return None, "incomplete first measure"
    if annotations["num_beats"] % 4 != 0:
        return None, "incomplete last measure"
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
        "hookpad_url": f"{HOOKPAD}?idOfSong={example['hooktheory']['id']}&enableYouTube=true",
        **audio_fields(example),
        "melody": sorted(melody),
        "chords": sorted(chords, key=lambda chord: chord[0]),
    }, "kept"


def pretty_json(data: dict) -> str:
    """Indented JSON for perusing in a text editor, but with each [beat, value] event on
    one line, rather than one line per number."""
    text = json.dumps(data, indent=2)
    return re.sub(r"\[\s+([^\[\]{}]*?)\s+\]",
                  lambda m: "[" + re.sub(r",\s+", ", ", m.group(1)) + "]", text)


def main() -> None:
    with gzip.open(RAW, "rt") as f:
        dataset = json.load(f)
    simple, reasons = {}, Counter()
    for hooktheory_id, example in dataset.items():
        result, reason = simplify(example)
        reasons[reason] += 1
        if result is not None:
            simple[hooktheory_id] = result
    text = pretty_json(simple)
    assert json.loads(text) == simple
    with gzip.open(OUTPUT, "wt", compresslevel=9) as f:
        f.write(text + "\n")

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
