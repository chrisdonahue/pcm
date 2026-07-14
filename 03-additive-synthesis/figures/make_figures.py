"""Generate figures for chapter 3 (additive synthesis).

Outputs are written to ../assets/.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pyquist as pq

ASSETS = Path(__file__).resolve().parent.parent / "assets"
ASSETS.mkdir(exist_ok=True)

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
    path = ASSETS / name
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  wrote {path.relative_to(Path.cwd())}")


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
        str(ASSETS / "154030__carlos_vaquero__classical-guitar-f-3-plucked-non-vibrato.wav")
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

    _, ax = plt.subplots(figsize=(10, 4))
    ax.plot(t, x, linewidth=2.5)
    ax.axhline(0, color="black", linewidth=0.6)

    # Dashed lines at +/- amplitude
    ax.axhline(a, color="red", linewidth=1.2, linestyle="--", alpha=0.6)
    ax.axhline(-a, color="red", linewidth=1.2, linestyle="--", alpha=0.6)

    # Annotate amplitude
    ax.annotate("", xy=(0.76, a), xytext=(0.76, 0),
                arrowprops=dict(arrowstyle="<->", color="red", linewidth=2))
    ax.text(0.79, a / 2, r"$a = 0.8$", fontsize=16, color="red", va="center")

    # Vertical dashed lines at period boundaries
    for t_mark in [0.0, 0.5, 1.0]:
        ax.axvline(t_mark, color="green", linewidth=1.2, linestyle="--", alpha=0.6)

    # Annotate period
    ax.annotate("", xy=(0.5, -1.05), xytext=(0, -1.05),
                arrowprops=dict(arrowstyle="<->", color="green", linewidth=2))
    ax.text(0.25, -1.15, r"$1/f = 0.5\;\mathrm{s}$", ha="center", fontsize=16, color="green")

    ax.set_ylim(-1.3, 1.15)
    ax.set_yticks([-1, -0.8, 0, 0.8, 1])
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    save("fig-sinusoid-parameters.png")


# ---------- Frequency examples (individual) ----------

def _single_waveform(t_ms, x, ylim, yticks, name):
    """Helper: single wide waveform plot."""
    _, ax = plt.subplots(figsize=(10, 2.2))
    ax.plot(t_ms, x, linewidth=2)
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Amplitude")
    ax.set_ylim(*ylim)
    ax.set_yticks(yticks)
    ax.set_xlim(t_ms[0], t_ms[-1])
    save(name)


def fig_frequency_individual():
    """One figure per frequency value."""
    f_s = 44100
    dur = 0.01
    t = np.arange(int(f_s * dur)) / f_s
    for f in [220, 330, 440]:
        _single_waveform(t * 1000, np.sin(2 * np.pi * f * t),
                         (-1.3, 1.3), [-1, 0, 1], f"fig-sine-{f}.png")


def fig_amplitude_individual():
    """One figure per amplitude value."""
    f_s = 44100
    dur = 0.01
    t = np.arange(int(f_s * dur)) / f_s
    for a in [0.5, 0.05, 0.005]:
        label = str(a).replace(".", "p")
        _single_waveform(t * 1000, a * np.sin(2 * np.pi * 220 * t),
                         (-0.6, 0.6), [-0.5, 0, 0.5], f"fig-sine-amp-{label}.png")


def fig_phase_individual():
    """One figure per phase value."""
    f_s = 44100
    dur = 0.01
    t = np.arange(int(f_s * dur)) / f_s
    for i, phi in enumerate([0.0, np.pi / 2, np.pi]):
        _single_waveform(t * 1000, np.sin(2 * np.pi * 220 * t + phi),
                         (-1.3, 1.3), [-1, 0, 1], f"fig-sine-phase-{i}.png")


# ---------- Harmonics overlay ----------

def fig_harmonics_overlay():
    """Four harmonics (k=1..4) of f0=2 Hz overlaid, all at unit amplitude."""
    t = np.linspace(0, 1, 2000)
    _, ax = plt.subplots(figsize=(10, 3.4))
    for k in range(1, 5):
        ax.plot(t, np.sin(2 * np.pi * k * 2 * t), linewidth=2,
                color=COLORS[k - 1], label=rf"$k = {k}$  ($f = {2*k}$ Hz)")
    ax.axhline(0, color="black", linewidth=0.6)
    # Dashed vertical lines at fundamental period boundaries
    for t_mark in [0.0, 0.5, 1.0]:
        ax.axvline(t_mark, color="gray", linewidth=0.8, linestyle="--")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    ax.set_ylim(-1.3, 1.3)
    ax.set_yticks([-1, 0, 1])
    ax.legend(loc="upper right", fontsize=12)
    save("fig-harmonics-overlay.png")


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


def fig_wavetable_comparison():
    """Generate audio comparing exact sine vs wavetable naive/interp at M=8."""
    f_s = 44100
    T = 1.5
    N = int(T * f_s)
    f_0 = 440.0
    amp_val = pq.helper.db_to_amplitude(-6)

    # Exact sine
    t = np.arange(N) / f_s
    exact = amp_val * np.sin(2 * np.pi * f_0 * t)

    # Wavetable with M=8 (very coarse — makes artifacts audible)
    M = 8
    m = np.arange(M)
    table = np.sin(2 * np.pi * m / M)

    # Naive lookup
    phase_inc = f_0 * M / f_s
    phase = np.arange(N) * phase_inc
    naive = amp_val * table[phase.astype(int) % M]

    # Interp lookup
    m_idx = phase.astype(int)
    alpha = phase - m_idx
    interp = amp_val * ((1 - alpha) * table[m_idx % M] + alpha * table[(m_idx + 1) % M])

    pq.Audio(exact, sample_rate=f_s).write(str(ASSETS / "audio-wt-exact.wav"))
    pq.Audio(naive, sample_rate=f_s).write(str(ASSETS / "audio-wt-naive-8.wav"))
    pq.Audio(interp, sample_rate=f_s).write(str(ASSETS / "audio-wt-interp-8.wav"))
    print("  wrote wavetable comparison audio")


if __name__ == "__main__":
    fig_period_2hz()
    fig_period_4hz()
    fig_guitar_pluck()
    fig_sinusoid_parameters()
    fig_frequency_individual()
    fig_amplitude_individual()
    fig_phase_individual()
    fig_harmonics_overlay()
    fig_additive_coefficients()
    fig_additive_buildup()
    fig_basic_waveforms()
    fig_wavetable_concept()
    fig_wavetable_comparison()
    print("done.")
