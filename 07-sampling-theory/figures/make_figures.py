"""Generate figures and sound examples for Chapter 7 (sampling theory).

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
BLUE, ORANGE, GREEN, RED, PURPLE = COLORS[0], COLORS[1], COLORS[2], COLORS[3], COLORS[4]


def save_fig(name: str) -> None:
    plt.tight_layout()
    plt.savefig(ASSETS / name, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  wrote {name}")


def write_audio(samples: np.ndarray, name: str, sr: int = F_S) -> None:
    audio = pq.Audio(samples.astype(np.float32), sr)
    audio.normalize(peak_dbfs=PEAK_DBFS)
    audio.write(str(ASSETS / name))
    print(f"  wrote {name}")


def stem(ax, xs, ys, color, ms=7, lw=2.0):
    ml, sl, bl = ax.stem(xs, ys)
    plt.setp(ml, color=color, markersize=ms)
    plt.setp(sl, color=color, linewidth=lw)
    plt.setp(bl, color="0.7", linewidth=1.0)


def alias_freq(f: np.ndarray, f_s: float) -> np.ndarray:
    """The apparent (aliased) frequency after sampling f at rate f_s."""
    m = np.mod(f, f_s)
    return np.minimum(m, f_s - m)


def phase_osc(freq: np.ndarray, f_s: float) -> np.ndarray:
    """Time-varying oscillator via phase accumulation (from Chapter 6)."""
    return np.sin(np.cumsum(2 * np.pi * freq / f_s))


# ---------------------------------------------------------------------------
# 1. Sampling as multiplication, in both domains (2 rows x 3 cols)
# ---------------------------------------------------------------------------


# Running example: x(t) = sin(2 pi 1 t) + sin(2 pi 2 t), sampled at f_s = 10 Hz.
_SAMP_FS = 10.0
_SAMP_DUR = 2.0
SHA = r"\mathrm{Ш}"  # the Dirac comb, at text height (not the tall \coprod)


def _draw_time_row(row) -> None:
    t = np.linspace(0, _SAMP_DUR, 2000)
    x = np.sin(2 * np.pi * 1 * t) + np.sin(2 * np.pi * 2 * t)
    n = np.arange(0, int(_SAMP_DUR * _SAMP_FS) + 1)
    ts, xs = n / _SAMP_FS, np.sin(2 * np.pi * 1 * (n / _SAMP_FS)) + np.sin(2 * np.pi * 2 * (n / _SAMP_FS))

    row[0].plot(t, x, color=ORANGE)
    row[0].set_title(r"$x(t) = \sin(2\pi\, t) + \sin(2\pi\, 2t)$", fontsize=14)
    row[0].set_ylabel("Amplitude")

    ml, sl, bl = row[1].stem(ts, np.ones_like(ts))
    plt.setp(ml, color=RED, markersize=5)
    plt.setp(sl, color=RED, linewidth=1.5)
    plt.setp(bl, visible=False)
    row[1].set_title(rf"${SHA}_{{f_s}}(t)$  (impulse train)", fontsize=15)

    row[2].plot(t, x, color=ORANGE, alpha=0.3, linestyle="--")
    row[2].plot(ts, xs, "o", color=GREEN, markersize=6)
    row[2].set_title(rf"$x_{{f_s}}(t) = x(t)\cdot {SHA}_{{f_s}}(t)$", fontsize=14)
    for ax in row:
        ax.set_xlabel("Time (s)")
        ax.set_xlim(0, _SAMP_DUR)


def _draw_freq_row(row) -> None:
    # All spectral lines drawn at unit amplitude for clarity.
    stem(row[0], [-2, -1, 1, 2], [1.0] * 4, ORANGE)
    row[0].set_title(r"$|X(\omega)|$", fontsize=15)
    row[0].set_ylabel("Amplitude")

    ks = np.arange(-3, 4)
    stem(row[1], ks * _SAMP_FS, np.ones_like(ks, dtype=float), RED)
    row[1].set_title(rf"$|{SHA}_{{f_s}}(\omega)|$", fontsize=15)

    copies = [k * _SAMP_FS + base for k in ks for base in (-2, -1, 1, 2)]
    stem(row[2], copies, [1.0] * len(copies), GREEN)
    row[2].set_title(r"$|X_{f_s}(\omega)|$  (copies at $k f_s$)", fontsize=14)
    for ax in row:
        ax.set_xlabel("Frequency (Hz)")
        ax.set_xlim(-27, 27)
        ax.set_ylim(0, 1.25)


def fig_sampling_time() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14, 3.2))
    _draw_time_row(axes)
    save_fig("fig-sampling-time.png")


def fig_sampling_domains() -> None:
    fig, axes = plt.subplots(2, 3, figsize=(14, 6))
    _draw_time_row(axes[0])
    _draw_freq_row(axes[1])
    save_fig("fig-sampling-domains.png")


# ---------------------------------------------------------------------------
# 2. Aliasing: many continuous sinusoids, identical samples
# ---------------------------------------------------------------------------


def fig_aliasing_sines() -> None:
    f_s = 1.0
    t = np.linspace(0, 4, 2000)
    fig, ax = plt.subplots(figsize=(12, 4))
    for f, c in [(1, BLUE), (2, ORANGE), (4, GREEN)]:
        ax.plot(t, np.sin(2 * np.pi * f * t), color=c, linewidth=1.8,
                label=f"$\\sin(2\\pi \\cdot {f}\\, t)$", alpha=0.85)
    ns = np.arange(0, 5)
    for x0 in ns / f_s:
        ax.axvline(x0, color="0.6", linestyle="--", linewidth=1.0, zorder=1)
    ax.plot(ns / f_s, np.zeros_like(ns), "o", color="black", markersize=10,
            zorder=5, label=f"samples ($f_s = 1$ Hz)")
    ax.axhline(0, color="0.7", linewidth=0.8)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    ax.set_xlim(0, 4)
    ax.set_ylim(-1.2, 1.2)
    ax.legend(loc="upper right", fontsize=11, ncol=2)
    save_fig("fig-aliasing-sines.png")


# ---------------------------------------------------------------------------
# 3. Nyquist bandwidth: properly sampled vs. undersampled (overlap)
# ---------------------------------------------------------------------------


def _baseband(ax, center, f_max, color, alpha):
    # A richer, irregular spectral shape (several uneven lobes), like a real
    # bandlimited spectrum rather than a smooth bump.
    xs = np.linspace(center - f_max, center + f_max, 300)
    u = (xs - center) / f_max  # in [-1, 1]
    env = np.cos(np.pi * u / 2) ** 2  # tapers to zero at the band edges
    wiggle = (1.0 + 0.5 * np.cos(2 * np.pi * 2.5 * u)
              + 0.3 * np.cos(2 * np.pi * 4.0 * u + 1.0)
              + 0.2 * np.sin(2 * np.pi * 6.0 * u))
    shape = env * np.clip(wiggle, 0.05, None)
    shape = 0.9 * shape / shape.max()
    ax.fill_between(xs, 0, shape, color=color, alpha=alpha, linewidth=0)
    ax.plot(xs, shape, color=color, linewidth=1.3, alpha=min(1, alpha + 0.3))


def _fs_lines(ax, f_s, f_max):
    for xline, lab, col in [(-f_s, r"$-f_s$", RED), (f_s, r"$f_s$", RED),
                            (-f_max, r"$-f_{\max}$", BLUE), (f_max, r"$f_{\max}$", BLUE)]:
        ax.axvline(xline, color=col, linewidth=1.3, alpha=0.7)
        ax.annotate(lab, xy=(xline, 1.02), ha="center", fontsize=12, color=col)


def fig_nyquist_bandwidth() -> None:
    f_max = 1.0
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6))

    # properly sampled: f_s = 3 > 2 f_max, copies clear of baseband
    f_s = 3.0
    for k in range(-2, 3):
        _baseband(ax1, k * f_s, f_max, BLUE if k == 0 else PURPLE, 0.55 if k == 0 else 0.25)
    _fs_lines(ax1, f_s, f_max)
    ax1.text(0.5, 0.98, r"$f_s > 2 f_{\max}$: copies stay separate", transform=ax1.transAxes,
             ha="center", va="top", fontsize=13, color="0.3")

    # undersampled: f_s = 1.5 < 2 f_max, copies overlap baseband
    f_s = 1.5
    for k in range(-3, 4):
        _baseband(ax2, k * f_s, f_max, BLUE if k == 0 else PURPLE, 0.55 if k == 0 else 0.28)
    _fs_lines(ax2, f_s, f_max)
    ax2.text(0.5, 0.98, r"$f_s < 2 f_{\max}$: copies overlap", transform=ax2.transAxes,
             ha="center", va="top", fontsize=13, color=RED)

    for ax in (ax1, ax2):
        ax.axhline(0, color="0.6", linewidth=1.0)
        ax.set_ylim(0, 1.35)
        ax.set_yticks([])
        ax.set_xlim(-5, 5)
    ax2.set_xlabel("Frequency (Hz)")
    save_fig("fig-nyquist-bandwidth.png")


# ---------------------------------------------------------------------------
# 4. Aliasing in practice: a pitch sweep at three sample rates
# ---------------------------------------------------------------------------

# Frequency control points (time_s, Hz), linearly interpolated in frequency.
FREQ_PWL = [(0.0, 220.0), (1.0, 220.0), (6.0, 880.0),
            (7.0, 880.0), (12.0, 220.0), (13.0, 220.0)]


def sweep_freq(t: np.ndarray) -> np.ndarray:
    times = [p[0] for p in FREQ_PWL]
    freqs = [p[1] for p in FREQ_PWL]
    return np.interp(t, times, freqs)


def fig_aliasing_practice() -> None:
    dur = FREQ_PWL[-1][0]
    panels = [(2000, ""), (1000, "  (foldover)"), (500, "  (aliasing)")]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharex=True)
    for ax, (f_s, tag) in zip(axes, panels):
        t = np.linspace(0, dur, 1500)
        f = sweep_freq(t)
        ax.plot(t, f, color=BLUE, label="true frequency")
        ax.plot(t, alias_freq(f, f_s), color=ORANGE, linestyle="--", label="heard (aliased)")
        ax.axhline(f_s / 2, color=RED, linewidth=1.3, label="Nyquist $f_s/2$")
        ax.set_title(f"$f_s = {f_s}$ Hz{tag}", fontsize=14)
        ax.set_xlabel("Time (s)")
        ax.set_ylim(0, 1000)
    axes[0].set_ylabel("Frequency (Hz)")
    axes[0].legend(fontsize=10, loc="upper right")
    save_fig("fig-aliasing-practice.png")


# ---------------------------------------------------------------------------
# 5. Quantization: staircase and noise at low bit depths
# ---------------------------------------------------------------------------


def quantize(x: np.ndarray, b: int) -> np.ndarray:
    levels = 2 ** (b - 1) - 1
    return np.round(x * levels) / levels


def fig_quantization() -> None:
    t = np.linspace(0, 1, 800)
    x = 0.9 * np.sin(2 * np.pi * 2 * t)
    fig, axes = plt.subplots(1, 2, figsize=(13, 4), sharey=True)
    for ax, b in zip(axes, (2, 4)):
        xq = quantize(x, b)
        ax.plot(t, x, color=BLUE, alpha=0.5, label="original")
        ax.plot(t, xq, color=RED, drawstyle="steps-mid", linewidth=1.5,
                label=f"quantized ($b={b}$)")
        for lvl in np.arange(-(2**(b-1) - 1), 2**(b-1)) / (2**(b-1) - 1):
            ax.axhline(lvl, color="0.85", linewidth=0.8, zorder=0)
        ax.set_title(f"$b = {b}$ bits ($2^{b} = {2**b}$ levels)", fontsize=14)
        ax.set_xlabel("Time (s)")
        ax.legend(fontsize=10, loc="upper right")
    axes[0].set_ylabel("Amplitude")
    save_fig("fig-quantization.png")


# ---------------------------------------------------------------------------
# 6. Anti-aliasing filter before sampling
# ---------------------------------------------------------------------------


def fig_antialiasing() -> None:
    f = np.linspace(0, 40, 1000)
    # a spectrum with content extending past 20 kHz
    spec = np.exp(-f / 12) * (1 + 0.3 * np.sin(2 * np.pi * f / 5) ** 2)
    spec = spec / spec.max()
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.fill_between(f, 0, spec, color=BLUE, alpha=0.3)
    ax.plot(f, spec, color=BLUE, label="signal spectrum")
    # ideal filter response
    cutoff = 20.0
    ax.plot([0, cutoff, cutoff, 40], [1.05, 1.05, 0, 0], color=RED, linewidth=2.0,
            label="anti-aliasing filter")
    ax.fill_between(f[f > cutoff], 0, spec[f > cutoff], color=RED, alpha=0.25,
                    hatch="//", label="removed before sampling")
    ax.axvline(cutoff, color=RED, linestyle=":", linewidth=1.5)
    ax.annotate("20 kHz", xy=(cutoff, 1.08), ha="center", fontsize=12, color=RED)
    ax.set_xlabel("Frequency (kHz)")
    ax.set_ylabel("Amplitude")
    ax.set_xlim(0, 40)
    ax.set_ylim(0, 1.2)
    ax.legend(fontsize=11)
    save_fig("fig-antialiasing.png")


# ---------------------------------------------------------------------------
# 7. Resampling by interpolation
# ---------------------------------------------------------------------------


def fig_resampling() -> None:
    f0 = 1.2
    n1 = np.arange(0, 9)
    fs1 = 8.0
    x1 = np.sin(2 * np.pi * f0 * n1 / fs1)
    fs2 = 12.0
    n2 = np.arange(0, int(len(n1) * fs2 / fs1))
    p = n2 * fs1 / fs2
    lo = np.floor(p).astype(int)
    alpha = p - lo
    hi = np.minimum(lo + 1, len(x1) - 1)
    y = (1 - alpha) * x1[lo] + alpha * x1[hi]

    fig, ax = plt.subplots(figsize=(12, 4))
    tt = np.linspace(0, (len(n1) - 1) / fs1, 500)
    ax.plot(tt, np.sin(2 * np.pi * f0 * tt), color="0.8", linewidth=1.2,
            label="underlying signal")
    stem(ax, n1 / fs1, x1, BLUE)
    ax.plot(n1 / fs1, x1, "o", color=BLUE, markersize=9, label="original ($f_s^1 = 8$ Hz)")
    ax.plot(n2 / fs2, y, "x", color=RED, markersize=9, markeredgewidth=2.5,
            label="resampled ($f_s^2 = 12$ Hz)")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    ax.legend(fontsize=11, loc="upper right")
    save_fig("fig-resampling.png")


# ---------------------------------------------------------------------------
# 7b. Strobe-dance GIF: the wagon-wheel effect, using the raw 1 Hz dance clip
# ---------------------------------------------------------------------------


def fig_strobe_dance() -> None:
    from matplotlib.patches import Rectangle
    from PIL import Image, ImageSequence

    raw = HERE.parent / "raw" / "1hzdance.gif"
    if not raw.exists():
        print("  (skip fig-strobe-dance.gif: raw/1hzdance.gif missing)")
        return

    # One 1 Hz cycle = 16 frames, treated as exactly 16 fps.
    src = Image.open(str(raw))
    dance = []
    for fr in ImageSequence.Iterator(src):
        rgba = fr.convert("RGBA")
        bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        dance.append(np.asarray(Image.alpha_composite(bg, rgba).convert("RGB")))
    NF = len(dance)

    # (title, subtitle, sample period in frames; None = continuous original)
    panels = [(r"$x(t)$", r"$f_{\max} = 1$ Hz", None),
              (r"$f_s = 4$ Hz", "oversampled", 4),
              (r"$f_s = 2$ Hz", "critically sampled", 8),
              (r"$f_s = \frac{4}{3}$ Hz", "foldover", 12),
              (r"$f_s = 1$ Hz", "aliased to 0 Hz", 16)]

    FPS, N_OUT = 16, 48  # LCM(16, 4, 8, 12) = 48 frames -> seamless 3 s loop
    frames = []
    for i in range(N_OUT):
        fig, axes = plt.subplots(1, len(panels), figsize=(13, 3.6), dpi=95)
        for ax, (title, sub, sp) in zip(axes, panels):
            fidx = (i % NF) if sp is None else ((i // sp) * sp) % NF
            ax.imshow(dance[fidx])
            ax.set_title(f"{title}\n{sub}", fontsize=12)
            ax.axis("off")
            # Flash a 2px black outline on the frame a sampled panel refreshes,
            # to convey the "snapshot" being taken at that sampling instant.
            if sp is not None and i % sp == 0:
                h, w = dance[fidx].shape[:2]
                ax.add_patch(Rectangle((-0.5, -0.5), w, h, fill=False,
                                       edgecolor="black", linewidth=2, clip_on=False))
        fig.text(0.06, 0.95, f"$t = {i / FPS:4.2f}$ s", ha="left", fontsize=15, fontweight="bold")
        fig.subplots_adjust(left=0.01, right=0.99, top=0.72, bottom=0.01, wspace=0.06)
        fig.canvas.draw()
        rgba = np.asarray(fig.canvas.buffer_rgba())  # (h, w, 4), physical pixels
        img = Image.fromarray(rgba, "RGBA").convert("RGB")
        # buffer_rgba() is at the physical (retina) resolution; downscale to a
        # fixed target width to keep the GIF small.
        tw = 960
        img = img.resize((tw, round(img.height * tw / img.width)), Image.LANCZOS)
        frames.append(img)
        plt.close(fig)

    # 16 fps ideal is 62.5 ms/frame; GIF stores centiseconds and rounds to 60 ms
    # (16.667 fps), a deliberate approximation for presentational clarity.
    # Quantize every frame to ONE shared palette with no transparency, so each
    # frame is a full opaque image. (Letting save() auto-convert introduces a
    # transparent index that, without disposal, makes frames ghost together.)
    pal = frames[0].convert("P", palette=Image.ADAPTIVE, colors=255)
    frames_p = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    frames_p[0].save(str(ASSETS / "fig-strobe-dance.gif"), save_all=True,
                     append_images=frames_p[1:], duration=1000.0 / FPS, loop=0,
                     disposal=1, optimize=False)
    print("  wrote fig-strobe-dance.gif")


# ---------------------------------------------------------------------------
# 8. Analog-to-digital and digital-to-analog conversion pipelines
# ---------------------------------------------------------------------------


def _pipeline_arrows(fig, axes):
    fig.canvas.draw()  # finalize positions before measuring
    for a, b in zip(axes[:-1], axes[1:]):
        x = (a.get_position().x1 + b.get_position().x0) / 2
        fig.text(x, 0.5, r"$\rightarrow$", ha="center", va="center",
                 fontsize=26, color="0.4")


def _wave(ax):
    t = np.linspace(0, _SAMP_DUR, 1000)
    ax.plot(t, np.sin(2 * np.pi * t) + np.sin(2 * np.pi * 2 * t), color=ORANGE)
    ax.set_xticks([]); ax.set_yticks([])


def _samples(ax):
    t = np.linspace(0, _SAMP_DUR, 1000)
    n = np.arange(0, int(_SAMP_DUR * _SAMP_FS) + 1)
    ts = n / _SAMP_FS
    ax.plot(t, np.sin(2 * np.pi * t) + np.sin(2 * np.pi * 2 * t), color=ORANGE, alpha=0.3, ls="--")
    ax.plot(ts, np.sin(2 * np.pi * ts) + np.sin(2 * np.pi * 2 * ts), "o", color=GREEN, ms=5)
    ax.set_xticks([]); ax.set_yticks([])


def _copies(ax, highlight=False):
    ks = np.arange(-3, 4)
    copies = [k * _SAMP_FS + base for k in ks for base in (-2, -1, 1, 2)]
    stem(ax, copies, [1.0] * len(copies), GREEN, ms=4)
    if highlight:
        ax.axvspan(-3, 3, color=RED, alpha=0.12)
        ax.plot([-3, -3, 3, 3], [0, 1.15, 1.15, 0], color=RED, lw=2.0)
    ax.set_xlim(-27, 27); ax.set_ylim(0, 1.3); ax.set_xticks([]); ax.set_yticks([])


def _baseband_only(ax):
    stem(ax, [-2, -1, 1, 2], [1.0] * 4, GREEN, ms=5)
    ax.set_xlim(-27, 27); ax.set_ylim(0, 1.3); ax.set_xticks([]); ax.set_yticks([])


def fig_adc() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(13, 2.8))
    fig.subplots_adjust(wspace=0.35)
    _wave(axes[0]); axes[0].set_title(r"sound  $x(t)$", fontsize=14)
    _samples(axes[1]); axes[1].set_title(r"samples  $x_{f_s}(t)$", fontsize=14)
    _copies(axes[2]); axes[2].set_title(r"spectrum  $X_{f_s}(\omega)$", fontsize=14)
    _pipeline_arrows(fig, axes)
    save_fig("fig-adc.png")


def fig_dac() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(13, 2.8))
    fig.subplots_adjust(wspace=0.35)
    _copies(axes[0], highlight=True)
    axes[0].set_title(r"spectrum  $X_{f_s}(\omega)$", fontsize=14)
    _baseband_only(axes[1]); axes[1].set_title(r"isolate  $X(\omega)$  (filter)", fontsize=14)
    _wave(axes[2]); axes[2].set_title(r"sound  $x(t)$", fontsize=14)
    _pipeline_arrows(fig, axes)
    save_fig("fig-dac.png")


# ---------------------------------------------------------------------------
# Audio examples
# ---------------------------------------------------------------------------


def make_audio() -> None:
    # Aliasing sonification: synthesize the pitch sweep at low f_s, then
    # resample to F_S for playback (the aliasing is baked in at synthesis).
    dur = FREQ_PWL[-1][0]
    for f_s in (2000, 1000, 500):
        n = np.arange(int(dur * f_s))
        f = sweep_freq(n / f_s)
        x = phase_osc(f, f_s)
        audio = pq.Audio(x.astype(np.float32), f_s).resample(F_S)
        write_audio(np.asarray(audio.samples).reshape(-1), f"audio-alias-{f_s}.wav")

    # Decibel demo: the same 440 Hz sine at a ladder of dBFS levels. Written
    # WITHOUT the usual -6 dBFS normalization so the levels are exact.
    t = np.arange(int(2.0 * F_S)) / F_S
    tone = np.sin(2 * np.pi * 440 * t)
    fade = np.ones_like(tone)
    k = int(0.01 * F_S)
    ramp = 0.5 * (1 - np.cos(np.linspace(0, np.pi, k)))
    fade[:k] = ramp
    fade[-k:] = ramp[::-1]
    tone *= fade
    for db in (-6, -26, -46, -66, -86):
        amp = float(pq.helper.db_to_amplitude(db))
        out = pq.Audio((tone * amp).astype(np.float32), F_S)
        out.write(str(ASSETS / f"audio-db-{abs(db)}.wav"))
        print(f"  wrote audio-db-{abs(db)}.wav")


def main() -> None:
    print("Figures:")
    fig_sampling_time()
    fig_sampling_domains()
    fig_adc()
    fig_dac()
    fig_aliasing_sines()
    fig_nyquist_bandwidth()
    fig_aliasing_practice()
    fig_quantization()
    fig_antialiasing()
    fig_resampling()
    fig_strobe_dance()
    print("Audio:")
    make_audio()


if __name__ == "__main__":
    main()
