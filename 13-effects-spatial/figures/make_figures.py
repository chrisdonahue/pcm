"""Generate figures and sound examples for Chapter 13 (effects and spatial audio).

Outputs are written to ../assets/. This file is *not* student-facing.

Sources (each trimmed, mixed to mono, resampled to 44.1 kHz, faded at the
cuts, normalized, and written as WAV, which the in-browser runtime can decode):

- Freesound previews, read from pyquist's default cache (~/.cache/pyquist) and
  fetched with pyquist's Freesound client if missing, which needs an API key
  (NEVER copy credentials into the repo). See SOUNDS below for IDs, authors,
  and licenses.
- ../../09-filters/assets/audio-reverb-dry.wav, the dry marimba loop from
  Chapter 9 (Freesound 522193 by BrickDeveloper171, CC0).
- The opening of Beethoven's Symphony No. 5, performed by Arturo Toscanini and
  the NBC Symphony Orchestra (1939), from https://archive.org/details/
  BeethovenSymphonyNo.5 (public domain). Only the first ~220 kB of the 64 kbps
  MP3 is downloaded, with an HTTP range request.

Run with the project virtualenv (pyquist reached via PYTHONPATH):
    PYTHONPATH=../../../pyquist python make_figures.py
"""

import urllib.request
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pyquist as pq
from matplotlib.patches import Arc, Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle
from pyquist.paths import CACHE_DIR
from pyquist.web.freesound import fetch_freesound

HERE = Path(__file__).resolve().parent
CHAPTER = HERE.parent
ASSETS = CHAPTER / "assets"
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
GOLD_ = "#C9A227"

# Freesound ID: (asset name, start s, end s or None for the whole sound, credit)
SOUNDS = {
    445724: ("ball.wav", 0.0, 4.0, "BOUNCING Ball.wav by 180241virtualwindow.co.za, CC BY-NC 3.0"),
    453384: ("guitar-arpeggio.wav", 1.9, 5.3, "Clean Strumming & Arpeggio by loudernoises, CC0"),
    484841: ("yodel.wav", 2.25, 3.5, "Yodel by Astounded, CC0"),
    37746: ("pad.wav", 0.0, 8.0, "Quilt_Electro-choral_Pad 0001.ogg by Quilt, CC0"),
    235538: ("guitar-distorted.wav", 0.0, None, "distorted open guitar strings.wav by simosco, CC0"),
    187700: ("guitar-acoustic.wav", 0.0, 8.0, "Acoustic Guitar - Sleepy - end 2 - 127bpm Gm.wav by afrodrumming, CC BY 4.0"),
    102888: ("kick-loop.wav", 0.0, None, "Drum Loop Solo Kick - 119 Bpm.wav by Uknow Dude, CC0"),
    149732: ("ping-pong.wav", 0.0, None, "Balle Ping-Pong 2.aif by beskhu, CC BY 4.0"),
}
MARIMBA = CHAPTER.parent / "09-filters" / "assets" / "audio-reverb-dry.wav"
BEETHOVEN_URL = ("https://archive.org/download/BeethovenSymphonyNo.5/"
                 "ToscaniniBeethoven5_64kb.mp3")
BEETHOVEN_HEAD = CACHE_DIR / "archive.org" / "ToscaniniBeethoven5_64kb-head.mp3"
BEETHOVEN_SECONDS = 20.0
ROOM_IR = CHAPTER.parent / "09-filters" / "assets" / "audio-reverb-ir.wav"
# Tamara Smyth's tape flanging figure, reproduced with attribution from
# https://musicweb.ucsd.edu/~trsmyth/filtersDelayII/Flanger.html
SMYTH_FIGURE_URL = "https://musicweb.ucsd.edu/~trsmyth/filtersDelayII/img6.png"
SMYTH_FIGURE = ASSETS / "fig-tape-flanger.png"


def save_fig(name: str) -> None:
    plt.tight_layout()
    plt.savefig(ASSETS / name, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  wrote {name}")


def to_mono_44k(audio: pq.Audio) -> np.ndarray:
    audio = audio.as_mono()
    if audio.sample_rate != F_S:
        audio = audio.resample(F_S)
    return np.asarray(audio.samples, dtype=np.float64).reshape(-1)


def fade(x: np.ndarray, in_s: float = 0.005, out_s: float = 0.02) -> np.ndarray:
    """Short linear fades so a cut-out clip (mono or multichannel) starts and
    ends without clicks."""
    x = x.copy()
    n_in, n_out = int(in_s * F_S), int(out_s * F_S)
    shape = (-1,) + (1,) * (x.ndim - 1)
    if n_in:
        x[:n_in] *= np.linspace(0.0, 1.0, n_in).reshape(shape)
    if n_out:
        x[-n_out:] *= np.linspace(1.0, 0.0, n_out).reshape(shape)
    return x


def write_audio(x: np.ndarray, name: str, peak_dbfs: float = PEAK_DBFS) -> None:
    audio = pq.Audio(np.asarray(x, dtype=np.float32), F_S)
    audio.normalize(peak_dbfs=peak_dbfs)
    audio.write(str(ASSETS / name))
    print(f"  wrote {name} ({audio.duration:.2f} s)")


# ---------------------------------------------------------------------------
# Source preparation
# ---------------------------------------------------------------------------


def freesound_preview(fsid: int) -> pq.Audio:
    """A Freesound preview from pyquist's DEFAULT cache, fetched (with an API key) if missing."""
    path = CACHE_DIR / "freesound" / str(fsid) / "preview-hq.ogg"
    if not path.exists():
        fetch_freesound(fsid)
    return pq.Audio.from_file(str(path))


def prepare_sources() -> None:
    for fsid, (name, start, end, _) in SOUNDS.items():
        x = to_mono_44k(freesound_preview(fsid))
        x = x[int(start * F_S):None if end is None else int(end * F_S)]
        write_audio(fade(x), name)
    write_audio(fade(to_mono_44k(pq.Audio.from_file(str(MARIMBA)))), "marimba.wav")
    if not BEETHOVEN_HEAD.exists():                  # download only the opening, once
        BEETHOVEN_HEAD.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(BEETHOVEN_URL, headers={"Range": "bytes=0-219999"})
        BEETHOVEN_HEAD.write_bytes(urllib.request.urlopen(request).read())
    x = to_mono_44k(pq.Audio.from_file(str(BEETHOVEN_HEAD)))[:int(BEETHOVEN_SECONDS * F_S)]
    write_audio(fade(x, 0.0, 0.5), "beethoven.wav")
    # The pad is genuinely stereo (left-right correlation about 0.3), so it
    # also serves as the source for the widening example.
    pad = freesound_preview(37746)
    assert pad.sample_rate == F_S and pad.num_channels == 2
    write_audio(fade(np.asarray(pad.samples, dtype=np.float64)[:int(8.0 * F_S)]),
                "pad-stereo.wav")
    if not SMYTH_FIGURE.exists():
        SMYTH_FIGURE.write_bytes(urllib.request.urlopen(SMYTH_FIGURE_URL).read())
        print(f"  wrote {SMYTH_FIGURE.name}")


def audio_loudness() -> None:
    """A click, a 440 Hz sinusoid, and white noise, all at the same (gentle)
    peak amplitude of -30 dBFS. The noise takes random values of -1 or 1, so its
    RMS amplitude equals its peak amplitude."""
    n = np.arange(int(1.5 * F_S))
    click = np.zeros(len(n))
    click[int(0.5 * F_S)] = 1.0
    sine = fade(np.sin(2 * np.pi * 440 * n / F_S), 0.005, 0.005)
    noise = fade(np.random.default_rng(0).choice([-1.0, 1.0], len(n)), 0.005, 0.005)
    for name, x in (("click", click), ("sine", sine), ("noise", noise)):
        write_audio(x, f"audio-loudness-{name}.wav", peak_dbfs=-30.0)


# ---------------------------------------------------------------------------
# The algorithms (mirrors of the chapter's notebooks)
# ---------------------------------------------------------------------------


def rms_envelope(x: np.ndarray, frame_length: int, hop: int) -> np.ndarray:
    padded = np.pad(x, frame_length // 2)
    frames = np.lib.stride_tricks.sliding_window_view(padded, frame_length)[::hop]
    return np.sqrt(np.mean(frames ** 2, axis=1))


def compress(x: np.ndarray, threshold_db: float, ratio: float, frame_length: int = 1764,
             hop: int = 441) -> np.ndarray:
    level_db = 20 * np.log10(np.maximum(rms_envelope(x, frame_length, hop), 1e-6))
    target_db = np.where(level_db > threshold_db,
                         threshold_db + (level_db - threshold_db) / ratio, level_db)
    gain = 10 ** ((target_db - level_db) / 20)
    return x * np.interp(np.arange(len(x)), np.arange(len(gain)) * hop, gain)


# ---------------------------------------------------------------------------
# Signal-flow diagram helpers (in the style of Chapters 9 and 12)
# ---------------------------------------------------------------------------


def _adder(ax, cx, cy, r=0.18):
    ax.add_patch(Circle((cx, cy), r, facecolor="white", edgecolor="0.2", lw=1.8, zorder=3))
    ax.text(cx, cy, "+", ha="center", va="center", fontsize=20, zorder=4)


def _box(ax, cx, cy, text, w=0.9, h=0.5, fontsize=15):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle="round,pad=0.01",
                                facecolor="0.92", edgecolor="0.3", lw=1.6, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fontsize, zorder=4)


def _gain(ax, cx, cy, text, size=0.24, fontsize=13):
    s = size
    pts = [[cx - s, cy + s], [cx - s, cy - s], [cx + s, cy]]          # pointing right
    ax.add_patch(Polygon(pts, closed=True, facecolor="white", edgecolor="0.3", lw=1.6, zorder=3))
    ax.text(cx - s / 4, cy, text, ha="center", va="center", fontsize=fontsize, zorder=4)


def _arrow(ax, p0, p1, color="0.3"):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=14,
                                 color=color, lw=1.6, shrinkA=0, shrinkB=0, zorder=2))


def _wire(ax, pts, color="0.3"):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=color, lw=1.6, zorder=1)


def _to_adder(ax, pts, center, r=0.18):
    """A wire through pts, ending with an arrow on the edge of the adder at center."""
    (x0, y0), (cx, cy) = pts[-1], center
    d = np.hypot(cx - x0, cy - y0)
    end = (cx - r * (cx - x0) / d, cy - r * (cy - y0) / d)
    _wire(ax, list(pts) + [end])
    _arrow(ax, (end[0] - 0.12 * (cx - x0) / d, end[1] - 0.12 * (cy - y0) / d), end)


def _diagram_axes(figsize, xlim, ylim):
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


# ---------------------------------------------------------------------------
# Feedback delay: impulse and magnitude responses across M and g
# ---------------------------------------------------------------------------


def fig_feedback_grid() -> None:
    """Impulse responses (top of each cell) and magnitude responses (bottom) of
    y[n] = x[n] + g y[n - M], for four gains g (rows) and four delays M (columns)."""
    gains = [0.25, 0.5, 0.75, 0.95]
    delays = [50, 200, 2205, 11025]
    f = np.linspace(0, 1000, 64001)
    fig = plt.figure(figsize=(16, 15))
    outer = fig.add_gridspec(4, 4, hspace=0.42, wspace=0.28)
    for r, g in enumerate(gains):
        for c, M in enumerate(delays):
            inner = outer[r, c].subgridspec(2, 1, hspace=0.45)
            axt, axf = fig.add_subplot(inner[0]), fig.add_subplot(inner[1])
            k = np.arange(9)
            t_ms = k * M / F_S * 1000
            ml, sl, bl = axt.stem(t_ms, g ** k)
            plt.setp(ml, color=RED, markersize=3.5)
            plt.setp(sl, color=RED, linewidth=1.3)
            plt.setp(bl, color="0.75", linewidth=0.8)
            axt.set_xlim(-0.03 * t_ms[-1], 1.04 * t_ms[-1])
            axt.set_ylim(-0.05, 1.12)
            mag_db = -20 * np.log10(np.abs(1 - g * np.exp(-2j * np.pi * f * M / F_S)))
            axf.plot(f, mag_db, color=PURPLE, lw=1.0)
            axf.set_xlim(0, 1000)
            axf.set_ylim(-8, 28)
            for ax in (axt, axf):
                ax.tick_params(labelsize=10)
            axt.set_xlabel("Time (ms)", fontsize=11, labelpad=1)
            axf.set_xlabel("Frequency (Hz)", fontsize=11, labelpad=1)
            if c == 0:
                axt.set_ylabel("$h[n]$", fontsize=12)
                axf.set_ylabel("dB", fontsize=12)
                axt.text(-0.62, -0.25, f"$g = {g}$", transform=axt.transAxes, fontsize=16,
                         ha="right", va="center", rotation=90)
            if r == 0:
                axt.set_title(f"$M = {M}$ ({1000 * M / F_S:.1f} ms)\n"
                              f"$f_s / M = {F_S / M:.1f}$ Hz", fontsize=14, pad=8)
    save_fig("fig-feedback-grid.png")


# ---------------------------------------------------------------------------
# Variable, tapped, and multitap delay lines, and chorus
# ---------------------------------------------------------------------------


def fig_tapped_delay() -> None:
    """A fixed delay line, and a delay line of length M' with a time-varying tap."""
    fig, ax = _diagram_axes((12, 3.6), (-0.6, 11.4), (-1.7, 1.9))
    y1, y2 = 1.2, -0.2
    ax.text(-0.5, y1 + 0.45, "Fixed delay", fontsize=13, color="0.35")
    ax.text(0.0, y1, "$x[n]$", ha="center", va="center", fontsize=16)
    _arrow(ax, (0.55, y1), (2.0, y1))
    _box(ax, 4.6, y1, "$z^{-M}$", w=5.2)
    _arrow(ax, (7.2, y1), (8.7, y1))
    ax.text(9.6, y1, "$x[n-M]$", ha="center", va="center", fontsize=16)
    ax.text(-0.5, y2 + 0.45, "Variable delay", fontsize=13, color="0.35")
    ax.text(0.0, y2, "$x[n]$", ha="center", va="center", fontsize=16)
    _arrow(ax, (0.55, y2), (2.0, y2))
    _box(ax, 3.2, y2, "$z^{-M[n]}$", w=2.4)
    _wire(ax, [(4.4, y2), (5.2, y2)])
    _arrow(ax, (5.2, y2), (5.6, y2))
    _box(ax, 6.4, y2, "$z^{-(M' - M[n])}$", w=1.6, fontsize=13)
    _arrow(ax, (7.2, y2), (8.7, y2))
    ax.text(9.6, y2, "$x[n-M']$", ha="center", va="center", fontsize=16)
    ax.add_patch(Circle((4.8, y2), 0.06, color="0.3", zorder=3))
    _arrow(ax, (4.8, y2), (4.8, y2 - 0.85))
    ax.text(4.8, y2 - 1.05, "tap: $x[n - M[n]]$", ha="center", va="top", fontsize=15)
    save_fig("fig-tapped-delay.png")


def fig_multitap() -> None:
    """A delay line of length M' with taps at M_a and M_b."""
    fig, ax = _diagram_axes((12, 2.6), (-0.6, 11.6), (-1.3, 0.6))
    y = 0.0
    ax.text(0.0, y, "$x[n]$", ha="center", va="center", fontsize=16)
    _arrow(ax, (0.55, y), (1.3, y))
    _box(ax, 2.0, y, "$z^{-M_a}$", w=1.4)
    _wire(ax, [(2.7, y), (4.0, y)])
    _arrow(ax, (4.0, y), (4.2, y))
    _box(ax, 5.1, y, "$z^{-(M_b - M_a)}$", w=1.8, fontsize=14)
    _wire(ax, [(6.0, y), (7.3, y)])
    _arrow(ax, (7.3, y), (7.5, y))
    _box(ax, 8.4, y, "$z^{-(M' - M_b)}$", w=1.8, fontsize=14)
    _arrow(ax, (9.3, y), (10.1, y))
    ax.text(10.8, y, "$x[n-M']$", ha="center", va="center", fontsize=16)
    for xt, label in ((3.35, "$x[n - M_a]$"), (6.65, "$x[n - M_b]$")):
        ax.add_patch(Circle((xt, y), 0.06, color="0.3", zorder=3))
        _arrow(ax, (xt, y), (xt, y - 0.7))
        ax.text(xt, y - 0.85, label, ha="center", va="top", fontsize=15)
    save_fig("fig-multitap.png")


def fig_chorus() -> None:
    """Chorus: the dry signal plus several delayed copies, each with its own
    slowly varying delay and gain."""
    fig, ax = _diagram_axes((10, 5.0), (-0.8, 9.6), (-2.6, 2.2))
    rows = [0.7, -0.4, -1.5]
    ax.text(-0.3, -0.4, "$x[n]$", ha="center", va="center", fontsize=16)
    _wire(ax, [(0.2, -0.4), (1.0, -0.4)])
    _wire(ax, [(1.0, 1.7), (1.0, -1.5)])
    _to_adder(ax, [(1.0, 1.7), (7.2, 1.7)], (7.2, 0.0))          # the dry path
    ax.text(4.1, 1.85, "dry", ha="center", va="bottom", fontsize=13, color="0.4")
    for k, yk in enumerate(rows, start=1):
        _arrow(ax, (1.0, yk), (2.0, yk))
        _box(ax, 3.0, yk, f"$z^{{-M_{k}[n]}}$", w=2.0, h=0.62)
        _wire(ax, [(4.0, yk), (4.9, yk)])
        _gain(ax, 5.15, yk, f"$g_{k}$")
        _to_adder(ax, [(5.39, yk), (6.4, yk)], (7.2, 0.0))
    _adder(ax, 7.2, 0.0)
    _arrow(ax, (7.38, 0.0), (8.3, 0.0))
    ax.text(8.9, 0.0, "$y[n]$", ha="center", va="center", fontsize=16)
    save_fig("fig-chorus.png")


def fig_flanger() -> None:
    """A flanger's delay, M[n] = M_c (1 + A sin(2 pi f_m n / f_s)), in milliseconds, and
    the frequency of the lowest tooth of its comb, f_s / M[n]."""
    t = np.linspace(0, 8, 8000)
    M_c, A, f_m = 3.0, 0.9, 0.25              # M_c in ms, as in the flanging notebook
    delay = M_c * (1 + A * np.sin(2 * np.pi * f_m * t))
    fig, (axd, axf) = plt.subplots(2, 1, figsize=(10, 5.4), sharex=True)
    axd.plot(t, delay, color=RED)
    axd.axhline(M_c, color="0.6", lw=1, ls="--")
    axd.text(8.05, M_c, "$M_c$", va="center", fontsize=14, color="0.4")
    axd.set_ylim(0, 6)
    axd.set_ylabel("Delay (ms)")
    axf.plot(t, 1000 / delay, color=PURPLE)
    axf.set_ylim(0, 3600)
    axf.set_ylabel("Frequency (Hz)")
    axf.set_xlabel("Time (s)")
    axf.set_xlim(0, 8)
    fig.align_ylabels()
    save_fig("fig-flanger.png")


# ---------------------------------------------------------------------------
# All-pass filters and Schroeder's reverberator
# ---------------------------------------------------------------------------


def fig_allpass() -> None:
    """Magnitude responses of a feedback comb and an all-pass with the same M
    and g, and the phase response of the all-pass."""
    M, g = 20, 0.7
    f = np.linspace(0, F_S / 2, 4000)
    z = np.exp(-2j * np.pi * f * M / F_S)
    comb = 1 / (1 - g * z)
    allpass = (-g + z) / (1 - g * z)
    fig, (axm, axp) = plt.subplots(1, 2, figsize=(13, 3.9))
    axm.plot(f / 1000, 20 * np.log10(np.abs(comb)), color=RED, lw=1.4, label="feedback comb")
    axm.plot(f / 1000, 20 * np.log10(np.abs(allpass)), color=PURPLE, lw=2.2, label="all-pass")
    axm.set_xlabel("Frequency (kHz)")
    axm.set_ylabel("Magnitude (dB)")
    axm.set_xlim(0, F_S / 2000)
    axm.set_ylim(-8, 14)
    axm.legend(loc="upper right", fontsize=12, frameon=False, ncol=2)
    axp.plot(f / 1000, np.unwrap(np.angle(comb)), color=RED, lw=1.4, label="feedback comb")
    axp.plot(f / 1000, np.unwrap(np.angle(allpass)), color=PURPLE, lw=2.2, label="all-pass")
    axp.legend(loc="lower left", fontsize=12, frameon=False)
    axp.set_xlabel("Frequency (kHz)")
    axp.set_ylabel("Phase (radians)")
    axp.set_xlim(0, F_S / 2000)
    save_fig("fig-allpass.png")


def fig_room_ir() -> None:
    """The church impulse response from Chapter 9: in full, and its first 100 ms,
    where the individual early reflections are visible."""
    ir = pq.Audio.from_file(str(ROOM_IR)).as_mono()
    h = np.asarray(ir.samples, dtype=np.float64).reshape(-1)
    h /= np.abs(h).max()
    t = np.arange(len(h)) / ir.sample_rate
    fig, (axa, axb) = plt.subplots(1, 2, figsize=(13, 3.9), gridspec_kw={"width_ratios": [1.6, 1]})
    axa.plot(t, h, color=BLUE, lw=0.5)
    axa.set_xlim(0, t[-1])
    axa.set_xlabel("Time (s)")
    axa.set_ylabel("Amplitude")
    onset = int(np.argmax(np.abs(h) > 0.05))
    seg = slice(onset, onset + int(0.1 * ir.sample_rate))
    axb.plot(1000 * (t[seg] - t[onset]), h[seg], color=BLUE, lw=0.8)
    axb.set_xlim(0, 100)
    axb.set_xlabel("Time (ms)")
    for ax in (axa, axb):
        ax.set_ylim(-1.05, 1.05)
    save_fig("fig-room-ir.png")


def fig_schroeder() -> None:
    """Schroeder's reverberator: four feedback comb filters in parallel, then two
    all-pass filters in series (after Fig. 6 of Schroeder 1962)."""
    fig, ax = _diagram_axes((13, 4.6), (-0.8, 14.2), (-2.6, 2.4))
    rows = [1.65, 0.55, -0.55, -1.65]
    ax.text(-0.3, 0.0, "$x[n]$", ha="center", va="center", fontsize=16)
    _wire(ax, [(0.2, 0.0), (0.8, 0.0)])
    _wire(ax, [(0.8, rows[0]), (0.8, rows[-1])])
    for k, yk in enumerate(rows, start=1):
        _arrow(ax, (0.8, yk), (1.6, yk))
        _box(ax, 3.0, yk, f"comb: $\\tau_{k},\\ g_{k}$", w=2.8, h=0.62, fontsize=13)
        _to_adder(ax, [(4.4, yk), (5.0, yk)], (5.8, 0.0))
    _adder(ax, 5.8, 0.0)
    _arrow(ax, (5.98, 0.0), (6.9, 0.0))
    _box(ax, 8.1, 0.0, "all-pass: $\\tau_5,\\ g_5$", w=2.4, h=0.62, fontsize=13)
    _arrow(ax, (9.3, 0.0), (10.0, 0.0))
    _box(ax, 11.2, 0.0, "all-pass: $\\tau_6,\\ g_6$", w=2.4, h=0.62, fontsize=13)
    _arrow(ax, (12.4, 0.0), (13.1, 0.0))
    ax.text(13.6, 0.0, "$y[n]$", ha="center", va="center", fontsize=16)
    save_fig("fig-schroeder.png")


# ---------------------------------------------------------------------------
# Waveshaping: clipping and Chebyshev polynomials
# ---------------------------------------------------------------------------


def _waveshaping_grid(rows, name: str, amp: float) -> None:
    """Rows of (input sinusoid, transfer function f, output f(x[n]))."""
    t = np.linspace(0, 2, 1000)
    x = amp * np.sin(2 * np.pi * t)
    u = np.linspace(-1.35, 1.35, 400)
    fig, axes = plt.subplots(len(rows), 3, figsize=(14, 3.3 * len(rows)))
    for (label, f, color), (axx, axf, axy) in zip(rows, axes):
        axx.plot(t, x, color=BLUE)
        axx.set_ylabel("$x[n]$")
        axf.plot(u, u, color="0.75", lw=1, ls="--")
        axf.plot(u, f(u), color=color)
        axf.set_xlim(-1.35, 1.35)
        axf.set_ylim(-1.35, 1.35)
        axf.set_aspect("equal")
        axf.set_xlabel("$x$")
        axf.set_ylabel("$f(x)$")
        axf.set_title(label, fontsize=14)
        axy.plot(t, x, color="0.75", lw=1, ls="--")
        axy.plot(t, f(x), color=color)
        axy.set_ylabel("$f(x[n])$")
        for ax in (axx, axy):
            ax.set_xlim(0, 2)
            ax.set_ylim(-1.5, 1.5)
            ax.set_xticks([])
            ax.set_xlabel("Time")
    save_fig(name)


def fig_clipping() -> None:
    _waveshaping_grid([("Hard clipping: $\\min(1, \\max(-1, x))$",
                        lambda u: np.clip(u, -1, 1), RED),
                       ("Soft clipping: $\\tanh(3x)$", lambda u: np.tanh(3 * u), GREEN)],
                      "fig-clipping.png", amp=1.25)


def fig_chebyshev() -> None:
    _waveshaping_grid([("Chebyshev $T_2(x) = 2x^2 - 1$", lambda u: 2 * u ** 2 - 1, ORANGE),
                       ("Chebyshev $T_3(x) = 4x^3 - 3x$", lambda u: 4 * u ** 3 - 3 * u, ORANGE)],
                      "fig-chebyshev.png", amp=1.0)


# ---------------------------------------------------------------------------
# Dynamic range compression
# ---------------------------------------------------------------------------


def fig_rms() -> None:
    """A sine wave, its square, and its RMS amplitude, 1/sqrt(2)."""
    t = np.linspace(0, 1, 1000)
    x = np.sin(2 * np.pi * t)
    fig, ax = plt.subplots(figsize=(10, 3.8))
    ax.axhline(0, color="0.85", lw=1, zorder=0)
    ax.plot(t, x, color=BLUE, label="$x[n]$")
    ax.plot(t, x ** 2, color=ORANGE, label="$x[n]^2$")
    ax.axhline(1 / np.sqrt(2), color=RED, ls="--", lw=1.8,
               label=r"$x_\mathrm{RMS} = 1/\sqrt{2} \approx 0.707$")
    ax.set_xlim(0, 1)
    ax.set_ylim(-1.15, 1.15)
    ax.set_xlabel("Time (one period)")
    ax.set_ylabel("Amplitude")
    ax.set_xticks([])
    ax.legend(loc="lower left", fontsize=12, frameon=False)
    save_fig("fig-rms.png")


def fig_compression_curves() -> None:
    """Static compression curves: output level versus input level, in dB."""
    level = np.linspace(-80, 0, 400)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))
    for ax, threshold, ratios, title in (
            (axes[0], -20.0, [1, 2, 4, np.inf], "Compression ratio $R$"),
            (axes[1], -40.0, [1, 2, 4, np.inf], "Upward compression ratio $R$")):
        ax.plot(level, level, color="black", ls="--", lw=1.2, label="no processing")
        for R, color in zip(ratios[1:], (ORANGE, GREEN, RED)):
            if ax is axes[0]:
                out = np.where(level > threshold, threshold + (level - threshold) / R, level)
            else:
                out = np.where(level < threshold, threshold + (level - threshold) / R, level)
            ax.plot(level, out, color=color, label="$R = \\infty$" if np.isinf(R) else f"$R = {R}$")
        ax.axvline(threshold, color="0.6", lw=1, ls=":")
        ax.text(threshold + 1, -78, f"threshold\n${threshold:.0f}$ dB", fontsize=12, color="0.4")
        ax.set_xlim(-80, 0)
        ax.set_ylim(-80, 2)
        ax.set_aspect("equal")
        ax.set_xlabel("Input level (dB)")
        ax.set_ylabel("Output level (dB)")
        ax.set_title(title, fontsize=14)
        ax.legend(loc="upper left", fontsize=12, frameon=False)
    save_fig("fig-compression-curves.png")


def fig_compression_beethoven() -> None:
    """The opening of Beethoven's Fifth, before and after compression (both
    normalized to the same peak)."""
    x = np.asarray(pq.Audio.from_file(str(ASSETS / "beethoven.wav")).samples).reshape(-1)
    y = compress(x, threshold_db=-30.0, ratio=4.0)
    y *= np.abs(x).max() / np.abs(y).max()
    fig, axes = plt.subplots(2, 1, figsize=(13, 4.6), sharex=True, sharey=True)
    for ax, s, color, label in ((axes[0], x, BLUE, "Original"),
                                (axes[1], y, PURPLE, "Compressed")):
        block = int(0.01 * F_S)
        n = len(s) // block * block
        b = s[:n].reshape(-1, block)
        tb = (np.arange(len(b)) + 0.5) * block / F_S
        ax.fill_between(tb, b.min(1), b.max(1), color=color, lw=0)
        ax.set_ylabel(label)
        ax.set_yticks([])
        ax.set_ylim(-0.55, 0.55)
    axes[1].set_xlabel("Time (s)")
    axes[1].set_xlim(0, len(x) / F_S)
    save_fig("fig-compression-beethoven.png")


# ---------------------------------------------------------------------------
# Spatial audio: stereo, panning
# ---------------------------------------------------------------------------


def fig_stereo() -> None:
    """Stereo recording (two microphones), storage (two channels), and playback
    (two loudspeakers)."""
    fig, ax = _diagram_axes((13, 4.6), (0, 15), (-0.4, 5.4))
    for xc, title in ((2.5, "Recording"), (7.5, "Storage"), (12.5, "Playback")):
        ax.text(xc, 5.1, title, ha="center", fontsize=16, fontweight="bold", color="0.25")
    # Recording: a source closer to the left microphone, and its wavefronts.
    src = (1.6, 3.6)
    ax.add_patch(Circle(src, 0.18, color=GOLD_, zorder=3))
    ax.text(src[0], src[1] + 0.35, "source", ha="center", fontsize=12, color="0.35")
    for r in (0.6, 1.2, 1.8):
        ax.add_patch(Arc(src, 2 * r, 2 * r, theta1=200, theta2=340, color="0.6", lw=1.3))
    for xm, label in ((1.0, "L"), (4.0, "R")):
        ax.add_patch(Circle((xm, 1.0), 0.16, color="0.25", zorder=3))
        ax.plot([xm, xm], [0.84, 0.35], color="0.25", lw=2)
        ax.text(xm, 0.05, label, ha="center", va="top", fontsize=14)
    # Storage: two channels; the right one arrives later and quieter.
    t = np.linspace(0, 1, 300)
    pulse = lambda c: np.exp(-((t - c) / 0.07) ** 2) * np.sin(2 * np.pi * 9 * (t - c))
    for yc, s, label in ((3.4, pulse(0.35), "L"), (1.6, 0.55 * pulse(0.5), "R")):
        ax.plot(6.0 + 3.0 * t, yc + 0.7 * s, color=BLUE, lw=1.6)
        ax.plot([6.0, 9.0], [yc, yc], color="0.8", lw=1)
        ax.text(5.7, yc, label, ha="right", va="center", fontsize=14)
    ax.text(7.5, 0.4, r"$\mathbf{x} \in \mathbb{R}^{T f_s \times 2}$", ha="center", fontsize=16)
    # Playback: two loudspeakers and a listener.
    for xs, label, (theta1, theta2) in ((11.0, "L", (255, 345)), (14.0, "R", (195, 285))):
        ax.add_patch(Rectangle((xs - 0.2, 3.5), 0.4, 0.6, facecolor="0.3", edgecolor="0.2"))
        ax.text(xs, 4.35, label, ha="center", fontsize=14)
        for r in (0.5, 0.9):                         # wavefronts aimed at the listener
            ax.add_patch(Arc((xs, 3.8), 2 * r, 2 * r, theta1=theta1, theta2=theta2,
                             color="0.6", lw=1.3))
    ax.add_patch(Circle((12.5, 1.4), 0.45, facecolor="0.85", edgecolor="0.4", lw=1.5))
    for xe in (12.05, 12.95):
        ax.add_patch(Circle((xe, 1.4), 0.1, facecolor="0.7", edgecolor="0.4"))
    ax.text(12.5, 0.65, "listener", ha="center", va="top", fontsize=12, color="0.35")
    save_fig("fig-stereo.png")


def fig_panning() -> None:
    """Linear and constant-power pan laws: channel gains and total power."""
    a = np.linspace(0, 1, 400)
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.2), sharey=True)
    for ax, (left, right), title in (
            (axes[0], (1 - a, a), "Linear panning"),
            (axes[1], (np.cos(a * np.pi / 2), np.sin(a * np.pi / 2)), "Constant-power panning")):
        ax.plot(a, left, color=BLUE, label="left gain")
        ax.plot(a, right, color=RED, label="right gain")
        ax.plot(a, left ** 2 + right ** 2, color="0.4", ls="--", lw=1.5,
                label="sum of squared gains")
        mid = left[len(a) // 2]
        ax.plot([0.5, 0.5], [0, mid], color="0.6", lw=1, ls=":")
        ax.text(0.53, mid + 0.04, f"{mid:.3f}", fontsize=12, color="0.35")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1.15)
        ax.set_xlabel(r"Pan position $\alpha$ (left to right)")
        ax.set_title(title, fontsize=14)
    axes[0].set_ylabel("Gain")
    axes[0].legend(loc="center left", fontsize=12, frameon=False)
    save_fig("fig-panning.png")


if __name__ == "__main__":
    print("Sources:")
    prepare_sources()
    print("Sound examples:")
    audio_loudness()
    print("Figures:")
    fig_feedback_grid()
    fig_tapped_delay()
    fig_multitap()
    fig_chorus()
    fig_flanger()
    fig_room_ir()
    fig_allpass()
    fig_schroeder()
    fig_clipping()
    fig_chebyshev()
    fig_rms()
    fig_compression_curves()
    fig_compression_beethoven()
    fig_stereo()
    fig_panning()
