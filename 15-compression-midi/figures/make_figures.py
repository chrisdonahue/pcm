"""Generate figures and sound examples for Chapter 15 (compression and MIDI).

Outputs are written to ../assets/. This file is *not* student-facing.

Sources:

- A drum loop from Freesound: 157373 ("On Rd loop 2") by cheeseymofodude, CC0,
  fetched with pyquist's Freesound client (`pyquist.web.fetch_freesound`), which
  caches it under ~/.cache/pyquist. The original upload needs Freesound OAuth: if
  the cached token has expired, run
      fetch_freesound(157373, preview_tag=None, reauthenticate=True)
  once interactively. Otherwise this script falls back to the high-quality OGG
  preview, which is itself lossy (NEVER copy credentials into the repo).
- MP3 encoding uses the `lame` command-line encoder, which must be on PATH.
- Equal-loudness contours follow ISO 226:2003 (see ISO_226 below).
- A nylon guitar riff bundled with pyquist's test data (`pyquist.paths.TEST_DATA_DIR`):
  Freesound 388954 ("Blues Riff in G (Nylon)") by FullMetalJedi, CC0. Unlike the drum
  loop's preview, it is lossless, so it shows exactly what MP3 removes.
- The semantic compression figure reuses Chapter 4's notation of Twinkle, Twinkle.
- twinkle-band.mid (for the MIDI notebook) is written here with mido.

Run with the project virtualenv (pyquist reached via PYTHONPATH):
    PYTHONPATH=../../../pyquist python make_figures.py
"""

import subprocess
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import mido
import numpy as np
import pyquist as pq
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle
from scipy.signal import stft

HERE = Path(__file__).resolve().parent
CHAPTER = HERE.parent
ASSETS = CHAPTER / "assets"
ASSETS.mkdir(exist_ok=True)

F_S = 44100
PEAK_DBFS = -6.0
TONE_DBFS = -18.0  # pure test tones are piercing at -6 dBFS, so they sit lower

plt.rcParams.update({
    "font.size": 14, "axes.labelsize": 16, "xtick.labelsize": 13,
    "ytick.labelsize": 13, "axes.spines.top": False, "axes.spines.right": False,
    "lines.linewidth": 2.0,
})
COLORS = plt.rcParams["axes.prop_cycle"].by_key()["color"]
BLUE, ORANGE, GREEN, RED, PURPLE = COLORS[0], COLORS[1], COLORS[2], COLORS[3], COLORS[4]
GRAY = "#999999"

FREESOUND_ID = 157373

# ISO 226:2003 equal-loudness contour parameters: frequency (Hz), exponent af,
# magnitude of the linear transfer function Lu (dB), and threshold of hearing Tf (dB SPL).
ISO_226 = {
    "f": [20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630,
          800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000, 12500],
    "af": [0.532, 0.506, 0.480, 0.455, 0.432, 0.409, 0.387, 0.367, 0.349, 0.330, 0.315,
           0.301, 0.288, 0.276, 0.267, 0.259, 0.253, 0.250, 0.246, 0.244, 0.243, 0.243,
           0.243, 0.242, 0.242, 0.245, 0.254, 0.271, 0.301],
    "Lu": [-31.6, -27.2, -23.0, -19.1, -15.9, -13.0, -10.3, -8.1, -6.2, -4.5, -3.1,
           -2.0, -1.1, -0.4, 0.0, 0.3, 0.5, 0.0, -2.7, -4.1, -1.0, 1.7, 2.5, 1.2, -2.1,
           -7.1, -11.2, -10.7, -3.1],
    "Tf": [78.5, 68.7, 59.5, 51.1, 44.0, 37.5, 31.5, 26.5, 22.1, 17.9, 14.4, 11.4, 8.6,
           6.2, 4.4, 3.0, 2.2, 2.4, 3.5, 1.7, -1.3, -4.2, -6.0, -5.4, -1.5, 6.0, 12.6,
           13.9, 12.3],
}

# Critical band (Bark) edges in Hz, after Zwicker (1961): 24 bands.
BARK_EDGES = [20, 100, 200, 300, 400, 510, 630, 770, 920, 1080, 1270, 1480, 1720, 2000,
              2320, 2700, 3150, 3700, 4400, 5300, 6400, 7700, 9500, 12000, 15500]

# Approximate frequency (Hz) and level (dB SPL) of some familiar sounds.
FAMILIAR_SOUNDS = [
    ("Rustling leaves", 3000, 15), ("Mosquito", 600, 25), ("Whisper", 2000, 30),
    ("Dripping faucet", 3500, 38), ("Birdsong", 5000, 48), ("Refrigerator hum", 125, 40),
    ("Conversation", 700, 60), ("Cat meowing", 1000, 70), ("Piano", 300, 76),
    ("Telephone ringing", 2500, 82), ("Dog barking", 800, 88), ("Truck", 160, 90),
    ("Motorcycle", 250, 100), ("Chainsaw", 1500, 110), ("Thunder", 60, 120),
    ("Jet engine", 1000, 130),
]


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------


def save(fig: plt.Figure, name: str) -> None:
    fig.savefig(ASSETS / name, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


def write_audio(name: str, x: np.ndarray, peak_dbfs: float | None = PEAK_DBFS) -> None:
    """Write 16-bit WAV, normalized to `peak_dbfs` (None: write as-is)."""
    x = np.asarray(x, dtype=np.float64)
    if peak_dbfs is not None:
        x = x * (10 ** (peak_dbfs / 20) / np.abs(x).max())
    assert np.abs(x).max() <= 1.0, name
    pq.Audio(x, sample_rate=F_S).write(str(ASSETS / name), subtype="PCM_16")
    print("wrote", name)


def write_mp3(name: str, x: np.ndarray, kbps: int) -> None:
    """Encode x (already at its final level) to a constant bit rate MP3 with `lame`."""
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "in.wav"
        pq.Audio(x, sample_rate=F_S).write(str(wav), subtype="PCM_16")
        subprocess.run(["lame", "--quiet", "--cbr", "-b", str(kbps), "--resample", "44.1",
                        str(wav), str(ASSETS / name)], check=True)
    print("wrote", name)


def fade(x: np.ndarray, seconds: float = 0.02) -> np.ndarray:
    """Raised-cosine fade in and out (along the first axis)."""
    n = int(seconds * F_S)
    ramp = 0.5 - 0.5 * np.cos(np.pi * np.arange(n) / n)
    x = x.copy()
    x[:n] *= ramp if x.ndim == 1 else ramp[:, None]
    x[-n:] *= ramp[::-1] if x.ndim == 1 else ramp[::-1, None]
    return x


def sine(f: float, seconds: float, dbfs: float = 0.0) -> np.ndarray:
    t = np.arange(int(seconds * F_S)) / F_S
    return 10 ** (dbfs / 20) * np.sin(2 * np.pi * f * t)


def tone(f: float, seconds: float, harmonics: int = 6) -> np.ndarray:
    """A tone with a few harmonics (amplitude 1/k), faded in and out."""
    t = np.arange(int(seconds * F_S)) / F_S
    x = sum(np.sin(2 * np.pi * k * f * t) / k for k in range(1, harmonics + 1))
    return fade(x / np.abs(x).max())


def silence(seconds: float) -> np.ndarray:
    return np.zeros(int(seconds * F_S))


def iso226(phon: float) -> tuple[np.ndarray, np.ndarray]:
    """Frequencies (Hz) and sound pressure levels (dB SPL) of an equal-loudness contour."""
    f, af, Lu, Tf = (np.array(ISO_226[k], dtype=float) for k in ("f", "af", "Lu", "Tf"))
    Af = 4.47e-3 * (10 ** (0.025 * phon) - 1.15) + (0.4 * 10 ** ((Tf + Lu) / 10 - 9)) ** af
    return f, 10 / af * np.log10(Af) - Lu + 94


def spl_at(f: float, phon: float) -> float:
    """The level (dB SPL) at which a tone of frequency f has the given loudness (phons)."""
    ff, spl = iso226(phon)
    return float(np.interp(np.log(f), np.log(ff), spl))


def phons_at(f: float, spl: float) -> float:
    """The loudness (phons) of a tone of frequency f at the given level (dB SPL)."""
    lo, hi = 0.0, 120.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if spl_at(f, mid) < spl else (lo, mid)
    return (lo + hi) / 2


def threshold_at(f: float) -> float:
    """The threshold of hearing (dB SPL) at frequency f, held constant beyond the table."""
    return float(np.interp(np.log(f), np.log(ISO_226["f"]), ISO_226["Tf"]))


def load_drums() -> np.ndarray:
    """The drum loop (stereo, float), looped twice, fetched with pyquist."""
    from pyquist.web import fetch_freesound
    try:
        audio, _ = fetch_freesound(FREESOUND_ID, preview_tag=None)  # the original upload
    except (RuntimeError, EOFError, OSError):
        audio, _ = fetch_freesound(FREESOUND_ID)  # the lossy high-quality OGG preview
        print("WARNING: using Freesound's lossy OGG preview (original needs OAuth)")
    assert audio.sample_rate == F_S
    return np.concatenate([audio.samples, audio.samples])


def lame_roundtrip(x: np.ndarray, kbps: int) -> np.ndarray:
    """Encode to MP3 at a constant bit rate with `lame`, then decode, aligned to x."""
    with tempfile.TemporaryDirectory() as tmp:
        wav, mp3, out = Path(tmp) / "in.wav", Path(tmp) / "x.mp3", Path(tmp) / "out.wav"
        pq.Audio(x, sample_rate=F_S).write(str(wav), subtype="PCM_16")
        subprocess.run(["lame", "--quiet", "--cbr", "-b", str(kbps), "--resample", "44.1",
                        str(wav), str(mp3)], check=True)
        subprocess.run(["lame", "--quiet", "--decode", str(mp3), str(out)], check=True)
        decoded = pq.Audio.from_file(out)
    y = decoded.samples
    assert decoded.sample_rate == F_S
    # Align: lame's decoder output is padded at the start; find the lag by correlation.
    a, b = x[:, 0], y[:, 0]
    lags = np.arange(0, 4000)
    scores = [np.dot(a[:F_S], b[lag:lag + F_S]) for lag in lags]
    lag = lags[int(np.argmax(scores))]
    y = y[lag:lag + len(x)]
    return np.pad(y, ((0, len(x) - len(y)), (0, 0)))


def box(ax, xy, w, h, text, color, fontsize=14):
    ax.add_patch(FancyBboxPatch(xy, w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=color, ec="black", lw=1.2, alpha=0.9))
    ax.text(xy[0] + w / 2, xy[1] + h / 2, text, ha="center", va="center", fontsize=fontsize)


def arrow(ax, start, end, color="black"):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=18,
                                 color=color, lw=1.5))


def log_freq_axis(ax, lo: float = 20, hi: float = 12500) -> None:
    ax.set_xscale("log")
    ax.set_xticks([31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000])
    ax.set_xticklabels(["31.5", "63", "125", "250", "500", "1k", "2k", "4k", "8k"])
    ax.minorticks_off()
    ax.set_xlim(lo, hi)


# --------------------------------------------------------------------------------------
# Introduction
# --------------------------------------------------------------------------------------


def fig_codec() -> None:
    fig, ax = plt.subplots(figsize=(13, 2.8))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 2.8)
    ax.axis("off")
    t = np.linspace(0, 1, 200)
    wave = np.sin(2 * np.pi * 2 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.7 * t))
    ax.plot(0.2 + 1.6 * t, 1.4 + 0.5 * wave, color=BLUE)
    ax.text(1.0, 2.35, r"Audio $\mathbf{x}$", ha="center", fontsize=15)
    arrow(ax, (2.0, 1.4), (2.8, 1.4))
    box(ax, (2.9, 0.95), 1.7, 0.9, "Coder", "#f2d4d7")
    arrow(ax, (4.7, 1.4), (5.5, 1.4))
    ax.text(6.5, 1.4, "0010110…", ha="center", va="center", fontsize=17,
            family="monospace")
    ax.text(6.5, 2.35, "Codes", ha="center", fontsize=15)
    arrow(ax, (7.5, 1.4), (8.3, 1.4))
    box(ax, (8.4, 0.95), 1.7, 0.9, "Decoder", "#d4e3f2")
    arrow(ax, (10.2, 1.4), (11.0, 1.4))
    noisy = wave + 0.06 * np.random.default_rng(0).standard_normal(len(t))
    ax.plot(11.2 + 1.6 * t, 1.4 + 0.5 * noisy, color=RED)
    ax.text(12.0, 2.35, r"Round trip $\hat{\mathbf{x}}$", ha="center", fontsize=15)
    ax.annotate("", xy=(12.0, 0.55), xytext=(1.0, 0.55),
                arrowprops=dict(arrowstyle="<->", color=GRAY, lw=1.2, ls="--"))
    ax.text(6.5, 0.15, r"distortion: $\mathtt{error}(\mathbf{x}, \hat{\mathbf{x}})$",
            ha="center", fontsize=14, color="#555555")
    save(fig, "fig-codec.png")


def fig_rate_distortion() -> None:
    """Rate vs. distortion, relative to uncompressed digital audio (16-bit PCM) as input."""
    fig, ax = plt.subplots(figsize=(8, 7.5))
    levels = ["None\n(lossless)", "Imperceptible", "Perceptible", "Only the score\nsurvives"]
    ax.annotate("", xy=(0.07, -0.3), xytext=(4000, 3.45),
                arrowprops=dict(arrowstyle="-|>", color=GRAY, lw=1.8, ls="--",
                                mutation_scale=22))
    ax.text(0.5, 0.75, "better", color=GRAY, fontsize=15, rotation=38, ha="center")
    # (label, low kbps, high kbps, distortion at low kbps, at high kbps, color, label offset)
    codecs = [
        ("WAV (16-bit PCM)", 1411.2, 1411.2, 0, 0, BLUE, (0, 0.3)),
        ("FLAC", 700, 1000, 0, 0, GREEN, (0, -0.32)),
        ("MP3", 64, 320, 2.0, 1.0, ORANGE, (-0.42, -0.25)),
        ("MIDI", 0.1, 1, 3, 3, RED, (0, 0.3)),
    ]
    for label, lo, hi, d_lo, d_hi, color, (dx, dy) in codecs:
        if lo == hi:
            ax.scatter([lo], [d_lo], s=180, color=color, zorder=3)
            x_text, y_text = lo, d_lo
        else:
            ax.plot([lo, hi], [d_lo, d_hi], color=color, lw=10, alpha=0.7,
                    solid_capstyle="round", zorder=3)
            x_text, y_text = np.sqrt(lo * hi), (d_lo + d_hi) / 2
        ax.text(x_text * 10 ** dx, y_text + dy, label, ha="center", va="center",
                fontsize=15, color=color)
    ax.set_xscale("log")
    ax.set_xlim(0.05, 5000)
    ax.set_ylim(-0.45, 3.6)
    ax.set_yticks(range(4))
    ax.set_yticklabels(levels)
    ax.set_xlabel("Information rate (kbps, log scale)")
    ax.set_ylabel("Distortion")
    save(fig, "fig-rate-distortion.png")


# --------------------------------------------------------------------------------------
# Psychoacoustics and tuning
# --------------------------------------------------------------------------------------


def fig_familiar_sounds() -> None:
    """Familiar sounds in linear units (left) and logarithmic units (right)."""
    fig, (ax_lin, ax_log) = plt.subplots(1, 2, figsize=(17, 7),
                                         gridspec_kw={"width_ratios": [1, 1.35]})
    names = [name for name, _, _ in FAMILIAR_SOUNDS]
    freqs = np.array([f for _, f, _ in FAMILIAR_SOUNDS], dtype=float)
    spls = np.array([db for _, _, db in FAMILIAR_SOUNDS], dtype=float)
    pascals = 20e-6 * 10 ** (spls / 20)

    ax_lin.scatter(freqs / 1000, pascals, color=BLUE, s=45, zorder=3)
    for name, f, p in zip(names, freqs, pascals):
        if p > 1:  # only the loudest few stand apart from the pile near zero
            ax_lin.annotate(name, (f / 1000, p), xytext=(8, -4), textcoords="offset points",
                            fontsize=13)
    ax_lin.annotate("everything else", (1.2, 0.8), xytext=(7, 12), fontsize=13,
                    color="#555555", arrowprops=dict(arrowstyle="-|>", color=GRAY))
    ax_lin.set_xlim(0, 20)
    ax_lin.set_ylim(0, 70)
    ax_lin.set_xlabel("Frequency (kHz)")
    ax_lin.set_ylabel("Sound pressure (Pa)")

    for y, label, color in [(0, "threshold of hearing", GRAY), (120, "threshold of pain", RED)]:
        ax_log.axhline(y, color=color, ls="--", lw=1.5)
        ax_log.text(12000, y + 2, label, color=color, fontsize=12, ha="right")
    ax_log.scatter(freqs, spls, color=BLUE, s=45, zorder=3)
    for name, f, db in zip(names, freqs, spls):
        ax_log.annotate(name, (f, db), xytext=(7, -4), textcoords="offset points", fontsize=12)
    log_freq_axis(ax_log, 40, 12500)
    ax_log.set_ylim(-10, 140)
    ax_log.set_xlabel("Frequency (Hz, log scale)")
    ax_log.set_ylabel("Sound pressure level (dB SPL)")
    save(fig, "fig-familiar-sounds.png")


# Behind the scenes, the octave tones are attenuated by how much more sensitive we are
# to each one than to 1280 Hz, at the threshold of hearing (ISO 226, where the
# differences are largest). We never boost: 1280 Hz at TONE_DBFS is comfortable.
# OCTAVE_EXTRA_DB adds manual trims on top, in case a tone is still harsh.
OCTAVE_EXTRA_DB = {}


def octave_gain_db(f: float) -> float:
    return min(0.0, threshold_at(f) - threshold_at(1280)) + OCTAVE_EXTRA_DB.get(f, 0.0)


def audio_octaves() -> None:
    for k in range(11):
        f = 20 * 2 ** k
        write_audio(f"audio-octave-{f:05d}.wav", fade(sine(f, 1.5)), TONE_DBFS + octave_gain_db(f))
    print("Octave gains (dB):", {20 * 2 ** k: round(octave_gain_db(20 * 2 ** k), 1)
                                 for k in range(11)})


def fig_equal_loudness() -> None:
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(ISO_226["f"], ISO_226["Tf"], color=GRAY, ls="--", lw=2)
    ax.text(160, -7, "threshold of hearing", color=GRAY, fontsize=13)
    for phon in [20, 40, 60, 80, 100]:
        f, spl = iso226(phon)
        ax.plot(f, spl, color=BLUE)
        ax.text(1000, phon + 2.5, f"{phon} phon", ha="center", fontsize=12, color=BLUE)
    ax.scatter([1000] * 5, [20, 40, 60, 80, 100], color=BLUE, s=25, zorder=3)
    log_freq_axis(ax)
    ax.set_ylim(-10, 130)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Sound pressure level (dB SPL)")
    save(fig, "fig-equal-loudness.png")


# The listening comparison: the reference (1000 Hz at -20 dBFS) stands in for +0 phons.
# To read relative loudness off the contours, assume it plays at about 60 dB SPL.
LOUDNESS_FREQS = [1000, 3150, 250, 100, 10000]
LOUDNESS_ANCHOR_SPL = 60.0


def audio_equal_loudness() -> None:
    print("Relative loudness (phons):")
    for f in LOUDNESS_FREQS:
        row = []
        for db in [20, 40]:
            write_audio(f"audio-loudness-{f}-{db}.wav", fade(sine(f, 1.5, -db)), None)
            spl = LOUDNESS_ANCHOR_SPL - (db - 20)
            row.append(round(phons_at(f, spl) - LOUDNESS_ANCHOR_SPL))
        print(f"  {f:>5} Hz: -20 dBFS -> {row[0]:+d}, -40 dBFS -> {row[1]:+d}")


def audio_intervals() -> None:
    a = 220.0
    pairs = {
        "harmonic": 3 * a,                 # an integer ratio: fuses into one tone
        "step": a * 2 ** (4 / 12),         # four steps up
        "polyphony": 1.5 * a,              # a non-integer ratio: two distinct tones
        "beating": a + 4,                  # 4 Hz apart: beats 4 times per second
    }
    for name, b in pairs.items():
        both = 3 if name == "beating" else 2
        x = np.concatenate([fade(sine(a, 1)), silence(0.2), fade(sine(b, 1)), silence(0.2),
                            fade(sine(a, both) + sine(b, both))])
        write_audio(f"audio-interval-{name}.wav", x, TONE_DBFS)


def audio_just() -> None:
    a = 220.0
    for n, m in [(5, 4), (3, 2), (4, 3), (16, 15)]:
        b = a * n / m
        x = np.concatenate([tone(a, 1), silence(0.2), tone(b, 1), silence(0.2),
                            tone(a, 2.5) + tone(b, 2.5)])
        write_audio(f"audio-just-{n}-{m}.wav", x)


JUST = [(6, 5), (5, 4), (4, 3), (3, 2), (5, 3)]


def edo_error(n: int) -> float:
    """Mean relative distance (%) from each just interval to its nearest step of n-EDO."""
    errors = []
    for p, q in JUST:
        ratio = p / q
        k = round(n * np.log2(ratio))
        errors.append(abs(2 ** (k / n) - ratio) / ratio * 100)
    return float(np.mean(errors))


def fig_edo() -> None:
    ns = np.arange(3, 37)
    errors = [edo_error(n) for n in ns]
    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.plot(ns, errors, color=GRAY, lw=1.5, zorder=1)
    ax.scatter(ns, errors, color=BLUE, s=30, zorder=2)
    for n in [12, 19, 31]:
        ax.scatter([n], [edo_error(n)], color=RED, s=90, zorder=3)
        ax.annotate(f"$n = {n}$", (n, edo_error(n)), xytext=(0, -26),
                    textcoords="offset points", ha="center", color=RED, fontsize=14)
    ax.set_xlim(2, 37)
    ax.set_ylim(-0.8, 5)
    ax.set_xlabel("Steps per octave $n$")
    ax.set_ylabel("Mean distance to\njust intervals (%)")
    save(fig, "fig-edo-error.png")
    print("EDO errors (%):", {n: round(edo_error(n), 2) for n in [7, 11, 12, 13, 19, 31]})


def fig_audio_just_vs_et() -> None:
    a = 220.0
    for name, b in [("just", a * 5 / 4), ("et", a * 2 ** (4 / 12))]:
        t = np.arange(int(0.05 * F_S)) / F_S
        fig, ax = plt.subplots(figsize=(6, 2.6))
        ax.plot(1000 * t, np.sin(2 * np.pi * a * t) + np.sin(2 * np.pi * b * t), color=BLUE,
                lw=1.5)
        if name == "just":
            for k in range(3):
                ax.axvline(1000 * k * 4 / a, color=RED, ls="--", lw=1.2)
        ax.set_xlim(0, 50)
        ax.set_ylim(-2.2, 2.2)
        ax.set_xlabel("Time (ms)")
        ax.set_yticks([])
        save(fig, f"fig-wave-{name}-third.png")
        x = np.concatenate([tone(a, 1), silence(0.2), tone(b, 1), silence(0.2),
                            tone(a, 3) + tone(b, 3)])
        write_audio(f"audio-{name}-third.wav", x)


# --------------------------------------------------------------------------------------
# Lossy compression
# --------------------------------------------------------------------------------------


def audio_test_your_ears() -> None:
    """Version 1 is a 128 kbps MP3, version 2 uncompressed, version 3 a 64 kbps MP3."""
    drums = load_drums()
    drums = drums * (10 ** (PEAK_DBFS / 20) / np.abs(drums).max())
    write_mp3("audio-ears-1.mp3", drums, 128)
    write_audio("audio-ears-2.wav", drums, None)
    write_mp3("audio-ears-3.mp3", drums, 64)


def spectrogram_db(x: np.ndarray, nperseg: int = 2048) -> tuple:
    f, t, Z = stft(x, fs=F_S, nperseg=nperseg, noverlap=nperseg * 3 // 4)
    return f, t, 20 * np.log10(np.abs(Z) + 1e-12)


MP3_KBPS = 128


def fig_mp3_spectrogram() -> None:
    from pyquist.paths import TEST_DATA_DIR
    guitar = pq.Audio.from_file(TEST_DATA_DIR / "388954__fullmetaljedi__blues-riff-in-g-nylon.wav")
    x = guitar.resample(F_S).samples[: int(4.5 * F_S)]
    x = x / np.abs(x).max() * 0.5
    mp3 = lame_roundtrip(x, MP3_KBPS)[:, 0]
    original = x[:, 0]
    reference = 20 * np.log10(np.abs(stft(original, fs=F_S, nperseg=2048, noverlap=1536)[2]).max())
    fig, axes = plt.subplots(1, 2, figsize=(16, 5), sharey=True)
    cmap = plt.get_cmap("magma").copy()
    cmap.set_under("black")
    for ax, y, title in [(axes[0], original, "Original"), (axes[1], mp3, f"MP3, {MP3_KBPS} kbps")]:
        f, t, S = spectrogram_db(y)
        mesh = ax.pcolormesh(t, f / 1000, S - reference, vmin=-110, vmax=0, cmap=cmap,
                             shading="auto", rasterized=True)
        ax.set_xlim(0, 4.5)
        ax.set_xlabel("Time (seconds)")
        ax.set_title(title, fontsize=16)
        ax.spines["top"].set_visible(True)
        ax.spines["right"].set_visible(True)
    axes[0].set_ylabel("Frequency (kHz)")
    axes[0].set_ylim(0, 20)
    cbar = fig.colorbar(mesh, ax=axes, pad=0.01, extend="min")
    cbar.set_label("Magnitude (dB)")
    save(fig, "fig-mp3-spectrogram.png")


def triangular_filterbank(freqs: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """24 triangular filters, one per critical band, peaking at each band's center."""
    edges = np.array(BARK_EDGES, dtype=float)
    centers = np.sqrt(edges[:-1] * edges[1:])
    points = np.concatenate([[edges[0]], centers, [edges[-1]]])
    bank = np.zeros((24, len(freqs)))
    for i in range(24):
        lo, mid, hi = points[i], points[i + 1], points[i + 2]
        rise = (freqs - lo) / (mid - lo)
        fall = (hi - freqs) / (hi - mid)
        bank[i] = np.clip(np.minimum(rise, fall), 0, None)
    return centers, bank


def fig_critical_bands() -> None:
    freqs = np.geomspace(20, 20000, 4000)
    _, bank = triangular_filterbank(freqs)
    fig = plt.figure(figsize=(16, 9))
    grid = fig.add_gridspec(2, 2, height_ratios=[1, 1.3], hspace=0.45, wspace=0.15)
    ax = fig.add_subplot(grid[0, :])
    for i in range(24):
        ax.plot(freqs, bank[i], color=COLORS[i % 2], lw=1.5)
    ax.set_xscale("log")
    ax.set_xlim(20, 16000)
    ax.set_ylim(0, 1.1)
    ax.set_xticks([50, 100, 200, 500, 1000, 2000, 5000, 10000])
    ax.set_xticklabels(["50", "100", "200", "500", "1k", "2k", "5k", "10k"])
    ax.minorticks_off()
    ax.set_xlabel("Frequency (Hz, log scale)")
    ax.set_ylabel("Filter gain")

    drums = load_drums()[: 3 * F_S, 0]
    f, t, Z = stft(drums, fs=F_S, nperseg=2048, noverlap=1536)
    power = np.abs(Z) ** 2
    S = 10 * np.log10(power + 1e-12)
    S -= S.max()
    ax1 = fig.add_subplot(grid[1, 0])
    ax1.pcolormesh(t, f / 1000, S, vmin=-80, vmax=0, cmap="magma", shading="auto",
                   rasterized=True)
    ax1.set_ylim(0, 16)
    ax1.set_xlabel("Time (seconds)")
    ax1.set_ylabel("Frequency (kHz)")
    ax1.set_title("Spectrogram (1025 frequency bins)", fontsize=15)
    _, bank_lin = triangular_filterbank(np.maximum(f, 1e-3))
    bands = 10 * np.log10(bank_lin @ power + 1e-12)
    bands -= bands.max()
    ax2 = fig.add_subplot(grid[1, 1])
    t_edges = np.linspace(t[0], t[-1], len(t) + 1)
    ax2.pcolormesh(t_edges, np.arange(25), bands, vmin=-80, vmax=0, cmap="magma",
                   shading="flat", rasterized=True)
    ax2.set_xlabel("Time (seconds)")
    ax2.set_ylabel("Critical band")
    ax2.set_yticks([0.5, 6.5, 12.5, 18.5, 23.5])
    ax2.set_yticklabels(["1", "7", "13", "19", "24"])
    ax2.set_title("Critical-band representation (24 bands)", fontsize=15)
    save(fig, "fig-critical-bands.png")


def fig_audio_frequency_masking() -> None:
    masker_db, probe_f, masker_f = -12.0, 1100.0, 1000.0
    probe_levels = [-6, -20, -40]  # relative to the masker, in dB

    def probe(level: float, seconds: float = 3.0) -> np.ndarray:
        x = silence(seconds)
        for start in [0.5, 1.25, 2.0]:
            i = int(start * F_S)
            beep = fade(sine(probe_f, 0.3, masker_db + level), 0.02)
            x[i:i + len(beep)] += beep
        return x

    masker = fade(sine(masker_f, 3.0, masker_db))
    # The reference: the masker alone, then the quietest probe alone (no masker).
    reference = np.concatenate([fade(sine(masker_f, 1.5, masker_db)), silence(0.5),
                                probe(probe_levels[-1])])
    write_audio("audio-mask-freq-reference.wav", reference, None)
    for level in probe_levels:
        write_audio(f"audio-mask-freq-{-level}.wav", masker + probe(level), None)

    fig, ax = plt.subplots(figsize=(12, 4.8))
    f = np.geomspace(300, 4000, 500)
    bark = lambda hz: 13 * np.arctan(0.00076 * hz) + 3.5 * np.arctan((hz / 7500) ** 2)
    dz = bark(f) - bark(masker_f)
    spread = np.where(dz < 0, 27 * dz, -12 * dz)  # a simple spreading function, dB per Bark
    ax.plot(f, -14 + spread, color=GRAY, ls="--", lw=2)
    ax.fill_between(f, -60, -14 + spread, color=GRAY, alpha=0.12)
    ax.text(1550, -48, "masked\n(inaudible)", color=GRAY, fontsize=14)
    ax.vlines(masker_f, -60, 0, color=BLUE, lw=6)
    ax.text(masker_f, 3, "masker", ha="center", color=BLUE, fontsize=14)
    for level in probe_levels:
        ax.scatter([probe_f], [level], color=RED, s=110, zorder=3)
        ax.text(probe_f * 1.04, level, f"probe, {level} dB", va="center", color=RED,
                fontsize=13)
    ax.set_xscale("log")
    ax.set_xticks([300, 500, 1000, 2000, 4000])
    ax.set_xticklabels(["300", "500", "1k", "2k", "4k"])
    ax.minorticks_off()
    ax.set_xlim(300, 4000)
    ax.set_ylim(-60, 10)
    ax.set_xlabel("Frequency (Hz, log scale)")
    ax.set_ylabel("Level relative\nto masker (dB)")
    save(fig, "fig-mask-freq.png")


def fig_audio_temporal_masking() -> None:
    f, masker_db, probe_rel = 1000.0, -12.0, -40.0
    gaps_ms = [200, 50, 5]
    masker = fade(sine(f, 0.5, masker_db), 0.005)

    def clip(gap_ms: float) -> np.ndarray:
        x = silence(1.5)
        i = int(0.2 * F_S)
        x[i:i + len(masker)] += masker
        j = i + len(masker) + int(gap_ms / 1000 * F_S)
        beep = fade(sine(f, 0.03, masker_db + probe_rel), 0.005)
        x[j:j + len(beep)] += beep
        return x

    # The reference: a gap long enough that the probe is clearly unmasked.
    for gap in [500] + gaps_ms:
        write_audio(f"audio-mask-time-{gap}.wav", clip(gap), None)

    fig, axes = plt.subplots(1, 3, figsize=(16, 3.8), sharey=True)
    for ax, gap in zip(axes, gaps_ms):
        ax.add_patch(Rectangle((0, -60), 500, 60, color=BLUE, alpha=0.7))
        start = 500 + gap
        ax.add_patch(Rectangle((start, -60), 30, 60 + probe_rel, color=RED))
        t = np.linspace(500, 800, 200)
        threshold = -15 - 45 * (1 - np.exp(-(t - 500) / 60))  # schematic forward masking
        ax.plot(t, threshold, color=GRAY, ls="--", lw=2)
        ax.set_xlim(300, 800)
        ax.set_ylim(-60, 5)
        ax.set_xlabel("Time (ms)")
        ax.set_title(f"gap of {gap} ms", fontsize=15)
    axes[0].set_ylabel("Level relative\nto masker (dB)")
    axes[0].text(320, -8, "masker", color="white", fontsize=13)
    save(fig, "fig-mask-time.png")


THRESHOLD_DBFS = -40.0


def fig_audio_absolute_threshold() -> None:
    low, high = 50, 4000
    for f in [high, low]:
        write_audio(f"audio-threshold-{f}.wav", fade(sine(f, 1.5, THRESHOLD_DBFS)), None)
    level = threshold_at(high) + 3  # "barely audible": just above the 4000 Hz threshold
    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.plot(ISO_226["f"], ISO_226["Tf"], color=GRAY, ls="--", lw=2)
    ax.fill_between(ISO_226["f"], -15, ISO_226["Tf"], color=GRAY, alpha=0.12)
    ax.text(300, -10, "inaudible", color=GRAY, fontsize=14)
    for f, color, label in [(high, BLUE, "4000 Hz: barely audible"),
                            (low, RED, "50 Hz: inaudible")]:
        ax.scatter([f], [level], color=color, s=120, zorder=3)
        ax.annotate(label, (f, level), xytext=(0, 14), textcoords="offset points",
                    ha="center", color=color, fontsize=14)
    log_freq_axis(ax)
    ax.set_ylim(-15, 80)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Sound pressure\nlevel (dB SPL)")
    save(fig, "fig-threshold.png")


def fig_mp3_pipeline() -> None:
    stages = [("Digital\naudio", "#eeeeee"), ("Time-frequency\ntransform", "#d4e3f2"),
              ("Psychoacoustic\nmodel", "#f2d4d7"), ("Quantized\nspectrogram", "#f2d4d7"),
              ("Lossless\ncompression", "#d7ecd4"), ("File\n(.mp3, .ogg)", "#eeeeee")]
    w, gap, margin = 2.2, 0.55, 0.15
    width = 2 * margin + len(stages) * w + (len(stages) - 1) * gap
    fig, ax = plt.subplots(figsize=(width, 2.6))
    ax.set_xlim(0, width)
    ax.set_ylim(0, 2.6)
    ax.axis("off")
    for i, (label, color) in enumerate(stages):
        x0 = margin + i * (w + gap)
        box(ax, (x0, 0.8), w, 1.1, label, color, fontsize=13)
        if i:
            arrow(ax, (x0 - gap + 0.03, 1.35), (x0 - 0.03, 1.35))
    ax.text(margin + 2.5 * (w + gap) + w / 2 - gap / 2, 0.3,
            "lossy: removes what we can't hear", ha="center", color=RED, fontsize=13)
    ax.text(margin + 4 * (w + gap) + w / 2, 0.3, "lossless", ha="center", color=GREEN,
            fontsize=13)
    save(fig, "fig-mp3-pipeline.png")


# --------------------------------------------------------------------------------------
# Lossless compression
# --------------------------------------------------------------------------------------


def entropy(p: np.ndarray) -> np.ndarray:
    p = np.asarray(p, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        h = -(p * np.log2(p) + (1 - p) * np.log2(1 - p))
    return np.nan_to_num(h)


def fig_entropy() -> None:
    p = np.linspace(0, 1, 501)
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(p, entropy(p), color=BLUE)
    for q, offset, ha in [(0.5, (0, -30), "center"), (0.1, (12, -4), "left"),
                          (0.01, (12, -4), "left")]:
        h = float(entropy(q))
        ax.scatter([q], [h], color=RED, s=70, zorder=3)
        text = f"$p = {q}$: " + ("1 bit" if q == 0.5 else f"{h:.3g} bits")
        ax.annotate(text, (q, h), xytext=offset, textcoords="offset points", ha=ha,
                    fontsize=13, color=RED)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.12)
    ax.set_xlabel("$p = P(X = \\mathrm{heads})$")
    ax.set_ylabel("Entropy $H(X)$ (bits)")
    save(fig, "fig-entropy.png")


def fig_huffman() -> None:
    """The worked example: blocks of N = 2 tosses with P(heads) = 0.1.

    Merges: HH (0.01) + HT (0.09) -> 0.10, then TH (0.09) + 0.10 -> 0.19, then
    TT (0.81) + 0.19 -> 1. Bit 0 goes to the more probable child.
    """
    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.set_xlim(-0.5, 10.5)
    ax.set_ylim(-0.9, 4.6)
    ax.axis("off")
    nodes = {"root": (3.0, 4.0, "1.00"), "a": (6.0, 2.8, "0.19"), "b": (8.0, 1.6, "0.10"),
             "TT": (0.5, 2.8, None), "TH": (4.5, 1.6, None), "HT": (6.8, 0.4, None),
             "HH": (9.2, 0.4, None)}
    leaves = {"TT": ("0.81", "0"), "TH": ("0.09", "11"), "HT": ("0.09", "100"),
              "HH": ("0.01", "101")}
    edges = [("root", "TT", "0"), ("root", "a", "1"), ("a", "b", "0"), ("a", "TH", "1"),
             ("b", "HT", "0"), ("b", "HH", "1")]
    for parent, child, bit in edges:
        (x0, y0, _), (x1, y1, _) = nodes[parent], nodes[child]
        ax.plot([x0, x1], [y0, y1], color="#555555", lw=1.5, zorder=1)
        ax.text((x0 + x1) / 2 + (0.15 if x1 > x0 else -0.15), (y0 + y1) / 2 + 0.1, bit,
                fontsize=15, color=RED, ha="center")
    for name, (x, y, prob) in nodes.items():
        if name in leaves:
            p, code = leaves[name]
            ax.add_patch(FancyBboxPatch((x - 0.55, y - 0.3), 1.1, 0.6,
                                        boxstyle="round,pad=0.02", fc="#d4e3f2", ec="black"))
            ax.text(x, y, f"{name}", ha="center", va="center", fontsize=15)
            ax.text(x, y - 0.62, f"$P = {p}$\ncode {code}", ha="center", va="top", fontsize=13)
        else:
            ax.scatter([x], [y], s=900, color="#eeeeee", edgecolor="black", zorder=2)
            ax.text(x, y, prob, ha="center", va="center", fontsize=11, zorder=3)
    save(fig, "fig-huffman.png")


def fig_lpc_residual() -> None:
    """A block of the drum loop as 16-bit integers, its quantized LPC prediction, and the
    residual, as in FLAC."""
    drums = load_drums()[:, 0]
    x = np.round(drums / np.abs(drums).max() * 0.5 * 32767).astype(np.int64)
    start, N, K, shift = int(0.74 * F_S), 4096, 8, 12
    block = x[start - K:start + N].astype(float)
    X = np.stack([block[K - k:K - k + N] for k in range(1, K + 1)], axis=1)
    h, *_ = np.linalg.lstsq(X, block[K:], rcond=None)
    q = np.round(h * 2 ** shift).astype(np.int64)
    prediction = (X.astype(np.int64) @ q) >> shift
    residual = block[K:].astype(np.int64) - prediction
    t = 1000 * np.arange(N) / F_S
    fig, axes = plt.subplots(1, 2, figsize=(16, 4.8), gridspec_kw={"width_ratios": [2.2, 1]})
    show = slice(0, 400)
    axes[0].plot(t[show], block[K:][show], color=BLUE, label="signal $x[n]$")
    axes[0].plot(t[show], prediction[show], color=ORANGE, ls="--",
                 label="prediction $\\hat{x}[n]$")
    axes[0].plot(t[show], residual[show], color=RED, label="residual $e[n]$")
    axes[0].set_xlabel("Time (ms)")
    axes[0].set_ylabel("Sample value (16-bit integer)")
    axes[0].legend(loc="upper right", fontsize=12, frameon=False)
    bins = np.arange(-2000, 2001, 50)
    axes[1].hist(block[K:], bins=bins, color=BLUE, alpha=0.6, label="signal")
    axes[1].hist(residual, bins=bins, color=RED, alpha=0.6, label="residual")
    axes[1].set_yscale("log")
    axes[1].set_xlabel("Sample value")
    axes[1].set_ylabel("Count")
    axes[1].legend(fontsize=12, frameon=False)
    save(fig, "fig-lpc-residual.png")


def audio_drums() -> None:
    """One pass through the drum loop, for the toy FLAC notebook."""
    drums = load_drums()
    drums = drums[: len(drums) // 2]
    write_audio("audio-drums.wav", drums)


# --------------------------------------------------------------------------------------
# Semantic compression and MIDI
# --------------------------------------------------------------------------------------

TWINKLE = [(0.0, 60, 0.5), (0.5, 60, 0.5), (1.0, 67, 0.5), (1.5, 67, 0.5), (2.0, 69, 0.5),
           (2.5, 69, 0.5), (3.0, 67, 1.0)]  # (onset in seconds, pitch, duration) at 120 BPM


def twinkle_midi_bytes() -> int:
    """The size of the first phrase of Twinkle as a standard MIDI file."""
    track = mido.MidiTrack()
    events = sorted([(on, "note_on", p) for on, p, d in TWINKLE]
                    + [(on + d, "note_off", p) for on, p, d in TWINKLE], key=lambda e: e[0])
    previous = 0
    for time, kind, pitch in events:
        tick = round(time * 2 * 480)
        track.append(mido.Message(kind, note=pitch, velocity=100 if kind == "note_on" else 0,
                                  time=tick - previous))
        previous = tick
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "twinkle.mid"
        mido.MidiFile(ticks_per_beat=480, tracks=[track]).save(path)
        return path.stat().st_size


def render_twinkle(harmonics: int, decay: float) -> np.ndarray:
    x = silence(4.5)
    for onset, pitch, duration in TWINKLE:
        f = 440 * 2 ** ((pitch - 69) / 12)
        t = np.arange(int((duration + 0.3) * F_S)) / F_S
        note = sum(np.sin(2 * np.pi * k * f * t) / k ** 1.5 for k in range(1, harmonics + 1))
        note *= np.exp(-decay * t)
        i = int(onset * F_S)
        x[i:i + len(note)] += fade(note, 0.005)
    return x / np.abs(x).max()


def fig_semantic() -> None:
    fig = plt.figure(figsize=(16, 3.6))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 3.6)
    ax.axis("off")
    t = np.arange(int(4.5 * F_S)) / F_S
    audio_in = render_twinkle(harmonics=8, decay=2.5)
    audio_out = render_twinkle(harmonics=1, decay=0.8)
    for x0, y, color, label in [(0.1, audio_in, BLUE, "Audio (CD quality):\n705,600 bytes"),
                                (12.6, audio_out, RED, "Round trip audio")]:
        step = 40
        ax.plot(x0 + 3.2 * t[::step] / t[-1], 1.9 + 0.7 * y[::step], color=color, lw=0.6)
        ax.text(x0 + 1.6, 0.55, label, ha="center", va="center", fontsize=17)
    arrow(ax, (3.45, 1.9), (3.95, 1.9))
    box(ax, (4.0, 1.45), 1.7, 0.9, "Transcribe", "#f2d4d7", fontsize=16)
    arrow(ax, (5.75, 1.9), (6.25, 1.9))
    score = plt.imread(CHAPTER.parent / "04-score-timbre" / "assets" / "fig-twinkle-melody.png")
    ax_score = fig.add_axes([6.3 / 16, 1.0 / 3.6, 3.3 / 16, 1.9 / 3.6])
    ax_score.imshow(score)
    ax_score.axis("off")
    ax.text(7.95, 0.55, f"Score (MIDI):\n{twinkle_midi_bytes()} bytes", ha="center",
            va="center", fontsize=17)
    arrow(ax, (9.65, 1.9), (10.15, 1.9))
    box(ax, (10.2, 1.45), 1.8, 0.9, "Synthesize", "#d4e3f2", fontsize=16)
    arrow(ax, (12.05, 1.9), (12.55, 1.9))
    save(fig, "fig-semantic.png")


def midi_twinkle_band() -> None:
    """A short MIDI file with three instruments, program changes, and a sustain pedal.

    Channel 1 (0): piano melody (program 0, Acoustic Grand Piano), with the sustain
    pedal (control 64) pressed for each measure. Channel 2 (1): bass (program 32,
    Acoustic Bass). Channel 10 (9): drums (kick 36, snare 38, closed hi-hat 42).
    """
    tpb = 480
    melody = [60, 60, 67, 67, 69, 69, 67, None, 65, 65, 64, 64, 62, 62, 60, None]
    bass = [48, 41, 48, 43, 41, 48, 43, 48]  # one half note each
    messages = [(0, mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(120))),
                (0, mido.Message("program_change", channel=0, program=0)),
                (0, mido.Message("program_change", channel=1, program=32))]
    for beat, pitch in enumerate(melody):
        if pitch is not None:
            on, off = beat * tpb, beat * tpb + (2 * tpb if melody[beat + 1] is None else tpb) - 10
            messages += [(on, mido.Message("note_on", channel=0, note=pitch, velocity=90)),
                         (off, mido.Message("note_off", channel=0, note=pitch, velocity=0))]
    for measure in range(4):
        messages += [(measure * 4 * tpb + 5, mido.Message("control_change", channel=0,
                                                          control=64, value=127)),
                     ((measure + 1) * 4 * tpb - 5, mido.Message("control_change", channel=0,
                                                                control=64, value=0))]
    for k, pitch in enumerate(bass):
        messages += [(k * 2 * tpb, mido.Message("note_on", channel=1, note=pitch, velocity=80)),
                     ((k + 1) * 2 * tpb - 20, mido.Message("note_off", channel=1, note=pitch,
                                                           velocity=0))]
    for eighth in range(len(melody) * 2):
        tick = eighth * tpb // 2
        hits = [42] + ([36] if eighth % 4 == 0 else []) + ([38] if eighth % 4 == 2 else [])
        for note in hits:
            messages += [(tick, mido.Message("note_on", channel=9, note=note, velocity=70)),
                         (tick + 60, mido.Message("note_off", channel=9, note=note, velocity=0))]
    messages.sort(key=lambda m: (m[0], m[1].type == "note_on"))  # note offs before note ons
    track = mido.MidiTrack()
    previous = 0
    for tick, msg in messages:
        track.append(msg.copy(time=tick - previous))
        previous = tick
    mido.MidiFile(ticks_per_beat=tpb, tracks=[track]).save(ASSETS / "twinkle-band.mid")
    print("wrote twinkle-band.mid")


# --------------------------------------------------------------------------------------
# Musical examples
# --------------------------------------------------------------------------------------


def audio_shepard() -> None:
    """A Shepard tone rising by one step every 0.5 s, for 11 full cycles (66 s)."""
    step_seconds, steps, octaves = 0.5, 132, 9
    base = 20.0  # lowest component at the start of each cycle (Hz)
    t = np.arange(int(step_seconds * F_S)) / F_S
    center, width = np.log2(base) + octaves / 2, octaves / 4  # Gaussian envelope over log f
    notes = []
    for s in range(steps):
        x = np.zeros(len(t))
        for k in range(octaves):
            f = base * 2 ** (k + (s % 12) / 12)
            gain = np.exp(-0.5 * ((np.log2(f) - center) / width) ** 2)
            x += gain * np.sin(2 * np.pi * f * t)
        notes.append(fade(x, 0.02))
    x = np.concatenate(notes)
    write_mp3("audio-shepard.mp3", x * (10 ** (PEAK_DBFS / 20) / np.abs(x).max()), 128)


if __name__ == "__main__":
    fig_codec()
    fig_rate_distortion()
    fig_familiar_sounds()
    audio_octaves()
    fig_equal_loudness()
    audio_equal_loudness()
    audio_intervals()
    audio_just()
    fig_edo()
    fig_audio_just_vs_et()
    audio_test_your_ears()
    fig_mp3_spectrogram()
    fig_critical_bands()
    fig_audio_frequency_masking()
    fig_audio_temporal_masking()
    fig_audio_absolute_threshold()
    fig_mp3_pipeline()
    fig_entropy()
    fig_huffman()
    fig_lpc_residual()
    audio_drums()
    fig_semantic()
    midi_twinkle_band()
    audio_shepard()
