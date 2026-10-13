"""Generate figures and sound examples for Chapter 11 (sample-based synthesis).

Outputs are written to ../assets/. This file is *not* student-facing.

Sources:

- ../raw/amen.wav, the Amen break, normalized and copied to assets/amen.wav.
- ../raw/356904__mtg__clarinet-asharp5.wav, the running example: an A#5 on a
  clarinet (Freesound 356904 by MTG, CC BY 3.0). It is trimmed, fine-tuned to
  exactly A#5 (the recording is about 31 cents sharp), normalized, and written
  to assets/clarinet.wav. WAV matters: the in-browser runtime can only decode
  WAV, and the chapter's notebooks run in the browser.
- Freesound sounds, fetched with pyquist's Freesound client. Fetching needs a
  Freesound API key cached in pyquist's default cache (~/.cache/pyquist), so
  this script must run once on a machine with credentials. It
    * copies the drum sounds used by notebooks/drum-machine.ipynb into
      assets/freesound/<id>/ (metadata.json and the preview only, NEVER any
      credentials), so the notebook can load them offline, and
    * draws two more clarinet notes from the same MTG pack in the grid of
      recorded pitches and durations.
"""

import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pyquist as pq
import soxr
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, Rectangle
from numpy.lib.stride_tricks import sliding_window_view
from pyquist.helper import pitch_name_to_pitch, pitch_to_frequency
from pyquist.web.freesound import fetch_freesound
from pyquist.paths import CACHE_DIR

HERE = Path(__file__).resolve().parent
CHAPTER = HERE.parent
ASSETS = CHAPTER / "assets"
ASSETS.mkdir(exist_ok=True)

F_S = 44100
PEAK_DBFS = -6.0

# Freesound IDs.
DRUMS = {"hats": 399897, "snare": 46709, "kick": 673512}

CLARINET_RAW = CHAPTER / "raw" / "356904__mtg__clarinet-asharp5.wav"
CLARINET_PITCH = "A#5"
F0 = pitch_to_frequency(pitch_name_to_pitch(CLARINET_PITCH))

# The clarinet's phases (seconds into assets/clarinet.wav), read off its amplitude.
PHASES = {"Attack": (0.0, 0.14), "Decay": (0.14, 0.32), "Sustain": (0.32, 3.85),
          "Release": (3.85, 4.70)}
# The sustain loop and the jump to the release, in audio samples, as found by
# find_loop_points() below (the notebooks and code/sampler.py hardcode them in
# seconds). Assuming whole periods of the nominal A#5 does NOT work: the
# clarinet's pitch drifts slightly, so the seams clicked audibly. The jump to
# the release lands a bit before the release itself, because just before the
# release the clarinet briefly gets brighter, and jumping there from the loop
# changed the tone audibly.
LOOP_START_N, LOOP_END_N, RELEASE_N = 25878, 33821, 146472
LOOP_START, LOOP_END, RELEASE = LOOP_START_N / F_S, LOOP_END_N / F_S, RELEASE_N / F_S
SEAM = int(0.005 * F_S)                          # compare +/- 5 ms around each splice

plt.rcParams.update(
    {
        "font.size": 14,
        "axes.labelsize": 16,
        "xtick.labelsize": 13,
        "ytick.labelsize": 13,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "lines.linewidth": 2.0,
    }
)
COLORS = plt.rcParams["axes.prop_cycle"].by_key()["color"]
BLUE, ORANGE, GREEN, RED, PURPLE = COLORS[0], COLORS[1], COLORS[2], COLORS[3], COLORS[4]
GOLD = "#C9A227"


def save_fig(name: str) -> None:
    plt.tight_layout()
    plt.savefig(ASSETS / name, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  wrote {name}")


def write_audio(samples: np.ndarray, name: str, peak: float = PEAK_DBFS) -> None:
    audio = pq.Audio(samples.astype(np.float32), F_S)
    audio.normalize(peak_dbfs=peak)
    audio.write(str(ASSETS / name))
    print(f"  wrote {name}")


def fade(x: np.ndarray, in_s: float = 0.002, out_s: float = 0.002) -> np.ndarray:
    """Short linear fades so a cut-out clip starts and ends without clicks."""
    x = x.copy()
    n_in, n_out = int(in_s * F_S), int(out_s * F_S)
    if n_in:
        x[:n_in] *= np.linspace(0.0, 1.0, n_in)
    if n_out:
        x[-n_out:] *= np.linspace(1.0, 0.0, n_out)
    return x


# ---------------------------------------------------------------------------
# The algorithms (mirrors of code/sampler.py, the student-facing versions)
# ---------------------------------------------------------------------------


def resample(x: np.ndarray, ratio: float) -> np.ndarray:
    """Read x at `ratio` times its original speed with linear interpolation."""
    N = len(x)
    M = int(N / ratio)
    p = np.arange(M) * ratio
    p_floor = np.floor(p).astype(int)
    alpha = p - p_floor
    nxt = np.minimum(p_floor + 1, N - 1)
    return (1 - alpha) * x[p_floor] + alpha * x[nxt]


def repitch(x: np.ndarray, k: float) -> np.ndarray:
    """Shift by k steps: read 2^(k/12) times as fast."""
    return resample(x, 2.0 ** (k / 12.0))


# ---------------------------------------------------------------------------
# Source preparation
# ---------------------------------------------------------------------------


def fetch(fsid: int) -> pq.Audio:
    """Fetch a Freesound preview through pyquist's DEFAULT cache (credentials)."""
    audio, _ = fetch_freesound(fsid)
    return audio


def measure_f0(x: np.ndarray, sr: int, f_nominal: float) -> float:
    """Median autocorrelation pitch over the steady middle of a note."""
    win = int(0.08 * sr)
    lo, hi = int(sr / (1.5 * f_nominal)), int(sr / (0.67 * f_nominal))
    f0s = []
    for start in range(int(0.3 * len(x)), int(0.7 * len(x)) - win, win // 2):
        seg = x[start:start + win] - x[start:start + win].mean()
        ac = np.correlate(seg, seg, "full")[win - 1:]
        lag = lo + np.argmax(ac[lo:hi])
        a, b, c = ac[lag - 1], ac[lag], ac[lag + 1]
        f0s.append(sr / (lag + 0.5 * (a - c) / (a - 2 * b + c)))   # parabolic refine
    return float(np.median(f0s))


def prepare_note(audio: pq.Audio, name: str) -> np.ndarray:
    """Mono, 44.1 kHz, trimmed, tuned to exact pitch, normalized."""
    x = np.asarray(audio.as_mono().samples, dtype=np.float64).reshape(-1)
    x = soxr.resample(x, audio.sample_rate, F_S)
    k = int(0.01 * F_S)
    env = np.sqrt(np.convolve(x ** 2, np.ones(k) / k, mode="same"))
    on = int(np.argmax(env > 0.02 * env.max()))
    off = len(env) - int(np.argmax(env[::-1] > 0.002 * env.max()))
    x = x[max(0, on - int(0.005 * F_S)):off + int(0.05 * F_S)]
    f_nominal = pitch_to_frequency(pitch_name_to_pitch(name))
    f0 = measure_f0(x, F_S, f_nominal)
    ratio = f_nominal / f0                        # > 1 raises the pitch
    # Reading `ratio` times faster: pretend x was recorded at F_S * ratio.
    x = soxr.resample(x, F_S * ratio, F_S)
    cents = 1200 * np.log2(f0 / f_nominal)
    print(f"  {name}: measured {f0:.2f} Hz ({cents:+.1f} cents), retuned to {f_nominal:.2f} Hz")
    x = fade(x, 0.003, 0.02)
    return 10 ** (PEAK_DBFS / 20) * x / np.abs(x).max()


def prepare_sources() -> np.ndarray:
    # The Amen break (normalized copy; stays stereo).
    amen = pq.Audio.from_file(str(CHAPTER / "raw" / "amen.wav"))
    amen.normalize(peak_dbfs=PEAK_DBFS)
    amen.write(str(ASSETS / "amen.wav"))
    print("  wrote amen.wav")

    # Drum sounds: copy only the cached metadata and preview into assets.
    for fsid in DRUMS.values():
        fetch(fsid)                                  # populate the default cache
        src, dst = CACHE_DIR / "freesound" / str(fsid), ASSETS / "freesound" / str(fsid)
        dst.mkdir(parents=True, exist_ok=True)
        for fname in ("metadata.json", "preview-hq.ogg"):
            shutil.copyfile(src / fname, dst / fname)
        print(f"  cached freesound/{fsid}")

    # The running example.
    clarinet = prepare_note(pq.Audio.from_file(str(CLARINET_RAW)), CLARINET_PITCH)
    pq.Audio(clarinet.astype(np.float32), F_S).write(str(ASSETS / "clarinet.wav"))
    clarinet = np.asarray(pq.Audio.from_file(str(ASSETS / "clarinet.wav")).samples,
                          dtype=np.float64).reshape(-1)
    print("  wrote clarinet.wav")
    return clarinet


# ---------------------------------------------------------------------------
# Sampling vs. synthesis: additive synthesis vs. the real clarinet
# ---------------------------------------------------------------------------


def additive_clarinet(T: float) -> np.ndarray:
    """An attempt at the clarinet note with Chapters 3 and 4: a two-harmonic
    wavetable at A#5, read with truncating lookup, times a piecewise-linear
    envelope fit by eye to the recording."""
    M = 1024
    m = np.arange(M)[:, np.newaxis]
    table = (np.array([5500, 1500]) * np.sin(2 * np.pi * np.array([1, 2]) * m / M)).sum(axis=1)
    table /= np.abs(table).max()
    n = np.arange(int(T * F_S))
    x = table[(n * M * F0 / F_S).astype(int) % M]
    env = np.interp(n / F_S, [0.0, 0.1, 0.2, 3.8, 4.8], [0.0, 0.3, 0.25, 0.25, 0.0])
    return x * env


def fig_waveform(x: np.ndarray, name: str, color: str) -> None:
    """A whole note (top) above a 5 ms close-up of its waveform (bottom)."""
    t = np.arange(len(x)) / F_S
    fig, (ax, ax_zoom) = plt.subplots(2, 1, figsize=(6.4, 4.6),
                                      gridspec_kw={"height_ratios": [2.0, 1.3]})
    ax.plot(t, x, color=color, lw=0.4)
    ax.set_xlim(0, 4.95)
    ax.set_ylim(-0.55, 0.55)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    i = int(2.0 * F_S)
    ax_zoom.plot((t[i:i + int(0.005 * F_S)] - t[i]) * 1000, x[i:i + int(0.005 * F_S)],
                 color=color, lw=1.8)
    ax_zoom.set_xlim(0, 5)
    ax_zoom.set_ylim(-0.55, 0.55)
    ax_zoom.set_xlabel("Time (ms)")
    ax_zoom.set_ylabel("Amplitude")
    save_fig(name)


def fig_and_audio_synthesis_vs_recording(clarinet: np.ndarray) -> None:
    synth = fade(additive_clarinet(len(clarinet) / F_S), 0.0, 0.02)
    synth *= np.abs(clarinet).max() / np.abs(synth).max()
    write_audio(synth, "audio-clarinet-additive.wav")
    fig_waveform(synth, "fig-clarinet-additive.png", BLUE)
    fig_waveform(clarinet, "fig-clarinet-recording.png", RED)


# ---------------------------------------------------------------------------
# The combinatorics of recording every combination of parameters
# ---------------------------------------------------------------------------

GRID_PITCHES = ["G#5", "A5", "A#5", "B5", "C6"]
GRID_DURATIONS = [1, 3, 6, 9]                    # seconds
GRID_SPAN = 9.0                                  # every cell spans 9 seconds


def _schematic_note(duration: float, sampled: bool, rng: np.random.Generator) -> np.ndarray:
    """A schematic waveform, not real audio: an additive-synthesis note with a
    piecewise-linear envelope, or a "recorded" note with a less regular one."""
    t = np.linspace(0.0, GRID_SPAN, 6000)
    if sampled:
        env = np.interp(t, [0, 0.04, 0.15, duration - 0.35, duration], [0, 1.0, 0.8, 0.7, 0.0])
        env *= 1 + 0.07 * np.sin(2 * np.pi * rng.uniform(1.5, 3.0) * t + rng.uniform(0, 6.3))
    else:
        env = np.interp(t, [0, 0.1, 0.2, duration - 0.3, duration], [0, 1.0, 0.85, 0.85, 0.0])
    env[t > duration] = 0.0
    return env * np.sin(2 * np.pi * 37 * t)


def fig_parameter_grid() -> None:
    """Which combinations of pitch and duration can each approach produce?
    Additive synthesis: all of them. Samples: only those that were recorded."""
    rng = np.random.default_rng(3)
    rows, cols = len(GRID_DURATIONS), len(GRID_PITCHES)
    recorded = set(rng.choice(rows * cols, size=3, replace=False).tolist())
    t = np.linspace(0.0, GRID_SPAN, 6000)
    fig, axes = plt.subplots(rows, cols, figsize=(11, 6.0))
    for r, dur in enumerate(GRID_DURATIONS):
        for c, pitch in enumerate(GRID_PITCHES):
            ax = axes[r, c]
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_visible(True)
                spine.set_color("0.75")
            ax.plot(t, 1.1 + 0.9 * _schematic_note(dur, False, rng), color=BLUE, lw=0.4)
            ax.axhline(0.0, color="0.85", lw=0.8)
            if r * cols + c in recorded:
                ax.plot(t, -1.1 + 0.9 * _schematic_note(dur, True, rng), color=RED, lw=0.4)
            else:
                ax.text(GRID_SPAN / 2, -1.1, "?", ha="center", va="center", fontsize=20,
                        color="0.6")
            ax.set_xlim(0, GRID_SPAN)
            ax.set_ylim(-2.2, 2.2)
            if c == 0:
                ax.set_ylabel(f"{dur} s", rotation=0, ha="right", va="center", fontsize=14)
            if r == rows - 1:
                ax.set_xlabel(pitch, fontsize=14)
    fig.supxlabel("Pitch", fontsize=16)
    fig.supylabel("Duration", fontsize=16)
    fig.legend(handles=[Line2D([], [], color=BLUE, lw=3, label="additive synthesis"),
                        Line2D([], [], color=RED, lw=3, label="samples")],
               loc="upper center", ncol=2, fontsize=14, frameon=False,
               bbox_to_anchor=(0.5, 1.06))
    save_fig("fig-parameter-grid.png")


# ---------------------------------------------------------------------------
# Changing pitch via resampling
# ---------------------------------------------------------------------------

REPITCH_TARGETS = ["A#4", "D5", "F5", "A#5", "D6"]


def audio_repitch(clarinet: np.ndarray) -> None:
    for target in REPITCH_TARGETS:
        k = pitch_name_to_pitch(target) - pitch_name_to_pitch(CLARINET_PITCH)
        name = target.replace("#", "s")          # no '#' in asset URLs
        write_audio(fade(repitch(clarinet, k)), f"audio-repitch-{name}.wav")


def fig_repitch_keyboard() -> None:
    """A keyboard from A4 to D6: the A#5 recording (red) is repitched to the
    target keys (blue) by changing its playback speed."""
    lo, hi = pitch_name_to_pitch("A4"), pitch_name_to_pitch("D6")
    black_pcs = {1, 3, 6, 8, 10}
    whites = [p for p in range(lo, hi + 1) if p % 12 not in black_pcs]
    x_of = {p: i for i, p in enumerate(whites)}       # white-key x positions
    targets = {pitch_name_to_pitch(t): t for t in REPITCH_TARGETS}
    src = pitch_name_to_pitch(CLARINET_PITCH)

    def color_of(p: int, default: str) -> str:
        return RED if p == src else (BLUE if p in targets else default)

    def center(p: int) -> float:                      # middle of a key, white or black
        return x_of[p] + 0.5 if p in x_of else x_of[p - 1] + 1.0

    fig, ax = plt.subplots(figsize=(12, 4.6))
    for p in whites:
        color = color_of(p, "white")
        ax.add_patch(Rectangle((x_of[p], 0), 1, 4, facecolor=color, edgecolor="0.25",
                               alpha=0.85 if color != "white" else 1.0, zorder=1))
    for p in range(lo, hi + 1):
        if p % 12 in black_pcs:
            color = color_of(p, "0.15")
            ax.add_patch(Rectangle((x_of[p - 1] + 0.68, 1.55), 0.64, 2.45,
                                   facecolor=color, edgecolor="0.15", zorder=2))
    for p, name in targets.items():
        k = p - src
        label = f"{name}\n(original)" if k == 0 else f"{name}\n$k = {k:+d}$"
        ax.text(center(p), -0.25, label, ha="center", va="top", fontsize=18,
                color=RED if k == 0 else BLUE)
    # The recording, above the keyboard, with arrows to each target key.
    sx, sy = center(src), 6.4
    ax.text(sx, sy, f"recording of {CLARINET_PITCH}", ha="center", va="bottom",
            fontsize=19, color=RED, fontweight="bold")
    for p in targets:
        ax.add_patch(FancyArrowPatch((sx, sy - 0.1), (center(p), 3.9),
                                     arrowstyle="-|>", mutation_scale=16, lw=1.8,
                                     color=RED if p == src else BLUE, zorder=3))
    ax.set_xlim(-0.2, len(whites) + 0.2)
    ax.set_ylim(-2.1, 7.4)
    ax.axis("off")
    save_fig("fig-repitch-keyboard.png")


# ---------------------------------------------------------------------------
# Changing duration via looping
# ---------------------------------------------------------------------------


def find_loop_points(x: np.ndarray) -> tuple[int, int, int]:
    """Search the sustain for a seamless loop: a start s at an upward zero
    crossing, and an end e 0.18 to 0.30 s later, whose surrounding waveforms
    match best (so wrapping from e back to s continues the waveform). Then find
    where to jump to the release: the point r late in the sustain whose
    surroundings best match those of e, over a longer window (+/- 25 ms) that
    also penalizes differences in level and timbre, not just in phase."""
    def windows(lo: int, hi: int) -> np.ndarray:      # windows centered on lo..hi
        return sliding_window_view(x[lo - SEAM:hi + SEAM], 2 * SEAM)

    zc = np.where((x[:-1] < 0) & (x[1:] >= 0))[0] + 1
    best = (np.inf, 0, 0)
    for s in zc[(zc > 0.45 * F_S) & (zc < 0.60 * F_S)]:
        ref = x[s - SEAM:s + SEAM]
        lo, hi = s + int(0.18 * F_S), s + int(0.30 * F_S)
        d = np.sum((windows(lo, hi) - ref) ** 2, axis=1) / np.sum(ref ** 2)
        if d.min() < best[0]:
            best = (d.min(), int(s), lo + int(np.argmin(d)))
    _, s, e = best
    W = 5 * SEAM
    ref = x[e - W:e + W]
    lo, hi = int(3.0 * F_S), int(3.95 * F_S)
    d = np.sum((sliding_window_view(x[lo - W:hi + W], 2 * W) - ref) ** 2, axis=1) / np.sum(ref ** 2)
    return s, e, lo + int(np.argmin(d))


def fig_clarinet_loop(clarinet: np.ndarray) -> None:
    """The clarinet's phases, and how the sampler plays them: everything before
    the loop once, the loop as many times as needed, then the release."""
    t = np.arange(len(clarinet)) / F_S
    T = t[-1]
    colors = {"Attack": BLUE, "Decay": RED, "Sustain": GREEN, "Release": PURPLE}
    fig, (ax, ax_bar) = plt.subplots(2, 1, figsize=(12, 4.8), sharex=True,
                                     gridspec_kw={"height_ratios": [3.2, 1.0]})
    tx = ax.get_xaxis_transform()
    for name, (a, b) in PHASES.items():
        ax.axvspan(a, b, color=colors[name], alpha=0.18, lw=0)
    for name, (a, b) in PHASES.items():
        style = dict(fontsize=13, color=colors[name], fontweight="bold", va="bottom")
        if name in ("Attack", "Decay"):           # narrow bands: labels off to the right
            x_text, y_text = {"Attack": (0.95, 1.22), "Decay": (1.25, 1.04)}[name]
            ax.annotate(name, xy=((a + b) / 2, 1.0), xycoords=tx, xytext=(x_text, y_text),
                        textcoords=tx, ha="left",
                        arrowprops=dict(arrowstyle="-|>", color=colors[name], lw=1.5,
                                        shrinkA=2, shrinkB=0), **style)
        else:
            ax.text((a + b) / 2, 1.03, name, transform=tx, ha="center", **style)
    ax.axvspan(LOOP_START, LOOP_END, color=ORANGE, alpha=0.55, lw=0)
    ax.plot(t, clarinet, color="0.45", lw=0.3)
    ax.set_ylabel("Amplitude")
    ax.set_ylim(-0.62, 0.62)

    # How the sampler plays each region (cf. the slides' attack/sustain/release bar).
    regions = [(0.0, LOOP_START, "", "0.6"),
               (LOOP_START, LOOP_END, "", ORANGE),
               (LOOP_END, RELEASE, "rest of the sustain: skipped", "0.85"),
               (RELEASE, T, "end of the note: plays once", PURPLE)]
    for a, b, label, color in regions:
        ax_bar.add_patch(Rectangle((a, 0.1), b - a, 0.8, facecolor=color, alpha=0.30,
                                   edgecolor=color, lw=1.5,
                                   hatch="//" if "skipped" in label else None))
        if label:
            ax_bar.text((a + b) / 2, 0.5, label, ha="center", va="center", fontsize=13)
    ax_bar.annotate("plays once", xy=(LOOP_START / 2, 0.92), xytext=(0.05, 1.6),
                    fontsize=13, ha="left", va="center", color="0.35",
                    arrowprops=dict(arrowstyle="-|>", color="0.35", lw=1.4))
    ax_bar.annotate("loop: repeats", xy=((LOOP_START + LOOP_END) / 2, 0.92),
                    xytext=(0.95, 1.6), fontsize=13, ha="left", va="center", color=ORANGE,
                    fontweight="bold", arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1.6))
    ax_bar.set_ylim(0, 1.95)
    ax_bar.set_yticks([])
    ax_bar.spines["left"].set_visible(False)
    ax_bar.set_xlabel("Time (s)")
    ax_bar.set_xlim(0, T)
    save_fig("fig-clarinet-loop.png")


def fig_loop_crossfade() -> None:
    """Schematic of a crossfaded loop wrap: the loop's last L samples fade out
    while the L samples just before the loop start fade in on top of them, so
    the next pass begins exactly where the faded-in audio leaves off."""
    fig, ax = plt.subplots(figsize=(12, 4.8))
    s, e, L = 3.0, 9.0, 1.6           # schematic units
    y1, y2, h = 3.4, 0.6, 1.0         # rows: the recording, one pass of the loop

    def box(x0, x1, y, color, alpha=0.25):
        ax.add_patch(Rectangle((x0, y), x1 - x0, h, facecolor=color, alpha=alpha,
                               edgecolor=color, lw=1.6))

    # Row 1: the recording, with the pre-start window, the loop, and its tail.
    ax.text(-0.2, y1 + h / 2, "recording", ha="right", va="center", fontsize=13, color="0.3")
    box(0.0, 11.5, y1, "0.6", alpha=0.08)
    box(s, e, y1, ORANGE, alpha=0.18)
    box(s - L, s, y1, GOLD, alpha=0.50)
    box(e - L, e, y1, RED, alpha=0.40)
    for xv, lab in [(s, "$t_s$"), (e, "$t_e$")]:
        ax.plot([xv, xv], [y1 - 0.15, y1 + h + 0.15], color="black", lw=1.4)
        ax.text(xv, y1 + h + 0.25, lab, ha="center", fontsize=15)
    ax.text((s + e - L) / 2, y1 + h / 2, "loop", ha="center", va="center", fontsize=13,
            color=ORANGE, fontweight="bold")
    ax.text(s - L / 2, y1 + h / 2, "pre-start", ha="center", va="center", fontsize=12)
    ax.text(e - L / 2, y1 + h / 2, "tail", ha="center", va="center", fontsize=12)

    # Row 2: one pass of the loop, whose tail crossfades into the pre-start audio.
    ax.text(-0.2, y2 + h / 2, "one pass\nof the loop", ha="right", va="center",
            fontsize=13, color="0.3")
    box(s, e, y2, ORANGE, alpha=0.18)
    box(e - L, e, y2, RED, alpha=0.12)
    ax.plot([e - L, e], [y2 + h, y2], color=RED, lw=2.6)       # tail fades out
    ax.plot([e - L, e], [y2, y2 + h], color=GOLD, lw=2.6)      # pre-start fades in
    ax.text(e + 0.2, y2 + h / 2, "crossfade:\ntail out,\npre-start in", ha="left",
            va="center", fontsize=12)
    # The pre-start audio is laid over the tail (between the rows).
    ax.add_patch(FancyArrowPatch((s - L / 2, y1 - 0.05), (e - L / 2 - 0.2, y2 + h + 0.08),
                                 connectionstyle="arc3,rad=0.12", arrowstyle="-|>",
                                 mutation_scale=18, lw=1.8, color=GOLD))
    # ...then playback wraps back to the loop start (below row 2).
    ax.add_patch(FancyArrowPatch((e, y2 - 0.08), (s, y2 - 0.08),
                                 connectionstyle="arc3,rad=-0.22", arrowstyle="-|>",
                                 mutation_scale=18, lw=1.8, color="0.35"))
    ax.text((s + e) / 2, y2 - 1.05, "then wrap back to $t_s$ and continue", ha="center",
            va="top", fontsize=12, color="0.35")
    ax.set_xlim(-2.2, 11.8)
    ax.set_ylim(-1.7, 5.1)
    ax.axis("off")
    save_fig("fig-loop-crossfade.png")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("Sources:")
    clarinet = prepare_sources()
    found = find_loop_points(clarinet)
    print(f"  loop points (audio samples): {found}")
    assert found == (LOOP_START_N, LOOP_END_N, RELEASE_N), "update the hardcoded loop points"
    print("Figures and audio:")
    fig_and_audio_synthesis_vs_recording(clarinet)
    fig_parameter_grid()
    audio_repitch(clarinet)
    fig_repitch_keyboard()
    fig_clarinet_loop(clarinet)
    fig_loop_crossfade()


if __name__ == "__main__":
    main()
