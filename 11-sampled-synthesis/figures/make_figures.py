"""Generate figures and sound examples for Chapter 11 (sample-based synthesis).

Outputs are written to ../assets/. This file is *not* student-facing.

Sources:

- ../raw/amen.wav, the Amen break, normalized and copied to assets/amen.wav.
- Freesound sounds, fetched with pyquist's Freesound client. Fetching needs a
  Freesound API key cached in pyquist's default cache (~/.cache/pyquist), so
  this script must run once on a machine with credentials. It then
    * copies the drum sounds used by notebooks/drum-machine.ipynb into
      assets/freesound/<id>/ (metadata.json and the preview only, NEVER any
      credentials), so the notebook can load them offline, and
    * prepares the saxophone notes as WAV files (mono, 44.1 kHz, leading
      silence trimmed, fine-tuned to equal-tempered pitch, normalized). WAV
      matters: the in-browser runtime can only decode WAV, not the OGG
      previews, and the chapter's widgets run in the browser.
"""

import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pyquist as pq
import soxr
from matplotlib.patches import FancyArrowPatch, Rectangle
from pyquist.helper import pitch_name_to_pitch, pitch_to_frequency
from pyquist.web.freesound import fetch_freesound
from pyquist.paths import CACHE_DIR
from scipy.signal import lfilter

HERE = Path(__file__).resolve().parent
CHAPTER = HERE.parent
ASSETS = CHAPTER / "assets"
ASSETS.mkdir(exist_ok=True)

F_S = 44100
PEAK_DBFS = -6.0

# Freesound IDs.
DRUMS = {"hats": 332372, "snare": 46709, "kick": 673512}
RECORDER = (620964, "G5")                      # cdonahueucsd, CC BY 4.0
SAX = {"C4": 359634, "C5": 359646, "C6": 359658}  # MTG Good-sounds pack, CC BY 3.0

# The running example's sustain loop: it ends just before the release begins
# and spans a whole number of cycles of C5.
LOOP_END = 3.30           # seconds
LOOP_CYCLES = 131         # cycles of the C5 fundamental

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


def loop_note(x: np.ndarray, t_s: float, t_e: float, duration: float,
              xfade: float = 0.0) -> np.ndarray:
    """Extend a note by looping its sustain region [t_s, t_e) seconds.

    Everything before the loop plays once, the loop repeats, and everything
    after the loop plays once. Whenever the loop wraps back to its start, its
    last `xfade` seconds are crossfaded into the audio just *before* the loop
    start, so playback flows continuously into x[s] on the next pass.
    """
    s, e = int(round(t_s * F_S)), int(round(t_e * F_S))
    L = int(round(xfade * F_S))
    d_A, d_S, d_R = s, e - s, len(x) - e
    n_loops = max(1, int(round((duration * F_S - d_A - d_R) / d_S)))
    body = x[s:e].copy()
    if L:
        w = np.linspace(0.0, 1.0, L)                       # fade-in weights
        body[-L:] = (1 - w) * x[e - L:e] + w * x[s - L:s]  # blend tail into pre-start
    return np.concatenate([x[:s]] + [body] * (n_loops - 1) + [x[s:e], x[e:]])


def lpf(f_c: float, Q: float, f_s: int) -> tuple[np.ndarray, np.ndarray]:
    """RBJ Audio EQ Cookbook low-pass biquad (as in Chapter 9's rbj.py)."""
    w0 = 2 * np.pi * f_c / f_s
    c, alpha = np.cos(w0), np.sin(w0) / (2 * Q)
    b = np.array([(1 - c) / 2, 1 - c, (1 - c) / 2])
    a = np.array([1 + alpha, -2 * c, 1 - alpha])
    return b / a[0], a / a[0]


def velocity(x: np.ndarray, v: float, filtered: bool = True,
             f_lo: float = 1000.0, f_hi: float = 12000.0) -> np.ndarray:
    """Scale a note's amplitude by velocity v in (0, 1]; optionally also
    low-pass it with a cutoff that rises exponentially with v."""
    y = v * x
    if filtered:
        f_c = f_lo * (f_hi / f_lo) ** v
        b, a = lpf(f_c, 0.707, F_S)
        y = lfilter(b, a, y)
    return y


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


def prepare_sources() -> dict[str, np.ndarray]:
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

    notes = {}
    for name, fsid in SAX.items():
        notes[name] = prepare_note(fetch(fsid), name)
        pq.Audio(notes[name].astype(np.float32), F_S).write(str(ASSETS / f"sax-{name}.wav"))
        print(f"  wrote sax-{name}.wav")
    fsid, name = RECORDER
    notes["recorder"] = prepare_note(fetch(fsid), name)
    return notes


# ---------------------------------------------------------------------------
# Sample-based synthesis: repitching the recorder
# ---------------------------------------------------------------------------

RECORDER_TARGETS = ["G4", "C5", "E5", "G5", "C6"]


def audio_recorder(rec: np.ndarray) -> None:
    for target in RECORDER_TARGETS:
        k = pitch_name_to_pitch(target) - pitch_name_to_pitch("G5")
        write_audio(fade(repitch(rec, k)), f"audio-recorder-{target}.wav")


def fig_recorder_keyboard() -> None:
    """A keyboard from G4 to C6: the G5 recording (red) is repitched to the
    target keys (blue) by changing its playback speed."""
    lo, hi = pitch_name_to_pitch("G4"), pitch_name_to_pitch("C6")
    black_pcs = {1, 3, 6, 8, 10}
    whites = [p for p in range(lo, hi + 1) if p % 12 not in black_pcs]
    x_of = {p: i for i, p in enumerate(whites)}       # white-key x positions
    targets = {pitch_name_to_pitch(t): t for t in RECORDER_TARGETS}
    src = pitch_name_to_pitch("G5")

    fig, ax = plt.subplots(figsize=(12, 4.6))
    for p in whites:
        color = RED if p == src else (BLUE if p in targets else "white")
        ax.add_patch(Rectangle((x_of[p], 0), 1, 4, facecolor=color, edgecolor="0.25",
                               alpha=0.85 if color != "white" else 1.0, zorder=1))
    for p in range(lo, hi + 1):
        if p % 12 in black_pcs:
            ax.add_patch(Rectangle((x_of[p - 1] + 0.68, 1.55), 0.64, 2.45,
                                   facecolor="0.15", edgecolor="0.15", zorder=2))
    for p, name in targets.items():
        k = p - src
        label = f"{name}\n(original)" if k == 0 else f"{name}\n$k = {k:+d}$"
        ax.text(x_of[p] + 0.5, -0.25, label, ha="center", va="top", fontsize=13,
                color=RED if k == 0 else BLUE)
    # The recording, above the keyboard, with arrows to each target key.
    sx, sy = x_of[src] + 0.5, 6.4
    ax.text(sx, sy, "recording of G5", ha="center", va="bottom", fontsize=14,
            color=RED, fontweight="bold")
    for p in targets:
        ax.add_patch(FancyArrowPatch((sx, sy - 0.1), (x_of[p] + 0.5, 3.9),
                                     arrowstyle="-|>", mutation_scale=16, lw=1.8,
                                     color=RED if p == src else BLUE, zorder=3))
    ax.set_xlim(-0.2, len(whites) + 0.2)
    ax.set_ylim(-1.6, 7.2)
    ax.axis("off")
    save_fig("fig-recorder-keyboard.png")


# ---------------------------------------------------------------------------
# Changing pitch via resampling (soprano saxophone)
# ---------------------------------------------------------------------------


def audio_sax_repitch(c5: np.ndarray) -> None:
    for k, name in [(0, "C5"), (4, "E5"), (7, "G5"), (12, "C6")]:
        write_audio(fade(repitch(c5, k)), f"audio-sax-repitch-{name}.wav")


# ---------------------------------------------------------------------------
# Changing duration via looping
# ---------------------------------------------------------------------------


def default_loop() -> tuple[float, float]:
    f0 = pitch_to_frequency(pitch_name_to_pitch("C5"))
    e = int(round(LOOP_END * F_S))
    s = e - int(round(LOOP_CYCLES * F_S / f0))
    return s / F_S, e / F_S


def fig_sax_phases(c5: np.ndarray) -> None:
    """The C5 note's phases, and how sample-based synthesis plays them."""
    t = np.arange(len(c5)) / F_S
    t_s, t_e = default_loop()
    T = t[-1]

    fig, (ax, ax_bar) = plt.subplots(2, 1, figsize=(12, 4.6), sharex=True,
                                     gridspec_kw={"height_ratios": [3.2, 1.0]})
    phases = [("Attack", 0.0, 0.06, BLUE), ("Sustain", 0.06, t_e, GREEN),
              ("Release", t_e, T, PURPLE)]
    tx = ax.get_xaxis_transform()
    for name, a, b, color in phases:
        ax.axvspan(a, b, color=color, alpha=0.18, lw=0)
        x_lab, ha = (a, "left") if name == "Attack" else ((a + b) / 2, "center")
        ax.text(x_lab, 1.03, name, transform=tx, ha=ha, va="bottom", fontsize=13,
                color=color, fontweight="bold")
    ax.axvspan(t_s, t_e, color=ORANGE, alpha=0.55, lw=0)
    ax.annotate("loop", xy=((t_s + t_e) / 2, 0.40), xytext=(t_s - 0.75, 0.47),
                fontsize=13, color=ORANGE, fontweight="bold", va="center",
                arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1.6))
    ax.plot(t, c5, color="0.45", lw=0.3)
    ax.set_ylabel("Amplitude")
    ax.set_ylim(-0.62, 0.62)

    # How the sampler plays each region (cf. the slides' attack/sustain/release bar).
    regions = [(0.0, t_s, "before the loop: plays once ($d_A$)", "0.6"),
               (t_s, t_e, "", ORANGE),
               (t_e, T, "after: plays once ($d_R$)", PURPLE)]
    for a, b, label, color in regions:
        ax_bar.add_patch(Rectangle((a, 0.1), b - a, 0.8, facecolor=color, alpha=0.30,
                                   edgecolor=color, lw=1.5))
        if label:
            ax_bar.text((a + b) / 2, 0.5, label, ha="center", va="center", fontsize=13)
    ax_bar.annotate("loops ($d_S$)", xy=((t_s + t_e) / 2, 0.92), xytext=(t_s - 0.15, 1.55),
                    fontsize=13, ha="right", va="center", color=ORANGE, fontweight="bold",
                    arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1.6))
    ax_bar.set_ylim(0, 1.9)
    ax_bar.set_yticks([])
    ax_bar.spines["left"].set_visible(False)
    ax_bar.set_xlabel("Time (s)")
    ax_bar.set_xlim(0, T)
    save_fig("fig-sax-phases.png")


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


def audio_looping(c5: np.ndarray) -> None:
    write_audio(c5, "audio-loop-original.wav")
    t_s, t_e = default_loop()
    naive_s = t_e - 0.250                      # exactly 250 ms: a fractional number of cycles
    write_audio(fade(loop_note(c5, naive_s, t_e, 8.0)), "audio-loop-naive.wav")
    write_audio(fade(loop_note(c5, t_s, t_e, 8.0)), "audio-loop-cycles.wav")
    write_audio(fade(loop_note(c5, t_s, t_e, 8.0, xfade=0.03)), "audio-loop-xfade.wav")


# ---------------------------------------------------------------------------
# Changing dynamics
# ---------------------------------------------------------------------------

VELOCITIES = [0.2, 0.5, 1.0]


def _excerpt(c5: np.ndarray, dur: float = 1.6) -> np.ndarray:
    return fade(c5[:int(dur * F_S)], 0.003, 0.25)


def audio_dynamics(c5: np.ndarray) -> None:
    """Six clips sharing ONE gain, so their relative loudness is preserved:
    the loudest (v = 1, unfiltered) peaks at -6 dBFS."""
    note = _excerpt(c5)
    clips = {}
    for v in VELOCITIES:
        clips[f"audio-dyn-gain-{int(100 * v)}.wav"] = velocity(note, v, filtered=False)
        clips[f"audio-dyn-filter-{int(100 * v)}.wav"] = velocity(note, v, filtered=True)
    scale = 10 ** (PEAK_DBFS / 20) / max(np.abs(c).max() for c in clips.values())
    for name, clip in clips.items():
        pq.Audio((scale * clip).astype(np.float32), F_S).write(str(ASSETS / name))
        print(f"  wrote {name}")


def fig_dynamics(c5: np.ndarray) -> None:
    note = _excerpt(c5)
    seg = slice(int(0.4 * F_S), int(0.4 * F_S) + 8192)
    win = np.hanning(8192)
    f = np.fft.rfftfreq(8192, 1 / F_S)
    fig, ax = plt.subplots(figsize=(12, 4.2))
    for v, color in reversed(list(zip(VELOCITIES, [BLUE, ORANGE, RED]))):
        y = velocity(note, v, filtered=True)[seg]
        mag = 20 * np.log10(np.abs(np.fft.rfft(y * win)) / win.sum() * 2 + 1e-9)
        f_c = 1000.0 * 12.0 ** v
        ax.plot(f / 1000, mag, color=color, lw=1.4,
                label=f"velocity $v = {v}$ (cutoff {f_c / 1000:.1f} kHz)")
    ax.set_xlim(0, 8)
    ax.set_ylim(-110, -10)
    ax.set_xlabel("Frequency (kHz)")
    ax.set_ylabel("Amplitude (dB)")
    ax.legend(loc="upper right", fontsize=12)
    save_fig("fig-dynamics.png")


# ---------------------------------------------------------------------------
# The complete instrument (mirrors sax() and the phrase in code/sampler.py)
# ---------------------------------------------------------------------------

PHRASE = [(0.0, "G4", 0.4, 0.4), (0.5, "C5", 0.4, 0.6), (1.0, "E5", 0.4, 0.8),
          (1.5, "G5", 6.0, 1.0)]       # (onset, pitch, duration, velocity)


def cut_off(x: np.ndarray, duration: float, r_dur: float = 0.1) -> np.ndarray:
    y = x[:int(duration * F_S)].copy()
    n_r = min(len(y), int(r_dur * F_S))
    y[len(y) - n_r:] *= np.linspace(1.0, 0.0, n_r)
    return y


def audio_phrase(c5: np.ndarray) -> None:
    t_s, t_e = default_loop()
    rendered = []
    for onset, pitch, dur, v in PHRASE:
        k = pitch_name_to_pitch(pitch) - pitch_name_to_pitch("C5")
        ratio = 2.0 ** (k / 12.0)
        note = repitch(c5, k)
        if dur < len(note) / F_S:
            note = cut_off(note, dur)
        else:
            note = loop_note(note, t_s / ratio, t_e / ratio, dur, xfade=0.03)
        rendered.append((int(onset * F_S), velocity(note, v)))
    out = np.zeros(max(i + len(n) for i, n in rendered))
    for i, n in rendered:
        out[i:i + len(n)] += n
    write_audio(out, "audio-sampler-phrase.wav")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("Sources:")
    notes = prepare_sources()
    print("Figures and audio:")
    audio_recorder(notes["recorder"])
    fig_recorder_keyboard()
    audio_sax_repitch(notes["C5"])
    fig_sax_phases(notes["C5"])
    fig_loop_crossfade()
    audio_looping(notes["C5"])
    audio_dynamics(notes["C5"])
    fig_dynamics(notes["C5"])
    audio_phrase(notes["C5"])


if __name__ == "__main__":
    main()
