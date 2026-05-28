"""Generate figures for chapter 3 (additive synthesis).

Outputs are written to ../assets/.
"""

import os
import sys

import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.abspath(os.path.join(HERE, "..", "assets"))
os.makedirs(ASSETS, exist_ok=True)

sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "pyquist")))
import pyquist as pq

plt.rcParams.update({
    "font.size": 14,
    "axes.labelsize": 16,
    "xtick.labelsize": 13,
    "ytick.labelsize": 13,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "lines.linewidth": 2.5,
})

COLORS = plt.rcParams["axes.prop_cycle"].by_key()["color"]


def save(name):
    path = os.path.join(ASSETS, name)
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  wrote {os.path.relpath(path)}")


def _annotate_period(ax, t0, label):
    ax.annotate("", xy=(t0, 1.25), xytext=(0, 1.25),
                arrowprops=dict(arrowstyle="<->", linewidth=2))
    ax.text(t0 / 2, 1.32, label, ha="center", fontsize=16)


# ---------- Periodicity ----------

def fig_period_2hz():
    t = np.linspace(0, 1, 2000)
    x = np.sin(2 * np.pi * 2 * t)
    _, ax = plt.subplots(figsize=(10, 3.4))
    ax.plot(t, x)
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_ylim(-1.2, 1.5)
    ax.set_yticks([-1, 0, 1])
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    _annotate_period(ax, 0.5, r"$t_0 = 0.5\,\mathrm{s}$")
    save("fig-period-2hz.png")


def fig_period_4hz():
    t = np.linspace(0, 1, 2000)
    x = np.sin(2 * np.pi * 4 * t)
    _, ax = plt.subplots(figsize=(10, 3.4))
    ax.plot(t, x)
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_ylim(-1.2, 1.5)
    ax.set_yticks([-1, 0, 1])
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    _annotate_period(ax, 0.25, r"$t_0 = 0.25\,\mathrm{s}$")
    save("fig-period-4hz.png")


# ---------- Guitar pluck ----------

def fig_guitar_pluck():
    audio = pq.Audio.from_file(
        os.path.join(ASSETS, "154030__carlos_vaquero__classical-guitar-f-3-plucked-non-vibrato.wav")
    )
    seg_wide = audio.segment(offset=0.4, duration=1.7)
    seg_zoom = audio.segment(offset=0.552, duration=0.023)

    fig, axes = plt.subplots(2, 1, figsize=(10, 5.5))

    # Wide view
    ax = axes[0]
    t_wide = np.arange(seg_wide.num_samples) / seg_wide.sample_rate + 0.4
    ax.plot(t_wide, seg_wide.samples[:, 0], linewidth=1.0)
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    ax.set_xlim(t_wide[0], t_wide[-1])

    # Zoomed view
    ax = axes[1]
    t_zoom = np.arange(seg_zoom.num_samples) / seg_zoom.sample_rate + 0.552
    ax.plot(t_zoom, seg_zoom.samples[:, 0], linewidth=1.5)
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    ax.set_xlim(t_zoom[0], t_zoom[-1])

    save("fig-guitar-pluck.png")


# ---------- Basic sinusoid parameters ----------

def fig_sinusoid_parameters():
    """Diagram of basic sinusoid x(t) = 0.8 sin(2pi * 2 * t)."""
    f = 2.0
    a = 0.8
    t = np.linspace(0, 1, 2000)
    x = a * np.sin(2 * np.pi * f * t)

    _, ax = plt.subplots(figsize=(10, 3.4))
    ax.plot(t, x)
    ax.axhline(0, color="black", linewidth=0.6)

    # Annotate amplitude
    ax.annotate("", xy=(0.76, a), xytext=(0.76, 0),
                arrowprops=dict(arrowstyle="<->", color="red", linewidth=2))
    ax.text(0.78, a / 2, r"$a = 0.8$", fontsize=14, color="red", va="center")

    # Annotate period
    ax.annotate("", xy=(0.5, -1.05), xytext=(0, -1.05),
                arrowprops=dict(arrowstyle="<->", color="green", linewidth=2))
    ax.text(0.25, -1.18, r"$1/f = 0.5\,\mathrm{s}$", ha="center", fontsize=14, color="green")

    ax.set_ylim(-1.35, 1.1)
    ax.set_yticks([-0.8, 0, 0.8])
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    save("fig-sinusoid-parameters.png")


# ---------- Frequency examples ----------

def fig_frequency_examples():
    """Three sine waves at 220, 330, 440 Hz (zoomed to ~10ms)."""
    f_s = 44100
    dur = 0.01
    n = np.arange(int(f_s * dur))
    t = n / f_s

    freqs = [220, 330, 440]
    labels = [
        r"$\sin(2\pi \cdot 220 \, t)$",
        r"$\sin(2\pi \cdot 330 \, t)$",
        r"$\sin(2\pi \cdot 440 \, t)$",
    ]

    fig, axes = plt.subplots(3, 1, figsize=(10, 6), sharex=True)
    for ax, f, label in zip(axes, freqs, labels):
        ax.plot(t * 1000, np.sin(2 * np.pi * f * t), linewidth=2)
        ax.axhline(0, color="black", linewidth=0.6)
        ax.set_ylabel("Amplitude")
        ax.set_ylim(-1.3, 1.3)
        ax.set_yticks([-1, 0, 1])
        ax.text(0.97, 0.85, label, transform=ax.transAxes,
                ha="right", va="top", fontsize=14,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="gray", alpha=0.8))
    axes[-1].set_xlabel("Time (ms)")
    save("fig-frequency-examples.png")


# ---------- Amplitude examples ----------

def fig_amplitude_examples():
    """Sine waves at different amplitudes."""
    f_s = 44100
    dur = 0.01
    n = np.arange(int(f_s * dur))
    t = n / f_s
    f = 220

    amps = [0.5, 0.05, 0.005]
    labels = [
        r"$0.5\,\sin(2\pi \cdot 220 \, t)$",
        r"$0.05\,\sin(2\pi \cdot 220 \, t)$",
        r"$0.005\,\sin(2\pi \cdot 220 \, t)$",
    ]

    fig, axes = plt.subplots(3, 1, figsize=(10, 6), sharex=True)
    for ax, a, label in zip(axes, amps, labels):
        ax.plot(t * 1000, a * np.sin(2 * np.pi * f * t), linewidth=2)
        ax.axhline(0, color="black", linewidth=0.6)
        ax.set_ylabel("Amplitude")
        ax.set_ylim(-0.6, 0.6)
        ax.set_yticks([-0.5, 0, 0.5])
        ax.text(0.97, 0.85, label, transform=ax.transAxes,
                ha="right", va="top", fontsize=14,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="gray", alpha=0.8))
    axes[-1].set_xlabel("Time (ms)")
    save("fig-amplitude-examples.png")


# ---------- Phase examples ----------

def fig_phase_examples():
    """Sine waves at different initial phases."""
    f_s = 44100
    dur = 0.01
    n = np.arange(int(f_s * dur))
    t = n / f_s
    f = 220

    phases = [0, np.pi / 2, np.pi]
    labels = [
        r"$\sin(2\pi \cdot 220 \, t + 0)$",
        r"$\sin(2\pi \cdot 220 \, t + \pi/2)$",
        r"$\sin(2\pi \cdot 220 \, t + \pi)$",
    ]

    fig, axes = plt.subplots(3, 1, figsize=(10, 6), sharex=True)
    for ax, phi, label in zip(axes, phases, labels):
        ax.plot(t * 1000, np.sin(2 * np.pi * f * t + phi), linewidth=2)
        ax.axhline(0, color="black", linewidth=0.6)
        ax.set_ylabel("Amplitude")
        ax.set_ylim(-1.3, 1.3)
        ax.set_yticks([-1, 0, 1])
        ax.text(0.97, 0.85, label, transform=ax.transAxes,
                ha="right", va="top", fontsize=14,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="gray", alpha=0.8))
    axes[-1].set_xlabel("Time (ms)")
    save("fig-phase-examples.png")


# ---------- Additive synthesis coefficients (individual harmonics + sum) ----------

def fig_additive_coefficients():
    """Side-by-side: summed waveform and individual color-coded harmonics."""
    f_s = 44100
    dur = 0.01
    n = np.arange(int(f_s * dur))
    t = n / f_s
    f0 = 220
    K = 4
    amps = [1, 1/2, 1/4, 1/8]

    fig, axes = plt.subplots(1, 2, figsize=(12, 3.5), sharey=False)

    # Left: summed waveform
    ax = axes[0]
    x = np.zeros_like(t)
    for k in range(1, K + 1):
        x += amps[k - 1] * np.sin(2 * np.pi * k * f0 * t)
    ax.plot(t * 1000, x, linewidth=2, color=COLORS[0])
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Amplitude")
    ax.set_title("Sum", fontsize=14)

    # Right: individual harmonics
    ax = axes[1]
    for k in range(1, K + 1):
        h = amps[k - 1] * np.sin(2 * np.pi * k * f0 * t)
        ax.plot(t * 1000, h, linewidth=1.8, color=COLORS[k - 1],
                label=rf"$k = {k}$")
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Amplitude")
    ax.set_title("Individual harmonics", fontsize=14)
    ax.legend(loc="upper right", fontsize=12)

    save("fig-additive-coefficients.png")


# ---------- Additive synthesis building harmonics ----------

def fig_additive_buildup():
    """Show K=1,2,4,8 harmonics being summed."""
    f_s = 44100
    dur = 0.01
    n = np.arange(int(f_s * dur))
    t = n / f_s
    f0 = 220

    Ks = [1, 2, 4, 8]
    fig, axes = plt.subplots(4, 1, figsize=(10, 7), sharex=True)
    for ax, K in zip(axes, Ks):
        x = np.zeros_like(t)
        for k in range(1, K + 1):
            x += (1.0 / (2 ** (k - 1))) * np.sin(2 * np.pi * k * f0 * t)
        ax.plot(t * 1000, x, linewidth=2)
        ax.axhline(0, color="black", linewidth=0.6)
        ax.set_ylabel("Amplitude")
        ax.set_ylim(-2.1, 2.1)
        label = f"$K = {K}$"
        ax.text(0.97, 0.85, label, transform=ax.transAxes,
                ha="right", va="top", fontsize=14,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="gray", alpha=0.8))
    axes[-1].set_xlabel("Time (ms)")
    save("fig-additive-buildup.png")


# ---------- Basic waveform shapes ----------

def _sawtooth_coeffs(K):
    a = np.zeros(K)
    for k in range(1, K + 1):
        a[k - 1] = 2 * ((-1) ** (k + 1)) / (np.pi * k)
    return a


def _square_coeffs(K):
    a = np.zeros(K)
    for k in range(1, K + 1):
        if k % 2 == 1:
            a[k - 1] = 4 / (np.pi * k)
    return a


def _triangle_coeffs(K):
    a = np.zeros(K)
    for k in range(1, K + 1):
        if k % 2 == 1:
            a[k - 1] = 8 * ((-1) ** ((k - 1) // 2)) / (np.pi ** 2 * k ** 2)
    return a


def fig_basic_waveforms():
    """Sawtooth, square, triangle from additive synthesis."""
    f_s = 44100
    dur = 0.01
    n_arr = np.arange(int(f_s * dur))
    t = n_arr / f_s
    f0 = 220
    K = 32

    waveforms = {
        "Sawtooth": _sawtooth_coeffs(K),
        "Square": _square_coeffs(K),
        "Triangle": _triangle_coeffs(K),
    }

    fig, axes = plt.subplots(3, 1, figsize=(10, 6), sharex=True)
    for ax, (name, coeffs) in zip(axes, waveforms.items()):
        x = np.zeros_like(t)
        for k in range(1, K + 1):
            x += coeffs[k - 1] * np.sin(2 * np.pi * k * f0 * t)
        ax.plot(t * 1000, x, linewidth=2)
        ax.axhline(0, color="black", linewidth=0.6)
        ax.set_ylabel("Amplitude")
        ax.set_ylim(-1.3, 1.3)
        ax.set_yticks([-1, 0, 1])
        ax.text(0.97, 0.85, name, transform=ax.transAxes,
                ha="right", va="top", fontsize=14,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="gray", alpha=0.8))
    axes[-1].set_xlabel("Time (ms)")
    save("fig-basic-waveforms.png")


# ---------- Wavetable diagram ----------

def fig_wavetable_concept():
    """Show a single-cycle wavetable and its repetition."""
    M = 256
    phi = np.linspace(0, 2 * np.pi, M, endpoint=False)
    # Sawtooth-ish table with a few harmonics
    table = np.zeros(M)
    for k in range(1, 9):
        table += (1.0 / k) * np.sin(k * phi)
    table /= np.max(np.abs(table))

    fig, axes = plt.subplots(2, 1, figsize=(10, 5))

    # Top: single cycle table
    ax = axes[0]
    ax.plot(np.arange(M), table, linewidth=2)
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_xlabel("Table index $m$")
    ax.set_ylabel("Amplitude")
    ax.set_xlim(0, M - 1)
    ax.text(0.97, 0.85, f"Wavetable ($M = {M}$)", transform=ax.transAxes,
            ha="right", va="top", fontsize=14,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="gray", alpha=0.8))

    # Bottom: repeated to make audio
    reps = 4
    repeated = np.tile(table, reps)
    ax = axes[1]
    ax.plot(np.arange(len(repeated)), repeated, linewidth=1.5)
    ax.axhline(0, color="black", linewidth=0.6)
    for i in range(1, reps):
        ax.axvline(i * M, color="gray", linewidth=0.8, linestyle="--")
    ax.set_xlabel("Sample index $n$")
    ax.set_ylabel("Amplitude")
    ax.set_xlim(0, len(repeated) - 1)
    ax.text(0.97, 0.85, "Repeated output", transform=ax.transAxes,
            ha="right", va="top", fontsize=14,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="gray", alpha=0.8))

    save("fig-wavetable-concept.png")


if __name__ == "__main__":
    fig_period_2hz()
    fig_period_4hz()
    fig_guitar_pluck()
    fig_sinusoid_parameters()
    fig_frequency_examples()
    fig_amplitude_examples()
    fig_phase_examples()
    fig_additive_coefficients()
    fig_additive_buildup()
    fig_basic_waveforms()
    fig_wavetable_concept()
    print("done.")
