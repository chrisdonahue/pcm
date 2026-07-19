"""Generate figures and sound examples for Chapter 7 (sampling theory).

Outputs are written to ../assets/. This file is *not* student-facing.

Run with the project virtualenv (pyquist reached via PYTHONPATH):
    PYTHONPATH=../../../../pyquist ../../../.venv/bin/python make_figures.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pyquist as pq

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
ASSETS.mkdir(exist_ok=True)

F_S = 44100
PEAK_DBFS = -6.0

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


def save_fig(name: str) -> None:
    plt.tight_layout()
    plt.savefig(ASSETS / name, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  wrote {name}")


def write_audio(samples: np.ndarray, name: str, sr: int = F_S) -> None:
    audio = pq.Audio(samples.astype(np.float32), sr)
    audio.normalize(peak_dbfs=PEAK_DBFS)
    audio.write(str(ASSETS / name))
    print(f"  wrote {name}")


def stem(ax, xs, ys, color, ms=7, lw=2.0):
    ml, sl, bl = ax.stem(xs, ys)
    plt.setp(ml, color=color, markersize=ms)
    plt.setp(sl, color=color, linewidth=lw)
    plt.setp(bl, color="0.7", linewidth=1.0)


def alias_freq(f: np.ndarray, f_s: float) -> np.ndarray:
    """The apparent (aliased) frequency after sampling f at rate f_s."""
    m = np.mod(f, f_s)
    return np.minimum(m, f_s - m)


def phase_osc(freq: np.ndarray, f_s: float) -> np.ndarray:
    """Time-varying oscillator via phase accumulation (from Chapter 6)."""
    return np.sin(np.cumsum(2 * np.pi * freq / f_s))


# ---------------------------------------------------------------------------
# 1. Sampling as multiplication, in both domains (2 rows x 3 cols)
# ---------------------------------------------------------------------------


def fig_sampling_domains() -> None:
    f_s = 10.0
    dur = 2.0
    t = np.linspace(0, dur, 2000)
    x = np.sin(2 * np.pi * 1 * t) + np.sin(2 * np.pi * 2 * t)
    n = np.arange(0, int(dur * f_s) + 1)
    ts = n / f_s
    xs = np.sin(2 * np.pi * 1 * ts) + np.sin(2 * np.pi * 2 * ts)

    fig, axes = plt.subplots(2, 3, figsize=(14, 6))

    # --- top row: time domain ---
    axes[0, 0].plot(t, x, color=ORANGE)
    axes[0, 0].set_title(r"$x(t)$", fontsize=15)
    axes[0, 0].set_ylabel("Amplitude")

    markerline, stemlines, baseline = axes[0, 1].stem(ts, np.ones_like(ts))
    plt.setp(markerline, color=RED, markersize=5)
    plt.setp(stemlines, color=RED, linewidth=1.5)
    plt.setp(baseline, visible=False)
    axes[0, 1].set_title(r"$\coprod_{f_s}(t)$  (impulse train)", fontsize=15)

    axes[0, 2].plot(t, x, color=ORANGE, alpha=0.3, linestyle="--")
    axes[0, 2].plot(ts, xs, "o", color=GREEN, markersize=6)
    axes[0, 2].set_title(r"$x(t)\cdot\coprod_{f_s}(t)$", fontsize=15)

    for ax in axes[0]:
        ax.set_xlabel("Time (s)")
        ax.set_xlim(0, dur)

    # --- bottom row: frequency domain ---
    stem(axes[1, 0], [-2, -1, 1, 2], [0.5, 0.5, 0.5, 0.5], ORANGE)
    axes[1, 0].set_title(r"$|X(\omega)|$", fontsize=15)
    axes[1, 0].set_ylabel("Amplitude")

    ks = np.arange(-3, 4)
    stem(axes[1, 1], ks * f_s, np.ones_like(ks, dtype=float), RED)
    axes[1, 1].set_title(r"$|D(\omega)|$", fontsize=15)

    copies = []
    for k in ks:
        for base in (-2, -1, 1, 2):
            copies.append(k * f_s + base)
    stem(axes[1, 2], copies, [0.5] * len(copies), GREEN)
    axes[1, 2].set_title(r"$|X_{f_s}(\omega)|$  (copies at $k f_s$)", fontsize=15)

    for ax in axes[1]:
        ax.set_xlabel("Frequency (Hz)")
        ax.set_xlim(-27, 27)
        ax.set_ylim(0, 1.2)
    save_fig("fig-sampling-domains.png")


# ---------------------------------------------------------------------------
# 2. Aliasing: many continuous sinusoids, identical samples
# ---------------------------------------------------------------------------


def fig_aliasing_sines() -> None:
    f_s = 1.0
    t = np.linspace(0, 4, 2000)
    fig, ax = plt.subplots(figsize=(12, 4))
    for f, c in [(1, BLUE), (2, ORANGE), (4, GREEN)]:
        ax.plot(t, np.sin(2 * np.pi * f * t), color=c, linewidth=1.8,
                label=f"$\\sin(2\\pi \\cdot {f}\\, t)$", alpha=0.85)
    ns = np.arange(0, 5)
    ax.plot(ns / f_s, np.zeros_like(ns), "o", color="black", markersize=10,
            zorder=5, label=f"samples ($f_s = 1$ Hz)")
    ax.axhline(0, color="0.7", linewidth=0.8)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    ax.set_xlim(0, 4)
    ax.set_ylim(-1.2, 1.2)
    ax.legend(loc="upper right", fontsize=11, ncol=2)
    save_fig("fig-aliasing-sines.png")


# ---------------------------------------------------------------------------
# 3. Nyquist bandwidth: properly sampled vs. undersampled (overlap)
# ---------------------------------------------------------------------------


def _baseband(ax, center, f_max, color, alpha):
    xs = np.linspace(center - f_max, center + f_max, 200)
    shape = 0.6 * (1 + 0.35 * np.cos(2 * np.pi * 3 * (xs - center) / (2 * f_max)))
    ax.fill_between(xs, 0, shape, color=color, alpha=alpha, linewidth=0)
    ax.plot(xs, shape, color=color, linewidth=1.5, alpha=min(1, alpha + 0.3))


def fig_nyquist_bandwidth() -> None:
    f_max = 1.0
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6))

    # properly sampled: f_s = 3 > 2 f_max, copies clear of baseband
    f_s = 3.0
    for k in range(-2, 3):
        _baseband(ax1, k * f_s, f_max, BLUE if k == 0 else PURPLE, 0.5 if k == 0 else 0.25)
    for xline, lab, col in [(-f_s, r"$-f_s$", RED), (f_s, r"$f_s$", RED),
                            (-f_max, r"$-f_{\max}$", BLUE), (f_max, r"$f_{\max}$", BLUE)]:
        ax1.axvline(xline, color=col, linewidth=1.3, alpha=0.7)
        ax1.annotate(lab, xy=(xline, 1.02), ha="center", fontsize=12, color=col)
    ax1.text(0.5, 0.98, r"$f_s > 2 f_{\max}$: copies stay separate", transform=ax1.transAxes,
             ha="center", va="top", fontsize=13, color="0.3")

    # undersampled: f_s = 1.5 < 2 f_max, copies overlap baseband
    f_s = 1.5
    for k in range(-3, 4):
        _baseband(ax2, k * f_s, f_max, BLUE if k == 0 else PURPLE, 0.5 if k == 0 else 0.28)
    ax2.text(0.5, 0.9, r"$f_s < 2 f_{\max}$: copies overlap (aliasing)",
             transform=ax2.transAxes, ha="center", va="top", fontsize=13, color=RED)

    for ax in (ax1, ax2):
        ax.axhline(0, color="0.6", linewidth=1.0)
        ax.set_ylim(0, 1.35)
        ax.set_yticks([])
        ax.set_xlim(-5, 5)
    ax2.set_xlabel("Frequency (Hz)")
    save_fig("fig-nyquist-bandwidth.png")


# ---------------------------------------------------------------------------
# 4. Aliasing in practice: a pitch sweep at three sample rates
# ---------------------------------------------------------------------------

# MIDI-note control points (time_s, midi) rising A3 -> A5 -> A3.
STEP_PWL = [(0.0, 57), (1.0, 57), (6.0, 81), (7.0, 81), (12.0, 57), (13.0, 57)]


def sweep_freq(t: np.ndarray) -> np.ndarray:
    times = [p[0] for p in STEP_PWL]
    steps = [p[1] for p in STEP_PWL]
    midi = np.interp(t, times, steps)
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def fig_aliasing_practice() -> None:
    dur = STEP_PWL[-1][0]
    rates = [2000, 1000, 500]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharex=True)
    for ax, f_s in zip(axes, rates):
        t = np.linspace(0, dur, 1500)
        f = sweep_freq(t)
        ax.plot(t, f, color=BLUE, label="true frequency")
        ax.plot(t, alias_freq(f, f_s), color=ORANGE, linestyle="--", label="heard (aliased)")
        ax.axhline(f_s / 2, color=RED, linewidth=1.3, label="Nyquist $f_s/2$")
        ax.set_title(f"$f_s = {f_s}$ Hz", fontsize=14)
        ax.set_xlabel("Time (s)")
        ax.set_ylim(0, 1000)
    axes[0].set_ylabel("Frequency (Hz)")
    axes[0].legend(fontsize=10, loc="upper right")
    save_fig("fig-aliasing-practice.png")


# ---------------------------------------------------------------------------
# 5. Quantization: staircase and noise at low bit depths
# ---------------------------------------------------------------------------


def quantize(x: np.ndarray, b: int) -> np.ndarray:
    levels = 2 ** (b - 1) - 1
    return np.round(x * levels) / levels


def fig_quantization() -> None:
    t = np.linspace(0, 1, 800)
    x = 0.9 * np.sin(2 * np.pi * 2 * t)
    fig, axes = plt.subplots(1, 2, figsize=(13, 4), sharey=True)
    for ax, b in zip(axes, (2, 4)):
        xq = quantize(x, b)
        ax.plot(t, x, color=BLUE, alpha=0.5, label="original")
        ax.plot(t, xq, color=RED, drawstyle="steps-mid", linewidth=1.5,
                label=f"quantized ($b={b}$)")
        for lvl in np.arange(-(2**(b-1) - 1), 2**(b-1)) / (2**(b-1) - 1):
            ax.axhline(lvl, color="0.85", linewidth=0.8, zorder=0)
        ax.set_title(f"$b = {b}$ bits ($2^{b} = {2**b}$ levels)", fontsize=14)
        ax.set_xlabel("Time (s)")
        ax.legend(fontsize=10, loc="upper right")
    axes[0].set_ylabel("Amplitude")
    save_fig("fig-quantization.png")


# ---------------------------------------------------------------------------
# 6. Anti-aliasing filter before sampling
# ---------------------------------------------------------------------------


def fig_antialiasing() -> None:
    f = np.linspace(0, 40, 1000)
    # a spectrum with content extending past 20 kHz
    spec = np.exp(-f / 12) * (1 + 0.3 * np.sin(2 * np.pi * f / 5) ** 2)
    spec = spec / spec.max()
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.fill_between(f, 0, spec, color=BLUE, alpha=0.3)
    ax.plot(f, spec, color=BLUE, label="signal spectrum")
    # ideal filter response
    cutoff = 20.0
    ax.plot([0, cutoff, cutoff, 40], [1.05, 1.05, 0, 0], color=RED, linewidth=2.0,
            label="anti-aliasing filter")
    ax.fill_between(f[f > cutoff], 0, spec[f > cutoff], color=RED, alpha=0.25,
                    hatch="//", label="removed before sampling")
    ax.axvline(cutoff, color=RED, linestyle=":", linewidth=1.5)
    ax.annotate("20 kHz", xy=(cutoff, 1.08), ha="center", fontsize=12, color=RED)
    ax.set_xlabel("Frequency (kHz)")
    ax.set_ylabel("Amplitude")
    ax.set_xlim(0, 40)
    ax.set_ylim(0, 1.2)
    ax.legend(fontsize=11)
    save_fig("fig-antialiasing.png")


# ---------------------------------------------------------------------------
# 7. Resampling by interpolation
# ---------------------------------------------------------------------------


def fig_resampling() -> None:
    f0 = 1.2
    n1 = np.arange(0, 9)
    fs1 = 8.0
    x1 = np.sin(2 * np.pi * f0 * n1 / fs1)
    fs2 = 12.0
    n2 = np.arange(0, int(len(n1) * fs2 / fs1))
    p = n2 * fs1 / fs2
    lo = np.floor(p).astype(int)
    alpha = p - lo
    hi = np.minimum(lo + 1, len(x1) - 1)
    y = (1 - alpha) * x1[lo] + alpha * x1[hi]

    fig, ax = plt.subplots(figsize=(12, 4))
    tt = np.linspace(0, (len(n1) - 1) / fs1, 500)
    ax.plot(tt, np.sin(2 * np.pi * f0 * tt), color="0.8", linewidth=1.2,
            label="underlying signal")
    stem(ax, n1 / fs1, x1, BLUE)
    ax.plot(n1 / fs1, x1, "o", color=BLUE, markersize=9, label="original ($f_s^1 = 8$ Hz)")
    ax.plot(n2 / fs2, y, "x", color=RED, markersize=9, markeredgewidth=2.5,
            label="resampled ($f_s^2 = 12$ Hz)")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    ax.legend(fontsize=11, loc="upper right")
    save_fig("fig-resampling.png")


# ---------------------------------------------------------------------------
# Audio examples
# ---------------------------------------------------------------------------


def make_audio() -> None:
    # Aliasing sonification: synthesize the pitch sweep at low f_s, then
    # resample to F_S for playback (the aliasing is baked in at synthesis).
    dur = STEP_PWL[-1][0]
    for f_s in (2000, 1000, 500):
        n = np.arange(int(dur * f_s))
        f = sweep_freq(n / f_s)
        x = phase_osc(f, f_s)
        audio = pq.Audio(x.astype(np.float32), f_s).resample(F_S)
        write_audio(np.asarray(audio.samples).reshape(-1), f"audio-alias-{f_s}.wav")


def main() -> None:
    print("Figures:")
    fig_sampling_domains()
    fig_aliasing_sines()
    fig_nyquist_bandwidth()
    fig_aliasing_practice()
    fig_quantization()
    fig_antialiasing()
    fig_resampling()
    print("Audio:")
    make_audio()


if __name__ == "__main__":
    main()
