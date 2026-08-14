"""Generate figures and sound examples for Chapter 10 (Frame-based processing).

Outputs are written to ../assets/. This file is *not* student-facing.

Run with the project virtualenv (pyquist reached via PYTHONPATH):
    PYTHONPATH=../../../../pyquist ../../../.venv/bin/python make_figures.py
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

plt.rcParams.update({
    "font.size": 14, "axes.labelsize": 16, "xtick.labelsize": 13,
    "ytick.labelsize": 13, "axes.spines.top": False, "axes.spines.right": False,
    "lines.linewidth": 2.0,
})
COLORS = plt.rcParams["axes.prop_cycle"].by_key()["color"]
BLUE, ORANGE, GREEN, RED, PURPLE = COLORS[0], COLORS[1], COLORS[2], COLORS[3], COLORS[4]


def save_fig(name: str) -> None:
    plt.tight_layout()
    plt.savefig(ASSETS / name, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  wrote {name}")


def write_audio(samples: np.ndarray, name: str, sr: int = F_S, peak: float = PEAK_DBFS) -> None:
    audio = pq.Audio(samples.astype(np.float32), sr)
    audio.normalize(peak_dbfs=peak)
    audio.write(str(ASSETS / name))
    print(f"  wrote {name}")


def load_trio() -> np.ndarray:
    a = pq.Audio.from_file(str(ASSETS / "audio-trio.wav"))
    return np.asarray(a.samples).reshape(-1)


# ---------------------------------------------------------------------------
# DSP building blocks (agent-side copies of the chapter's code)
# ---------------------------------------------------------------------------


def hann(n: int) -> np.ndarray:
    return 0.5 * (1 - np.cos(2 * np.pi * np.arange(n) / n))


def stft(x, hop, nF, window):
    return np.array([np.fft.rfft(x[s:s + nF] * window)
                     for s in range(0, len(x) - nF + 1, hop)])


def istft(S, hop, nF, window, trim=True):
    length = hop * (S.shape[0] - 1) + nF
    out = np.zeros(length)
    wsum = np.zeros(length)
    for k in range(S.shape[0]):
        frame = np.fft.irfft(S[k], nF) * window
        out[k * hop:k * hop + nF] += frame
        wsum[k * hop:k * hop + nF] += window ** 2
    out = out / np.maximum(wsum, 1e-8)
    return out[nF:-nF] if trim else out   # drop under-overlapped edges


def granular(x, grain_len, hop_extract, hop_overlap, window, manipulate=None):
    """Extract windowed grains, optionally manipulate the list, overlap-add."""
    grains = [x[s:s + grain_len] * window
              for s in range(0, len(x) - grain_len + 1, hop_extract)]
    if manipulate is not None:
        grains = manipulate(grains)
    length = hop_overlap * (len(grains) - 1) + grain_len
    out = np.zeros(length)
    for k, g in enumerate(grains):
        out[k * hop_overlap:k * hop_overlap + grain_len] += g
    return out


def phase_vocoder(D, rate, hop):
    """Standard phase-vocoder time stretch of a complex STFT by `rate`
    (>1 = faster/shorter, <1 = slower/longer)."""
    n_bins = D.shape[1]
    phi_adv = np.linspace(0, np.pi * hop, n_bins)
    D = np.concatenate([D, np.zeros((2, n_bins))], axis=0)
    steps = np.arange(0, D.shape[0] - 2, rate)
    out = np.zeros((len(steps), n_bins), dtype=complex)
    phase = np.angle(D[0])
    for i, step in enumerate(steps):
        j = int(np.floor(step))
        a = step - j
        mag = (1 - a) * np.abs(D[j]) + a * np.abs(D[j + 1])
        out[i] = mag * np.exp(1j * phase)
        dphi = np.angle(D[j + 1]) - np.angle(D[j]) - phi_adv
        dphi -= 2 * np.pi * np.round(dphi / (2 * np.pi))
        phase += phi_adv + dphi
    return out


def resample_by(x, factor):
    """Linearly resample x to length len(x)/factor (factor>1 shortens)."""
    n_out = int(round(len(x) / factor))
    return np.interp(np.arange(n_out) * factor, np.arange(len(x)), x)


# ===========================================================================
# AUDIO EXAMPLES
# ===========================================================================


def audio_melody():
    """A simple C-D-E-F-G melody of sine tones (running example for the STFT)."""
    pitches = [261.63, 293.66, 329.63, 349.23, 392.00]  # C4 D4 E4 F4 G4
    dur = 0.5
    n = int(dur * F_S)
    t = np.arange(n) / F_S
    env = np.interp(t, [0, 0.02, dur - 0.05, dur], [0, 1, 1, 0])
    x = np.concatenate([np.sin(2 * np.pi * f * t) * env for f in pitches])
    write_audio(x, "audio-melody.wav")
    return x


def audio_granular(trio):
    sr = F_S
    # (1) A few long grains with a big gap, so each grain is audible on its own.
    grain_len = int(0.05 * sr)          # 50 ms grains
    ioi = int(0.5 * sr)                 # 500 ms inter-onset interval
    starts = np.arange(0, len(trio) - grain_len, int(0.35 * sr))[:14]
    rect = np.ones(grain_len)
    w = hann(grain_len)
    rect_out = np.zeros(ioi * len(starts) + grain_len)
    hann_out = np.zeros_like(rect_out)
    for k, s in enumerate(starts):
        g = trio[s:s + grain_len]
        rect_out[k * ioi:k * ioi + grain_len] += g * rect
        hann_out[k * ioi:k * ioi + grain_len] += g * w
    write_audio(rect_out, "audio-grains-rect.wav")
    write_audio(hann_out, "audio-grains-hann.wav")

    # (2) Dense granular texture: shuffle grain order within short segments.
    gl, hop = int(0.05 * sr), int(0.025 * sr)   # 50 ms grains, 50% overlap
    rng = np.random.default_rng(0)

    def shuffle_segments(grains, seg=40):
        grains = list(grains)
        for i in range(0, len(grains), seg):
            block = grains[i:i + seg]
            rng.shuffle(block)
            grains[i:i + seg] = block
        return grains
    tex = granular(trio, gl, hop, hop, hann(gl), manipulate=shuffle_segments)
    write_audio(tex, "audio-granular-texture.wav")

    # (3) For contrast: randomize the raw SAMPLES (not grains) -> just noise.
    scrambled = trio.copy()
    rng.shuffle(scrambled)
    write_audio(scrambled, "audio-scrambled-samples.wav")


def audio_time_stretch(trio):
    sr = F_S
    gl = int(0.06 * sr)
    hop = gl // 4                        # 75% overlap for smooth stretching
    w = hann(gl)
    # Granular time stretch: overlap grains at a different hop than extraction.
    half = granular(trio, gl, hop, hop * 2, w)      # spacing x2 -> 0.5x speed (longer)
    dbl = granular(trio, gl, hop, hop // 2, w)      # spacing /2 -> 2x speed (shorter)
    write_audio(half, "audio-stretch-half.wav")
    write_audio(dbl, "audio-stretch-double.wav")
    # Resampling for comparison: changes speed AND pitch together.
    write_audio(resample_by(trio, 0.5), "audio-resample-half.wav")
    write_audio(resample_by(trio, 2.0), "audio-resample-double.wav")
    # Decoupled: time-stretch to 0.5x speed, then resample grains to drop pitch.
    decoupled = resample_by(granular(trio, gl, hop, hop * 2, w), 2.0)  # ~orig length, octave down
    write_audio(decoupled, "audio-decoupled.wav")


def audio_spectral(trio):
    nF, hop = 2048, 512
    w = hann(nF)
    S = stft(trio, hop, nF, w)
    rng = np.random.default_rng(0)
    # Phase randomization: keep magnitudes, scramble phases -> transients smear.
    Sr = np.abs(S) * np.exp(1j * rng.uniform(-np.pi, np.pi, S.shape))
    write_audio(istft(Sr, hop, nF, w), "audio-phase-random.wav")
    # Cross synthesis: magnitude of the trio, phase of white noise.
    noise = rng.standard_normal(len(trio))
    Sn = stft(noise, hop, nF, w)
    m = min(S.shape[0], Sn.shape[0])
    Sx = np.abs(S[:m]) * np.exp(1j * np.angle(Sn[:m]))
    write_audio(istft(Sx, hop, nF, w), "audio-cross-synth.wav")


def audio_phase_vocoder(trio):
    nF, hop = 2048, 512
    w = hann(nF)
    S = stft(trio, hop, nF, w)
    half = istft(phase_vocoder(S, 0.5, hop), hop, nF, w)   # 0.5x speed, pitch kept
    dbl = istft(phase_vocoder(S, 2.0, hop), hop, nF, w)     # 2x speed, pitch kept
    write_audio(half, "audio-pv-half.wav")
    write_audio(dbl, "audio-pv-double.wav")
    # Pitch shift up an octave: stretch 2x then resample back to original length.
    stretched = istft(phase_vocoder(S, 0.5, hop), hop, nF, w)
    write_audio(resample_by(stretched, 2.0), "audio-pv-pitch.wav")


# ===========================================================================
# FIGURES
# ===========================================================================


def spectrogram(ax, x, nF, hop, window, sr=F_S, fmax=None):
    S = np.abs(stft(x, hop, nF, window)).T
    db = 20 * np.log10(S / S.max() + 1e-6)
    ax.imshow(db, origin="lower", aspect="auto", cmap="magma", vmin=-80, vmax=0,
              extent=[0, len(x) / sr, 0, sr / 2000])
    ax.set_ylim(0, (fmax or sr / 2) / 1000)


def fig_frame_extraction(trio):
    seg = trio[:4096]
    nF = 1024
    t = np.arange(len(seg)) / F_S * 1000
    cmap = [BLUE, ORANGE, GREEN, RED, PURPLE, "#8c564b"]
    fig, axes = plt.subplots(2, 1, figsize=(12, 5), sharex=True)
    for ax, hop, title in [(axes[0], 1024, "0% overlap  ($N_H = N_F$)"),
                           (axes[1], 512, "50% overlap  ($N_H = N_F/2$)")]:
        ax.plot(t, seg, color="0.4", lw=0.8)
        starts = list(range(0, len(seg) - nF + 1, hop))[:6]
        for k, s in enumerate(starts):
            ax.axvspan(s / F_S * 1000, (s + nF) / F_S * 1000, color=cmap[k % len(cmap)],
                       alpha=0.16, ymin=0.5 - 0.06 * (k % 2), ymax=1.0)
            ax.text((s + nF / 2) / F_S * 1000, 0.9, f"frame {k}", ha="center",
                    fontsize=9, color=cmap[k % len(cmap)])
        ax.set_title(title, fontsize=13)
        ax.set_ylabel("Amplitude")
        ax.set_ylim(-1, 1)
    axes[1].set_xlabel("Time (ms)")
    axes[1].set_xlim(0, t[-1])
    save_fig("fig-frame-extraction.png")


def fig_cola():
    nF, hop = 200, 100                      # Hann at 50% overlap
    w = hann(nF)
    n = np.arange(700)
    fig, ax = plt.subplots(figsize=(11, 3.4))
    total = np.zeros(len(n))
    for k in range(-1, 7):
        start = k * hop
        seg = np.zeros(len(n))
        idx = np.arange(nF) + start
        valid = (idx >= 0) & (idx < len(n))
        seg[idx[valid]] = w[valid]
        ax.plot(n, seg, color=BLUE, lw=1.2, alpha=0.5)
        total += seg
    ax.plot(n, total, color=RED, lw=2.6, label="sum of windows")
    ax.axhline(1.0, color="0.6", ls="--", lw=1.0)
    ax.set_xlim(0, 600)
    ax.set_ylim(0, 1.3)
    ax.set_xlabel("Sample index $n$")
    ax.set_ylabel("Window value")
    ax.legend(loc="upper right", fontsize=12)
    save_fig("fig-cola.png")


def fig_reconstruction_cases():
    nF = 100
    fig, axes = plt.subplots(1, 3, figsize=(14, 3.4), sharey=True)
    specs = [(100, r"$N_H = N_F$", "perfect reconstruction"),
             (140, r"$N_H > N_F$", "gaps (samples lost)"),
             (60, r"$N_H < N_F$", "overlap (amplitude gain)")]
    n = np.arange(560)
    for ax, (hop, title, sub) in zip(axes, specs):
        total = np.zeros(len(n))
        for k in range(6):
            s = k * hop
            if s >= len(n):
                break
            idx = np.arange(nF) + s
            valid = idx < len(n)
            total[idx[valid]] += 1.0
            ax.axvspan(s, min(s + nF, len(n)), color=BLUE, alpha=0.10)
        ax.plot(n, total, color=RED, lw=2.4)
        ax.axhline(1.0, color="0.6", ls="--", lw=1.0)
        ax.set_title(title + "\n" + sub, fontsize=13)
        ax.set_xlabel("Sample index $n$")
        ax.set_xlim(0, 500)
        ax.set_ylim(0, 2.4)
    axes[0].set_ylabel("Reconstruction gain")
    save_fig("fig-reconstruction-cases.png")


def _grain_shape(x0, w, h, npts=100):
    t = np.linspace(0, 1, npts)
    return x0 + t * w, h * 0.5 * (1 - np.cos(2 * np.pi * t))


def fig_granular_collage(trio):
    fig, axes = plt.subplots(3, 1, figsize=(12, 5.2))
    cmap = [BLUE, ORANGE, GREEN, "#17becf", "0.5", "#9467bd"]
    # source
    seg = trio[:int(2.2 * F_S)]
    axes[0].plot(np.linspace(0, 10, len(seg)), seg, color=BLUE, lw=0.5)
    axes[0].set_ylabel("Source\nmaterial", rotation=0, ha="right", va="center", fontsize=12)
    # extract grains (overlapping windows)
    gw, gh = 1.7, 1.0
    for k, x0 in enumerate(np.arange(0, 10, 1.5)):
        xs, ys = _grain_shape(x0, gw, gh)
        axes[1].fill_between(xs, 0, ys, color=cmap[k % len(cmap)], alpha=0.45)
    axes[1].set_ylabel(r"Extract" + "\n" + r"grains $\times$", rotation=0, ha="right", va="center", fontsize=12)
    # reassemble (rearranged, some gaps)
    order = [0, 3, 1, 5, 2, 4]
    for slot, k in enumerate(order):
        xs, ys = _grain_shape(slot * 1.6 + 0.3, gw, gh)
        axes[2].fill_between(xs, 0, ys, color=cmap[k % len(cmap)], alpha=0.45)
    axes[2].set_ylabel(r"Reassemble" + "\n" + r"$+$", rotation=0, ha="right", va="center", fontsize=12)
    for ax in axes:
        ax.set_xlim(0, 10.5)
        ax.set_xticks([])
        ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(False)
    save_fig("fig-granular-collage.png")


def fig_granular_randomize():
    rng = np.random.default_rng(2)
    n = 16
    cols = plt.cm.viridis(np.linspace(0, 1, n))
    fig, axes = plt.subplots(2, 1, figsize=(12, 3.6))
    for ax, title, perm in [
        (axes[0], "Randomize order globally", rng.permutation(n)),
        (axes[1], "Randomize order within segments of 4",
         np.concatenate([rng.permutation(4) + i for i in range(0, n, 4)]))]:
        for i in range(n):
            ax.add_patch(plt.Rectangle((i, 1.1), 0.9, 0.7, color=cols[i]))     # original order
            ax.add_patch(plt.Rectangle((i, 0.0), 0.9, 0.7, color=cols[perm[i]]))  # shuffled
        ax.annotate("", xy=(n / 2, 0.85), xytext=(n / 2, 1.05),
                    arrowprops=dict(arrowstyle="-|>", color="0.4"))
        ax.set_title(title, fontsize=13)
        ax.set_xlim(-0.3, n + 0.3)
        ax.set_ylim(-0.15, 1.95)
        ax.axis("off")
    axes[0].text(-0.3, 1.45, "grains", ha="right", fontsize=10, color="0.4")
    axes[0].text(-0.3, 0.35, "output", ha="right", fontsize=10, color="0.4")
    save_fig("fig-granular-randomize.png")


def fig_stft_melody(melody):
    fig = plt.figure(figsize=(13, 6))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.3])
    # score-like panel: note names stepping up over time
    ax0 = fig.add_subplot(gs[0, 0])
    names = ["C4", "D4", "E4", "F4", "G4"]
    for i, nm in enumerate(names):
        ax0.text(i * 0.5 + 0.25, i, nm, ha="center", va="center", fontsize=15, color=BLUE,
                 bbox=dict(boxstyle="round,pad=0.3", fc="#e8f0fe", ec=BLUE))
    ax0.set_xlim(0, 2.5)
    ax0.set_ylim(-0.7, 4.7)
    ax0.set_title("The melody: C D E F G (rising)", fontsize=13)
    ax0.set_xlabel("Time (s)")
    ax0.set_yticks([])
    # full-signal DFT: all 5 pitches as peaks, but no sense of order
    ax1 = fig.add_subplot(gs[0, 1])
    X = np.abs(np.fft.rfft(melody * np.hanning(len(melody))))
    f = np.fft.rfftfreq(len(melody), 1 / F_S)
    ax1.plot(f, X / X.max(), color=PURPLE, lw=1.0)
    ax1.set_xlim(0, 600)
    ax1.set_title("DFT of the whole signal (time lost)", fontsize=13)
    ax1.set_xlabel("Frequency (Hz)")
    ax1.set_ylabel("Amplitude")
    # spectrogram: pitches step up over time
    ax2 = fig.add_subplot(gs[1, :])
    spectrogram(ax2, melody, 4096, 512, hann(4096), fmax=1200)
    ax2.set_title("Spectrogram (frequency over time)", fontsize=13)
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("Frequency (kHz)")
    save_fig("fig-stft-melody.png")


def _leakage_row(axes, window, wlabel):
    fs, dur = 200.0, 4.0
    t = np.arange(int(dur * fs)) / fs
    x = np.sin(2 * np.pi * 1 * t) + np.sin(2 * np.pi * 2 * t)
    a, b = 1.0, 3.0
    w = np.zeros_like(t)
    win_idx = (t >= a) & (t < b)
    w[win_idx] = window(win_idx.sum())
    xw = x * w

    def spec(sig):
        S = np.fft.fftshift(np.abs(np.fft.fft(sig)))
        fr = np.fft.fftshift(np.fft.fftfreq(len(sig), 1 / fs))
        return fr, S / S.max()
    axes[0].plot(t, x, color=ORANGE, alpha=0.3, ls="--")
    axes[0].plot(t, xw, color=ORANGE)
    axes[0].set_title(r"$x(t)$", fontsize=14)
    axes[1].plot(t, w, color=RED)
    axes[1].set_title(wlabel, fontsize=14)
    axes[2].plot(t, x, color=ORANGE, alpha=0.3, ls="--")
    axes[2].plot(t, xw, color=GREEN)
    axes[2].set_title(r"$x(t)\cdot w(t)$", fontsize=14)
    fr, S = spec(xw)
    axes[3].plot(fr, S, color=GREEN)
    axes[3].set_title(r"$|X(\omega) * W(\omega)|$", fontsize=13)
    for ax in axes[:3]:
        ax.set_xlim(0, dur)
        ax.set_xlabel("Time (s)")
    axes[3].set_xlim(-5, 5)
    axes[3].set_xlabel("Frequency (Hz)")


def fig_leakage_windowing():
    for name, window, wlabel in [
        ("fig-leakage.png", np.ones, r"$w(t)$ (rectangular)"),
        ("fig-windowing.png", hann, r"$w(t)$ (Hann)")]:
        fig, axes = plt.subplots(1, 4, figsize=(15, 3.2))
        _leakage_row(axes, window, wlabel)
        save_fig(name)


def fig_spectrogram_window(trio):
    fig, axes = plt.subplots(1, 2, figsize=(13, 4))
    nF, hop = 1024, 256
    spectrogram(axes[0], trio, nF, hop, np.ones(nF), fmax=8000)
    axes[0].set_title("Rectangular window (strong leakage)", fontsize=13)
    spectrogram(axes[1], trio, nF, hop, hann(nF), fmax=8000)
    axes[1].set_title("Hann window (leakage reduced)", fontsize=13)
    for ax in axes:
        ax.set_xlabel("Time (s)")
    axes[0].set_ylabel("Frequency (kHz)")
    save_fig("fig-spectrogram-window.png")


def fig_stft_diagram():
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    fig, ax = plt.subplots(figsize=(13, 3.6))
    ax.axis("off")
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 4)

    def box(x, label, color="0.93"):
        ax.add_patch(FancyBboxPatch((x, 1.4), 1.7, 1.2, boxstyle="round,pad=0.03",
                                    fc=color, ec="0.3", lw=1.5))
        ax.text(x + 0.85, 2.0, label, ha="center", va="center", fontsize=12)

    def arrow(x0, x1):
        ax.add_patch(FancyArrowPatch((x0, 2.0), (x1, 2.0), arrowstyle="-|>",
                                     mutation_scale=16, color="0.35", lw=1.6))
    ax.text(0.5, 2.0, r"$x[n]$", ha="center", va="center", fontsize=15, color=BLUE)
    arrow(0.9, 1.4)
    box(1.4, "frame\n$x_k$")
    arrow(3.1, 3.6)
    box(3.6, "DFT")
    arrow(5.3, 5.8)
    box(5.8, "spectra\n(edit)", color="#e8f0fe")
    arrow(7.5, 8.0)
    box(8.0, "IDFT")
    arrow(9.7, 10.2)
    box(10.2, "overlap\nadd")
    arrow(11.9, 12.4)
    ax.text(12.6, 2.0, r"$\hat{x}[n]$", ha="center", va="center", fontsize=15, color=PURPLE)
    ax.text(4.45, 3.2, "analysis (STFT)", ha="center", fontsize=12, style="italic", color="0.4")
    ax.text(9.05, 3.2, "synthesis (ISTFT)", ha="center", fontsize=12, style="italic", color="0.4")
    save_fig("fig-stft-diagram.png")


def fig_phase_ambiguity():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, ang, lab in [(axes[0], np.pi / 4, r"$\angle X[i,\,k] = \pi/4$"),
                         (axes[1], 5 * np.pi / 4, r"$\angle X[i{+}1,\,k] = 5\pi/4$")]:
        ax.add_patch(plt.Circle((0, 0), 1, fill=False, ec="0.4", lw=1.5))
        ax.annotate("", xy=(np.cos(ang), np.sin(ang)), xytext=(0, 0),
                    arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=2.5))
        ax.axhline(0, color="0.8", lw=0.8)
        ax.axvline(0, color="0.8", lw=0.8)
        ax.set_xlim(-1.3, 1.3)
        ax.set_ylim(-1.3, 1.3)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(lab, fontsize=15)
    fig.suptitle(r"Phase advanced by $\pi$... or $3\pi$, or $5\pi$?  The STFT cannot tell.",
                 fontsize=13, y=0.04)
    save_fig("fig-phase-ambiguity.png")


def gif_nf_sweep(trio):
    from PIL import Image
    frames = []
    for nF in [256, 512, 1024, 2048, 4096, 8192]:
        fig, ax = plt.subplots(figsize=(8, 3.6), dpi=100)
        spectrogram(ax, trio, nF, nF // 4, hann(nF), fmax=8000)
        ax.set_title(f"$N_F = {nF}$ samples  ({nF / F_S * 1000:.0f} ms)", fontsize=14)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Frequency (kHz)")
        fig.tight_layout()
        fig.canvas.draw()
        img = Image.fromarray(np.asarray(fig.canvas.buffer_rgba())).convert("RGB")
        frames.append(img.resize((img.width // 2, img.height // 2), Image.LANCZOS))
        plt.close(fig)
    frames += [frames[-1]] * 3
    pal = frames[3].convert("P", palette=Image.ADAPTIVE, colors=128)
    fp = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    fp[0].save(str(ASSETS / "fig-nf-sweep.gif"), save_all=True,
               append_images=fp[1:], duration=900, loop=0)
    print("  wrote fig-nf-sweep.gif")


def gif_nh_overlap(trio):
    from PIL import Image
    seg = trio[:4096]
    nF = 1024
    t = np.arange(len(seg)) / F_S * 1000
    frames = []
    cmap = [BLUE, ORANGE, GREEN, RED, PURPLE, "#8c564b", "#17becf", "#e377c2"]
    for overlap, hop in [(0, 1024), (50, 512), (75, 256)]:
        fig, ax = plt.subplots(figsize=(10, 3.2))
        ax.plot(t, seg, color="0.4", lw=0.8)
        for k, s in enumerate(range(0, len(seg) - nF + 1, hop)):
            ax.axvspan(s / F_S * 1000, (s + nF) / F_S * 1000, color=cmap[k % len(cmap)],
                       alpha=0.16, ymin=0.5, ymax=1.0)
        ax.set_title(f"{overlap}% overlap  ($N_H = {hop}$, $N_F = {nF}$)", fontsize=14)
        ax.set_xlabel("Time (ms)")
        ax.set_ylim(-1, 1)
        ax.set_xlim(0, t[-1])
        fig.tight_layout()
        fig.canvas.draw()
        frames.append(Image.fromarray(np.asarray(fig.canvas.buffer_rgba())).convert("RGB"))
        plt.close(fig)
    frames += [frames[-1]] * 2
    frames[0].save(str(ASSETS / "fig-nh-overlap.gif"), save_all=True,
                   append_images=frames[1:], duration=1100, loop=0)
    print("  wrote fig-nh-overlap.gif")


def main_audio():
    print("Audio:")
    trio = load_trio()
    audio_melody()
    audio_granular(trio)
    audio_time_stretch(trio)
    audio_spectral(trio)
    audio_phase_vocoder(trio)


def main_figures():
    print("Figures:")
    trio = load_trio()
    melody = pq.Audio.from_file(str(ASSETS / "audio-melody.wav"))
    melody = np.asarray(melody.samples).reshape(-1)
    fig_frame_extraction(trio)
    fig_cola()
    fig_reconstruction_cases()
    fig_granular_collage(trio)
    fig_granular_randomize()
    fig_stft_melody(melody)
    fig_leakage_windowing()
    fig_spectrogram_window(trio)
    fig_stft_diagram()
    fig_phase_ambiguity()
    print("Animations:")
    gif_nf_sweep(trio)
    gif_nh_overlap(trio)


if __name__ == "__main__":
    main_audio()
    main_figures()
