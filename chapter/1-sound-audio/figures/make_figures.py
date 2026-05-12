"""Generate every figure and audio asset used in chapter 1.

Outputs are written to ../assets/. Run with the project venv:

    .venv-figures/bin/python chapter/1-sound-audio/figures/make_figures.py

This file lives in figures/ (not code/) because nothing here is meant for
students to read; it exists solely to produce static assets for the chapter.
"""

import math
import os
import struct
import wave

import matplotlib.pyplot as plt
import numpy as np

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


def _annotate_period(ax, t0, label):
    ax.annotate("", xy=(t0, 1.25), xytext=(0, 1.25),
                arrowprops=dict(arrowstyle="<->", linewidth=2))
    ax.text(t0 / 2, 1.32, label, ha="center", fontsize=16)


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


def write_wav(samples, f_s, path):
    with wave.open(path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(f_s)
        for s in samples:
            s_c = max(-1.0, min(s, 1.0))
            f.writeframes(struct.pack("<h", int(round(s_c * 32767))))


def audio_sine_440():
    f_s = 44100
    N = f_s
    gain = 0.5
    samples = [gain * math.sin(2 * math.pi * 440 * i / f_s) for i in range(N)]
    write_wav(samples, f_s, os.path.join(ASSETS, "audio-sine-440.wav"))
    print("  wrote audio-sine-440.wav")


def audio_clipped_sine():
    """A sine driven to 2x its allowed amplitude, hard-clipped, then attenuated.

    The attenuation keeps the playback volume modest while preserving the
    distinctive clipped shape (and thus the harsh timbre).
    """
    f_s = 44100
    N = f_s
    out_gain = 0.5
    samples = []
    for i in range(N):
        x = 2.0 * math.sin(2 * math.pi * 440 * i / f_s)
        x = max(-1.0, min(x, 1.0))
        samples.append(out_gain * x)
    write_wav(samples, f_s, os.path.join(ASSETS, "audio-clipped-sine.wav"))
    print("  wrote audio-clipped-sine.wav")


if __name__ == "__main__":
    fig_sine_pressure()
    fig_sine_amplitude()
    fig_period_2hz()
    fig_period_4hz()
    fig_sampling()
    fig_quantization()
    fig_clipping()
    audio_sine_440()
    audio_clipped_sine()
    print("done.")
