"""Generate every figure and audio asset used in chapter 2.

Outputs are written to ../assets/. Run with the project venv:

    .venv-figures/bin/python chapter/2-pyquist-vectorized/figures/make_figures.py
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
    "lines.linewidth": 2.0,
})


def _dbfs_gain(db):
    return 10 ** (db / 20)


def save_fig(name):
    path = os.path.join(ASSETS, name)
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  wrote {os.path.relpath(path)}")


def write_wav(samples, f_s, name):
    path = os.path.join(ASSETS, name)
    sf.write(path, samples, f_s, subtype="PCM_16")
    print(f"  wrote {os.path.relpath(path)}")


# ----------------------------------------------------------------------
# Audio assets
# ----------------------------------------------------------------------

def audio_sine_440():
    """Clean 440 Hz sine at -6 dBFS, 1 second."""
    f_s = 44100
    n = np.arange(f_s)
    samples = _dbfs_gain(-6) * np.sin(2 * np.pi * 440 * n / f_s)
    write_wav(samples, f_s, "audio-sine-440.wav")


def audio_noise():
    """Two seconds of low-amplitude white noise, matching the prose snippet."""
    f_s = 44100
    N = 2 * f_s
    rng = np.random.default_rng(seed=42)
    samples = rng.standard_normal(N).astype(np.float32) * 0.01
    # Clamp anything that accidentally exceeds [-1, 1] (extremely unlikely at
    # this gain, but worth a safety net).
    samples = np.clip(samples, -1.0, 1.0)
    write_wav(samples, f_s, "audio-noise.wav")


def audio_stereo_220_330():
    """One second of stereo audio: 220 Hz L, 330 Hz R, each at -6 dBFS."""
    f_s = 44100
    N = f_s
    n = np.arange(N)
    t = n / f_s
    freqs = np.array([220.0, 330.0])
    # Broadcasting: t[:, np.newaxis] is (N, 1); freqs is (2,); result is (N, 2).
    stereo = _dbfs_gain(-6) * np.sin(2 * np.pi * freqs * t[:, np.newaxis])
    write_wav(stereo.astype(np.float32), f_s, "audio-stereo-220-330.wav")
    return stereo, f_s


def audio_mono_mix(stereo, f_s):
    """Mono downmix of the 220/330 stereo example via channel mean."""
    mono = stereo.mean(axis=1).astype(np.float32)
    write_wav(mono, f_s, "audio-mono-220-330-mix.wav")


def audio_chord_major():
    """C major triad (C4, E4, G4) summed as Pyquist would, normalized to -6 dBFS.

    Returns (samples, f_s) so the segment-extracted clip can reuse the data.
    """
    f_s = 44100
    N = 2 * f_s  # 2 seconds so segment(offset=0.25, duration=0.5) is well inside
    n = np.arange(N)
    t = n / f_s
    freqs = np.array([261.63, 329.63, 392.00])  # C4, E4, G4
    # Each sine at 0.3, summed -> peak up to ~0.9 depending on phase.
    chord = (0.3 * np.sin(2 * np.pi * freqs * t[:, np.newaxis])).sum(axis=1)
    # Normalize to -6 dBFS for safe playback.
    peak = np.abs(chord).max()
    chord = chord * (_dbfs_gain(-6) / peak)
    write_wav(chord.astype(np.float32), f_s, "audio-chord-major.wav")
    return chord, f_s


def audio_chord_segment(chord, f_s):
    """The middle 0.5 s of the chord, matching the segment(offset=0.25, duration=0.5) example."""
    start = int(0.25 * f_s)
    end = start + int(0.5 * f_s)
    write_wav(chord[start:end].astype(np.float32), f_s, "audio-chord-segment.wav")


# ----------------------------------------------------------------------
# Figures
# ----------------------------------------------------------------------

def fig_stereo_waveform():
    """Show a short window of the L (220 Hz) and R (330 Hz) channels stacked."""
    f_s = 44100
    duration = 0.025  # 25 ms — enough for ~5 cycles of 220, ~7 of 330
    N = int(f_s * duration)
    t = np.arange(N) / f_s
    left = _dbfs_gain(-6) * np.sin(2 * np.pi * 220 * t)
    right = _dbfs_gain(-6) * np.sin(2 * np.pi * 330 * t)

    fig, axs = plt.subplots(2, 1, figsize=(10, 4.5), sharex=True)
    axs[0].plot(t * 1000, left, color="#1f77b4")
    axs[1].plot(t * 1000, right, color="#d62728")
    for ax in axs:
        ax.axhline(0, color="black", linewidth=0.5)
        ax.set_ylim(-0.7, 0.7)
        ax.set_yticks([-0.5, 0, 0.5])
    axs[0].set_ylabel("Left ch.\n(220 Hz)", rotation=0, ha="right", va="center",
                      fontsize=13, labelpad=20)
    axs[1].set_ylabel("Right ch.\n(330 Hz)", rotation=0, ha="right", va="center",
                      fontsize=13, labelpad=20)
    axs[1].set_xlabel("Time (ms)")
    save_fig("fig-stereo-waveform.png")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

if __name__ == "__main__":
    audio_sine_440()
    audio_noise()
    stereo, f_s = audio_stereo_220_330()
    audio_mono_mix(stereo, f_s)
    chord, f_s = audio_chord_major()
    audio_chord_segment(chord, f_s)
    fig_stereo_waveform()
    print("done.")
