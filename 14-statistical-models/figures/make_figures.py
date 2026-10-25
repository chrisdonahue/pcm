"""Generate figures and sound examples for Chapter 14 (statistical models).

Outputs are written to ../assets/. This file is *not* student-facing.

Sources:

- Five sung vowels from Freesound (368725-368729 by antoinevg, CC0), read from
  pyquist's default cache (~/.cache/pyquist) and fetched with pyquist's
  Freesound client if missing, which needs an API key (NEVER copy credentials
  into the repo). Previews only (the originals need OAuth).
- ../raw/: the Bach prelude and Super Mario Bros. MIDI files, and the EMI
  "musical Turing test" recordings (real and fake Bartok and Joplin), trimmed
  to excerpts with ffmpeg (which must be on PATH).
- The Musikalisches Wurfelspiel (K.516f) bars and lookup table, see DICE_DATA.

Run with the project virtualenv (pyquist reached via PYTHONPATH):
    PYTHONPATH=../../../pyquist python make_figures.py
"""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pyquist as pq
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle
from pyquist.web.freesound import fetch_freesound
from scipy.signal import lfilter

HERE = Path(__file__).resolve().parent
CHAPTER = HERE.parent
ASSETS = CHAPTER / "assets"
RAW = CHAPTER / "raw"
ASSETS.mkdir(exist_ok=True)

F_S = 44100
PEAK_DBFS = -6.0

plt.rcParams.update({
    "font.size": 14, "axes.labelsize": 16, "xtick.labelsize": 13,
    "ytick.labelsize": 13, "axes.spines.top": False, "axes.spines.right": False,
    "lines.linewidth": 2.0,
})
COLORS = plt.rcParams["axes.prop_cycle"].by_key()["color"]
BLUE, ORANGE, GREEN, RED, PURPLE = COLORS[0], COLORS[1], COLORS[2], COLORS[3], COLORS[4]

# Freesound ID: vowel. "Male voice singing the vowel ... at 110 Hz", by antoinevg, CC0.
VOWELS = {368728: "a", 368727: "e", 368726: "i", 368725: "o", 368729: "u"}

MIDI_FILES = {"Bach prelude.MID": "bach-prelude.mid",
              "Mario Bros. - Super Mario Bros. Theme.mid": "mario.mid"}

# The musical Turing test: (source, asset). Which excerpt is "A" and which is "B"
# is deliberately mixed up, so students can't guess from the order. The answers:
# Bartok A = real (Allegro barbaro), B = EMI (Kosmos, after Bartok);
# Joplin A = EMI (Rag, after Joplin), B = real (Weeping Willow).
EMI = {"EMI/Bartok/bartok_real.mp3": "audio-turing-bartok-a.mp3",
       "EMI/Bartok/bartok_fake.mp3": "audio-turing-bartok-b.mp3",
       "EMI/Joplin/joplin_fake.mp3": "audio-turing-joplin-a.mp3",
       "EMI/Joplin/joplin_real.mp3": "audio-turing-joplin-b.mp3"}
EMI_SECONDS = 30.0

# The Musikalisches Wurfelspiel (K.516f, now catalogued as K.Anh.C.30.01): the 11 x 16
# lookup table and the notes of its 176 bars, following the 1793 Simrock print. Based
# on Craig Sapp, Daniel Shanahan, and Mauricio Rodriguez's Humdrum encoding
# (https://github.com/craigsapp/Musikalisches-Wuerfelspiel, which has no license
# statement), corrected against scans of the Simrock print (IMSLP #20432, public domain).
# The full extraction, with notes on sources, variants, and ornaments, is in
# ../raw/mozart-dice-full.json.
DICE_DATA = RAW / "mozart-dice-full.json"

# The first phrase of Twinkle, Twinkle, Little Star, and the whole song.
TWINKLE = [60, 60, 67, 67, 69, 69, 67]
TWINKLE_SONG = (TWINKLE + [65, 65, 64, 64, 62, 62, 60]
                + [67, 67, 65, 65, 64, 64, 62] * 2
                + TWINKLE + [65, 65, 64, 64, 62, 62, 60])
NAMES = {60: "C", 62: "D", 64: "E", 65: "F", 67: "G", 69: "A"}


def save_fig(name: str) -> None:
    plt.tight_layout()
    plt.savefig(ASSETS / name, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  wrote {name}")


def write_audio(x: np.ndarray, name: str, peak_dbfs: float = PEAK_DBFS) -> None:
    audio = pq.Audio(np.asarray(x, dtype=np.float32), F_S)
    audio.normalize(peak_dbfs=peak_dbfs)
    audio.write(str(ASSETS / name))
    print(f"  wrote {name}")


# ---------------------------------------------------------------------------
# Algorithm mirrors (keep in sync with the notebooks)
# ---------------------------------------------------------------------------


def lpc(x: np.ndarray, K: int) -> np.ndarray:
    """The coefficients h_1, ..., h_K that best predict x[n] from x[n-1], ..., x[n-K]."""
    N = len(x)
    X = np.stack([x[K - k:N - k] for k in range(1, K + 1)], axis=1)
    h, *_ = np.linalg.lstsq(X, x[K:], rcond=None)
    return h


def pulse_train(f0: float, duration: float, f_s: int = F_S) -> np.ndarray:
    e = np.zeros(int(duration * f_s))
    e[::round(f_s / f0)] = 1.0
    return e


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------


def prepare_sources() -> None:
    for fsid, vowel in VOWELS.items():
        audio, _ = fetch_freesound(fsid)
        x = np.asarray(audio.as_mono().samples)[:, 0]
        assert audio.sample_rate == F_S
        write_audio(x, f"vowel-{vowel}.wav")
    for source, name in MIDI_FILES.items():
        shutil.copy(RAW / source, ASSETS / name)
        print(f"  wrote {name}")
    for source, name in EMI.items():
        excerpt(RAW / source, ASSETS / name, EMI_SECONDS)
    prepare_dice()
    write_twinkle_midi()


def write_twinkle_midi() -> None:
    """All six phrases of Twinkle, Twinkle, Little Star: six quarter notes and a half note
    each, at 120 BPM."""
    import mido
    ticks = 480                                   # ticks per quarter note
    track = mido.MidiTrack([mido.MetaMessage("set_tempo", tempo=500_000, time=0)])
    for i, pitch in enumerate(TWINKLE_SONG):
        length = 2 * ticks if i % 7 == 6 else ticks
        track.append(mido.Message("note_on", note=pitch, velocity=80, time=0))
        track.append(mido.Message("note_off", note=pitch, velocity=0, time=length))
    midi = mido.MidiFile(ticks_per_beat=ticks)
    midi.tracks.append(track)
    midi.save(str(ASSETS / "twinkle.mid"))
    print("  wrote twinkle.mid")


def excerpt(source: Path, destination: Path, seconds: float) -> None:
    """The first `seconds` of a recording (after any leading silence), faded out,
    peak-normalized to PEAK_DBFS, as a mono 128 kbps MP3."""
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "excerpt.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(source),
                        "-af", "silenceremove=start_periods=1:start_threshold=-50dB",
                        "-t", str(seconds), "-ac", "1", "-ar", str(F_S), str(wav)], check=True)
        audio = pq.Audio.from_file(str(wav))
        x = np.asarray(audio.samples)[:, 0].astype(np.float64)
        fade = int(2.0 * F_S)
        x[-fade:] *= np.linspace(1.0, 0.0, fade)
        x *= 10 ** (PEAK_DBFS / 20) / np.abs(x).max()
        pq.Audio(x.astype(np.float32), F_S).write(str(wav))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
                        "-b:a", "128k", str(destination)], check=True)
    print(f"  wrote {destination.name}")


def audio_vowel_lpc() -> None:
    """The vowel /a/, resynthesized from its LPC filter and a 110 Hz pulse train."""
    x = np.asarray(pq.Audio.from_file(str(ASSETS / "vowel-a.wav")).samples)[:, 0].astype(np.float64)
    h = lpc(x[F_S:F_S + F_S // 2], K=40)
    y = lfilter([1.0], np.concatenate([[1.0], -h]), pulse_train(110.0, 3.0))
    ramp = int(0.05 * F_S)
    y[:ramp] *= np.linspace(0.0, 1.0, ramp)
    y[-ramp:] *= np.linspace(1.0, 0.0, ramp)
    write_audio(y, "audio-vowel-a-lpc.wav")


# ---------------------------------------------------------------------------
# Notation
# ---------------------------------------------------------------------------

LILY_TWINKLE = r"""
\version "2.24.0"
\header { tagline = ##f }
\score {
  <<
    \new Staff \with { \remove "Time_signature_engraver" } {
      \clef treble \time 4/4 c'4 c' g' g' a' a' g'2 }
    \addlyrics { C C G G A A G }
    \addlyrics { "60" "60" "67" "67" "69" "69" "67" }
  >>
  \layout { \context { \Lyrics \override LyricText.font-size = #-1.5 } }
}
"""


def render_lilypond(source: str, name: str) -> None:
    if shutil.which("lilypond") is None:
        print(f"  SKIP {name}: lilypond not found on PATH")
        return
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "score.ly").write_text(source)
        subprocess.run(["lilypond", "--png", "-dresolution=200", "-dcrop", "-o", "score", "score.ly"],
                       cwd=tmp, check=True, capture_output=True)
        shutil.copy(Path(tmp) / "score.cropped.png", ASSETS / name)
    print(f"  wrote {name}")


# ---------------------------------------------------------------------------
# Probability
# ---------------------------------------------------------------------------


def fig_dice_sums() -> None:
    """The distribution of the sum of two fair dice."""
    sums = np.arange(2, 13)
    p = (6 - np.abs(sums - 7)) / 36
    plt.figure(figsize=(10, 3.6))
    plt.bar(sums, p, color=BLUE, width=0.7)
    for s, q in zip(sums, p):
        plt.text(s, q + 0.004, f"{round(36 * q)}/36", ha="center", va="bottom", fontsize=12)
    plt.xticks(sums)
    plt.xlabel("Sum of two dice, $s$")
    plt.ylabel("$P(S = s)$")
    plt.ylim(0, 0.2)
    save_fig("fig-dice-sums.png")


LILY_NAMES = ["c", "cis", "d", "dis", "e", "f", "fis", "g", "gis", "a", "ais", "b"]
LILY_DURATIONS = {0.25: "32", 0.5: "16", 0.75: "16.", 1.0: "8", 1.5: "8.", 2.0: "4", 3.0: "4."}


def lily_pitch(pitch: int) -> str:
    octave = pitch // 12 - 4                     # c' is MIDI 60
    return LILY_NAMES[pitch % 12] + ("'" * octave if octave > 0 else "," * -octave)


def lily_staff(notes: list[dict]) -> str:
    """One staff of a 3/8 bar in LilyPond notation: chords for simultaneous notes,
    and rests for gaps."""
    onsets = sorted({n["onset"] for n in notes})
    music, t = [], 0.0
    for onset in onsets:
        if onset > t:
            music.append("r" + LILY_DURATIONS[onset - t])
        chord = [n for n in notes if n["onset"] == onset]
        duration = min(n["duration"] for n in chord)
        pitches = " ".join(lily_pitch(n["pitch"]) for n in sorted(chord, key=lambda n: n["pitch"]))
        music.append(f"<{pitches}>" + LILY_DURATIONS[duration])
        t = onset + duration
    if t < 3.0:
        music.append("r" + LILY_DURATIONS[3.0 - t])
    return " ".join(music)


def lily_bar(notes: list[dict]) -> str:
    treble = lily_staff([n for n in notes if n["staff"] == "treble"])
    bass = lily_staff([n for n in notes if n["staff"] == "bass"])
    return r"""
\version "2.24.0"
\header { tagline = ##f }
\paper { indent = 0 }
\score {
  \new PianoStaff <<
    \new Staff \with { \remove "Time_signature_engraver" } { \clef treble \time 3/8 TREBLE \bar "|" }
    \new Staff \with { \remove "Time_signature_engraver" } { \clef bass \time 3/8 BASS \bar "|" }
  >>
  \layout { }
}
""".replace("TREBLE", treble).replace("BASS", bass)


PIPS = {1: [(0, 0)], 2: [(-1, 1), (1, -1)], 3: [(-1, 1), (0, 0), (1, -1)],
        4: [(-1, 1), (1, 1), (-1, -1), (1, -1)], 5: [(-1, 1), (1, 1), (0, 0), (-1, -1), (1, -1)],
        6: [(-1, 1), (1, 1), (-1, 0), (1, 0), (-1, -1), (1, -1)]}


def _die(ax, x: float, y: float, value: int, size: float = 0.27) -> None:
    """A die showing `value`, centered at (x, y)."""
    from matplotlib.patches import FancyBboxPatch
    half = size / 2
    ax.add_patch(FancyBboxPatch((x - half, y - half), size, size, boxstyle="round,pad=0,rounding_size=0.05",
                                facecolor="white", edgecolor="0.3", lw=1.2, zorder=2))
    for px, py in PIPS[value]:
        ax.add_patch(Circle((x + px * 0.27 * size, y + py * 0.27 * size), 0.075 * size,
                            color="0.15", zorder=3))


def fig_dice_game() -> None:
    """The first three measures of the dice game, for dice sums 2, 3, and 4, with the
    path of one roll of the dice."""
    from matplotlib.image import imread
    data = json.loads((ASSETS / "mozart-dice.json").read_text())
    sums, measures, path = [2, 3, 4], [0, 1, 2], {0: 4, 1: 2, 2: 3}
    images = {}
    with tempfile.TemporaryDirectory() as tmp:
        for s in sums:
            for m in measures:
                bar = data["table"][str(s)][m]
                (Path(tmp) / "bar.ly").write_text(lily_bar(data["bars"][str(bar)]))
                subprocess.run(["lilypond", "--png", "-dresolution=220", "-dcrop", "-o", "bar", "bar.ly"],
                               cwd=tmp, check=True, capture_output=True)
                images[s, m] = imread(str(Path(tmp) / "bar.cropped.png"))
    fig = plt.figure(figsize=(12.8, 7.0))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 12.8)
    ax.set_ylim(0, 7.0)
    ax.axis("off")
    col_x = {0: 2.55, 1: 6.0, 2: 9.45}
    row_y = {2: 5.3, 3: 3.35, 4: 1.4}
    height = 1.45
    boxes = {}
    for s in sums:
        pairs = [(a, s - a) for a in range(1, 7) if 1 <= s - a <= 6]   # the rolls that sum to s
        for k, (a, b) in enumerate(pairs):
            y = row_y[s] + (len(pairs) - 1 - 2 * k) * 0.19
            _die(ax, 0.3, y, a)
            _die(ax, 0.63, y, b)
        ax.text(2.0, row_y[s] + 0.2, f"$S = {s}$", ha="right", va="center", fontsize=16, color="0.2")
        ax.text(2.0, row_y[s] - 0.25, f"{round(100 * (6 - abs(s - 7)) / 36)}%", ha="right",
                va="center", fontsize=13, color="0.45")
    for m in measures:
        widths = []
        for s in sums:
            img = images[s, m]
            h, w = img.shape[:2]
            width = height * w / h
            widths.append(width)
            x0, y0 = col_x[m], row_y[s] - height / 2
            ax.imshow(img, extent=(x0, x0 + width, y0, y0 + height), zorder=2)
            chosen = path[m] == s
            ax.add_patch(Rectangle((x0 - 0.08, y0 - 0.08), width + 0.16, height + 0.16, fill=False,
                                   lw=2.5 if chosen else 1.0, edgecolor=RED if chosen else "0.75",
                                   zorder=3))
            boxes[m, s] = (x0 - 0.08, x0 + width + 0.08, row_y[s])
        center = col_x[m] + max(widths) / 2
        ax.text(center, 6.65, f"Measure {m + 1}", ha="center", va="center", fontsize=17,
                fontweight="bold", color="0.3")
        ax.text(center, 0.3, "...", ha="center", va="center", fontsize=20, color="0.5")
    ax.text(12.35, 3.35, "...", ha="center", va="center", fontsize=20, color="0.5")
    for m in measures[:-1]:
        _, x_start, y_start = boxes[m, path[m]]
        x_end, _, y_end = boxes[m + 1, path[m + 1]]
        ax.add_patch(FancyArrowPatch((x_start + 0.05, y_start), (x_end - 0.05, y_end),
                                     arrowstyle="-|>", mutation_scale=18, lw=2, color=RED,
                                     linestyle="--", zorder=4))
    save_fig("fig-dice-game.png")


def prepare_dice() -> None:
    """The table and bars for the widget. The widget plays the waltz straight through,
    without repeating its first half, so the bars at position 8 use their second ending."""
    data = json.loads(DICE_DATA.read_text())
    bars = dict(data["bars"])
    bars.update(data["second_endings"])
    out = {"table": data["table"], "bars": bars, "time_signature": data["time_signature"],
           "source": "Musikalisches Wurfelspiel (Simrock, Bonn, 1793). Encoding based on "
                     "github.com/craigsapp/Musikalisches-Wuerfelspiel, corrected to the print."}
    (ASSETS / "mozart-dice.json").write_text(json.dumps(out, separators=(",", ":")))
    print("  wrote mozart-dice.json")


# ---------------------------------------------------------------------------
# Markov chains
# ---------------------------------------------------------------------------

R_STATE = 0.32
ZERO = "0.65"                    # transitions with probability 0, as in the matrices


def _state(ax, xy, label: str) -> None:
    ax.add_patch(Circle(xy, R_STATE, facecolor="#eeeeee", edgecolor=BLUE, lw=2.5, zorder=3))
    ax.text(xy[0], xy[1], label, ha="center", va="center", fontsize=24, zorder=4)


def _edge(ax, p, q, label: str, offset: float = 0.09, label_offset: float = 0.22) -> None:
    """A straight arrow from state p to state q, shifted to the right of its direction
    so that the opposite arrow doesn't overlap it."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    d = (q - p) / np.linalg.norm(q - p)
    right = np.array([d[1], -d[0]])
    start = p + d * (R_STATE + 0.03) + right * offset
    end = q - d * (R_STATE + 0.03) + right * offset
    color = ZERO if label == "0" else ORANGE
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=20, lw=2,
                                 color=color, zorder=2))
    mid = (start + end) / 2 + right * label_offset
    ax.text(mid[0], mid[1], label, ha="center", va="center", fontsize=17, color=color)


def _loop(ax, xy, label: str, angle: float) -> None:
    """A self-loop on the outside of a state, centered at `angle` degrees."""
    a = np.deg2rad(angle)
    xy = np.asarray(xy, float)
    start = xy + R_STATE * np.array([np.cos(a + 0.5), np.sin(a + 0.5)])
    end = xy + R_STATE * np.array([np.cos(a - 0.5), np.sin(a - 0.5)])
    color = ZERO if label == "0" else ORANGE
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=18, lw=2,
                                 color=color, connectionstyle="arc3,rad=-1.9", zorder=2))
    pos = xy + (R_STATE + 0.52) * np.array([np.cos(a), np.sin(a)])
    ax.text(pos[0], pos[1], label, ha="center", va="center", fontsize=17, color=color)


def _matrix(ax, labels: list[str], cells: list[list[str]]) -> None:
    """A transition matrix as a table: rows are the previous state, columns the next."""
    n = len(labels)
    for i in range(n):
        for j in range(n):
            zero = cells[i][j] == "0"
            ax.add_patch(Rectangle((j, n - 1 - i), 1, 1, facecolor="white", edgecolor="0.6", lw=1.2))
            ax.text(j + 0.5, n - 0.5 - i, cells[i][j], ha="center", va="center", fontsize=20,
                    color=ZERO if zero else ORANGE)
        ax.text(-0.35, n - 0.5 - i, labels[i], ha="center", va="center", fontsize=20, color=BLUE)
        ax.text(i + 0.5, n + 0.35, labels[i], ha="center", va="center", fontsize=20, color=BLUE)
    ax.text(n / 2, n + 0.95, "Next state", ha="center", va="center", fontsize=15, color="0.35")
    ax.text(-0.95, n / 2, "Previous state", ha="center", va="center", fontsize=15,
            color="0.35", rotation=90)
    ax.set_xlim(-1.3, n + 0.1)
    ax.set_ylim(-0.1, n + 1.3)
    ax.set_aspect("equal")
    ax.axis("off")


def fig_markov_two_state() -> None:
    """A two-state Markov chain, as a graph and as a transition matrix."""
    fig, (axg, axm) = plt.subplots(1, 2, figsize=(11, 3.8), gridspec_kw={"width_ratios": [1.5, 1]})
    c, g = (0.0, 0.0), (1.9, 0.0)
    _state(axg, c, "C")
    _state(axg, g, "G")
    _edge(axg, c, g, r"$\dfrac{2}{3}$")
    _edge(axg, g, c, r"$1$")
    _loop(axg, c, r"$\dfrac{1}{3}$", 180)
    _loop(axg, g, "0", 0)
    axg.set_xlim(-1.3, 3.2)
    axg.set_ylim(-0.9, 0.9)
    axg.set_aspect("equal")
    axg.axis("off")
    _matrix(axm, ["C", "G"], [[r"$\dfrac{1}{3}$", r"$\dfrac{2}{3}$"], [r"$1$", "0"]])
    save_fig("fig-markov-two-state.png")


def fig_markov_twinkle() -> None:
    """The Markov chain fit to the first phrase of Twinkle, Twinkle, Little Star."""
    fig, (axg, axm) = plt.subplots(1, 2, figsize=(12, 5.2), gridspec_kw={"width_ratios": [1.25, 1]})
    pos = {"C": (0.0, 1.55), "G": (-0.95, 0.0), "A": (0.95, 0.0)}
    for name, xy in pos.items():
        _state(axg, xy, name)
    half = r"$\dfrac{1}{2}$"
    _edge(axg, pos["C"], pos["G"], half)
    _edge(axg, pos["G"], pos["A"], half)
    _edge(axg, pos["A"], pos["G"], half)
    _edge(axg, pos["G"], pos["C"], "0")
    _edge(axg, pos["C"], pos["A"], "0")
    _edge(axg, pos["A"], pos["C"], "0")
    _loop(axg, pos["C"], half, 90)
    _loop(axg, pos["G"], half, 215)
    _loop(axg, pos["A"], half, -35)
    axg.set_xlim(-2.1, 2.1)
    axg.set_ylim(-0.95, 2.6)
    axg.set_aspect("equal")
    axg.axis("off")
    _matrix(axm, ["C", "G", "A"], [[half, half, "0"], ["0", half, half], ["0", half, half]])
    save_fig("fig-markov-twinkle.png")


# ---------------------------------------------------------------------------
# n-grams
# ---------------------------------------------------------------------------


def fig_ngram_sparsity() -> None:
    """Bigram and trigram counts of the whole of Twinkle, Twinkle, Little Star."""
    states = sorted(set(TWINKLE_SONG))
    idx = [states.index(p) for p in TWINKLE_SONG]
    S = len(states)
    bigrams = np.zeros((S, S))
    for a, b in zip(idx[:-1], idx[1:]):
        bigrams[a, b] += 1
    trigrams = np.zeros((S, S, S))
    for a, b, c in zip(idx[:-2], idx[1:-1], idx[2:]):
        trigrams[a, b, c] += 1
    trigrams = trigrams.reshape(S * S, S)
    names = [NAMES[p] for p in states]
    print(f"  bigrams: {int((bigrams > 0).sum())} of {bigrams.size} nonzero; "
          f"trigrams: {int((trigrams > 0).sum())} of {trigrams.size} nonzero")

    from matplotlib.colors import ListedColormap
    fig, (ax2, ax3) = plt.subplots(1, 2, figsize=(11, 9), gridspec_kw={"width_ratios": [1, 1]})
    for ax, counts, rows in [(ax2, bigrams, names),
                             (ax3, trigrams, [f"{a} {b}" for a in names for b in names])]:
        ax.imshow(counts > 0, cmap=ListedColormap(["white", "#FDE6CF"]), vmin=0, vmax=1,
                  aspect="equal")
        for (i, j), count in np.ndenumerate(counts):
            if count:
                ax.text(j, i, int(count), ha="center", va="center", color=ORANGE,
                        fontsize=11 if ax is ax3 else 15)
        ax.xaxis.tick_top()
        ax.xaxis.set_label_position("top")
        ax.set_xticks(range(S), names, color=BLUE)
        ax.set_yticks(range(len(rows)), rows, fontsize=10 if ax is ax3 else 13, color=BLUE)
        ax.set_xticks(np.arange(-0.5, S), minor=True)
        ax.set_yticks(np.arange(-0.5, len(rows)), minor=True)
        ax.grid(which="minor", color="0.75", lw=0.8)
        ax.tick_params(which="both", length=0)
        ax.set_xlabel("Next pitch", color="0.35")
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_color("0.6")
    ax2.set_ylabel("Previous pitch", color="0.35")
    ax3.set_ylabel("Previous two pitches", color="0.35")
    save_fig("fig-ngram-sparsity.png")


# ---------------------------------------------------------------------------
# Linear predictive coding
# ---------------------------------------------------------------------------


def fig_lpc_vowels() -> None:
    """The spectra of the five vowels, and the frequency responses of their LPC filters."""
    n = 1 << 15
    f = np.fft.rfftfreq(n, 1 / F_S)
    fig, axes = plt.subplots(5, 1, figsize=(12, 11), sharex=True)
    for ax, color, vowel in zip(axes, [RED, ORANGE, GREEN, BLUE, PURPLE], "aeiou"):
        x = np.asarray(pq.Audio.from_file(str(ASSETS / f"vowel-{vowel}.wav")).samples)[:, 0]
        x = x[F_S:F_S + F_S // 2].astype(np.float64)
        h = lpc(x, K=40)
        spectrum = 20 * np.log10(np.abs(np.fft.rfft(x * np.hanning(len(x)), n)) + 1e-12)
        response = -20 * np.log10(np.abs(np.fft.rfft(np.concatenate([[1.0], -h]), n)))
        band = f <= 4000
        response += (spectrum[band] - response[band]).max()   # rest on the tallest harmonic
        top = response[band].max()
        ax.plot(f, spectrum - top, color="0.7", lw=0.8)
        ax.plot(f, response - top, color=color, lw=2.4)
        ax.text(3950, -10, vowel.upper(), ha="right", va="center", fontsize=20, color=color)
        ax.set_ylim(-75, 4)
        ax.set_yticks([-60, -30, 0])
    axes[-1].set_xlim(0, 4000)
    axes[-1].set_xlabel("Frequency (Hz)")
    axes[2].set_ylabel("Magnitude (dB)")
    save_fig("fig-lpc-vowels.png")


if __name__ == "__main__":
    print("Sources:")
    prepare_sources()
    print("Sound examples:")
    audio_vowel_lpc()
    print("Figures:")
    render_lilypond(LILY_TWINKLE, "fig-twinkle.png")
    fig_dice_sums()
    fig_dice_game()
    fig_markov_two_state()
    fig_markov_twinkle()
    fig_ngram_sparsity()
    fig_lpc_vowels()
