---
title: "Chapter 1: Sound and Digital Audio"
---

# Sound and Digital Audio

This chapter establishes the foundation for the rest of the book. We'll first describe what sound _is_ in the physical world, then build up the standard way that computers _represent_ sound as **digital audio**. By the end, you'll synthesize your first sound from scratch with a few lines of Python, and you'll have the vocabulary to talk precisely about waveforms, sampling, quantization, frequency, and amplitude.

## What is sound, physically?

Sound is what happens when something in the world moves and disturbs the air around it. Strike a guitar string, snap your fingers, or push air past a vibrating reed, and you set the surrounding air molecules into motion. These disturbances propagate outward as alternating regions of higher and lower pressure — compressions and rarefactions — that we call **sound waves**.

A microphone, or your eardrum, sits at one fixed point in this traveling pressure field. If we measure the local air pressure at that point as a function of time, we get a one-dimensional signal: pressure goes up, pressure goes down, pressure passes through ambient atmospheric pressure on its way between the two. We call this measurement **analog sound**.

## Waveforms: sound as a continuous function

Formally, we describe an analog sound by a function

$$x(t) : [0, \infty) \to \mathbb{R},$$

mapping a real-valued time $t$ (seconds) to a real-valued pressure $x(t)$. We refer to such a function as a **waveform**, or more generally as a (continuous-time) **signal**.

<img src="./assets/fig-sine-pressure.png">

Pressure can be measured in physical units like pascals, but in computer music we usually work with a unitless, normalized representation. Once a sound is recorded through a microphone (or otherwise scaled to a known range), we refer to the measured quantity as **amplitude**, and we linearly rescale it so that the recording system's full dynamic range maps to the interval $[-1, 1]$:

<img src="./assets/fig-sine-amplitude.png">

For the rest of this book, you should imagine the vertical axis of a waveform plot as a unitless amplitude in $[-1, 1]$: $+1$ is the maximum positive deviation the system can represent, $-1$ is the maximum negative deviation, and $0$ is silence.

## Periodicity, period, and frequency

Natural and musical sounds tend to exhibit _periodic_ behavior — the waveform repeats itself, more or less, at a regular rate. A plucked guitar string, a sustained vowel, the tone of a flute: all produce signals whose shape recurs.

Formally, a continuous signal $x(t)$ is **periodic with period $t_0$** if

$$x(t + t_0) = x(t) \quad \text{for all } t \geq 0.$$

The smallest positive $t_0$ that satisfies this condition is called the **fundamental period**.

<img src="./assets/fig-period-2hz.png">

The **fundamental frequency** is the number of fundamental periods that fit in one second:

$$f_0 = \frac{1}{t_0}.$$

Frequency is measured in **hertz** (Hz), where 1 Hz means one period per second. The waveform above has $t_0 = 0.5\,\mathrm{s}$, so $f_0 = 2\,\mathrm{Hz}$. Compressing the same shape into a quarter of a second gives $f_0 = 4\,\mathrm{Hz}$:

<img src="./assets/fig-period-4hz.png">

Frequency is the property most strongly associated with what we perceive as _pitch_: higher frequencies sound higher in pitch, lower frequencies sound lower. We will have much more to say about pitch perception in later chapters.

## From analog to digital

Computers cannot store an analog signal $x(t)$ directly. The function takes real-valued inputs and produces real-valued outputs, so even a one-second clip carries an infinite amount of information. To bring sound into the digital world, we have to approximate $x(t)$ with a finite amount of data.

The plan involves three discretization steps:

1. **Sampling** in time: measure the signal at discrete, evenly spaced points.
2. **Quantizing** in amplitude: round each measurement to a value from a finite set.
3. **Encoding**: assign an integer symbol to each quantized value so that it can be stored in computer memory.

We'll take each in turn.

### Sampling

To **sample** a continuous signal means to evaluate it at a sequence of discrete time points, uniformly spaced at some interval $T_s$ (the **sampling period**). The reciprocal $f_s = 1 / T_s$ is the **sample rate**, measured in samples per second. Sample rates of 44,100 Hz and 48,000 Hz are common in practice; we will mostly use $f_s = 44{,}100$ Hz throughout this book.

We index samples by an integer $n$ and adopt the convention

$$x[n] = x(n / f_s),$$

so $x[0]$ is the signal at time $t = 0$, $x[1]$ is its value at time $t = 1 / f_s$, and so on. Continuous-time signals get parentheses ($x(t)$); discrete-time sample sequences get square brackets ($x[n]$). This distinction will matter throughout the book.

<img src="./assets/fig-sampling.png">

After sampling, an infinite continuous function has been replaced by a finite ordered sequence of real numbers. But the values $x[n]$ are still real-valued, and we still cannot store real numbers exactly.

### Quantization

To **quantize** a sample is to round its amplitude to the nearest value in a chosen finite set $V \subseteq [-1, 1]$. The simplest choice is a uniformly spaced grid such as $V = \{-1, -0.5, 0, 0.5, 1\}$. Each sample $x[n]$ is replaced by

$$\hat{x}[n] = \arg\min_{v \in V} |x[n] - v|.$$

<img src="./assets/fig-quantization.png">

Quantization introduces a small error — the difference $\hat{x}[n] - x[n]$, called **quantization noise** — but in exchange we get a sequence of values drawn from a finite alphabet, which a computer _can_ store.

### Encoding and bit depth

A finite set $V$ of size $|V|$ can be represented exactly by integer **symbols**, e.g., $\{0, 1, \ldots, |V| - 1\}$, or by signed integers in some symmetric range. Each symbol can be stored using a fixed number of bits:

$$b = \lceil \log_2 |V| \rceil.$$

This $b$ is called the **bit depth** of the digital audio. A small example: $|V| = 7$ requires $b = 3$ bits per sample. CD-quality audio uses $b = 16$ bits, allowing for $2^{16} = 65{,}536$ distinct amplitude levels.

Knowing the sample rate $f_s$ and the bit depth $b$ lets us compute the **bitrate** of uncompressed digital audio:

$$\text{bitrate} = f_s \cdot b \quad (\text{bits per second}).$$

A monaural CD-quality stream (44,100 Hz, 16-bit) is therefore $44{,}100 \times 16 = 705{,}600$ bits per second, or about 88 KB/s. Stereo doubles this.

### Storage as integer arrays

Put together, a digital audio signal is, in essence, an array of integers along with a sample rate. For example, at $b = 3$ bits per sample, the symbol sequence $[0, 2, 0, -2, 0, 2, 0, -2, 0]$ encodes the amplitude sequence $[0.0, 1.0, 0.0, -1.0, 0.0, 1.0, 0.0, -1.0, 0.0]$, which (interpreted at some sample rate) is a short fragment of a square-like wave.

Why integers instead of floats? Two reasons:

1. **Storage**. Integers can be packed at exactly $b$ bits per sample, with no waste.
2. **Hardware**. Digital-to-analog converters operate on integer codes directly, so integer sample arrays are the natural lingua franca between software, file formats, and audio hardware.

In practice, when you read or write a WAV file at 16-bit depth, the file stores signed integers in $[-32{,}768, 32{,}767]$. Audio libraries typically convert these to floating-point values in $[-1, 1]$ for you on the way in, and back to integers on the way out.

## Digital-to-analog conversion

To actually _hear_ digital audio, the discrete sample sequence has to be converted back into a continuous voltage that can drive a loudspeaker. This is the job of a **digital-to-analog converter** (**DAC**), a piece of hardware in every phone, laptop, and audio interface.

A DAC takes the integer samples, produces a piecewise-constant ("staircase") voltage signal, and then applies a **reconstruction filter** that smooths the staircase back into a continuous waveform. The whole pipeline looks like:

```
analog → [ ADC ] → samples → [ DAC ] → staircase → [ filter ] → analog
```

The big idea is that, under conditions we will formalize in a later chapter, this reconstruction can be made arbitrarily close to the original analog signal $x(t)$ — provided $f_s$ is high enough and $b$ is large enough. For now, trust that the DAC is doing the right thing, and focus on producing nice integer arrays for it to play.

## Synthesis: making sound from math

So far, we've discussed _recording_ an existing analog signal and storing it as digital audio. But we can also go the other direction. Rather than measuring some real-world sound, we can _invent_ a continuous function $x(t)$ and have the computer evaluate it at sample times. This is called **synthesis**.

The recipe is simple:

1. Pick a sample rate $f_s$ and a duration $T$ in seconds.
2. Decide the total number of samples, $N = \lfloor f_s \cdot T \rfloor$.
3. For each index $i \in \{0, 1, \ldots, N-1\}$, compute $x[i] = x(i / f_s)$.
4. Hand the resulting array (plus $f_s$) to the audio system to play.

Here is the simplest interesting example: a 440 Hz sine wave (concert A) for one second at CD-quality sample rate.

```python
import math

f_s = 44100         # samples per second
duration = 1.0      # seconds
f = 440.0           # Hz
N = int(duration * f_s)

samples = [0.0] * N
for i in range(N):
    t = i / f_s
    samples[i] = math.sin(2.0 * math.pi * f * t)
```

<audio src="./assets/audio-sine-440.wav">A 440 Hz sine tone, one second long, at $f_s = 44{,}100$ Hz.</audio>

The full runnable script — including code to write a WAV file — is in [code/synthesis.py](./code/synthesis.py).

Although this is just a `for` loop over `math.sin`, you have already done something nontrivial: used the relationship $x[i] = x(i / f_s)$ to bridge between the continuous mathematical description of a sound (a function of time) and its discrete computer representation (an array of samples). Most synthesis algorithms in this book are variations on this theme.

## Clipping

One last practical concern. Every DAC has a finite output range. When you hand it samples whose absolute values exceed $1$, it will simply **clip** them:

$$y[n] = \max(-1, \min(x[n], 1)).$$

<img src="./assets/fig-clipping.png">

Hard clipping is a nonlinear distortion: it introduces a harsh, raspy character into the sound, and at high amplitudes can damage speakers as well as ears. For example, multiplying a 440 Hz sine by 2 saturates the DAC and produces a signal that's close to a square wave:

<audio src="./assets/audio-clipped-sine.wav">A 440 Hz sine multiplied by 2, then clipped to $[-1, 1]$, then attenuated. Same fundamental frequency as the clean sine above, but with the harsh timbre of hard clipping.</audio>

A simple defensive habit while developing synthesis code is to **normalize** your output to lie within $[-1, 1]$ before sending it to the DAC, e.g.,

$$y[n] = \frac{x[n]}{\max_{j \in \{0, \ldots, N-1\}} |x[j]|}.$$

> **A safety note.** When experimenting with synthesis code, **do not wear headphones** until you know the output is bounded. It is very easy to write a one-line bug that produces a much louder sound than you intended, and a sudden loud signal directly against your eardrums can cause real damage. Listen through external speakers at low volume while you debug, then put headphones on once the output is well-behaved.

## Summary

- Physical sound is a traveling pattern of air-pressure variation. Analog sound is a continuous signal $x(t) : [0, \infty) \to \mathbb{R}$ describing the pressure measured at a single point.
- Amplitude is, by convention, a unitless quantity in $[-1, 1]$.
- Periodicity is captured by the **fundamental period** $t_0$ and the **fundamental frequency** $f_0 = 1 / t_0$, measured in hertz.
- Converting analog to digital requires **sampling** (in time, at rate $f_s$), **quantizing** (in amplitude, to a finite set), and **encoding** (as integer symbols of bit depth $b$).
- The discrete representation $x[n] = x(n / f_s)$ is what computers actually manipulate; we use parentheses for continuous time and square brackets for sample indices.
- A DAC reconstructs an analog signal by smoothing the discrete samples. Under conditions we will study later, this reconstruction can be made arbitrarily close to the original.
- **Synthesis** turns this pipeline around: we _define_ a function $x(t)$ in code and evaluate it at sample times to produce digital audio.
- Be wary of values outside $[-1, 1]$, which will clip — and keep headphones off until your output is bounded.

## Questions for the reader

1. **Period and frequency.** A waveform has a fundamental period of $t_0 = 2.27\,\mathrm{ms}$. What is its fundamental frequency in Hz? Roughly how many full periods occur in 1 second of audio at $f_s = 44{,}100$ Hz?
2. **Bit depth arithmetic.** You are designing a recording format that uses 24 bits per sample at a sample rate of 48,000 Hz. What is the uncompressed bitrate (bits per second) for a single channel? How many discrete amplitude levels can each sample distinguish?
3. **Sample count.** Write a one-line Python expression that computes the number of samples needed to store $T$ seconds of audio at sample rate $f_s$. Be explicit about how you handle a non-integer product of $T$ and $f_s$.
4. **Synthesis.** Modify the 440 Hz sine wave example to produce a 1-second tone at 220 Hz, then another at 880 Hz. Listen to all three. What relationship do you hear between consecutive pairs, and how does it correspond to the relationship between their frequencies?
5. **Clipping by hand.** Suppose $x[n] = 1.5 \cdot \sin(2 \pi \cdot 440 \cdot n / f_s)$ at $f_s = 44{,}100$ Hz. Sketch (or plot in code) what the clipped output looks like over one fundamental period. Why does this signal not sound like a clean sine?
6. **Quantization noise.** Quantize the sine $x(t) = \sin(2\pi \cdot 440 \cdot t)$ to a 2-bit representation (i.e., 4 amplitude levels) at $f_s = 44{,}100$ Hz, write it to a WAV file, and listen. Describe in words how it differs from the un-quantized version.
7. **Open.** Pick a recording you enjoy and listen for anything you can _hear_ that points to specific decisions about sample rate, bit depth, channels, or other digital-audio parameters. There is no wrong answer — the goal is to start associating engineering choices with sonic outcomes.

## Musical examples

A few recordings that engage explicitly with the digital-audio concepts in this chapter:

- Alvin Lucier — _I Am Sitting in a Room_ (an analog-domain example of repeated recording — useful as a contrast to faithful digital reproduction)
- Yasunao Tone — _Solo for Wounded CD_ (deliberate exploitation of clipping, error-correction failure, and bit-level glitches in CD playback)
- Aphex Twin — _Bucephalus Bouncing Ball_ (extreme dynamic range and an aggressive engagement with clipping)
- Ryoji Ikeda — _+/-_ (single-frequency sine tones, square waves, and very specific bit-depth and sample-rate choices)
- Daft Punk — _Around the World_ (heavy use of low bit depth and bit-crushing effects on the synthesized lead)
