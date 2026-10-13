"""Generate figures and sound examples for Chapter 12 (physical modeling).

Outputs are written to ../assets/. This file is *not* student-facing.

Sources:

- ../raw/{bachfugue,gtr-jazz,oboe-bassoon}.wav, sound examples from Julius O.
  Smith III's Physical Audio Signal Processing
  (https://ccrma.stanford.edu/~jos/waveguide/Sound_Examples.html): plucked
  strings on a NeXT computer (1989), an electric guitar with a bass pickup,
  and an oboe and bassoon on the Yamaha VL1 (1994). They are trimmed, mixed
  to mono, resampled to 44.1 kHz, and normalized.

Run with the project virtualenv (pyquist reached via PYTHONPATH):
    PYTHONPATH=../../../pyquist python make_figures.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pyquist as pq
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

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
WINE = "#8b1a1a"                                  # standing-wave envelopes


def save_fig(name: str) -> None:
    plt.tight_layout()
    plt.savefig(ASSETS / name, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  wrote {name}")


def write_audio(samples: np.ndarray, name: str) -> None:
    audio = pq.Audio(np.asarray(samples, dtype=np.float32), F_S)
    audio.normalize(peak_dbfs=PEAK_DBFS)
    audio.write(str(ASSETS / name))
    print(f"  wrote {name}")


def fade(x: np.ndarray, in_s: float = 0.005, out_s: float = 0.005) -> np.ndarray:
    x = x.copy()
    n_in, n_out = int(in_s * F_S), int(out_s * F_S)
    if n_in:
        x[:n_in] *= np.linspace(0.0, 1.0, n_in)
    if n_out:
        x[-n_out:] *= np.linspace(1.0, 0.0, n_out)
    return x


# ---------------------------------------------------------------------------
# The algorithms (mirrors of the chapter's notebooks)
# ---------------------------------------------------------------------------


def feedback_delay(x: np.ndarray, M: int, g: float = 1.0, lowpass: bool = False) -> np.ndarray:
    """y[n] = x[n] + g * y[n - M], or with the two-point average in the loop."""
    y = np.zeros(len(x))
    for n in range(len(x)):
        y[n] = x[n]
        if lowpass and n > M:
            y[n] += g * 0.5 * (y[n - M] + y[n - M - 1])
        elif not lowpass and n >= M:
            y[n] += g * y[n - M]
    return y


def decay_gain(M: float, duration: float, db: float = -60.0) -> float:
    """The loop gain that decays by `db` decibels after `duration` seconds."""
    return 10 ** (db * M / (20 * F_S * duration))


# ---------------------------------------------------------------------------
# Motivation: sound examples from Julius O. Smith's PASP
# ---------------------------------------------------------------------------

JOS = {"bachfugue.wav": ("audio-jos-strings.wav", 20.0),
       "gtr-jazz.wav": ("audio-jos-electric-guitar.wav", None),
       "oboe-bassoon.wav": ("audio-jos-oboe-bassoon.wav", 20.0)}


def audio_jos_examples() -> None:
    for src, (name, max_dur) in JOS.items():
        audio = pq.Audio.from_file(str(CHAPTER / "raw" / src)).as_mono().resample(F_S)
        x = np.asarray(audio.samples, dtype=np.float64).reshape(-1)
        if max_dur is not None and len(x) > max_dur * F_S:
            x = fade(x[:int(max_dur * F_S)], 0.0, 1.5)       # trim with a gentle fade-out
        write_audio(x, name)


# ---------------------------------------------------------------------------
# Musical acoustics: traveling waves, superposition, reflection
# ---------------------------------------------------------------------------


def _pulse(x: np.ndarray, center: float, width: float = 0.55) -> np.ndarray:
    return np.exp(-0.5 * ((x - center) / width) ** 2)


def fig_waves_gif() -> None:
    """Three panels animated together: a pulse traveling along a string, two
    pulses passing through each other, and a pulse reflecting (inverted) off a
    fixed end."""
    L = 10.0
    x = np.linspace(0.0, L, 800)
    frames, speed = 72, 2 * L / 72                     # each panel's story fits the loop
    fig, axes = plt.subplots(3, 1, figsize=(8, 6.6))
    titles = ["A pulse travels along the string",
              "Two pulses pass through each other, and their displacements add",
              "A pulse reflects at a fixed end, with opposite polarity"]
    lines = []
    for ax, title in zip(axes, titles):
        ax.set_xlim(0, L)
        ax.set_ylim(-1.3, 2.2)
        ax.axis("off")
        ax.set_title(title, fontsize=13, loc="left")
        ax.axhline(0, color="0.85", lw=1, zorder=0)
        lines.append(ax.plot([], [], color=BLUE, lw=2.5)[0])
    ghost_a = axes[1].plot([], [], color="0.6", lw=1.2, ls="--")[0]
    ghost_b = axes[1].plot([], [], color="0.6", lw=1.2, ls="--")[0]
    axes[2].plot([L, L], [-1.2, 1.2], color="0.2", lw=4)          # the fixed end
    axes[2].plot([L], [0], "o", color="0.2", ms=9)

    def update(i):
        t = i * speed
        lines[0].set_data(x, _pulse(x, -1.5 + t))
        a, b = _pulse(x, 1.0 + t / 2), _pulse(x, L - 1.0 - t / 2)
        ghost_a.set_data(x, a)
        ghost_b.set_data(x, b)
        lines[1].set_data(x, a + b)
        c = 1.5 + t                                     # incoming pulse center
        lines[2].set_data(x, _pulse(x, c) - _pulse(x, 2 * L - c))   # plus its inverted image
        return lines + [ghost_a, ghost_b]

    anim = FuncAnimation(fig, update, frames=frames, blit=True)
    anim.save(ASSETS / "fig-waves.gif", writer=PillowWriter(fps=18), dpi=80)
    plt.close()
    print("  wrote fig-waves.gif")


def fig_standing_wave_gif() -> None:
    """A right-traveling and a left-traveling sinusoid, and their sum: a
    standing wave whose nodes never move."""
    lam = 4.0
    x = np.linspace(0.0, 2.5 * lam, 800)
    k = 2 * np.pi / lam
    frames = 48
    fig, axes = plt.subplots(3, 1, figsize=(8, 6.2), sharex=True)
    labels = ["Traveling wave (to the right)", "Traveling wave (to the left)",
              "Their sum: a standing wave"]
    colors = [BLUE, ORANGE, PURPLE]
    lines = []
    for ax, label, color in zip(axes, labels, colors):
        ax.set_xlim(x[0], x[-1])
        ax.set_ylim(-2.3, 2.3)
        ax.axis("off")
        ax.set_title(label, fontsize=13, loc="left")
        ax.axhline(0, color="0.85", lw=1, zorder=0)
        lines.append(ax.plot([], [], color=color, lw=2.4)[0])
    nodes = np.arange(0, x[-1] + 1e-9, lam / 2)
    antinodes = nodes[:-1] + lam / 4
    axes[2].plot(nodes, 0 * nodes, "o", color="black", ms=8, zorder=3, label="nodes")
    axes[2].plot(antinodes, 0 * antinodes, "o", color="#C9A227", ms=8, zorder=3,
                 label="antinodes")
    axes[2].legend(loc="upper right", fontsize=11, frameon=False, ncol=2,
                   bbox_to_anchor=(1.0, 1.25))

    def update(i):
        wt = 2 * np.pi * i / frames
        right, left = np.sin(k * x - wt), np.sin(k * x + wt)
        lines[0].set_data(x, right)
        lines[1].set_data(x, left)
        lines[2].set_data(x, right + left)
        return lines

    anim = FuncAnimation(fig, update, frames=frames, blit=True)
    anim.save(ASSETS / "fig-standing-wave.gif", writer=PillowWriter(fps=16), dpi=80)
    plt.close()
    print("  wrote fig-standing-wave.gif")


# ---------------------------------------------------------------------------
# Standing waves and modes of oscillation
# ---------------------------------------------------------------------------


def fig_string_modes() -> None:
    """The first three standing waves on a string with fixed ends."""
    x = np.linspace(0, 1, 400)
    fig, axes = plt.subplots(3, 1, figsize=(10, 5.6))
    for i, ax in enumerate(axes, start=1):
        env = np.sin(i * np.pi * x)
        ax.plot(x, env, color=WINE, lw=2)
        ax.plot(x, -env, color=WINE, lw=2)
        ax.plot([0, 1], [0, 0], color="black", lw=1.4)
        ax.plot([0, 1], [0, 0], "o", color="black", ms=8)
        lam = {1: r"2L", 2: r"L", 3: r"\frac{2L}{3}"}[i]
        f = {1: r"\frac{v}{2L}", 2: r"2f_1", 3: r"3f_1"}[i]
        ax.text(1.08, 0, rf"$\lambda_{i} = {lam}$,  $f_{i} = {f}$", va="center", fontsize=15)
        ax.set_xlim(-0.02, 1.6)
        ax.set_ylim(-1.25, 1.25)
        ax.axis("off")
    axes[0].annotate("", xy=(0, 1.5), xytext=(1, 1.5), xycoords="data",
                     arrowprops=dict(arrowstyle="<->", color="0.3", lw=1.4))
    axes[0].text(0.5, 1.62, "$L$", ha="center", fontsize=16)
    axes[0].set_ylim(-1.25, 1.95)
    save_fig("fig-string-modes.png")


def fig_modes_table() -> None:
    """Modes 1-3 of a string with fixed ends, an open-open tube, and a
    closed-open tube, with their wavelengths and harmonic numbers."""
    x = np.linspace(0, 1, 300)
    fig, axes = plt.subplots(3, 3, figsize=(13, 5.2))
    heads = ["String (fixed ends)", "Tube (open at both ends)", "Tube (closed at the left end)"]
    for c, head in enumerate(heads):
        axes[0, c].set_title(head, fontsize=14, fontweight="bold", pad=12)
    for m in range(1, 4):
        for c in range(3):
            ax = axes[m - 1, c]
            ax.set_xlim(-0.08, 1.75)
            ax.set_ylim(-1.35, 1.35)
            ax.axis("off")
            if c == 0:                                   # string: nodes at both ends
                env, lam, h = np.sin(m * np.pi * x), {1: "2L", 2: "L", 3: "2L/3"}[m], m
                ax.plot([0, 1], [0, 0], color="black", lw=1.2)
                ax.plot([0, 1], [0, 0], "o", color="black", ms=6)
            else:
                ax.add_patch(Rectangle((0, -1.05), 1, 2.1, fill=False, edgecolor="0.25", lw=1.4))
                ax.plot([0, 1], [0, 0], color="0.6", lw=0.8, ls=":")
                if c == 1:                               # open-open: antinodes at both ends
                    env, lam, h = np.cos(m * np.pi * x), {1: "2L", 2: "L", 3: "2L/3"}[m], m
                    for xe in (0, 1):
                        ax.plot([xe, xe], [-1.05, 1.05], color="white", lw=2.5, zorder=3)
                        ax.plot([xe, xe], [-1.05, 1.05], color="0.25", lw=1, ls=":", zorder=4)
                else:                                    # closed-open: node at the closed end
                    env = np.sin((2 * m - 1) * np.pi * x / 2)
                    lam, h = {1: "4L", 2: "4L/3", 3: "4L/5"}[m], 2 * m - 1
                    ax.plot([0, 0], [-1.05, 1.05], color="0.1", lw=4)
                    ax.plot([1, 1], [-1.05, 1.05], color="white", lw=2.5, zorder=3)
                    ax.plot([1, 1], [-1.05, 1.05], color="0.25", lw=1, ls=":", zorder=4)
            ax.plot(x, 0.9 * env, color=WINE, lw=1.8)
            ax.plot(x, -0.9 * env, color=WINE, lw=1.8)
            ax.text(1.12, 0, rf"$\lambda = {lam}$" + "\n" + rf"$h = {h}$", va="center",
                    fontsize=13)
        axes[m - 1, 0].text(-0.3, 0, f"Mode {m}", ha="right", va="center", fontsize=14,
                            transform=axes[m - 1, 0].transData)
    save_fig("fig-modes-table.png")


# ---------------------------------------------------------------------------
# Physical modeling: properties of a string and their simulations
# ---------------------------------------------------------------------------


def fig_physical_model_map() -> None:
    """A plucked string, with each physical property paired with the
    simulation technique that models it."""
    fig, ax = plt.subplots(figsize=(12, 5.4))
    ax.set_xlim(-1.5, 11.5)
    ax.set_ylim(-3.6, 3.3)
    ax.axis("off")
    # The nut and bridge, and the plucked string (a triangle, pulled near the bridge).
    for xe, label in ((0, "nut"), (10, "bridge")):
        ax.add_patch(Rectangle((xe - 0.15, -0.9), 0.3, 1.0, facecolor="0.3", edgecolor="0.2"))
        ax.text(xe, -1.25, label, ha="center", va="top", fontsize=13, color="0.3")
    ax.plot([0, 8, 10], [0, 0.9, 0], color="black", lw=2.2)
    ax.plot([0, 10], [0, 0], color="0.75", lw=1.2, ls="--")
    # The pick.
    ax.add_patch(Polygon([[7.75, 1.7], [8.45, 1.7], [8.1, 1.05]], closed=True,
                         facecolor="0.15", edgecolor="0.15"))
    # The length of the string.
    ax.annotate("", xy=(0, -2.0), xytext=(10, -2.0),
                arrowprops=dict(arrowstyle="<->", color=GREEN, lw=1.8))
    ax.text(2.5, -1.85, "$L$", ha="center", va="bottom", fontsize=16, color=GREEN)

    def callout(xy, xytext, title, sim, color):
        ax.annotate("", xy=xy, xytext=xytext,
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=1.6))
        ax.text(*xytext, f"{title}\n" + r"$\rightarrow$ " + sim, ha="center", va="center",
                fontsize=13, color=color, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor=color))

    callout((8.1, 1.75), (8.4, 2.75), "Excitation (the pluck)", "a burst of noise", BLUE)
    callout((6.5, -2.05), (6.5, -3.1), "Propagation along the string", "delay", GREEN)
    callout((0.1, 0.15), (1.0, 2.45), "Reflection at the ends", "feedback", ORANGE)
    callout((4.0, 0.42), (4.6, 2.45), "Damping (friction)", "low-pass filter", PURPLE)
    save_fig("fig-physical-model-map.png")


# ---------------------------------------------------------------------------
# Signal-flow diagrams (in the style of Chapter 9)
# ---------------------------------------------------------------------------


def _adder(ax, cx, cy, r=0.18):
    ax.add_patch(Circle((cx, cy), r, facecolor="white", edgecolor="0.2", lw=1.8, zorder=3))
    ax.text(cx, cy, "+", ha="center", va="center", fontsize=20, zorder=4)


def _box(ax, cx, cy, text, w=0.7, h=0.44, fontsize=16):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle="round,pad=0.01",
                                facecolor="0.92", edgecolor="0.3", lw=1.6, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fontsize, zorder=4)


def _gain(ax, cx, cy, text, size=0.24, pointing="left", fontsize=13):
    s = size
    pts = ([[cx + s, cy + s], [cx + s, cy - s], [cx - s, cy]] if pointing == "left"
           else [[cx - s, cy + s], [cx - s, cy - s], [cx + s, cy]])
    ax.add_patch(Polygon(pts, closed=True, facecolor="white", edgecolor="0.3", lw=1.6, zorder=3))
    ax.text(cx + (s / 4 if pointing == "left" else -s / 4), cy, text, ha="center",
            va="center", fontsize=fontsize, zorder=4)


def _arrow(ax, p0, p1, color="0.3"):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=14,
                                 color=color, lw=1.6, shrinkA=0, shrinkB=0, zorder=2))


def _wire(ax, pts, color="0.3"):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=color, lw=1.6, zorder=1)


def _feedback_loop(ax, equation: str, with_gain: bool) -> None:
    X0, X1, AY, R = 0.9, 4.6, 2.0, 0.18
    C = 2.2
    tap = 3.9
    low = AY - 1.15
    ax.axis("off")
    ax.set_aspect("equal")
    ax.set_xlim(0, 5.4)
    ax.set_ylim(low - 0.45, AY + 1.0)
    ax.text((X0 + X1) / 2, AY + 0.7, equation, ha="center", fontsize=16, color="0.3")
    ax.text(X0 - 0.45, AY, r"$x[n]$", ha="center", va="center", fontsize=18, color=BLUE)
    _wire(ax, [(X0, AY), (C - R - 0.12, AY)])
    _arrow(ax, (C - R - 0.12, AY), (C - R, AY))
    _adder(ax, C, AY, r=R)
    _wire(ax, [(C + R, AY), (X1, AY)])
    _arrow(ax, (X1 - 0.14, AY), (X1, AY))
    ax.text(X1 + 0.15, AY, r"$y[n]$", ha="left", va="center", fontsize=18, color=PURPLE)
    ax.add_patch(Circle((tap, AY), 0.055, color="0.3", zorder=3))
    zc = 3.35 if with_gain else (C + tap) / 2
    _wire(ax, [(tap, AY), (tap, low), (zc + 0.35, low)])
    _box(ax, zc, low, r"$z^{-M}$")
    if with_gain:
        gc = 2.55
        _wire(ax, [(zc - 0.35, low), (gc + 0.24, low)])
        _gain(ax, gc, low, "$g$")
        _wire(ax, [(gc - 0.24, low), (C, low), (C, AY - R - 0.12)])
    else:
        _wire(ax, [(zc - 0.35, low), (C, low), (C, AY - R - 0.12)])
    _arrow(ax, (C, AY - R - 0.12), (C, AY - R))


def fig_feedback_delay() -> None:
    """The undamped and damped feedback delay lines, one figure each (they
    appear in different sections)."""
    for name, equation, with_gain in (
            ("fig-feedback-delay.png", r"$y[n] = x[n] + y[n-M]$", False),
            ("fig-feedback-delay-damped.png", r"$y[n] = x[n] + g \cdot y[n-M]$", True)):
        fig, ax = plt.subplots(figsize=(7.5, 3.6))
        _feedback_loop(ax, equation, with_gain)
        save_fig(name)


def fig_karplus_strong() -> None:
    """The Karplus-Strong signal flow: a noise burst, a delay of M samples, a
    two-point average, and an attenuation g in the feedback loop."""
    fig, ax = plt.subplots(figsize=(12, 4.0))
    X0, X1, AY, R, C, tap = 1.3, 8.6, 2.0, 0.2, 3.0, 7.9
    low = AY - 1.25
    ax.axis("off")
    ax.set_aspect("equal")
    ax.set_xlim(-0.2, 9.6)
    ax.set_ylim(low - 0.55, AY + 1.0)
    # The noise burst: one period of noise, then silence.
    rng = np.random.default_rng(1)
    t = np.linspace(-0.2, 1.0, 120)
    burst = np.where(t < 0.25, rng.uniform(-1, 1, len(t)), 0.0)
    ax.plot(0.1 + 1.0 * (t + 0.2), AY + 0.3 * burst, color=BLUE, lw=1.2)
    ax.text(0.7, AY - 0.55, "noise burst\n$x[n]$", ha="center", va="top", fontsize=14, color=BLUE)
    _wire(ax, [(X0, AY), (C - R - 0.12, AY)])
    _arrow(ax, (C - R - 0.12, AY), (C - R, AY))
    _adder(ax, C, AY, r=R)
    _wire(ax, [(C + R, AY), (X1, AY)])
    _arrow(ax, (X1 - 0.14, AY), (X1, AY))
    ax.text(X1 + 0.15, AY, r"$y[n]$", ha="left", va="center", fontsize=18, color=PURPLE)
    ax.add_patch(Circle((tap, AY), 0.06, color="0.3", zorder=3))
    _wire(ax, [(tap, AY), (tap, low), (7.3, low)])
    _box(ax, 6.85, low, r"$z^{-M}$", w=0.9)
    _wire(ax, [(6.4, low), (5.85, low)])
    _box(ax, 5.15, low, r"$\frac{1}{2}(1 + z^{-1})$", w=1.4, h=0.62, fontsize=15)
    _wire(ax, [(4.45, low), (4.14, low)])
    _gain(ax, 3.9, low, "$g$")
    _wire(ax, [(3.66, low), (C, low), (C, AY - R - 0.12)])
    _arrow(ax, (C, AY - R - 0.12), (C, AY - R))
    for xc, label in ((6.85, "delay"), (5.15, "low-pass"), (3.9, "attenuation")):
        ax.text(xc, low - 0.42, label, ha="center", va="top", fontsize=13, color="0.35")
    save_fig("fig-karplus-strong.png")


# ---------------------------------------------------------------------------
# Delay length quantization
# ---------------------------------------------------------------------------


def fig_delay_quantization() -> None:
    f = np.linspace(20, 8000, 4000)
    actual = F_S / np.round(F_S / f)
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.plot(f, f, color="0.7", lw=1.4, ls="--", label="desired frequency")
    ax.plot(f, actual, color=RED, lw=1.8, label=r"actual frequency, $f_s / \mathrm{round}(f_s / f)$")
    ax.set_xlabel("Desired frequency (Hz)")
    ax.set_ylabel("Frequency (Hz)")
    ax.set_xlim(0, 8000)
    ax.set_ylim(0, 8500)
    ax.legend(loc="upper left", fontsize=12, frameon=False)
    save_fig("fig-delay-quantization.png")


# ---------------------------------------------------------------------------
# Comb filters: undamped (propagation) and damped (attenuation)
# ---------------------------------------------------------------------------


def _ir(M: int, g: float, seconds: float) -> np.ndarray:
    x = np.zeros(int(seconds * F_S))
    x[0] = 1.0
    return feedback_delay(x, M, g)


def _magnitude_db(h: np.ndarray, n_fft: int = 1 << 16) -> tuple[np.ndarray, np.ndarray]:
    H = np.abs(np.fft.rfft(h, n_fft))
    return np.fft.rfftfreq(n_fft, 1 / F_S), 20 * np.log10(H / H.max() + 1e-12)


def fig_comb() -> None:
    """The impulse response of y[n] = x[n] + y[n - M] is an impulse train, and
    its spectrum is a comb with teeth at multiples of f_s / M."""
    M = 100
    h = _ir(M, 1.0, 0.25)
    fig, (axt, axf) = plt.subplots(1, 2, figsize=(13, 3.8))
    n = np.flatnonzero(h[:int(0.025 * F_S)])
    ml, sl, bl = axt.stem(n / F_S * 1000, h[n])
    plt.setp(ml, color=RED, markersize=5)
    plt.setp(sl, color=RED, linewidth=1.6)
    plt.setp(bl, color="0.7", linewidth=1.0)
    axt.set_xlabel("Time (ms)")
    axt.set_ylabel("Amplitude")
    axt.set_ylim(-0.05, 1.15)
    f, db = _magnitude_db(h * np.hanning(len(h)))
    axf.plot(f, db, color=RED, lw=1.2)
    for k in range(1, 12):
        axf.axvline(k * F_S / M, color="0.85", lw=0.8, zorder=0)
    axf.set_xlim(0, 4500)
    axf.set_ylim(-60, 3)
    axf.set_xlabel("Frequency (Hz)")
    axf.set_ylabel("Magnitude (dB)")
    save_fig("fig-comb.png")


def fig_comb_damped() -> None:
    """With attenuation g < 1, the impulse response decays exponentially, and
    the comb's teeth widen as g decreases."""
    M = 100
    fig, (axt, axf) = plt.subplots(1, 2, figsize=(13, 3.8))
    h = _ir(M, 0.8, 0.5)
    n = np.flatnonzero(h[:int(0.05 * F_S)])
    ml, sl, bl = axt.stem(n / F_S * 1000, h[n])
    plt.setp(ml, color=RED, markersize=5)
    plt.setp(sl, color=RED, linewidth=1.6)
    plt.setp(bl, color="0.7", linewidth=1.0)
    t = np.linspace(0, 50, 200)
    axt.plot(t, 0.8 ** (t / 1000 * F_S / M), color="0.5", lw=1.2, ls="--")
    axt.set_xlabel("Time (ms)")
    axt.set_ylabel("Amplitude")
    axt.set_ylim(-0.05, 1.15)
    for g, color in ((0.95, PURPLE), (0.8, RED), (0.5, ORANGE)):
        f, db = _magnitude_db(_ir(M, g, 0.5))
        axf.plot(f, db, color=color, lw=1.4, label=f"$g = {g}$")
    axf.set_xlim(0, 2300)
    axf.set_ylim(-35, 2)
    axf.set_xlabel("Frequency (Hz)")
    axf.set_ylabel("Magnitude (dB)")
    axf.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, fontsize=12,
               frameon=False)
    save_fig("fig-comb-damped.png")


# ---------------------------------------------------------------------------
# Damping with a low-pass filter
# ---------------------------------------------------------------------------


def _impulse_pluck(f0: float, duration: float, lowpass: bool) -> np.ndarray:
    M = round(F_S / f0 - (0.5 if lowpass else 0.0))
    g = decay_gain(M + (0.5 if lowpass else 0.0), duration)
    x = np.zeros(int(duration * F_S))
    x[0] = 1.0
    return feedback_delay(x, M, g, lowpass)


def fig_and_audio_lowpass() -> None:
    f0, dur = 110.0, 3.0
    plucks = {"gain only": _impulse_pluck(f0, dur, False),
              "gain and low-pass": _impulse_pluck(f0, dur, True)}
    write_audio(fade(plucks["gain only"], 0.0, 0.05), "audio-pluck-gain.wav")
    write_audio(fade(plucks["gain and low-pass"], 0.0, 0.05), "audio-pluck-lowpass.wav")
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.2), sharey=True)
    n_fft, hop = 4096, 512
    for ax, (title, y) in zip(axes, plucks.items()):
        frames = np.lib.stride_tricks.sliding_window_view(y, n_fft)[::hop] * np.hanning(n_fft)
        S = 20 * np.log10(np.abs(np.fft.rfft(frames, axis=1)).T + 1e-9)
        S -= S.max()
        f = np.fft.rfftfreq(n_fft, 1 / F_S)
        t = (np.arange(S.shape[1]) * hop + n_fft / 2) / F_S
        ax.pcolormesh(t, f / 1000, S, vmin=-80, vmax=0, cmap="magma", shading="auto")
        ax.set_ylim(0, 5)
        ax.set_title(title.capitalize(), fontsize=14)
        ax.set_xlabel("Time (s)")
    axes[0].set_ylabel("Frequency (kHz)")
    save_fig("fig-lowpass-decay.png")


# ---------------------------------------------------------------------------
# Excitation: white noise
# ---------------------------------------------------------------------------


def fig_white_noise() -> None:
    rng = np.random.default_rng(0)
    x = rng.uniform(-1, 1, F_S)
    fig, (axt, axf) = plt.subplots(1, 2, figsize=(13, 3.8))
    n = int(0.01 * F_S)
    axt.plot(np.arange(n) / F_S * 1000, x[:n], color=BLUE, lw=1.0)
    axt.set_xlabel("Time (ms)")
    axt.set_ylabel("Amplitude")
    axt.set_ylim(-1.2, 1.2)
    X = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    f = np.fft.rfftfreq(len(x), 1 / F_S)
    db = 20 * np.log10(X / X.max() + 1e-12)
    axf.plot(f / 1000, db, color=BLUE, lw=0.3, alpha=0.6)
    k = 400                                              # a moving average shows the trend
    smooth = 10 * np.log10(np.convolve(10 ** (db / 10), np.ones(k) / k, mode="same"))
    axf.plot(f[k:-k] / 1000, smooth[k:-k], color="black", lw=2.0)
    axf.set_xlim(0, F_S / 2000)
    axf.set_ylim(-60, 5)
    axf.set_xlabel("Frequency (kHz)")
    axf.set_ylabel("Magnitude (dB)")
    save_fig("fig-white-noise.png")


def audio_excitations() -> None:
    """The same damped, low-passed delay line excited two ways."""
    f0, dur = 196.0, 2.5
    M = round(F_S / f0 - 0.5)
    g = decay_gain(M + 0.5, dur)
    rng = np.random.default_rng(2)
    for name, x0 in (("impulse", np.r_[1.0, np.zeros(M - 1)]),
                     ("noise", rng.uniform(-1, 1, M))):
        x = np.zeros(int(dur * F_S))
        x[:M] = x0
        write_audio(fade(feedback_delay(x, M, g, lowpass=True), 0.0, 0.05),
                    f"audio-excitation-{name}.wav")


# ---------------------------------------------------------------------------
# Commuted synthesis: digital waveguides and lumped losses
# ---------------------------------------------------------------------------


def _rail(ax, x0, y, n, w=0.55, h=0.42):
    for i in range(n):
        ax.add_patch(Rectangle((x0 + i * w, y - h / 2), w, h, facecolor="0.94",
                               edgecolor="0.35", lw=1.2, zorder=2))


def fig_waveguide() -> None:
    """A digital waveguide string: a right-going and a left-going delay line,
    inverted reflections at both ends, and an output read from any point."""
    fig, ax = plt.subplots(figsize=(12, 5.4))
    ax.set_xlim(-1.4, 10.2)
    ax.set_ylim(-1.9, 3.5)
    ax.axis("off")
    n, w, x0 = 12, 0.55, 1.4
    x1 = x0 + n * w
    top, bot = 1.0, -0.6
    ym = (top + bot) / 2
    _rail(ax, x0, top, n)
    _rail(ax, x0, bot, n)
    ax.text(x0, top + 0.3, r"right-going wave $\rightarrow$", ha="left", va="bottom",
            fontsize=12, color=BLUE)
    ax.text(x1, bot - 0.3, r"$\leftarrow$ left-going wave", ha="right", va="top",
            fontsize=12, color=ORANGE)
    # Inverted reflections: the bridge on the right, the nut on the left.
    for xa, (ya, yb) in ((x1 + 0.03, (top, bot)), (x0 - 0.03, (bot, top))):
        ax.add_patch(FancyArrowPatch((xa, ya), (xa, yb), connectionstyle="arc3,rad=-0.8",
                                     arrowstyle="-|>", mutation_scale=14, color="0.3", lw=1.6))
    for xe, ha, label in ((x1 + 0.75, "left", "bridge"), (x0 - 0.75, "right", "nut")):
        ax.text(xe, ym + 0.1, r"$\times(-1)$", ha=ha, va="bottom", fontsize=13, color="0.3")
        ax.text(xe, ym - 0.1, label, ha=ha, va="top", fontsize=12, color="0.45")
    # The output: the sum of the two rails at any one point along the string.
    xr = x0 + 4.5 * w
    ax.plot([xr, xr], [top - 0.21, ym + 0.17], color=PURPLE, lw=2, zorder=1)
    ax.plot([xr, xr], [bot + 0.21, ym - 0.17], color=PURPLE, lw=2, zorder=1)
    _adder(ax, xr, ym, r=0.17)
    _arrow(ax, (xr + 0.17, ym), (xr + 1.1, ym), color=PURPLE)
    ax.text(xr + 1.2, ym, "output", ha="left", va="center", fontsize=12, color=PURPLE)
    # The plucked string, above.
    peak = x0 + 0.75 * (x1 - x0)
    ax.plot([x0, peak, x1], [2.3, 3.0, 2.3], color="black", lw=2)
    ax.plot([x0, x1], [2.3, 2.3], color="0.7", lw=1, ls="--")
    for xv in (x0, x1):
        ax.plot([xv, xv], [1.55, 2.3], color="0.8", lw=1, ls=":")
    ax.text((x0 + x1) / 2, 3.15, "string displacement = right-going + left-going",
            ha="center", fontsize=12, color="0.3")
    save_fig("fig-waveguide.png")


def fig_lumped_losses() -> None:
    fig, ax = plt.subplots(figsize=(11, 3.0))
    ax.set_xlim(-0.2, 10.4)
    ax.set_ylim(-0.4, 2.6)
    ax.axis("off")
    ax.text(0, 1.9, "Distributed", fontsize=14, va="center", color="0.3")
    ax.text(0, 0.5, "Lumped", fontsize=14, va="center", color="0.3")
    x = 2.4
    _arrow(ax, (x - 0.6, 1.9), (x - 0.35, 1.9))
    for i in range(3):
        _box(ax, x, 1.9, r"$z^{-1}$")
        _wire(ax, [(x + 0.35, 1.9), (x + 0.75, 1.9)])
        _gain(ax, x + 1.0, 1.9, f"$g_{i + 1}$", pointing="right")
        _wire(ax, [(x + 1.24, 1.9), (x + 1.6, 1.9)])
        x += 1.95
    _arrow(ax, (x - 0.4, 1.9), (x - 0.2, 1.9))
    _arrow(ax, (1.8, 0.5), (2.05, 0.5))
    _box(ax, 3.3, 0.5, r"$z^{-3}$", w=2.4)
    _wire(ax, [(4.5, 0.5), (6.3, 0.5)])
    _gain(ax, 6.75, 0.5, "$g_1 g_2 g_3$", size=0.45, pointing="right", fontsize=12)
    _wire(ax, [(7.2, 0.5), (8.0, 0.5)])
    _arrow(ax, (7.9, 0.5), (8.15, 0.5))
    save_fig("fig-lumped-losses.png")


def fig_waveguide_to_ks() -> None:
    """Listening at the bridge, a waveguide's round trip commutes into the
    single loop of Karplus-Strong."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 5.6),
                                   gridspec_kw={"height_ratios": [1.25, 1.0]})
    for ax in (ax1, ax2):
        ax.axis("off")
        ax.set_xlim(-0.4, 10.6)
    ax1.set_ylim(-1.5, 1.8)
    ax2.set_ylim(-1.5, 1.4)

    def vgain(ax, cx, cy, text, down=True, s=0.24):
        pts = ([[cx - s, cy + s], [cx + s, cy + s], [cx, cy - s]] if down
               else [[cx - s, cy - s], [cx + s, cy - s], [cx, cy + s]])
        ax.add_patch(Polygon(pts, closed=True, facecolor="white", edgecolor="0.3", lw=1.6,
                             zorder=3))
        ax.text(cx + 0.55, cy, text, ha="center", va="center", fontsize=13)

    ax1.text(-0.3, 1.5, "Digital waveguide", fontsize=14, fontweight="bold", color="0.25")
    _box(ax1, 5.0, 0.7, r"$M/2$ samples of delay, with losses", w=5.6, h=0.5, fontsize=13)
    _box(ax1, 5.0, -0.7, r"$M/2$ samples of delay, with losses", w=5.6, h=0.5, fontsize=13)
    _wire(ax1, [(7.8, 0.7), (8.6, 0.7), (8.6, 0.24)])            # bridge (right): down
    vgain(ax1, 8.6, 0.0, "$-1$", down=True)
    _wire(ax1, [(8.6, -0.24), (8.6, -0.7), (7.95, -0.7)])
    _arrow(ax1, (7.95, -0.7), (7.8, -0.7))
    _wire(ax1, [(2.2, -0.7), (1.4, -0.7), (1.4, -0.24)])          # nut (left): up
    vgain(ax1, 1.4, 0.0, "$-1$", down=False)
    _wire(ax1, [(1.4, 0.24), (1.4, 0.7), (2.05, 0.7)])
    _arrow(ax1, (2.05, 0.7), (2.2, 0.7))
    ax1.text(9.45, 0.0, "bridge", fontsize=12, va="center", color="0.45")
    ax1.text(0.55, 0.0, "nut", fontsize=12, va="center", ha="right", color="0.45")
    ax1.annotate("output", xy=(8.2, 0.72), xytext=(9.0, 1.4), fontsize=12, color=PURPLE,
                 arrowprops=dict(arrowstyle="<|-", color=PURPLE, lw=1.4))

    ax2.text(-0.3, 1.15, "Karplus-Strong", fontsize=14, fontweight="bold", color="0.25")
    _box(ax2, 5.0, 0.4, r"$M$ samples of delay", w=5.6, h=0.5, fontsize=13)
    _wire(ax2, [(7.8, 0.4), (8.6, 0.4), (8.6, -0.55), (6.4, -0.55)])
    _box(ax2, 5.0, -0.55, r"$g \cdot \frac{1}{2}(1 + z^{-1})$", w=2.8, h=0.6, fontsize=13)
    _wire(ax2, [(3.6, -0.55), (1.4, -0.55), (1.4, 0.4), (2.05, 0.4)])
    _arrow(ax2, (2.05, 0.4), (2.2, 0.4))
    ax2.text(5.0, -0.95, "all of the losses, lumped", ha="center", va="top", fontsize=12,
             color="0.45")
    ax2.annotate("output", xy=(8.2, 0.42), xytext=(9.0, 1.05), fontsize=12, color=PURPLE,
                 arrowprops=dict(arrowstyle="<|-", color=PURPLE, lw=1.4))
    save_fig("fig-waveguide-to-ks.png")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Audio:")
    audio_jos_examples()
    fig_and_audio_lowpass()
    audio_excitations()
    print("Figures:")
    fig_waves_gif()
    fig_standing_wave_gif()
    fig_string_modes()
    fig_modes_table()
    fig_physical_model_map()
    fig_feedback_delay()
    fig_karplus_strong()
    fig_delay_quantization()
    fig_comb()
    fig_comb_damped()
    fig_white_noise()
    fig_waveguide()
    fig_lumped_losses()
    fig_waveguide_to_ks()
