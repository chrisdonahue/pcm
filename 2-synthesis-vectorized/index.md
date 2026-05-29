---
title: "Chapter 2: Synthesis and Vectorized Computation"
---

# Synthesis and Vectorized Computation

In Chapter 1 we built the conceptual foundation of digital audio: how analog sound $x(t)$ gets sampled, quantized, and **stored on a computer as an array of numbers**. This chapter is an introduction to programming techniques that will allow you to synthesize and manipulate those arrays. We'll write our first real synthesis code, learn _vectorized computation_ in NumPy (the library that we'll use extensively for computer music programming in Python), and introduce _Pyquist_, a lightweight computer music Python library we'll use throughout the rest of the book.

## Review: digital audio is an array of numbers

To briefly recap Chapter 1, digital audio on a computer is just an array of numbers $x[n]$, together with a sample rate $f_s$. Each item in this discrete array constitutes a _sample_ from continuous sound $x(t)$:
$$x[n] = x(n / f_s),$$
so $x[0]$ is the value at $t = 0$, $x[1]$ is the value at $t = 1 / f_s$ seconds, and so on.

While digital audio is often _quantized_ as $b$-bit signed integers when stored on disk, here we will **forego quantization and work with $x[n]$ as floating-point numbers in nominal range $[-1, 1]$**. In practice, when synthesizing or manipulating samples in memory, we almost always use floating point numbers, as mixing, filtering, and synthesis are all easier in float arithmetic. Integer quantization and clipping typically only matter when we read or write files to disk.

This chapter focuses on the workflow of building such arrays in Python and packaging them into something we can listen to.

## Synthesis: making sound from math

So far, we've discussed _recording_ an existing analog signal and storing it as digital audio. Rather than measuring some real-world sound, we can alternatively _invent_ a continuous function $x(t)$ and perform _synthesis_ by having the computer create samples by evaluating $x(t)$ at integer multiples of the _sampling period_ $1 / f_s$.

Acoustic instruments are bound by the physics of vibrating strings, air columns, and membranes; the sounds they can produce occupy a tiny corner of the space of all possible waveforms. A computer has no such limitations: **any $x(t)$ you can describe in code is fair game**, whether inspired by physics or invented from scratch. Much of this book concerns how to navigate this enormously larger space of sonic possibilities.

:::{admonition} The recipe
:class: tip
1. Pick a sample rate $f_s$ and a duration $T$ in seconds.
2. Determine the total number of samples, $N = \lfloor T \cdot f_s \rfloor$.
3. For each index $n \in \{0, 1, \ldots, N-1\}$, compute $x[n] = x(n / f_s)$.
4. Hand the resulting array (plus $f_s$) to the audio system to play.
:::

:::{margin} Tight loops
Synthesis inner loops typically run at the sample rate — tens of thousands of iterations per second of audio. Efficiency matters here more than in most code.
:::

Because synthesis involves sampling the value of a function at many points in time, **loops are a ubiquitous primitive in computer music programming**. Here is an elementary example: a 440 Hz sine wave (concert A) for one second at CD-quality sample rate, written as a plain Python loop. Why a sine wave? We'll learn more about this in the next chapter!

```python
import math

f_s = 44100            # samples per second
T = 1.0                # duration in seconds
f = 440.0              # Hz, synthesis parameter
N = int(T * f_s)

samples = [0.0] * N    # sample "buffer" (memory)
for n in range(N):
    samples[n] = math.sin(2.0 * math.pi * f * (n / f_s))
```

:::{admonition} 🔊 Listen
:class: note listen
<audio controls src="./assets/audio-sine-440.wav"></audio>

A 440 Hz sine tone, one second long, at $f_s = 44{,}100$ Hz.
:::

The full runnable script (including code to write a WAV file) is in [code/synthesis.py](./code/synthesis.py).

Although this is just a `for` loop over `math.sin`, you have already done something nontrivial: used the relationship $x[n] = x(n / f_s)$ to bridge between the continuous mathematical description of a sound (a function of time) and its discrete computer representation (an array of samples).

## Vectorized computation and NumPy

The loop above works, but it has two problems. First, it is _slow_: Python's interpreter dispatches every `math.sin` call individually, and at 44,100 calls per second of audio that adds up quickly. Second, it is verbose: four lines of bookkeeping to do something that, conceptually, is just "compute the sine of these timestamps."

:::{margin} SIMD
Single Instruction, Multiple Data: a CPU instruction that applies one operation to several array elements in parallel, giving 10–100× speedups on vectorized math.
:::

Both problems are solved by _vectorized computation_: instead of writing a `for` loop that operates on one number at a time, we describe an operation on an entire _array_ at once. Under the hood, that single operation dispatches into precompiled, often [SIMD-accelerated](https://en.wikipedia.org/wiki/Single_instruction,_multiple_data) machine code, leaving Python's interpreter out of the inner loop.

In Python, _NumPy_ is the de facto standard vectorization library across many domains of scientific computing. The same 440 Hz sine in NumPy:

```python
import math
import numpy as np

# In vanilla Python as a for loop
samples = [0.0] * N    # sample buffer
for n in range(N):
    samples[n] = math.sin(2.0 * math.pi * f * (n / f_s))

# As vectorized operation in NumPy
n = np.arange(N)       # array of sample indices: 0, 1, ..., N-1
samples = np.sin(2 * np.pi * f * (n / f_s))
```

Notice the high-level difference: instead of calling `math.sin` 44,100 times, we apply `np.sin` once to the whole array of sample indices. The result is identical, but the code is shorter, the intent is clearer, and a modern CPU can churn through it many times faster. **Vectorized array operations are the working dialect of computer music in Python**, and the rest of this chapter is about becoming fluent in them.

## NumPy primer

Here we provide a basic overview of NumPy. For a more detailed tutorial, we point readers to the [official learning resources](https://numpy.org/learn/) and [the official quickstart tutorial](https://numpy.org/devdocs/user/quickstart.html).

### Creating arrays

A NumPy array (a `numpy.ndarray`) can be built from a Python list:

```python
import numpy as np

x = np.array([0.0, 0.5, 1.0, 0.5, 0.0, -0.5, -1.0, -0.5])
print(x.shape, x.dtype)   # (8,) float64
```

For audio buffers, we usually allocate by length instead, and optionally fill the initial buffer with some audio material.

```python
zeros = np.zeros(N)                    # a length-N silent buffer
noise = np.random.randn(N) * 0.01      # low amplitude white noise
```

`np.zeros(N)` is exactly silence: $x[n] = 0$ for all $n$. `np.random.randn(N) * 0.01` draws each sample independently from a standard normal distribution and scales it down by a factor of 100; the result is _white noise_ at a low amplitude.

:::{warning}
**Headphone warning.** **Never do computer music programming using headphones. You could seriously damage your ears.** Our perception of volume in relation to amplitude is a tricky relationship: just because a signal is in $[-1, 1]$ does not mean it cannot damage your ears. Random and synthesized signals are the most dangerous signals you can play through headphones while learning. A one-character typo (`0.01` → `1.0`) can turn a quiet hiss into a deafening full-scale roar. **Use external speakers at low volume during development.**
:::

:::{admonition} 🔊 Listen
:class: note listen
<audio controls src="./assets/audio-noise.wav"></audio>

Two seconds of low-amplitude white noise generated by `np.random.randn(N) * 0.01`.
:::

### Slicing arrays

If you are already familiar with Python list slicing, NumPy supports all the slicing patterns you would expect (they each return `np.ndarray`):

```python
x = np.arange(10)            # [0, 1, 2, ..., 9]
x[0]                         # 0
x[-1]                        # 9, the last element
x[2:5]                       # [2, 3, 4]
x[::2]                       # [0, 2, 4, 6, 8] - every other element
x[::-1]                      # [9, 8, 7, ..., 0] - reversed
```

For audio, slicing is how you grab a chunk of a recording. If `samples` is one second of audio at $f_s = 44{,}100$, then `samples[:22050]` is the first half-second and `samples[22050:]` is the second.

### Element-wise operations

Arithmetic on arrays is _element-wise_: every operation is applied independently to corresponding elements, with no Python-level loop in sight.

```python
x = np.array([1.0, 2.0, 3.0])
y = np.array([10.0, 20.0, 30.0])

x + y                # [11, 22, 33]
x * y                # [10, 40, 90]
x ** 2               # [1, 4, 9]
np.sqrt(x)           # [1.0, 1.414, 1.732]
```

A NumPy operation between an array and a scalar automatically _broadcasts_ the scalar across every element, i.e., it's equivalent to creating an array filled with the scalar value:

```python
x + 1                # [2, 3, 4]
0.5 * x              # [0.5, 1.0, 1.5]
```

This is exactly what happened when we wrote `2 * np.pi * f * (n / f_s)` above: all sample indices in array `n` are divided by sample rate `f_s` to convert them to times, and scalar `2 * np.pi * f` is multiplied into the entire `n / f_s` array in a single expression.

### Assignments and in-place operations

NumPy arrays can be modified after creation. You can assign to individual elements or to whole slices:

```python
samples = np.zeros(N)              # silent buffer of length N
samples[100] = 0.5                 # set a single sample
samples[:1000] = 1.0               # set the first 1000 samples to 1.0
samples[1000:2000] = np.sin(...)   # fill a slice with another array
```

NumPy also supports the compound arithmetic operators (`+=`, `-=`, `*=`, `/=`). On arrays these update the existing array **in place**, rather than allocating a new one. Compare the two ways to halve every sample of a buffer:

```python
# Out-of-place: allocates a new array; the original `samples` is unchanged
result = samples * 0.5

# In-place: updates `samples` directly, no new allocation
samples *= 0.5
```

The in-place form is usually faster and more memory-efficient, since there's no fresh array to allocate, fill, and (eventually) garbage-collect. Slice targets work too, which is handy for mixing additional material into part of an existing buffer:

```python
samples[:1000] += other            # mix `other` into the first 1000 samples in place
```

### Multi-channel arrays and stereo audio

Arrays in NumPy can be _multidimensional_. The arrays we've looked at so far are 1D _vectors_, but NumPy arrays can represent 2D _matrices_ or even higher-dimensional structures. Two helpful attributes characterize an array's layout:

- `arr.ndim`: the number of dimensions (1 for a vector, 2 for a matrix, ...).
- `arr.shape`: a tuple giving the size along each dimension.

```python
v = np.array([1.0, 2.0, 3.0])
v.ndim, v.shape                  # 1, (3,)

m = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
m.ndim, m.shape                  # 2, (3, 2)
```

Music is often rendered in _stereo_: two arrays of samples (often called _channels_), one for each ear, which allows for basic spatial effects. We represent a stereo signal as a 2D NumPy array.

:::{margin} Time-major
Channel-major is the older DSP convention, but time-major slices more naturally by time — useful for windowing and frame-based processing.
:::

There are two reasonable orderings: time-major `(num_samples, num_channels)` and channel-major `(num_channels, num_samples)`. We will adopt the time-major convention `(num_samples, num_channels)` throughout this book and in the Pyquist library below.

A small example: one second of stereo audio with a 220 Hz tone in the left channel and a 330 Hz tone in the right.

```python
f_s = 44100
N = f_s
n = np.arange(N)
t = n / f_s

left  = 0.5 * np.sin(2 * np.pi * 220 * t)   # shape (N,)
right = 0.5 * np.sin(2 * np.pi * 330 * t)   # shape (N,)

stereo = np.stack([left, right], axis=1)    # shape (N, 2)
print(stereo.shape)                         # (44100, 2)
```

`np.stack(..., axis=1)` glues two length-$N$ arrays side by side along a new axis at position 1, producing the time-major `(N, 2)` layout.

:::{figure} ./assets/fig-stereo-waveform.png
:name: fig-stereo-waveform
:width: 80%
:::

:::{admonition} 🔊 Listen
:class: note listen
<audio controls src="./assets/audio-stereo-220-330.wav"></audio>

One second of stereo audio: 220 Hz in the left channel, 330 Hz in the right channel. (Best heard with stereo speakers or, cautiously, with headphones.)
:::

Slicing a 2D array uses commas to address each axis:

```python
stereo[:, 0]             # the left channel only (1D, shape (N,))
stereo[:, 1]             # the right channel only
stereo[:1000, :]         # the first 1000 samples of both channels (2D, shape (1000, 2))
stereo[:1000]            # equivalent shorthand
```

### Broadcasting

The `np.stack` trick above works, but a more elegant pattern scales up to more channels. NumPy's [_broadcasting_](https://numpy.org/doc/stable/user/basics.broadcasting.html) rules let us combine arrays of different shapes, provided the shapes are compatible.

An example in music synthesis: let's say we wanted to synthesize stereo audio consisting of two sine waves with a different frequency in the left and right channel. To do this, we implicitly want to evaluate sine at all points in time and at two different frequencies, i.e., a nested loop. Using NumPy's broadcasting rules, we can concisely represent these types of multi-dimensional operations:

```python
# In vanilla Python as a nested loop
freqs = [220.0, 330.0]
stereo = [[0.0, 0.0]] * N
for n in range(N):
    t = n / f_s
    for c in range(2):
        stereo[n, c] = 0.5 * math.sin(2 * np.pi * freqs[c] * t)

# As vectorized / broadcasted operations in NumPy
t = np.arange(N) / f_s
freqs = np.array(freqs)
# t[:, np.newaxis] has shape (N, 1)
# freqs            has shape (2,)
# Their product broadcasts to shape (N, 2)
stereo = 0.5 * np.sin(2 * np.pi * freqs * t[:, np.newaxis])
```

`np.newaxis` adds an axis of length 1, reshaping `t` from `(N,)` to `(N, 1)`. NumPy then aligns the two shapes from the right (`(N, 1)` vs. `(2,)`), and where one shape has a `1`, it stretches (broadcasts) that array along that axis. The result has shape `(N, 2)`, identical to the `np.stack` version above.

To go from stereo back to mono, average across the channel axis:

```python
mono = stereo.mean(axis=1)        # shape (N,)
```

:::{admonition} 🔊 Listen
:class: note listen
<audio controls src="./assets/audio-mono-220-330-mix.wav"></audio>

The same stereo example, downmixed to mono by averaging the two channels. Both pitches are present in a single channel.
:::

:::{tip}
**If you didn't completely follow this, don't worry**. Mastering multidimensional operations and broadcasting rules in NumPy requires practice, and you will naturally gain experience throughout this course.
:::

## Pyquist: a thin computer music layer over NumPy

For the rest of this book we will use a small library called [`pyquist`](https://pyquist.org) that was created specifically for this book. It is _not_ a high-level computer music framework like Nyquist or Max MSP: there are no built-in instruments, effects, or sequencers. Instead, Pyquist is a thin wrapper around NumPy that gives us:

- A single `Audio` class that bundles a sample array with its sample rate.
- Convenient audio I/O: load and save WAV files, play through your speakers, plot waveforms and spectra.
- Some additional infrastructure (a musical `Score` object, other helpers) that we'll introduce later.

Everything pyquist does, you could do yourself with NumPy plus other libraries like `soundfile` plus `sounddevice`. The point of `pyquist` is to avoid continuously redefining those boilerplate pieces.

### The `Audio` object

The core of pyquist is the `Audio` class. An `Audio` bundles a `float32` array of samples (shape `(num_samples, num_channels)`) with a sample rate.

```python
import numpy as np
import pyquist as pq

f_s = 44100
N = f_s
n = np.arange(N)
samples = 0.5 * np.sin(2 * np.pi * 440 * n / f_s)    # shape (N,)

audio = pq.Audio(samples, f_s)
pq.play(audio)   # play audio out of speakers
print(audio)
# Audio(num_samples=44100, num_channels=1, sample_rate=44100)
```

A 1D input array is automatically reshaped to mono `(N, 1)`. The two key attributes are:

- `audio.samples`: the underlying NumPy array, shape `(num_samples, num_channels)`.
- `audio.sample_rate`: the sample rate in Hz.

Plus a few useful derived properties and helpers (`audio.num_samples`, `audio.num_channels`, `audio.duration`, `audio.peak_amplitude`), see the [full documentation](https://pyquist.org/api/audio.html) for details.

### Three takes on the same sine

The same one-second 440 Hz sine, in three styles:

```python
# 1. Plain Python loop (slow, verbose)
import math
samples_loop = [0.0] * N
for n in range(N):
    samples_loop[n] = 0.5 * math.sin(2 * math.pi * 440 * n / f_s)

# 2. Vectorized NumPy (fast, concise)
import numpy as np
n_arr = np.arange(N)
samples_np = 0.5 * np.sin(2 * np.pi * 440 * n_arr / f_s)

# 3. Pyquist Audio object (samples + sample rate together)
import pyquist as pq
audio = pq.Audio(samples_np, sample_rate=f_s)
audio.write("sine-440.wav")
```

All three describe the same signal, but each is a step up the abstraction ladder. The pyquist version is the one we'll use most: it carries the sample rate along with the samples, knows how to write itself to disk, and can be passed to `pq.play(audio)` or `pq.plot(audio)`.

### Mixing audio

Adding two `Audio` objects element-wise produces a new `Audio` containing their sum:

```python
sine_c = pq.Audio(0.3 * np.sin(2 * np.pi * 261.63 * n_arr / f_s), sample_rate=f_s)
sine_e = pq.Audio(0.3 * np.sin(2 * np.pi * 329.63 * n_arr / f_s), sample_rate=f_s)
sine_g = pq.Audio(0.3 * np.sin(2 * np.pi * 392.00 * n_arr / f_s), sample_rate=f_s)

chord = sine_c + sine_e + sine_g
chord.write("c-major-chord.wav")
```

:::{admonition} 🔊 Listen
:class: note listen
<audio controls src="./assets/audio-chord-major.wav"></audio>

A C major triad (C4, E4, G4) made by summing three sine waves.
:::

Pyquist validates shapes and sample rates for you: adding two `Audio` objects with different sample rates raises a clear error, instead of silently producing an unintended result.

Scalar multiplication scales the amplitude, and addition or subtraction with plain NumPy arrays also works:

```python
quieter = 0.5 * chord            # half-amplitude
inverted = -chord                # phase-inverted copy
```

### Slicing vs `segment`

You can index into an `Audio` exactly like a NumPy array. The result is itself a new `Audio` (carrying the same sample rate along), not a raw `ndarray`:

```python
audio[1000:2000]        # Audio of shape (1000, num_channels)
audio[:, 0]             # Audio of shape (N, 1) - the first channel only
audio[1000:2000, 0]     # Audio of shape (1000, 1) - first channel, samples 1000-1999
```

Pyquist rejects index patterns that would collapse the sample axis to a scalar (e.g. `audio[1000]` or `audio[1000, 0]`), since the result would no longer have the canonical `(num_samples, num_channels)` layout. If you need to read the value of a single sample, use `audio.samples[i, j]`; if you need a length-1 `Audio`, use `audio[i:i+1]`.

`segment` does the same kind of carving, but takes its arguments in _seconds_ rather than _samples_:

```python
first_half = chord.segment(duration=0.5)              # first 0.5 s
middle     = chord.segment(offset=0.25, duration=0.5) # the middle 0.5 s
```

:::{admonition} 🔊 Listen
:class: note listen
<audio controls src="./assets/audio-chord-segment.wav"></audio>

The middle 0.5 s of the C major chord above, extracted via `chord.segment(offset=0.25, duration=0.5)`.
:::

The rule of thumb: use array indexing when you want to think in sample indices, use `segment` when you want to think in seconds.

## Summary

- Digital audio is usually synthesized and manipulated in memory as an array of floats (unquantized) in nominal range $[-1, 1]$, paired with a sample rate $f_s$.
- _Synthesis_ is the inverse of recording: dream up a continuous function $x(t)$ and evaluate it at sample times $t = n / f_s$.
- _Loops_ are a ubiquitous primitive in computer music programming, because synthesis involves sampling functions at many points in time.
- _Vectorized computation_ replaces explicit Python loops with whole-array operations. It is equivalent but faster (precompiled inner loops) and more readable (one expression instead of many).
- _NumPy_ is the standard vectorization library. The core operations: array creation (`np.array`, `np.zeros`), slicing, element-wise arithmetic, multi-dimensional arrays, and broadcasting.
- Stereo audio is a 2D array of shape `(num_samples, num_channels)`. To downmix to mono, take `array.mean(axis=1)`.
- _Pyquist_ is a small wrapper around NumPy that bundles samples + sample rate into a single `Audio` object, plus I/O / playback / plotting helpers.
- Adding two `Audio` objects mixes them. Both array-style slicing (`audio[a:b]`, in samples) and `.segment(offset=, duration=)` (in seconds) return a new `Audio` with the sample rate carried along.

## Questions for the reader

:::{exercise} Loop vs vectorized
:label: ex-loop-vs-vectorized
Synthesize 5 seconds of a 440 Hz sine in two ways: once with a plain Python `for` loop calling `math.sin`, once vectorized with NumPy. Time them both with `time.perf_counter()` and report the speedup.
:::

:::{exercise} Stereo broadcasting
:label: ex-stereo-broadcasting
Using broadcasting with `np.newaxis`, synthesize a 1-second stereo signal where the left channel is a 220 Hz sine and the right is a 330 Hz sine. Then downmix to mono by averaging the channels. Listen to both stereo and mono; describe in one sentence what changes.
:::

:::{exercise} Headphone safety
:label: ex-headphone-safety
Write a small synthesis program that produces _intentionally_ unsafe output (say, a sine multiplied by 10), and **without running it through headphones**, inspect the array values (e.g. `audio.peak_amplitude`) to confirm they exceed full scale. What does `audio.write("path.wav")` do with samples outside $[-1, 1]$? (Read the docstring for `Audio.write`, or try it and inspect the output.)
:::
