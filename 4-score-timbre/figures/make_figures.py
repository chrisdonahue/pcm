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
    / "3-additive-synthesis"
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
  \new Staff { \clef treble \time 4/4 c'4 c' g' g' a' a' g'2 }
  \layout { }
}
"""

LILY_HARMONIZED = r"""
\version "2.24.0"
\header { tagline = ##f }
\score {
  \new PianoStaff <<
    \new Staff { \clef treble \time 4/4 c'4 c' g' g' a' a' g'2 }
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
    fig, ax = plt.subplots(figsize=(5, 5))

    def update(frame):
        t = frame / fps
        kwargs = active_event(t)
        ax.clear()
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.scatter(
            [0], [0], s=14000, c=kwargs["color"],
            marker=SHAPE_MARKERS[kwargs["shape"]],
        )
        ax.text(
            0.97, 0.97, f"t = {t:4.1f} s", transform=ax.transAxes,
            ha="right", va="top", fontsize=18, family="monospace",
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

    # One-control-point PWL approximation: attack to peak, linear release.
    peak_idx = int(np.argmax(env))
    t_peak = env_t[peak_idx]
    peak_val = env[peak_idx]
    pwl_t = [0.0, t_peak, t[-1]]
    pwl_v = [0.0, peak_val, 0.0]

    fig, axs = plt.subplots(3, 1, figsize=(11, 7), sharex=True)
    axs[0].plot(t, x, color=COLORS[0], linewidth=0.6)
    axs[0].set_ylabel("Amplitude")
    axs[0].set_title("Plucked string waveform", fontsize=14, loc="left")

    axs[1].plot(t, x, color=COLORS[0], linewidth=0.6, alpha=0.4)
    axs[1].plot(env_t, env, color=COLORS[3], linewidth=2.5)
    axs[1].plot(env_t, -env, color=COLORS[3], linewidth=2.5)
    axs[1].set_ylabel("Amplitude")
    axs[1].set_title("Estimated amplitude envelope", fontsize=14, loc="left")

    axs[2].plot(t, x, color=COLORS[0], linewidth=0.6, alpha=0.4)
    axs[2].plot(pwl_t, pwl_v, color=COLORS[2], linewidth=2.5, marker="o")
    axs[2].plot(pwl_t, [-v for v in pwl_v], color=COLORS[2], linewidth=2.5, marker="o")
    axs[2].set_ylabel("Amplitude")
    axs[2].set_xlabel("Time (s)")
    axs[2].set_title(
        "Piecewise-linear approximation (one control point)", fontsize=14, loc="left"
    )
    save_fig("fig-pluck-envelope.png")


# ---------------------------------------------------------------------------
# Envelope-application figure + audio (sine, envelope, product)
# ---------------------------------------------------------------------------


def fig_and_audio_envelope_apply() -> None:
    T = 2.0
    N = int(T * F_S)
    t = np.arange(N) / F_S
    sine = osc(220.0, N)
    env = adenv(0.4, 1.4, N)  # attack 0.4 s, release 1.4 s (fills 2 s)
    product = sine * env

    fig, axs = plt.subplots(3, 1, figsize=(11, 7), sharex=True)
    axs[0].plot(t, sine, color=COLORS[0], linewidth=0.4)
    axs[0].set_ylabel("$x(t)$")
    axs[0].set_title("Oscillator $x(t)$ (220 Hz sine)", fontsize=14, loc="left")

    axs[1].plot(t, env, color=COLORS[3])
    axs[1].set_ylabel("Envelope")
    axs[1].set_ylim(-0.1, 1.1)
    axs[1].set_title("Envelope (attack/release)", fontsize=14, loc="left")

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


def _box(ax, xy, text, color="#e8e8e8", w=0.26, h=0.12):
    x, y = xy
    ax.add_patch(
        FancyBboxPatch(
            (x - w / 2, y - h / 2), w, h,
            boxstyle="round,pad=0.02", facecolor=color, edgecolor="black", linewidth=1.5,
        )
    )
    ax.text(x, y, text, ha="center", va="center", fontsize=14, family="monospace")


def _arrow(ax, start, end):
    ax.add_patch(
        FancyArrowPatch(
            start, end, arrowstyle="-|>", mutation_scale=18, linewidth=1.5, color="black"
        )
    )


def fig_topology_mul() -> None:
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    _box(ax, (0.3, 0.85), "osc(220)")
    _box(ax, (0.7, 0.85), "adenv")
    _box(ax, (0.5, 0.5), "×", color="#cfe8cf")
    _box(ax, (0.5, 0.15), "output", color="#cfd8e8")
    _arrow(ax, (0.3, 0.79), (0.45, 0.56))
    _arrow(ax, (0.7, 0.79), (0.55, 0.56))
    _arrow(ax, (0.5, 0.44), (0.5, 0.21))
    save_fig("fig-topology-mul.png")


def fig_topology_add() -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    bw = 0.19
    _box(ax, (0.13, 0.88), "osc(220)", w=bw)
    _box(ax, (0.37, 0.88), "adenv", w=bw)
    _box(ax, (0.63, 0.88), "osc(330)", w=bw)
    _box(ax, (0.87, 0.88), "adenv", w=bw)
    _box(ax, (0.25, 0.55), "×", color="#cfe8cf", w=bw)
    _box(ax, (0.75, 0.55), "×", color="#cfe8cf", w=bw)
    _box(ax, (0.5, 0.28), "+", color="#e8e0cf", w=bw)
    _box(ax, (0.5, 0.08), "output", color="#cfd8e8", w=bw)
    _arrow(ax, (0.13, 0.82), (0.21, 0.61))
    _arrow(ax, (0.37, 0.82), (0.29, 0.61))
    _arrow(ax, (0.63, 0.82), (0.71, 0.61))
    _arrow(ax, (0.87, 0.82), (0.79, 0.61))
    _arrow(ax, (0.25, 0.49), (0.45, 0.34))
    _arrow(ax, (0.75, 0.49), (0.55, 0.34))
    _arrow(ax, (0.5, 0.22), (0.5, 0.14))
    save_fig("fig-topology-add.png")


def audio_topologies() -> None:
    N = F_S  # 1 s
    env = adenv(0.1, 0.9, N)
    mul = osc(220.0, N) * env
    add = osc(220.0, N) * env + osc(330.0, N) * env
    write_audio(mul, "audio-topology-mul.wav")
    write_audio(add, "audio-topology-add.wav")


# ---------------------------------------------------------------------------
# Timbre vs. score: arpeggiated sinusoids (harmonic vs. inharmonic)
# ---------------------------------------------------------------------------


def _arpeggio(freqs: list[float], onset_delay: float = 0.1, total: float = 1.6) -> np.ndarray:
    N = int(total * F_S)
    out = np.zeros(N)
    for i, f in enumerate(freqs):
        start = int(i * onset_delay * F_S)
        tone = fade(osc(f, N - start), ms=8.0)
        out[start:] += tone
    return out


def audio_timbre_vs_score() -> None:
    c4 = pq.helper.pitch_to_frequency(pq.helper.pitch_name_to_pitch("C4"))
    # Harmonic: integer multiples of C4 -> fuses into one timbre.
    harmonic = _arpeggio([c4 * k for k in (1, 2, 3, 4)])
    # C dominant-7 chord: C4 E4 G4 Bb4 -> heard as separate notes (a score).
    chord_pitches = ["C4", "E4", "G4", "Bb4"]
    chord_freqs = [
        pq.helper.pitch_to_frequency(pq.helper.pitch_name_to_pitch(p))
        for p in chord_pitches
    ]
    chord = _arpeggio(chord_freqs)
    write_audio(harmonic, "audio-timbre-harmonic.wav")
    write_audio(chord, "audio-timbre-chord.wav")


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
    audio_topologies()
    audio_timbre_vs_score()
    print("chapter 4 figures done.")
