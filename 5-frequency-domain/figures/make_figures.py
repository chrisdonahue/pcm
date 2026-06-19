"""Generate figures and sound examples for Chapter 5 (the frequency domain).

Outputs are written to ../assets/. This file is *not* student-facing: it
renders the matplotlib diagrams (time vs. frequency, the complex plane, the
phasor, a spectrum-analyzer-style plot, and the Fourier-transform "wrapping"
intuition) plus a few demonstration tones.

Run with the project virtualenv:
    ../../../.venv/bin/python make_figures.py
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
# Additive-synthesis helpers (mirror the student code from Chapter 3)
# ---------------------------------------------------------------------------


def additive(f_0: float, amps: np.ndarray, dur: float) -> np.ndarray:
    """Sum of harmonics k*f_0 with amplitudes amps[k-1]."""
    t = np.arange(int(dur * F_S)) / F_S
    x = np.zeros_like(t)
    for k, a in enumerate(amps, start=1):
        x += a * np.sin(2 * np.pi * k * f_0 * t)
    return x


# Running example: the four-harmonic recipe a = [1, 1/2, 1/4, 1/8].
RECIPE = np.array([1.0, 0.5, 0.25, 0.125])
F0 = 220.0


# ---------------------------------------------------------------------------
# 1. Time domain vs. frequency domain for the four-harmonic recipe
# ---------------------------------------------------------------------------


def fig_time_vs_freq() -> None:
    fig, (ax_t, ax_f) = plt.subplots(1, 2, figsize=(13, 4))

    # Time domain: a couple of periods of the summed waveform.
    t = np.arange(int(2.5 / F0 * F_S)) / F_S
    x = np.zeros_like(t)
    for k, a in enumerate(RECIPE, start=1):
        x += a * np.sin(2 * np.pi * k * F0 * t)
    ax_t.plot(t * 1000, x, color=COLORS[0])
    ax_t.set_xlabel("Time (ms)")
    ax_t.set_ylabel("Amplitude")
    ax_t.set_xlim(0, t[-1] * 1000)

    # Frequency domain: amplitude at each harmonic frequency.
    freqs = np.arange(1, len(RECIPE) + 1) * F0
    markerline, stemlines, baseline = ax_f.stem(freqs, RECIPE)
    plt.setp(markerline, color=COLORS[1], markersize=8)
    plt.setp(stemlines, color=COLORS[1])
    plt.setp(baseline, color="0.7", linewidth=1.0)
    ax_f.set_xlabel("Frequency (Hz)")
    ax_f.set_ylabel("Amplitude")
    ax_f.set_xlim(0, 2000)
    ax_f.set_ylim(0, 1.1)

    save_fig("fig-time-vs-freq.png")


# ---------------------------------------------------------------------------
# 2. Frequency-domain spectra of the basic waveform shapes
# ---------------------------------------------------------------------------


def fig_waveform_spectra() -> None:
    K = 24
    k = np.arange(1, K + 1)
    odd = k % 2 == 1

    # Signed Fourier coefficients so the time-domain shapes are recognizable.
    saw = 1.0 / k
    square = np.where(odd, 1.0 / k, 0.0)
    triangle = np.where(odd, ((-1.0) ** ((k - 1) // 2)) / k**2, 0.0)
    specs = [("Sawtooth", saw), ("Square", square), ("Triangle", triangle)]

    # Two periods of each waveform, reconstructed from its harmonics.
    t = np.linspace(0, 2.0 / F0, 1000)

    fig, axes = plt.subplots(2, 3, figsize=(14, 6.2))
    for col, (label, coeffs) in enumerate(specs):
        # Top row: time domain.
        ax_t = axes[0, col]
        x = np.zeros_like(t)
        for ki, c in zip(k, coeffs):
            x += c * np.sin(2 * np.pi * ki * F0 * t)
        x /= np.max(np.abs(x))
        ax_t.plot(t * 1000, x, color=COLORS[0])
        ax_t.set_xlim(0, t[-1] * 1000)
        ax_t.set_ylim(-1.2, 1.2)
        ax_t.text(0.5, 1.06, label, transform=ax_t.transAxes, ha="center",
                  va="bottom", fontsize=15, fontweight="bold")
        if col == 0:
            ax_t.set_ylabel("Amplitude")

        # Bottom row: frequency domain (amplitude spectrum).
        ax_f = axes[1, col]
        amps = np.abs(coeffs)
        amps = amps / amps.max()
        markerline, stemlines, baseline = ax_f.stem(k * F0, amps)
        plt.setp(markerline, color=COLORS[1], markersize=5)
        plt.setp(stemlines, color=COLORS[1])
        plt.setp(baseline, color="0.7", linewidth=1.0)
        ax_f.set_xlabel("Frequency (Hz)")
        ax_f.set_xlim(0, K * F0)
        ax_f.set_ylim(0, 1.1)
        if col == 0:
            ax_f.set_ylabel("Amplitude (norm.)")

    axes[0, 0].text(-0.32, 0.5, "Time domain", transform=axes[0, 0].transAxes,
                    rotation=90, va="center", ha="center", fontsize=13,
                    color="0.4")
    axes[1, 0].text(-0.32, 0.5, "Frequency domain",
                    transform=axes[1, 0].transAxes, rotation=90, va="center",
                    ha="center", fontsize=13, color="0.4")
    axes[0, 0].set_xlabel("Time (ms)")
    axes[0, 1].set_xlabel("Time (ms)")
    axes[0, 2].set_xlabel("Time (ms)")
    save_fig("fig-waveform-spectra.png")


# ---------------------------------------------------------------------------
# 3. The complex plane (Cartesian and polar)
# ---------------------------------------------------------------------------


def fig_complex_plane() -> None:
    fig, ax = plt.subplots(figsize=(7.5, 5.5))

    x, y = 2.2, 1.6
    theta = np.arctan2(y, x)

    # Vector to z.
    ax.annotate("", xy=(x, y), xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>", color=COLORS[0], lw=2.5))
    ax.plot([x], [y], "o", color=COLORS[0], markersize=9)
    ax.annotate(r"$z = x + jy$", xy=(x, y), xytext=(x + 0.1, y + 0.12),
                fontsize=16)

    # Projections.
    ax.plot([x, x], [0, y], "--", color="0.5", linewidth=1.3)
    ax.plot([0, x], [y, y], "--", color="0.5", linewidth=1.3)
    ax.annotate(r"$x = r\cos\theta$", xy=(x / 2, 0.04), ha="center",
                va="bottom", fontsize=14)
    ax.annotate(r"$y = r\sin\theta$", xy=(x + 0.08, y / 2), ha="left",
                va="center", fontsize=14)

    # Magnitude label along the vector.
    ax.annotate(r"$r = \sqrt{x^2 + y^2}$", xy=(x / 2 - 0.2, y / 2 + 0.12),
                ha="center", va="bottom", fontsize=14, rotation=np.degrees(theta),
                rotation_mode="anchor", color=COLORS[0])

    # Angle arc and its definition.
    arc = np.linspace(0, theta, 40)
    rad = 0.55
    ax.plot(rad * np.cos(arc), rad * np.sin(arc), color="0.3", linewidth=1.3)
    ax.annotate(r"$\theta = \tan^{-1}\!\frac{y}{x}$", xy=(0.7, 0.22),
                fontsize=15)

    ax.set_xlabel(r"Real  $\Re$")
    ax.set_ylabel(r"Imaginary  $\Im$")
    ax.set_xlim(0, 3.1)
    ax.set_ylim(0, 2.4)
    ax.set_aspect("equal")
    save_fig("fig-complex-plane.png")


# ---------------------------------------------------------------------------
# 4. The phasor: a rotating vector projecting to cos and sin
# ---------------------------------------------------------------------------


def fig_phasor() -> None:
    fig, (ax_c, ax_re, ax_im) = plt.subplots(1, 3, figsize=(14, 4.2))

    theta = 2 * np.pi * 0.13  # a representative instant
    circle = np.linspace(0, 2 * np.pi, 400)

    # Complex plane with the phasor at angle theta.
    ax_c.plot(np.cos(circle), np.sin(circle), color="0.55", linewidth=1.5)
    ax_c.axhline(0, color="0.7", linewidth=1.0)
    ax_c.axvline(0, color="0.7", linewidth=1.0)
    ax_c.annotate("", xy=(np.cos(theta), np.sin(theta)), xytext=(0, 0),
                  arrowprops=dict(arrowstyle="-|>", color=COLORS[0], lw=2.5))
    ax_c.plot([np.cos(theta)], [np.sin(theta)], "o", color=COLORS[0], ms=9)
    ax_c.plot([np.cos(theta), np.cos(theta)], [0, np.sin(theta)], "--",
              color=COLORS[2], lw=1.5)
    ax_c.plot([0, np.cos(theta)], [np.sin(theta), np.sin(theta)], "--",
              color=COLORS[3], lw=1.5)
    ax_c.annotate(r"$ae^{j\omega t}$", xy=(np.cos(theta), np.sin(theta)),
                  xytext=(-1.15, 1.05), fontsize=15, color=COLORS[0])
    ax_c.set_xlabel(r"Real $= a\cos(\omega t)$")
    ax_c.set_ylabel(r"Imaginary $= a\sin(\omega t)$")
    ax_c.set_xlim(-1.3, 1.3)
    ax_c.set_ylim(-1.3, 1.3)
    ax_c.set_aspect("equal")

    # Real projection: cos over time.
    tt = np.linspace(0, 1, 400)
    ax_re.plot(tt, np.cos(2 * np.pi * tt), color=COLORS[2])
    ax_re.axhline(0, color="0.7", linewidth=1.0)
    ax_re.plot([0.13], [np.cos(theta)], "o", color=COLORS[2], ms=9)
    ax_re.set_xlabel("Time (cycles)")
    ax_re.set_ylabel(r"$\Re = \cos(\omega t)$")
    ax_re.set_ylim(-1.3, 1.3)

    # Imaginary projection: sin over time.
    ax_im.plot(tt, np.sin(2 * np.pi * tt), color=COLORS[3])
    ax_im.axhline(0, color="0.7", linewidth=1.0)
    ax_im.plot([0.13], [np.sin(theta)], "o", color=COLORS[3], ms=9)
    ax_im.set_xlabel("Time (cycles)")
    ax_im.set_ylabel(r"$\Im = \sin(\omega t)$")
    ax_im.set_ylim(-1.3, 1.3)

    save_fig("fig-phasor.png")


# ---------------------------------------------------------------------------
# 5. A spectrum-analyzer-style amplitude spectrum of a real-ish tone
# ---------------------------------------------------------------------------


def fig_spectrum_analyzer() -> None:
    # A rich, slightly imperfect tone: many harmonics with a gentle rolloff,
    # detuned a touch and with a little broadband noise, windowed so the
    # spectrum has realistic-looking skirts around each peak.
    f_0 = 220.0
    dur = 1.0
    t = np.arange(int(dur * F_S)) / F_S
    x = np.zeros_like(t)
    rng = np.random.default_rng(0)
    for k in range(1, 31):
        amp = 1.0 / k**1.1
        detune = 1.0 + rng.normal(0, 0.001)
        x += amp * np.sin(2 * np.pi * k * f_0 * detune * t + rng.uniform(0, 2 * np.pi))
    x += 0.01 * rng.standard_normal(t.shape)
    x /= np.max(np.abs(x))

    window = np.hanning(len(x))
    X = np.fft.rfft(x * window)
    freqs = np.fft.rfftfreq(len(x), 1 / F_S)
    mag = np.abs(X)
    mag_db = 20 * np.log10(mag / mag.max() + 1e-9)

    fig, ax = plt.subplots(figsize=(13, 4.2))
    ax.semilogx(freqs[1:], mag_db[1:], color=COLORS[4], linewidth=1.2)
    ax.fill_between(freqs[1:], -80, mag_db[1:], color=COLORS[4], alpha=0.25)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Amplitude (dB)")
    ax.set_xlim(50, 20000)
    ax.set_ylim(-72, 3)
    ax.grid(True, which="both", color="0.9", linewidth=0.7)
    save_fig("fig-spectrum-analyzer.png")


# ---------------------------------------------------------------------------
# 6. Fourier transform intuition: wrapping a signal around the complex plane
# ---------------------------------------------------------------------------


def fig_ft_intuition() -> None:
    # A real signal: a 3 Hz cosine (offset so it is non-negative, like a
    # "pulse rate", which makes the center-of-mass effect dramatic).
    f_sig = 3.0
    dur = 2.0
    t = np.linspace(0, dur, 2000)
    x = 1.0 + np.cos(2 * np.pi * f_sig * t)  # >= 0

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.6))

    probes = [2.0, 3.0, 4.0]
    for ax, g in zip(axes, probes):
        wrapped = x * np.exp(-1j * 2 * np.pi * g * t)
        ax.plot(wrapped.real, wrapped.imag, color=COLORS[0], linewidth=1.3,
                alpha=0.8)
        com = np.mean(wrapped)
        ax.plot([com.real], [com.imag], "o", color=COLORS[3], ms=12,
                zorder=5)
        ax.annotate("center\nof mass", xy=(com.real, com.imag),
                    xytext=(com.real + 0.4, com.imag + 0.4), fontsize=11,
                    color=COLORS[3],
                    arrowprops=dict(arrowstyle="->", color=COLORS[3]))
        ax.axhline(0, color="0.8", linewidth=0.8)
        ax.axvline(0, color="0.8", linewidth=0.8)
        ax.text(0.5, 0.97, f"probe = {g:g} Hz", transform=ax.transAxes,
                ha="center", va="top", fontsize=14, fontweight="bold")
        ax.set_xlabel("Real")
        ax.set_xlim(-2.2, 2.2)
        ax.set_ylim(-2.2, 2.2)
        ax.set_aspect("equal")
    axes[0].set_ylabel("Imaginary")
    save_fig("fig-ft-intuition.png")


# ---------------------------------------------------------------------------
# Audio examples
# ---------------------------------------------------------------------------


def make_audio() -> None:
    # The running four-harmonic recipe whose spectrum we plot.
    write_audio(additive(F0, RECIPE, 2.0), "audio-recipe.wav")

    # The three basic waveform shapes, built from their harmonic spectra.
    K = 32
    k = np.arange(1, K + 1)
    odd = k % 2 == 1
    saw = additive(F0, 1.0 / k, 2.0)
    square = additive(F0, np.where(odd, 1.0 / k, 0.0), 2.0)
    triangle = additive(F0, np.where(odd, 1.0 / k**2, 0.0), 2.0)
    write_audio(saw, "audio-saw.wav")
    write_audio(square, "audio-square.wav")
    write_audio(triangle, "audio-triangle.wav")


def main() -> None:
    print("Figures:")
    fig_time_vs_freq()
    fig_waveform_spectra()
    fig_complex_plane()
    fig_phasor()
    fig_spectrum_analyzer()
    fig_ft_intuition()
    print("Audio:")
    make_audio()


if __name__ == "__main__":
    main()
