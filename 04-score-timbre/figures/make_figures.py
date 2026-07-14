"""Generate figures and sound examples for Chapter 4 (scores and timbre).

Outputs are written to ../assets/. This file is *not* student-facing: it
renders the LilyPond score images, the animated shapes GIF, the matplotlib
diagrams, and the demonstration audio used throughout the chapter.

Requires LilyPond on PATH (for the two notation figures).
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pyquist as pq
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
ASSETS.mkdir(exist_ok=True)
# The plucked-guitar recording reused from Chapter 3.
GUITAR = (
    HERE.parent.parent
    / "03-additive-synthesis"
    / "assets"
    / "154030__carlos_vaquero__classical-guitar-f-3-plucked-non-vibrato.wav"
)

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


def save_fig(name: str) -> None:
    path = ASSETS / name
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  wrote {name}")


def write_audio(samples: np.ndarray, name: str) -> None:
    audio = pq.Audio(samples.astype(np.float32), F_S)
    audio.normalize(peak_dbfs=PEAK_DBFS)
    audio.write(str(ASSETS / name))
    print(f"  wrote {name}")


# ---------------------------------------------------------------------------
# Small synthesis helpers (mirrors of the student code)
# ---------------------------------------------------------------------------


def osc(f_0: float, N: int, n: int = 0) -> np.ndarray:
    t = (n + np.arange(N)) / F_S
    return np.sin(2.0 * np.pi * f_0 * t)


def adenv(a_dur: float, d_dur: float, N: int, n: int = 0) -> np.ndarray:
    t = (n + np.arange(N)) / F_S
    return np.interp(
        t, [0.0, a_dur, a_dur + d_dur], [0.0, 1.0, 0.0], left=0.0, right=0.0
    )


def fade(samples: np.ndarray, ms: float = 5.0) -> np.ndarray:
    """Apply a short linear fade in/out to avoid onset/offset clicks."""
    k = max(1, int(ms / 1000.0 * F_S))
    ramp = np.linspace(0.0, 1.0, k)
    out = samples.copy()
    out[:k] *= ramp
    out[-k:] *= ramp[::-1]
    return out


# ---------------------------------------------------------------------------
# LilyPond score images
# ---------------------------------------------------------------------------

LILY_MELODY = r"""
\version "2.24.0"
\header { tagline = ##f }
\score {
  \new Staff { \clef treble \time 4/4 \tempo 4 = 120 c'4 c' g' g' a' a' g'2 }
  \layout { }
}
"""

LILY_HARMONIZED = r"""
\version "2.24.0"
\header { tagline = ##f }
\score {
  \new PianoStaff <<
    \new Staff { \clef treble \time 4/4 \tempo 4 = 120 c'4 c' g' g' a' a' g'2 }
    \new Staff { \clef bass \time 4/4 c1 f,2 c2 }
  >>
  \layout { }
}
"""


def render_lilypond(source: str, name: str) -> None:
    if shutil.which("lilypond") is None:
        print(f"  SKIP {name}: lilypond not found on PATH")
        return
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        ly = tmp_path / "score.ly"
        ly.write_text(source)
        subprocess.run(
            ["lilypond", "--png", "-dresolution=200", "-dcrop", "-o", "score", "score.ly"],
            cwd=tmp,
            check=True,
            capture_output=True,
        )
        cropped = tmp_path / "score.cropped.png"
        shutil.copy(cropped, ASSETS / name)
    print(f"  wrote {name}")


# ---------------------------------------------------------------------------
# Animated shapes GIF (a score need not be audio)
# ---------------------------------------------------------------------------

SHAPE_SCORE = [
    (0.0, {"color": "tab:red", "shape": "square"}),
    (2.0, {"color": "tab:blue", "shape": "star"}),
    (3.0, {"color": "tab:green", "shape": "circle"}),
]
SHAPE_MARKERS = {"square": "s", "star": "*", "circle": "o"}
LOOP_DURATION = 4.0


def active_event(t: float):
    """The most recent event at time t (the one currently 'sounding')."""
    current = SHAPE_SCORE[0][1]
    for onset, kwargs in SHAPE_SCORE:
        if t >= onset:
            current = kwargs
    return current


def make_shapes_gif() -> None:
    fps = 12
    n_frames = int(LOOP_DURATION * fps)
    # Wide, short frame so the figure doesn't dominate vertically.
    fig, ax = plt.subplots(figsize=(8, 3))

    def update(frame):
        t = frame / fps
        kwargs = active_event(t)
        ax.clear()
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)
        ax.axis("off")
        ax.scatter(
            [0], [0], s=9000, c=kwargs["color"],
            marker=SHAPE_MARKERS[kwargs["shape"]],
        )
        ax.text(
            0.02, 0.97, f"t = {t:4.1f} s", transform=ax.transAxes,
            ha="left", va="top", fontsize=18, family="monospace",
        )
        return ()

    anim = FuncAnimation(fig, update, frames=n_frames, blit=False)
    anim.save(ASSETS / "anim-shapes.gif", writer=PillowWriter(fps=fps, metadata={"loop": 0}))
    plt.close(fig)
    print("  wrote anim-shapes.gif")


# ---------------------------------------------------------------------------
# Pluck envelope figure (waveform, estimated envelope, PWL approximation)
# ---------------------------------------------------------------------------


def fig_pluck_envelope() -> None:
    if not GUITAR.exists():
        print("  SKIP fig-pluck-envelope.png: guitar sample not found")
        return
    audio = pq.Audio.from_file(str(GUITAR)).as_mono()
    x = audio.samples[:, 0]
    sr = audio.sample_rate
    # Trim leading silence and limit to ~1.6 s.
    onset = int(np.argmax(np.abs(x) > 0.02))
    x = x[onset : onset + int(1.6 * sr)]
    t = np.arange(len(x)) / sr

    # Rolling-peak amplitude envelope (visual only).
    win = int(0.01 * sr)
    pad = np.pad(np.abs(x), (win, win), mode="edge")
    env = np.array([pad[i : i + 2 * win].max() for i in range(0, len(x), win)])
    env_t = (np.arange(len(env)) * win) / sr

    # PWL approximation: attack to the peak, then linear decay (two segments).
    peak_idx = int(np.argmax(env))
    t_peak = env_t[peak_idx]
    peak_val = env[peak_idx]
    pwl_t = [0.0, t_peak, t[-1]]
    pwl_v = [0.0, peak_val, 0.0]

    fig, axs = plt.subplots(2, 1, figsize=(11, 6))

    # Panel 1: raw waveform, with a zoomed inset showing quasi-periodicity.
    axs[0].plot(t, x, color=COLORS[0], linewidth=0.6)
    axs[0].set_ylabel("Amplitude")
    axs[0].set_title("Plucked string waveform", fontsize=14, loc="left")
    axs[0].set_xlim(t[0], t[-1])
    # Inset: ~25 ms (about 4 periods of F3 ~175 Hz) shortly after the attack.
    z0 = int(0.30 * sr)
    z1 = z0 + int(0.025 * sr)
    inset = axs[0].inset_axes([0.55, 0.55, 0.4, 0.4])
    inset.plot(t[z0:z1], x[z0:z1], color=COLORS[0], linewidth=1.0)
    inset.set_title("zoomed: quasi-periodic", fontsize=10)
    inset.set_xticks([])
    inset.set_yticks([])
    axs[0].indicate_inset_zoom(inset, edgecolor="black")

    # Panel 2: top half only — estimated envelope and its PWL approximation.
    axs[1].plot(t, np.maximum(x, 0.0), color=COLORS[0], linewidth=0.6, alpha=0.35)
    axs[1].plot(env_t, env, color=COLORS[3], linewidth=2.5, label="estimated envelope")
    axs[1].plot(
        pwl_t, pwl_v, color=COLORS[2], linewidth=2.5, marker="o",
        label="piecewise-linear approximation",
    )
    axs[1].set_ylim(bottom=0.0)
    axs[1].set_ylabel("Amplitude")
    axs[1].set_xlabel("Time (s)")
    axs[1].set_xlim(t[0], t[-1])
    axs[1].legend(fontsize=12, loc="upper right")
    save_fig("fig-pluck-envelope.png")


# ---------------------------------------------------------------------------
# Envelope-application figure + audio (sine, envelope, product)
# ---------------------------------------------------------------------------


def fig_and_audio_envelope_apply() -> None:
    T = 1.0
    N = int(T * F_S)
    t = np.arange(N) / F_S
    sine = osc(220.0, N)
    env = adenv(0.1, 0.9, N)  # attack 0.1 s, decay 0.9 s (fills 1 s)
    product = sine * env

    fig, axs = plt.subplots(3, 1, figsize=(11, 7), sharex=True)
    axs[0].plot(t, sine, color=COLORS[0], linewidth=0.4)
    axs[0].set_ylabel("$x(t)$")
    axs[0].set_title("Oscillator $x(t)$ (220 Hz sine)", fontsize=14, loc="left")

    axs[1].plot(t, env, color=COLORS[3])
    axs[1].set_ylabel("Envelope")
    axs[1].set_ylim(-0.1, 1.1)
    axs[1].set_title("Envelope (attack/decay)", fontsize=14, loc="left")

    axs[2].plot(t, product, color=COLORS[0], linewidth=0.4)
    axs[2].plot(t, env, color=COLORS[3], linewidth=1.5, linestyle="--")
    axs[2].plot(t, -env, color=COLORS[3], linewidth=1.5, linestyle="--")
    axs[2].set_ylabel("Product")
    axs[2].set_xlabel("Time (s)")
    axs[2].set_title("Product $x(t) \\cdot \\mathrm{Envelope}(t)$", fontsize=14, loc="left")
    save_fig("fig-envelope-apply.png")

    write_audio(fade(sine), "audio-env-demo-sine.wav")
    write_audio(product, "audio-env-demo-enveloped.wav")


# ---------------------------------------------------------------------------
# adenv plot
# ---------------------------------------------------------------------------


def fig_adenv() -> None:
    N = F_S  # 1 s
    t = np.arange(N) / F_S
    env = adenv(0.1, 0.9, N)
    fig, ax = plt.subplots(figsize=(11, 3.4))
    ax.plot(t, env, color=COLORS[3])
    ax.plot([0.0, 0.1, 1.0], [0.0, 1.0, 0.0], "o", color=COLORS[2], markersize=9)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Envelope")
    ax.set_ylim(-0.05, 1.1)
    ax.annotate("attack", xy=(0.05, 0.5), fontsize=14, ha="center")
    ax.annotate("decay", xy=(0.55, 0.5), fontsize=14, ha="center")
    save_fig("fig-adenv.png")


# ---------------------------------------------------------------------------
# Unit-generator topology diagrams + audio
# ---------------------------------------------------------------------------


def _box(ax, xy, text, color="#e8e8e8", w=0.22, h=0.12):
    x, y = xy
    ax.add_patch(
        FancyBboxPatch(
            (x - w / 2, y - h / 2), w, h,
            boxstyle="round,pad=0.02", facecolor=color, edgecolor="black", linewidth=1.5,
        )
    )
    ax.text(x, y, text, ha="center", va="center", fontsize=13, family="monospace")


def _op(ax, xy, symbol, color="#cfe8cf"):
    """A standard block-diagram operator glyph: a circle with an operator."""
    ax.scatter([xy[0]], [xy[1]], s=2400, c=color, edgecolors="black",
               linewidths=1.5, zorder=3)
    ax.text(xy[0], xy[1], symbol, ha="center", va="center", fontsize=20, zorder=4)


def _arrow(ax, start, end):
    ax.add_patch(
        FancyArrowPatch(
            start, end, arrowstyle="-|>", mutation_scale=18, linewidth=1.5, color="black"
        )
    )


_ADENV = "adenv(0.1, 0.9)"


def fig_topology_mul() -> None:
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    _box(ax, (0.28, 0.85), _ADENV, w=0.34)
    _box(ax, (0.72, 0.85), "osc(220)", w=0.28)
    _op(ax, (0.5, 0.5), "×")
    _box(ax, (0.5, 0.15), "output", color="#cfd8e8", w=0.28)
    _arrow(ax, (0.28, 0.79), (0.46, 0.54))
    _arrow(ax, (0.72, 0.79), (0.54, 0.54))
    _arrow(ax, (0.5, 0.45), (0.5, 0.21))
    save_fig("fig-topology-mul.png")


def fig_topology_add() -> None:
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    _box(ax, (0.13, 0.88), _ADENV, w=0.22)
    _box(ax, (0.37, 0.88), "osc(220)", w=0.18)
    _box(ax, (0.63, 0.88), _ADENV, w=0.22)
    _box(ax, (0.87, 0.88), "osc(330)", w=0.18)
    _op(ax, (0.25, 0.55), "×")
    _op(ax, (0.75, 0.55), "×")
    _op(ax, (0.5, 0.28), "+", color="#e8e0cf")
    _box(ax, (0.5, 0.08), "output", color="#cfd8e8", w=0.18)
    _arrow(ax, (0.13, 0.82), (0.22, 0.59))
    _arrow(ax, (0.37, 0.82), (0.28, 0.59))
    _arrow(ax, (0.63, 0.82), (0.72, 0.59))
    _arrow(ax, (0.87, 0.82), (0.78, 0.59))
    _arrow(ax, (0.25, 0.5), (0.46, 0.32))
    _arrow(ax, (0.75, 0.5), (0.54, 0.32))
    _arrow(ax, (0.5, 0.23), (0.5, 0.14))
    save_fig("fig-topology-add.png")


def fig_topology_efficient() -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    _box(ax, (0.55, 0.88), "osc(220)", w=0.2)
    _box(ax, (0.85, 0.88), "osc(330)", w=0.2)
    _op(ax, (0.7, 0.58), "+", color="#e8e0cf")
    _box(ax, (0.2, 0.58), _ADENV, w=0.3)
    _op(ax, (0.45, 0.3), "×")
    _box(ax, (0.45, 0.08), "output", color="#cfd8e8", w=0.2)
    _arrow(ax, (0.55, 0.82), (0.66, 0.62))
    _arrow(ax, (0.85, 0.82), (0.74, 0.62))
    _arrow(ax, (0.2, 0.52), (0.41, 0.34))
    _arrow(ax, (0.7, 0.54), (0.49, 0.34))
    _arrow(ax, (0.45, 0.25), (0.45, 0.14))
    save_fig("fig-topology-efficient.png")


def audio_topologies() -> None:
    N = F_S  # 1 s
    env = adenv(0.1, 0.9, N)
    mul = env * osc(220.0, N)
    add = env * osc(220.0, N) + env * osc(330.0, N)
    write_audio(mul, "audio-topology-mul.wav")
    write_audio(add, "audio-topology-add.wav")


# ---------------------------------------------------------------------------
# Timbre vs. score: arpeggiated sinusoids (harmonic vs. inharmonic)
# ---------------------------------------------------------------------------


def _staggered_tones(freqs: list[float], onset_delay: float = 0.1, total: float = 8.0) -> np.ndarray:
    N = int(total * F_S)
    out = np.zeros(N)
    for i, f in enumerate(freqs):
        start = int(i * onset_delay * F_S)
        tone = fade(osc(f, N - start), ms=8.0)
        out[start:] += tone
    return out


def audio_timbre_vs_score() -> None:
    # Harmonic: integer multiples of 220 Hz -> fuse into one timbre.
    harmonic = _staggered_tones([220.0, 440.0, 660.0, 880.0])
    # Inharmonic (an A dominant-7 set) -> heard as separate tones.
    inharmonic = _staggered_tones([220.0, 277.18, 329.63, 392.00])
    write_audio(harmonic, "audio-timbre-harmonic.wav")
    write_audio(inharmonic, "audio-timbre-inharmonic.wav")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    render_lilypond(LILY_MELODY, "fig-twinkle-melody.png")
    render_lilypond(LILY_HARMONIZED, "fig-twinkle-harmonized.png")
    make_shapes_gif()
    fig_pluck_envelope()
    fig_and_audio_envelope_apply()
    fig_adenv()
    fig_topology_mul()
    fig_topology_add()
    fig_topology_efficient()
    audio_topologies()
    audio_timbre_vs_score()
    print("chapter 4 figures done.")
