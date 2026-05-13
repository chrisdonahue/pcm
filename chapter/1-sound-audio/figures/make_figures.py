"""Generate every figure and audio asset used in chapter 1.

Outputs are written to ../assets/. Run with the project venv:

    .venv-figures/bin/python chapter/1-sound-audio/figures/make_figures.py

This file lives in figures/ (not code/) because nothing here is meant for
students to read; it exists solely to produce static assets for the chapter.
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.abspath(os.path.join(HERE, "..", "assets"))
os.makedirs(ASSETS, exist_ok=True)

plt.rcParams.update({
    "font.size": 14,
    "axes.labelsize": 16,
    "xtick.labelsize": 13,
    "ytick.labelsize": 13,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "lines.linewidth": 2.5,
})


def save(name):
    path = os.path.join(ASSETS, name)
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  wrote {os.path.relpath(path)}")


def fig_sine_pressure():
    t = np.linspace(0, 1, 2000)
    x = np.sin(2 * np.pi * 2 * t)
    _, ax = plt.subplots(figsize=(10, 3))
    ax.plot(t, x)
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_xlabel("Time")
    ax.set_ylabel("Pressure")
    ax.set_xticks([])
    ax.set_yticks([])
    save("fig-sine-pressure.png")


def fig_sine_amplitude():
    t = np.linspace(0, 1, 2000)
    x = np.sin(2 * np.pi * 2 * t)
    _, ax = plt.subplots(figsize=(10, 3))
    ax.plot(t, x)
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    ax.set_ylim(-1.2, 1.2)
    ax.set_yticks([-1, 0, 1])
    save("fig-sine-amplitude.png")


def fig_sampling():
    t_cont = np.linspace(0, 1, 2000)
    x_cont = np.sin(2 * np.pi * 2 * t_cont)
    f_s = 8
    n = np.arange(f_s + 1)
    t_samp = n / f_s
    x_samp = np.sin(2 * np.pi * 2 * t_samp)
    _, ax = plt.subplots(figsize=(10, 3.4))
    ax.plot(t_cont, x_cont, alpha=0.5)
    for t_i, x_i in zip(t_samp, x_samp):
        ax.plot([t_i, t_i], [0, x_i], color="red", linewidth=1.4)
    ax.scatter(t_samp, x_samp, color="red", s=70, zorder=5)
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    ax.set_yticks([-1, 0, 1])
    save("fig-sampling.png")


def fig_quantization():
    f_s = 8
    n = np.arange(f_s + 1)
    t_samp = n / f_s
    # peak amplitude < 1 so that samples don't land exactly on quantization
    # levels — otherwise the figure would show zero rounding error.
    x_samp = 0.85 * np.sin(2 * np.pi * 2 * t_samp)
    levels = np.array([-1, -0.5, 0, 0.5, 1])
    x_quant = np.array([levels[np.argmin(np.abs(levels - v))] for v in x_samp])
    _, ax = plt.subplots(figsize=(10, 3.4))
    for L in levels:
        ax.axhline(L, color="purple", linestyle="--", alpha=0.5)
    for t_i, raw, q in zip(t_samp, x_samp, x_quant):
        ax.plot([t_i, t_i], [0, q], color="purple", linewidth=1.4)
        if abs(raw - q) > 0.02:
            ax.annotate("", xy=(t_i, q), xytext=(t_i, raw),
                        arrowprops=dict(arrowstyle="->", color="gray", linewidth=1.3))
    ax.scatter(t_samp, x_samp, color="red", s=40, alpha=0.6, label="before quantization")
    ax.scatter(t_samp, x_quant, color="purple", s=70, zorder=5, label="after quantization")
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    ax.set_yticks(levels)
    ax.set_ylim(-1.2, 1.2)
    ax.legend(fontsize=12, loc="lower right")
    save("fig-quantization.png")


def fig_clipping():
    t = np.linspace(0, 0.01, 4000)
    x = 2.0 * np.sin(2 * np.pi * 440 * t)
    y = np.clip(x, -1, 1)
    _, ax = plt.subplots(figsize=(10, 3.4))
    ax.plot(t * 1000, x, alpha=0.4, label=r"$x[n] = 2 \sin(2\pi \cdot 440 \cdot n / f_s)$")
    ax.plot(t * 1000, y, label="clipped to $[-1, 1]$")
    ax.axhline(1, color="red", linestyle="--", alpha=0.6)
    ax.axhline(-1, color="red", linestyle="--", alpha=0.6)
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Amplitude")
    ax.set_ylim(-2.3, 2.3)
    ax.legend(fontsize=12, loc="upper right")
    save("fig-clipping.png")


def fig_adc_dac_pipeline():
    """Show the round-trip analog -> samples -> staircase -> analog."""
    f_s_demo = 16
    f = 2
    t_cont = np.linspace(0, 1, 2000)
    x_cont = 0.85 * np.sin(2 * np.pi * f * t_cont)
    n = np.arange(f_s_demo + 1)
    t_samp = n / f_s_demo
    x_samp = 0.85 * np.sin(2 * np.pi * f * t_samp)

    fig, axs = plt.subplots(4, 1, figsize=(10, 7), sharex=True)
    labels = ["analog\ninput", "samples\n(post-ADC)",
              "staircase\n(pre-filter)", "analog\noutput"]

    axs[0].plot(t_cont, x_cont)

    axs[1].plot(t_cont, x_cont, alpha=0.25)
    for t_i, x_i in zip(t_samp, x_samp):
        axs[1].plot([t_i, t_i], [0, x_i], color="red", linewidth=1.3)
    axs[1].scatter(t_samp, x_samp, color="red", s=55, zorder=5)

    axs[2].step(t_samp, x_samp, where="post", color="black", linewidth=2)

    axs[3].plot(t_cont, x_cont)

    for ax, label in zip(axs, labels):
        ax.axhline(0, color="black", linewidth=0.4)
        ax.set_ylim(-1.1, 1.1)
        ax.set_yticks([])
        ax.set_ylabel(label, rotation=0, ha="right", va="center",
                      fontsize=13, labelpad=20)
    axs[3].set_xlabel("Time")
    save("fig-adc-dac-pipeline.png")


def _dbfs_gain(db):
    return 10 ** (db / 20)


def audio_sine_440():
    """Clean 440 Hz sine at -6 dBFS."""
    f_s = 44100
    n = np.arange(f_s)  # 1 second
    samples = _dbfs_gain(-6) * np.sin(2 * np.pi * 440 * n / f_s)
    path = os.path.join(ASSETS, "audio-sine-440.wav")
    sf.write(path, samples, f_s, subtype="PCM_16")
    print(f"  wrote {os.path.relpath(path)}")


def audio_clipped_sine():
    """440 Hz sine driven to 2x amplitude, hard-clipped, attenuated to -12 dBFS.

    The lower playback level (vs the clean reference at -6 dBFS) is deliberate:
    clipped waveforms have far more high-frequency energy than a clean sine,
    so we attenuate further to avoid hearing damage.
    """
    f_s = 44100
    n = np.arange(f_s)
    raw = 2.0 * np.sin(2 * np.pi * 440 * n / f_s)
    clipped = np.clip(raw, -1.0, 1.0)
    samples = _dbfs_gain(-12) * clipped
    path = os.path.join(ASSETS, "audio-clipped-sine.wav")
    sf.write(path, samples, f_s, subtype="PCM_16")
    print(f"  wrote {os.path.relpath(path)}")


if __name__ == "__main__":
    fig_sine_pressure()
    fig_sine_amplitude()
    fig_sampling()
    fig_quantization()
    fig_clipping()
    fig_adc_dac_pipeline()
    audio_sine_440()
    audio_clipped_sine()
    print("done.")
