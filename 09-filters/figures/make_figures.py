"""Generate figures and sound examples for Chapter 9 (Filters).

Outputs are written to ../assets/. This file is *not* student-facing.

Run with the project virtualenv (pyquist reached via PYTHONPATH):
    PYTHONPATH=../../../../pyquist ../../../.venv/bin/python make_figures.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pyquist as pq
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
ASSETS.mkdir(exist_ok=True)

F_S = 44100
PEAK_DBFS = -6.0

plt.rcParams.update({
    "font.size": 14, "axes.labelsize": 16, "xtick.labelsize": 13,
    "ytick.labelsize": 13, "axes.spines.top": False, "axes.spines.right": False,
    "lines.linewidth": 2.0,
})
COLORS = plt.rcParams["axes.prop_cycle"].by_key()["color"]
# Chapter color convention: x (input) is blue, h (filter) is red, y (output) is purple.
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


# ---------------------------------------------------------------------------
# 1. What is a filter? Input -> g -> output black box (with type signatures).
# ---------------------------------------------------------------------------


def fig_filter_blackbox() -> None:
    fig, ax = plt.subplots(figsize=(11, 3.6))
    ax.axis("off")
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 4)

    # top row: input -> box -> output
    y0 = 2.9
    xin, xout = 3.0, 10.6
    ax.text(xin, 3.55, "Input", ha="center", fontsize=14, color="0.35")
    ax.text(6.0, 3.55, "Filter", ha="center", fontsize=14, style="italic", color="0.35")
    ax.text(xout, 3.55, "Output", ha="center", fontsize=14, color="0.35")
    ax.text(xin, y0, r"$x[n]$", ha="center", va="center", fontsize=20, color=BLUE)
    ax.add_patch(FancyBboxPatch((5.1, y0 - 0.45), 1.8, 0.9,
                                boxstyle="round,pad=0.03", facecolor="0.92",
                                edgecolor="0.3", linewidth=1.6))
    ax.text(6.0, y0, r"$g$", ha="center", va="center", fontsize=22)
    ax.text(xout, y0, r"$y[n]$", ha="center", va="center", fontsize=20, color=PURPLE)
    for x0, x1 in [(3.9, 5.0), (7.0, 9.6)]:
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y0), arrowstyle="-|>",
                                     mutation_scale=20, color="0.35", lw=1.8))

    # annotation rows: as a function / as an array
    ax.text(0.1, 1.55, "As a function", fontsize=13, style="italic", color="0.35", va="center")
    ax.text(xin, 1.55, r"$x : \mathbb{N} \to \mathbb{R}$", ha="center", fontsize=16, color=BLUE)
    ax.text(6.0, 1.55, r"$g : x \mapsto y$", ha="center", fontsize=16)
    ax.text(xout, 1.55, r"$y : \mathbb{N} \to \mathbb{R}$", ha="center", fontsize=16, color=PURPLE)
    ax.text(0.1, 0.6, "As an array", fontsize=13, style="italic", color="0.35", va="center")
    ax.text(xin, 0.6, r"$x \in \mathbb{R}^N$", ha="center", fontsize=16, color=BLUE)
    ax.text(xout, 0.6, r"$y \in \mathbb{R}^N$", ha="center", fontsize=16, color=PURPLE)
    save_fig("fig-filter-blackbox.png")


# ---------------------------------------------------------------------------
# 2. High-level goal: sculpting the frequency domain, |Y| = |H| . |X|.
# ---------------------------------------------------------------------------


def fig_lti_goal() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14, 3.6))
    f = np.linspace(0, 1, 500)
    # input line spectrum: a handful of decreasing partials
    fx = np.array([0.10, 0.22, 0.34, 0.50, 0.66, 0.80])
    ax_amp = np.array([1.0, 0.85, 0.7, 0.55, 0.42, 0.30])
    # filter magnitude response: a smooth band emphasis peaking mid-low
    H = np.exp(-((f - 0.30) ** 2) / (2 * 0.16 ** 2))
    H = H / H.max()

    def Hval(freqs):
        return np.interp(freqs, f, H)

    stem(axes[0], fx, ax_amp, BLUE, ms=6)
    axes[0].set_title(r"Input  $|X[m]|$", fontsize=15, color=BLUE)
    axes[1].plot(f, H, color=RED)
    axes[1].fill_between(f, 0, H, color=RED, alpha=0.15)
    axes[1].set_title(r"Filter  $|H[m]|$", fontsize=15, color=RED)
    stem(axes[2], fx, ax_amp * Hval(fx), PURPLE, ms=6)
    axes[2].set_title(r"Output  $|Y[m]| = |H[m]|\,|X[m]|$", fontsize=15, color=PURPLE)
    for ax in axes:
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1.1)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["0", r"$f_s/2$"])
        ax.set_yticks([])
        ax.set_xlabel("Frequency")
    save_fig("fig-lti-goal.png")


# ---------------------------------------------------------------------------
# 3. Difference equation example 1: y[n] = x[n] + x[n-3].
# ---------------------------------------------------------------------------

_SQUARE = np.array(([1.0] * 5 + [-1.0] * 5) * 4)  # 10-sample period, 40 samples


def _diffeq_panels(rows, labels, colors, warmup, fname, ylim=(-2.3, 2.3)):
    N = 32
    n = np.arange(N)
    fig, axes = plt.subplots(3, 1, figsize=(11, 5.4), sharex=True)
    for ax, data, lab, col in zip(axes, rows, labels, colors):
        if warmup > 0:
            ax.axvspan(-0.5, warmup - 0.5, color="0.85", alpha=0.7)
        stem(ax, n, data[:N], col, ms=5)
        ax.set_ylabel(lab, fontsize=15, color=col)
        ax.set_ylim(*ylim)
        ax.set_xlim(-0.5, N - 0.5)
        ax.axhline(0, color="0.8", lw=0.8)
    axes[-1].set_xlabel(r"Sample index $n$")
    save_fig(fname)


def fig_diffeq_delay() -> None:
    x = _SQUARE
    xd = np.concatenate([np.zeros(3), x])[:len(x)]  # x[n-3], zeros before n=0
    y = x + xd
    _diffeq_panels(
        [x, xd, y],
        [r"$x[n]$", r"$x[n-3]$", r"$y[n]$"],
        [BLUE, RED, PURPLE],
        warmup=3,
        fname="fig-diffeq-delay.png",
    )


def fig_diffeq_difference() -> None:
    x = _SQUARE
    xd = np.concatenate([np.zeros(1), x])[:len(x)]  # x[n-1]
    half_x = 0.5 * x
    neg_half_xd = -0.5 * xd
    y = half_x + neg_half_xd
    _diffeq_panels(
        [half_x, neg_half_xd, y],
        [r"$\frac{1}{2}x[n]$", r"$-\frac{1}{2}x[n-1]$", r"$y[n]$"],
        [BLUE, RED, PURPLE],
        warmup=1,
        fname="fig-diffeq-difference.png",
        ylim=(-1.2, 1.2),
    )


# ---------------------------------------------------------------------------
# 4. What do these filters do to sound? spectra + audio (441 Hz square wave).
# ---------------------------------------------------------------------------


def fig_diffeq_spectra() -> None:
    f0 = 441.0
    period = int(round(F_S / f0))          # ~100 samples
    dur = 1.5
    reps = int(np.ceil(dur * F_S / period))
    one = np.array([1.0] * (period // 2) + [-1.0] * (period - period // 2))
    x = np.tile(one, reps)[:int(dur * F_S)]
    y1 = x + np.concatenate([np.zeros(3), x])[:len(x)]         # comb: x[n] + x[n-3]
    y2 = 0.5 * x - 0.5 * np.concatenate([np.zeros(1), x])[:len(x)]  # difference

    write_audio(x, "audio-diffeq-input.wav")
    write_audio(y1, "audio-diffeq-y1.wav")
    write_audio(y2, "audio-diffeq-y2.wav")

    def spec_db(sig):
        S = np.abs(np.fft.rfft(sig * np.hanning(len(sig))))
        f = np.fft.rfftfreq(len(sig), 1 / F_S)
        S = S / S.max()
        return f, 20 * np.log10(S + 1e-9)

    fig, axes = plt.subplots(1, 3, figsize=(14, 3.6), sharey=True)
    for ax, sig, title, col in zip(
        axes, [x, y1, y2],
        [r"$x[n]$ (square wave)", r"$y_1[n]=x[n]+x[n-3]$", r"$y_2[n]=\frac{1}{2}x[n]-\frac{1}{2}x[n-1]$"],
        [BLUE, PURPLE, PURPLE],
    ):
        f, S = spec_db(sig)
        ax.plot(f, S, color=col, linewidth=1.0)
        ax.fill_between(f, -80, S, color=col, alpha=0.2)
        ax.set_title(title, fontsize=13, color=col)
        ax.set_xlim(0, 10000)
        ax.set_ylim(-70, 3)
        ax.set_xlabel("Frequency (Hz)")
    axes[0].set_ylabel("Amplitude (dB)")
    save_fig("fig-diffeq-spectra.png")


# ---------------------------------------------------------------------------
# 5. Example of convolution: x=[1,1,1], h=[3,2,1], y = h*x = [3,5,6,3,1].
# ---------------------------------------------------------------------------


def fig_convolution_example() -> None:
    x = np.array([1.0, 1.0, 1.0])
    h = np.array([3.0, 2.0, 1.0])
    y = np.convolve(x, h)  # [3, 5, 6, 3, 1]
    fig, axes = plt.subplots(1, 3, figsize=(14, 3.4))
    idx = np.arange(6)
    stem(axes[0], np.arange(len(x)), x, BLUE)
    axes[0].set_title(r"$x[n] = [1,1,1]$  ($N=3$)", fontsize=14, color=BLUE)
    stem(axes[1], np.arange(len(h)), h, RED)
    axes[1].set_title(r"$h[n] = [3,2,1]$  ($K=3$)", fontsize=14, color=RED)
    stem(axes[2], np.arange(len(y)), y, PURPLE)
    axes[2].set_title(r"$y = h * x$  ($N+K-1 = 5$)", fontsize=14, color=PURPLE)
    for ax in axes:
        ax.set_xlim(-0.5, 5.5)
        ax.set_ylim(0, 6.5)
        ax.set_xticks(idx)
        ax.set_xlabel(r"$n$")
    axes[0].set_ylabel("Amplitude")
    save_fig("fig-convolution-example.png")


# ---------------------------------------------------------------------------
# 6. Recursive filters: signal flow diagrams (ordinary vs recursive).
# ---------------------------------------------------------------------------


def _adder(ax, cx, cy, r=0.16):
    ax.add_patch(Circle((cx, cy), r, facecolor="white", edgecolor="0.2", lw=1.6, zorder=3))
    ax.text(cx, cy, "+", ha="center", va="center", fontsize=16, zorder=4)


def _delay(ax, cx, cy, w=0.5, h=0.36):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle="round,pad=0.01", facecolor="0.92",
                                edgecolor="0.3", lw=1.5, zorder=3))
    ax.text(cx, cy, r"$z^{-1}$", ha="center", va="center", fontsize=13, zorder=4)


def _arrow(ax, p0, p1, color="0.3"):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=14,
                                 color=color, lw=1.6, shrinkA=0, shrinkB=0, zorder=2))


def _wire(ax, pts, color="0.3"):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=color, lw=1.6, zorder=1)


def fig_recursive_signalflow() -> None:
    fig, (axo, axr) = plt.subplots(1, 2, figsize=(13, 3.8))
    for ax in (axo, axr):
        ax.axis("off")
        ax.set_xlim(0, 5)
        ax.set_ylim(0, 3)

    # --- Ordinary (feedforward only): y[n] = x[n] + x[n-1] ---
    ax = axo
    yline = 2.2
    ax.text(0.15, yline, r"$x[n]$", ha="center", va="center", fontsize=15, color=BLUE)
    _wire(ax, [(0.5, yline), (1.3, yline)])          # into split node
    ax.add_patch(Circle((1.3, yline), 0.04, color="0.3", zorder=3))
    _wire(ax, [(1.3, yline), (3.5, yline)])          # top direct path to adder
    _arrow(ax, (3.5, yline), (3.84, yline))
    _wire(ax, [(1.3, yline), (1.3, 1.0)])            # down to delay
    _delay(ax, 1.9, 1.0)
    _wire(ax, [(1.3, 1.0), (1.66, 1.0)])
    _arrow(ax, (2.14, 1.0), (4.0, 1.0))              # delayed path
    _wire(ax, [(4.0, 1.0), (4.0, yline - 0.16)])
    _adder(ax, 4.0, yline)
    _arrow(ax, (4.16, yline), (4.85, yline))
    ax.text(4.95, yline, r"$y[n]$", ha="left", va="center", fontsize=15, color=PURPLE)
    ax.set_title("Ordinary (feedforward only)", fontsize=13)
    ax.text(2.5, 0.25, r"$y[n] = x[n] + x[n-1]$", ha="center", fontsize=13, color="0.3")

    # --- Recursive (with feedback): y[n] = x[n] + x[n-1] + y[n-1] ---
    ax = axr
    yline = 2.2
    fb = 0.75
    ax.text(0.05, yline, r"$x[n]$", ha="center", va="center", fontsize=15, color=BLUE)
    _wire(ax, [(0.4, yline), (1.2, yline)])
    ax.add_patch(Circle((1.2, yline), 0.04, color="0.3", zorder=3))
    _wire(ax, [(1.2, yline), (2.7, yline)])          # direct to adder
    _arrow(ax, (2.7, yline), (2.84, yline))
    _wire(ax, [(1.2, yline), (1.2, yline + 0.55)])   # up to feedforward delay
    _delay(ax, 1.8, yline + 0.55)
    _wire(ax, [(1.2, yline + 0.55), (1.56, yline + 0.55)])
    _wire(ax, [(2.04, yline + 0.55), (3.0, yline + 0.55), (3.0, yline + 0.16)])
    _arrow(ax, (3.0, yline + 0.4), (3.0, yline + 0.16))
    _adder(ax, 3.0, yline)
    _wire(ax, [(3.16, yline), (4.3, yline)])         # output
    ax.add_patch(Circle((3.7, yline), 0.04, color="0.3", zorder=3))
    _arrow(ax, (4.3, yline), (4.55, yline))
    ax.text(4.62, yline, r"$y[n]$", ha="left", va="center", fontsize=15, color=PURPLE)
    _wire(ax, [(3.7, yline), (3.7, fb)])             # feedback tap down
    _delay(ax, 3.1, fb)
    _wire(ax, [(3.34, fb), (3.7, fb)])
    _wire(ax, [(2.86, fb), (3.0, fb), (3.0, yline - 0.16)])
    _arrow(ax, (3.0, fb + 0.05), (3.0, yline - 0.16))
    ax.set_title("Recursive (with feedback)", fontsize=13)
    ax.text(2.5, 0.15, r"$y[n] = x[n] + x[n-1] + y[n-1]$", ha="center", fontsize=13, color="0.3")
    save_fig("fig-recursive-signalflow.png")


# ---------------------------------------------------------------------------
# 7. Filter types: idealized magnitude responses (low/high/band pass, notch).
# ---------------------------------------------------------------------------


def fig_filter_types() -> None:
    f = np.linspace(0, 1, 1000)
    order = 8

    def butter_lp(fc):
        return 1 / np.sqrt(1 + (f / fc) ** (2 * order))

    def butter_hp(fc):
        return (f / fc) ** order / np.sqrt(1 + (f / fc) ** (2 * order))

    lp = butter_lp(0.35)
    hp = butter_hp(0.35)
    bp = butter_hp(0.30) * butter_lp(0.65)
    notch = 1 - butter_hp(0.36) * butter_lp(0.60)

    fig, axes = plt.subplots(2, 2, figsize=(13, 6.5))
    specs = [
        (axes[0, 0], lp, "Low pass", [0.35], "pass low frequencies"),
        (axes[0, 1], hp, "High pass", [0.35], "pass high frequencies"),
        (axes[1, 0], bp, "Band pass", [0.30, 0.65], "pass a band"),
        (axes[1, 1], notch, "Band stop (notch)", [0.36, 0.60], "reject a band"),
    ]
    for ax, mag, title, cuts, _desc in specs:
        ax.plot(f, mag, color=RED)
        ax.fill_between(f, 0, mag, where=mag > 0.5, color=GREEN, alpha=0.18)
        for fc in cuts:
            ax.axvline(fc, color="0.5", ls="--", lw=1.2)
        ax.set_title(title, fontsize=14)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1.15)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["0", r"$f_s/2$"])
        ax.set_yticks([0, 1])
        ax.set_xlabel("Frequency")
        ax.set_ylabel(r"$|H(f)|$")
    # annotate anatomy on the low-pass panel
    ax = axes[0, 0]
    ax.annotate("passband", xy=(0.15, 0.5), xytext=(0.15, 0.2), ha="center",
                fontsize=11, color="0.25")
    ax.annotate("stopband", xy=(0.7, 0.05), xytext=(0.7, 0.35), ha="center",
                fontsize=11, color="0.25")
    ax.annotate("cutoff\n" + r"$f_c$", xy=(0.35, 0.5), xytext=(0.52, 0.72),
                ha="center", fontsize=11, color="0.25",
                arrowprops=dict(arrowstyle="->", color="0.4"))
    save_fig("fig-filter-types.png")


# ---------------------------------------------------------------------------
# 8. Empirical frequency response of a 2-tap averager y[n] = x[n] + x[n-1].
# ---------------------------------------------------------------------------


def fig_frequency_response() -> None:
    fs = 48000

    def sinusoid(freq):
        n = np.arange(fs)  # one second
        return np.cos(2 * np.pi * freq * n / fs)

    def amplitude(sig):
        # A pure sinusoid of amplitude A has RMS A/sqrt(2), so sqrt(2)*RMS
        # recovers its amplitude exactly, independent of the sample grid.
        return np.sqrt(2) * np.sqrt(np.mean(sig ** 2))

    test = np.linspace(0, fs / 2, 40)
    empirical = []
    for freq in test:
        x = sinusoid(freq)
        y = x[1:] + x[:-1]              # y[n] = x[n] + x[n-1]
        empirical.append(amplitude(y))
    empirical = np.array(empirical)

    fine = np.linspace(0, fs / 2, 500)
    analytical = 2 * np.abs(np.cos(np.pi * fine / fs))

    fig, ax = plt.subplots(figsize=(13, 4.0))
    ax.plot(fine, analytical, color=RED, lw=2.2,
            label=r"analytical  $2\,|\cos(\pi f / f_s)|$")
    stem(ax, test, empirical, BLUE)
    ax.plot([], [], color=BLUE, marker="o", lw=0, label="empirical (probe sinusoids)")
    ax.set_xlim(0, fs / 2)
    ax.set_ylim(0, 2.2)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Output amplitude")
    ax.legend(loc="upper right", fontsize=12)
    save_fig("fig-frequency-response.png")


# ---------------------------------------------------------------------------
# 9. Sliding-convolution animation (GIF): reversed filter slides across x.
# ---------------------------------------------------------------------------


def fig_convolution_sliding() -> None:
    from PIL import Image

    x = np.array([0, 0, 1, 2, 3, 3, 2, 1, 0, 1, 2, 1, 0, 0], dtype=float)
    h = np.array([3.0, 2.0, 1.0])           # asymmetric, so the reversal is visible
    K = len(h)
    y = np.convolve(x, h)
    xlim = (-K, len(y) + 0.5)

    frames = []
    order = list(range(len(y))) + [len(y) - 1] * 4  # hold on the last frame
    for n in order:
        fig, (axt, axb) = plt.subplots(2, 1, figsize=(9, 4.6), sharex=True)
        # top: input x (blue) with the reversed filter overlaid at position n
        stem(axt, np.arange(len(x)), x, BLUE, ms=6)
        axt.axvspan(n - K + 0.5, n + 0.5, color=RED, alpha=0.10)
        taps = [n - k for k in range(K)]        # tap k sits at index n-k
        stem(axt, taps, h, RED, ms=6)
        axt.set_ylabel(r"$x[n]$ and reversed $h$", fontsize=12)
        axt.set_ylim(-0.5, 3.5)
        # bottom: output y built up to index n, current sample highlighted
        stem(axb, np.arange(n + 1), y[:n + 1], PURPLE, ms=5)
        axb.plot([n], [y[n]], "o", color=PURPLE, ms=12)
        axb.set_ylabel(r"$y = h * x$", fontsize=12)
        axb.set_xlabel(r"Sample index $n$")
        axb.set_ylim(0, y.max() * 1.15)
        for ax in (axt, axb):
            ax.set_xlim(*xlim)
            ax.axhline(0, color="0.8", lw=0.8)
        fig.tight_layout()
        fig.canvas.draw()
        frames.append(Image.fromarray(np.asarray(fig.canvas.buffer_rgba())).convert("RGB"))
        plt.close(fig)

    pal = frames[0].convert("P", palette=Image.ADAPTIVE, colors=255)
    frames_p = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    frames_p[0].save(str(ASSETS / "fig-convolution-sliding.gif"), save_all=True,
                     append_images=frames_p[1:], duration=450, loop=0, disposal=2)
    print("  wrote fig-convolution-sliding.gif")


# ---------------------------------------------------------------------------
# 10. Room impulse response animation (GIF): reflections arrive over time.
# ---------------------------------------------------------------------------


def fig_room_ir() -> None:
    from PIL import Image

    W, H = 10.0, 7.0        # room dimensions (meters)
    S = np.array([2.0, 2.0])  # source
    M = np.array([8.0, 5.2])  # microphone
    c = 343.0                 # speed of sound (m/s)

    def reflect_point(image, wall_axis, wall_val):
        # intersection of the segment image->M with the wall plane
        t = (wall_val - image[wall_axis]) / (M[wall_axis] - image[wall_axis])
        return image + t * (M - image)

    # direct path plus first-order reflections off each of the four walls
    arrivals = []  # (delay_s, amplitude, polyline points or None)
    d0 = np.linalg.norm(M - S)
    arrivals.append((d0 / c, 1.0, [S, M]))
    walls = [(np.array([-S[0], S[1]]), 0, 0.0),          # left wall x=0
             (np.array([2 * W - S[0], S[1]]), 0, W),      # right wall x=W
             (np.array([S[0], -S[1]]), 1, 0.0),           # bottom wall y=0
             (np.array([S[0], 2 * H - S[1]]), 1, H)]      # top wall y=H
    for image, axis, val in walls:
        R = reflect_point(image, axis, val)
        dist = np.linalg.norm(R - S) + np.linalg.norm(M - R)
        arrivals.append((dist / c, d0 / dist, [S, R, M]))

    # a dense, decaying tail standing in for higher-order reflections
    rng = np.random.default_rng(1)
    t_last = max(a[0] for a in arrivals)
    for _ in range(28):
        td = t_last + rng.uniform(0.002, 0.055)
        arrivals.append((td, 0.55 * np.exp(-(td - t_last) / 0.02) * rng.uniform(0.4, 1.0), None))
    t_max = max(a[0] for a in arrivals) + 0.005

    frames = []
    for cursor in np.linspace(0, t_max, 44):
        fig, (axl, axr) = plt.subplots(1, 2, figsize=(11, 4.0),
                                       gridspec_kw={"width_ratios": [1, 1.3]})
        # left: the room, source, mic, expanding wavefront, arrived paths
        axl.add_patch(plt.Rectangle((0, 0), W, H, fill=False, edgecolor="0.3", lw=2))
        axl.plot(*S, "s", color=BLUE, ms=11)
        axl.plot(*M, "o", color=RED, ms=11)
        axl.text(S[0], S[1] - 0.6, "source", ha="center", color=BLUE, fontsize=11)
        axl.text(M[0], M[1] + 0.5, "mic", ha="center", color=RED, fontsize=11)
        axl.add_patch(plt.Circle(S, c * cursor, fill=False, edgecolor=BLUE,
                                 lw=1.0, alpha=0.35))
        for delay, _amp, poly in arrivals:
            if poly is not None and delay <= cursor:
                pts = np.array(poly)
                axl.plot(pts[:, 0], pts[:, 1], color="0.45", lw=1.3, alpha=0.7)
        axl.set_xlim(-0.5, W + 0.5)
        axl.set_ylim(-0.5, H + 0.5)
        axl.set_aspect("equal")
        axl.axis("off")
        axl.set_title("Room (top view)", fontsize=13)
        # right: the impulse response building up
        for delay, amp, _poly in arrivals:
            if delay <= cursor:
                axr.plot([delay * 1000, delay * 1000], [0, amp], color=PURPLE, lw=2)
                axr.plot(delay * 1000, amp, "o", color=PURPLE, ms=5)
        axr.axvline(cursor * 1000, color="0.6", lw=1.0, ls="--")
        axr.set_xlim(0, t_max * 1000)
        axr.set_ylim(0, 1.1)
        axr.set_xlabel("Delay (ms)")
        axr.set_ylabel("Amplitude")
        axr.set_title("Impulse response", fontsize=13)
        fig.tight_layout()
        fig.canvas.draw()
        frames.append(Image.fromarray(np.asarray(fig.canvas.buffer_rgba())).convert("RGB"))
        plt.close(fig)

    frames += [frames[-1]] * 6  # hold on the completed response
    pal = frames[0].convert("P", palette=Image.ADAPTIVE, colors=255)
    frames_p = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    frames_p[0].save(str(ASSETS / "fig-room-ir.gif"), save_all=True,
                     append_images=frames_p[1:], duration=140, loop=0, disposal=2)
    print("  wrote fig-room-ir.gif")


def main() -> None:
    print("Figures:")
    fig_filter_blackbox()
    fig_lti_goal()
    fig_diffeq_delay()
    fig_diffeq_difference()
    fig_convolution_example()
    fig_recursive_signalflow()
    fig_filter_types()
    fig_frequency_response()
    print("Spectra + audio:")
    fig_diffeq_spectra()
    print("Animations:")
    fig_convolution_sliding()
    fig_room_ir()


if __name__ == "__main__":
    main()
