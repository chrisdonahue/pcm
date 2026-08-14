---
title: "Chapter 10: Frame-based Processing"
---

# Frame-based Processing

So far we have studied two extremes of how a computer handles time. When we studied {ref}`sampling <sec-sampling-and-frequency>` in [Chapter 7](../07-sampling-theory), we saw that music audio is usually sampled at more than $40{,}000$ times per second, fast enough to capture the highest frequencies we can hear. When we studied the {ref}`Fourier transform <sec-fourier-transform>` in [Chapter 5](../05-frequency-domain) and its practical cousin the {ref}`DFT <def-dft>` in [Chapter 8](../08-dft), we did the opposite: we integrated across _all_ of time to produce a single summary of a sound's frequency content, in effect measuring it just once no matter how long it was (a "rate" of $0$ measurements per second).

Most phenomena in music live _between_ these two extremes. The attack of a plucked string lasts about a hundredth of a second, a four-on-the-floor kick drum at 120 BPM lands twice a second, a pianist rattling off Bach's Prelude in C plays around five notes a second, and the [world's fastest drummer](https://en.wikipedia.org/wiki/World%27s_Fastest_Drummer) can manage twenty strokes a second. None of these needs the microsecond precision of individual samples, but all of them are invisible to a single all-of-time Fourier transform.

:::{list-table} The rate at which things happen in music, from a single Fourier measurement to individual samples. The musically interesting middle (blue) is what this chapter is about.
:header-rows: 1
:name: tbl-rates

* - Phenomenon
  - Interval
  - Rate
* - Fourier transform (whole recording)
  - $\red{\infty}$
  - $\red{0}$ Hz
* - Kick drum at 120 BPM
  - $\blue{500}$ ms
  - $\blue{2}$ Hz
* - Melody (Bach, ~5 notes/sec)
  - $\blue{200}$ ms
  - $\blue{5}$ Hz
* - World's fastest drummer
  - $\blue{50}$ ms
  - $\blue{20}$ Hz
* - Instrument attack
  - $\blue{10}$ ms
  - $\blue{100}$ Hz
* - Audio samples
  - $\red{0.023}$ ms
  - $\red{44{,}100}$ Hz
:::

**How do we process phenomena that happen at these intermediate, musically intuitive rates, say tens to hundreds of times per second?** The answer is {vocab}`frame-based processing`, a family of techniques that aggregate audio samples into chunks called {vocab}`frames` and then manipulate those frames. It is the foundation for granular synthesis, the spectrogram, time stretching, and much of the audio software you use every day. Throughout the chapter we will use a recording of a jazz trio as a running example:

:::{audio}
[A jazz trio (our running example)](./assets/audio-trio.wav)

Eight seconds of a jazz trio, which we will slice, scramble, stretch, and analyze throughout this chapter. [725677](https://freesound.org/s/725677/) by draganov89, License: [Attribution NonCommercial 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
:::

## Extracting frames

We begin with the most basic operation: chopping a signal into frames. To extract frames of {vocab}`frame length` $N_F$ from a signal $x$, we define the $k$-th frame $x_k$ as

$$x_k[n] = \begin{cases} x[k \cdot N_H + n] & \text{for } n \in \{0, 1, \ldots, N_F - 1\}, \\ 0 & \text{otherwise,}\end{cases}$$

where $N_H$ is the {vocab}`hop length`, the spacing in samples between the start of one frame and the start of the next. That is all there is to it: we slide a window of $N_F$ samples along the signal in steps of $N_H$ samples, and each stop is a frame.

If the signal is sampled at $f_s$, this produces frames at a {vocab}`frame rate` of

$$f_{\text{frame}} \left[{unit}`frames,second`\right] = f_s \left[{unit}`samples,second`\right] \cdot \frac{1}{N_H} \left[{unit}`frames,sample`\right].$$

Frames give us a new unit of time, complementing the _seconds_ and _samples_ we already know. The offset of frame $k$ is $k \cdot N_H$ samples, so its natural timestamp is $\frac{k \cdot N_H}{f_s}$ seconds. For example, at $f_s = 44{,}100$ Hz with $N_H = 1024$, frame $10$ represents the moment $\frac{10 \cdot 1024}{44100} \approx 232$ ms. Conversely, a recording of duration $T$ spans $\frac{T \cdot f_s}{N_H}$ frames, so a ten-second file at these settings is about $\frac{10 \cdot 44100}{1024} \approx 430.7$ frames. (We will deal with that fractional frame shortly.)

The relationship between $N_F$ and $N_H$ controls how much consecutive frames _overlap_. The figure below shows the first few frames of our running example at two common settings, no overlap ($N_H = N_F$) and 50% overlap ($N_H = N_F/2$):

:::{figure}
![Two stacked panels of the same short waveform. Top: frames tiling the signal edge-to-edge with no overlap, each a differently-colored band. Bottom: frames spaced half a frame apart, so each colored band overlaps its neighbors by half.](./assets/fig-frame-extraction.png)

Extracting frames of length $N_F$ from the running example. Top: $N_H = N_F$ tiles the signal with no overlap. Bottom: $N_H = N_F/2$ gives 50% overlap, so every sample falls inside two frames.
:::

## Reassembly with overlap-add

Reassembling frames into a signal is just as simple. Given frames $x_k$ extracted at hop length $N_H$, we reconstruct an estimate $\hat{x}$ by adding each frame back at its original position:

:::{prf:definition} Overlap-add
:label: def-overlap-add
The {vocab}`overlap-add` reconstruction of frames $x_k$ at hop length $N_H$ is

$$\hat{x}[n] = \sum_{k} x_k[n - k \cdot N_H].$$
:::

Under what conditions does this round trip give _perfect reconstruction_, meaning $\hat{x} = x$? It depends entirely on the overlap, which we can see by tracking how many frames cover each sample:

:::{figure}
![Three panels showing the total coverage of each sample after overlap-add. Left, N_H equals N_F: coverage is a flat line at one, perfect reconstruction. Middle, N_H greater than N_F: coverage drops to zero in the gaps between frames, so samples are lost. Right, N_H less than N_F: coverage rises to two where frames overlap, doubling the amplitude.](./assets/fig-reconstruction-cases.png)

How overlap-add reconstructs, as a function of hop length. Only $N_H = N_F$ covers every sample exactly once (perfect reconstruction). Larger hops leave gaps; smaller hops double-count the overlaps, changing the amplitude.
:::

1. When $N_H = N_F$ (no overlap), the frames tile the signal exactly once, and $\hat{x} = x$. Perfect reconstruction.
1. When $N_H > N_F$, there are _gaps_ between frames, and the samples that fall in them are simply lost.
1. When $N_H < N_F$, the frames overlap, and the overlapping samples get added together more than once, boosting the amplitude.

The two building blocks, extraction and overlap-add, are just a few lines of code each. The full, runnable versions are in [code/frames.py](./code/frames.py). You can hear perfect reconstruction (and break it) by playing with $N_H$ and $N_F$ yourself below:

:::{interactive}[notebooks/frames.ipynb]
:::

## Windowing

The third case above, where overlapping frames double the amplitude, hints at a more flexible approach. Instead of adding raw frames, we can multiply each frame by a {vocab}`window` function $w \in \mathbb{R}^{N_F}$ before summing:

$$\hat{x}[n] = \sum_{k} w[n - k \cdot N_H] \cdot x_k[n - k \cdot N_H].$$

Perfect reconstruction now holds under a more general condition: the overlapping windows must add up to a constant at every sample. This is the {vocab}`constant overlap-add` (COLA) property,

$$\sum_{k} w[n - k \cdot N_H] = \text{constant} \quad \text{for all } n.$$

Many combinations of window, frame length, and hop length satisfy COLA. The simplest is the rectangular window (all ones) at 0% overlap, which is exactly the perfect-reconstruction case we already saw. A more useful one is the {vocab}`Hann window`,

$$w[n] = \frac{1}{2}\left(1 - \cos\!\left(\frac{2\pi n}{N_F}\right)\right),$$

a raised cosine bump that tapers smoothly to zero at both ends, used at 50% overlap:

:::{figure}
![Several bell-shaped Hann windows, each shifted half a window-width from the last so they overlap by 50%. Their sum, drawn as a bold line on top, is a flat constant across the interior.](./assets/fig-cola.png)

Hann windows at 50% overlap satisfy constant overlap-add: although each window rises and falls, the overlapping windows always sum to the same constant (bold line), so overlap-add reconstructs the signal exactly.
:::

Why would we ever prefer a tapered window to a plain rectangle, if both reconstruct perfectly? The reason has to do with what happens in the _frequency_ domain, and it will not become clear until we study the short-time Fourier transform later in this chapter. For now, take it on faith that smooth windows are often worth the trouble.

### Boundary conditions

An eagle-eyed reader will have noticed we glossed over some edge cases. What do we do with the _fractional frame_ at the end of a signal, where a frame starts inside the signal ($k \cdot N_H < N$) but runs off the end ($k \cdot N_H + N_F > N$)? Two conventions are common: we can {vocab}`zero-pad`, filling the missing tail of the frame with zeros, or we can simply truncate, discarding any frame that does not fit completely. Both are widely used.

A second question is where to anchor a frame's timestamp. We have been treating a frame's time as the position of its _first_ sample, but it is often more intuitive to _center_ the frame on its timestamp instead, so that frame $k$ spans $x[k \cdot N_H - \tfrac{N_F}{2} + n]$. You will meet both conventions in practice, exposed as arguments like `pad=True` or `center=False` in frame-processing libraries.

Ultimately these are just boundary conditions, affecting a smaller and smaller fraction of frames as the signal grows longer, so we will mostly ignore them from here on.

## Granular synthesis

We can now extract and reassemble frames, but so far the round trip has been pointless: when it is perfect reconstruction, we get back exactly what we started with. The interesting possibilities open up when we _manipulate_ the frames before reassembling them.

This is the idea behind {vocab}`granular synthesis`: chop a sound into many tiny slices, called {vocab}`grains` (typically tens of milliseconds long), then transform and rearrange those grains to build something new. It is a bit like making a collage out of a photograph, cutting it into little pieces and gluing them back in a new arrangement.

:::{figure}
![Three rows. Top: the source waveform. Middle, labeled extract grains times: a row of overlapping colored bell-shaped grains covering the source. Bottom, labeled reassemble plus: the same colored grains rearranged into a new order with small gaps.](./assets/fig-granular-collage.png)

Granular synthesis in three steps: extract short grains from the source (each multiplied by a smooth window), then reassemble them, possibly reordered, resized, or otherwise transformed, into a new sound.
:::

Because a grain is so short, it loses much of the recognizable character of the original sound. And a raw grain, sliced out with a hard rectangular window, has abrupt edges that produce an audible click. So in practice we multiply each grain by a smooth window (a Hann window, say) to taper those edges. Here is a handful of 50 ms grains lifted from the running example and played back with a big gap between them, first with hard rectangular edges and then windowed:

:::{audio-list}
{audio}`Raw (rectangular) grains <./assets/audio-grains-rect.wav>`

{audio}`Windowed (Hann) grains <./assets/audio-grains-hann.wav>`

The same grains, played with a rectangular window (note the click at each edge) and with a Hann window (smooth).
:::

### Manipulating grains

Individual grains are not very interesting on their own. The power of granular synthesis comes from manipulating them _as units_ before reassembly. The simplest manipulation is to _reorder_ them. We can shuffle grains across the whole signal, or shuffle them only within short segments:

:::{figure}
![Two small diagrams. Top: a row of colored grains and, below it, the same grains shuffled into a completely random order. Bottom: the grains shuffled only within blocks of four, so nearby grains stay roughly together.](./assets/fig-granular-randomize.png)

Two ways to randomize grain order: globally (top), which fully scrambles the sound, or within short segments (bottom), which keeps the large-scale structure while blurring the fine detail.
:::

Reordering grains produces a striking effect. It preserves the overall _texture_ of the sound while erasing its specifics, a kind of controlled blur:

:::{audio-list}
{audio}`Granular texture (grains shuffled within segments) <./assets/audio-granular-texture.wav>`

{audio}`For contrast: the raw samples shuffled <./assets/audio-scrambled-samples.wav>`

Shuffling _grains_ keeps the character of the sound. Shuffling the raw _samples_ (bottom) destroys it entirely, leaving only noise.
:::

That contrast is the whole point. Shuffling grains keeps the sound recognizable, but shuffling the underlying _samples_ (not grains) yields nothing but noise. Working at the level of grains, rather than samples, is what makes the effect musical. Order is not the only property we can manipulate: we could also change the grains' amplitude, duration, pitch, or density before reassembling. You can explore all of these by editing the `manipulate` function below:

:::{interactive}[notebooks/granular.ipynb]
:::

### Time stretching

Here is a particularly useful manipulation. What if we _decouple_ the hop length at which we extract grains from the hop length at which we overlap them back together? Call the extraction hop $N_H$ and the reassembly hop $N_H'$. If $N_H' = 2 N_H$, we spread the grains out to twice their original spacing, doubling the output's duration. If $N_H' = \tfrac{1}{2} N_H$, we pack them together, halving it:

:::{audio-list}
{audio}`Original <./assets/audio-trio.wav>`

{audio}`Half speed (grains spread out) <./assets/audio-stretch-half.wav>`

{audio}`Double speed (grains packed together) <./assets/audio-stretch-double.wav>`

Granular time stretching. Changing the spacing at reassembly changes the duration, and therefore the playback speed, while the grains themselves are untouched.
:::

We have achieved {vocab}`time stretching`. Spreading or packing the grains changes the total duration, and hence the playback speed, without touching the contents of the grains themselves.

This is the _second_ time we have changed playback speed. The first was {ref}`resampling <sec-resampling>` in [Chapter 7](../07-sampling-theory). Listen to the same speed changes done by resampling instead:

:::{audio-list}
{audio}`Half speed via resampling <./assets/audio-resample-half.wav>`

{audio}`Double speed via resampling <./assets/audio-resample-double.wav>`

Resampling also changes the speed, but notice that it changes the _pitch_ too, exactly like slowing down or speeding up a record.
:::

The difference is crucial. Resampling changes duration _and_ pitch together (slower means lower, faster means higher), which was exactly what we wanted for wavetable synthesis. But granular time stretching changes duration while keeping the pitch _constant_. Having both techniques suggests something powerful: _decoupled_ control over pitch and duration. We can first _resample_ the grains to change their pitch, and then independently _time stretch_ them by changing their spacing:

:::{audio-list}
{audio}`Half speed, one octave lower (resample + stretch) <./assets/audio-decoupled.wav>`

Combining resampling (to shift pitch) with granular time stretching (to change duration) lets us control the two independently.
:::

In practice, getting a clean result from granular time stretching requires a generous amount of overlap between grains, so that the crossfades between them are smooth.

## The short-time Fourier transform

Granular synthesis showed that frame-based processing can do genuinely creative things. Now we turn to perhaps its most powerful application: the {vocab}`short-time Fourier transform` (STFT), which reveals how a sound's frequency content evolves _over time_.

Recall the limitation of the DFT: it integrates over all time, turning $N$ samples into $N$ bins and, in the process, discarding _when_ each frequency occurred. But of course frequency content changes over time in music, that is what a melody _is_. How can we see those changes? The idea is exactly the frame-based recipe: slice the signal into frames and take the DFT of each one.

:::{prf:definition} Short-time Fourier transform
:label: def-stft
The {vocab}`short-time Fourier transform` of a signal $x$ applies the DFT to each extracted frame:

$$\texttt{STFT}(x)[k] = \texttt{DFT}(x_k), \qquad x_k[n] = x[k \cdot N_H + n].$$

For a signal of $N$ samples with hop length $N_H$ and frame length $N_F$, the output is a complex matrix of shape $\frac{N}{N_H} \times N_F$: one row per frame, one column per frequency bin (or $\frac{N_F}{2}+1$ columns for real-valued audio).
:::

Taking the magnitude of each frame and stacking the frames side by side gives a {vocab}`spectrogram`, a two-dimensional image with time on the horizontal axis, frequency on the vertical axis, and amplitude encoded as color intensity. Because our ears perceive amplitude roughly logarithmically, we usually take the $\log$ of the magnitude before mapping it to color. The spectrogram is one of the most important visualizations in all of audio. Here it is on a simple rising melody, C-D-E-F-G played as sine tones, alongside a plain DFT of the same signal for comparison:

:::{figure}
![Three panels. Top left: the melody as a rising staircase of note names C4 to G4. Top right: the DFT of the whole signal, showing five frequency peaks but no indication of their order in time. Bottom: the spectrogram, showing five horizontal segments stepping upward in frequency over time, so the rising melody is plainly visible.](./assets/fig-stft-melody.png)

A rising C-D-E-F-G melody. The plain DFT (top right) correctly finds all five pitches but has no idea in what _order_ they occurred. The spectrogram (bottom) shows each pitch at the moment it sounds, so the rising melody is unmistakable.
:::

The plain DFT sees all five notes as five peaks but cannot tell you their order. The spectrogram shows each note stepping up in turn. That extra time axis is the whole point of the STFT. As with plain frame processing, the STFT has an inverse and the whole pipeline, from analysis through optional editing to synthesis, is a single frame-based flow:

:::{figure}
![A left-to-right block diagram: the input signal is split into frames, each frame is sent through a DFT, the resulting spectra can be edited, then each is sent through an inverse DFT, and finally the frames are overlap-added back into an output signal. The first half is labeled analysis (STFT) and the second half synthesis (ISTFT).](./assets/fig-stft-diagram.png)

The STFT pipeline. Analysis frames the signal and takes the DFT of each frame; synthesis takes the inverse DFT of each frame and overlap-adds the results. In between, we are free to edit the spectra, which is the basis of spectral processing.
:::

### Configuring the frame length

The STFT has two key parameters, the frame length $N_F$ and the hop length $N_H$, and choosing them well is something of an art. Consider $N_F$ first. What happens as we make frames longer?

The upside is better _frequency_ resolution. Recall that the DFT bin spacing is $\Delta f = f_s / N_F$, so longer frames pack the bins closer together and resolve nearby frequencies more finely. But this comes at a cost in _time_ resolution: a longer frame smears a wider stretch of time into a single spectrum. In the extreme where $N_F$ grows to the whole signal length $N$, we are back to a single all-of-time DFT, having thrown away time entirely. This is a fundamental trade-off, and you can watch it play out by sweeping $N_F$ through powers of two:

:::{figure}
![An animation cycling through spectrograms of the same recording at frame lengths from 256 up to 8192 samples. At short frame lengths the image is sharp in time (crisp vertical onsets) but blurry in frequency; at long frame lengths it is sharp in frequency (crisp horizontal harmonics) but blurry in time.](./assets/fig-nf-sweep.gif)

The time-frequency resolution trade-off. Short frames (top) give sharp timing but coarse frequency; long frames (bottom) give fine frequency detail but blur events together in time.
:::

There is a second cost: computation. Under the FFT, one DFT of length $N_F$ costs $O(N_F \log N_F)$, and we compute $\frac{N}{N_H}$ of them, so the STFT costs roughly $O\!\left(N \cdot N_F \log N_F\right)$, which grows with the frame length. There is no universally best $N_F$; it depends on the application. A few rules of thumb: use a power of two for FFT efficiency, and make the frame at least one cycle of the lowest frequency you care about. The lower limit of human hearing is around $20$ Hz, a cycle of which is $50$ ms, and at $44.1$ kHz a $4096$-sample frame ($\approx 93$ ms) comfortably covers it.

### Configuring the hop length

The hop length $N_H$ is a gentler knob. Unlike $N_F$, it does _not_ affect frequency resolution at all: the DFT of each frame is unchanged no matter how far apart the frames sit. Instead, $N_H$ controls two things. The first is time resolution, since a smaller hop means more frames per second and a finer-grained view of how the sound changes. The second is computational cost: an STFT of $N$ samples produces $\frac{N}{N_H}$ frames, so halving the hop doubles the number of DFTs we must compute.

We usually express the hop as an amount of _overlap_ relative to the frame length. As we saw earlier, we must keep $N_H \le N_F$ or we will skip samples between frames. A common choice is $N_H = N_F / 2$ (50% overlap), and heavy overlaps like 75% ($N_H = N_F/4$) are typical when reconstruction quality matters. In general, the overlap is $\frac{N_F - N_H}{N_F}$, expressed as a percentage:

:::{figure}
![An animation of the same short waveform framed at increasing overlap: 0%, then 50%, then 75%, with the colored frame bands packing more densely each time.](./assets/fig-nh-overlap.gif)

Increasing the overlap by shrinking the hop length. More overlap means more frames covering each moment, giving finer time resolution (and more computation), without changing the frequency resolution.
:::

### Windowing revisited

We can now settle the question we deferred earlier: why bother with smooth windows? The answer is {ref}`spectral leakage <sec-windowing>`, which we first met in [Chapter 8](../08-dft). Extracting a frame is a _multiplicative_ operation: it is equivalent to multiplying the signal by a rectangular window that is one over the frame and zero everywhere else. And by the {ref}`convolution theorem <thm-convolution>` from [Chapter 9](../09-filters), multiplying by a window in time _convolves_ the signal's spectrum with the window's spectrum, smearing each sharp spectral line into a blur.

The rectangular window's spectrum is a sinc function with tall side lobes, so it smears energy far and wide:

:::{figure}
![A four-panel figure. Left to right: a signal x(t); a rectangular window w(t); their product; and the resulting spectrum, in which each frequency line is smeared into a lobe with tall ripples spreading far to either side.](./assets/fig-leakage.png)

Framing with a rectangular window causes strong spectral leakage: the sharp spectral lines of $x$ are convolved with the window's spectrum (a sinc with large side lobes), smearing energy across many bins.
:::

Because every frame is a windowed slice, this leakage is present in _every_ STFT, and it is worse than in a plain DFT because each frame is shorter. The fix is to multiply each frame by a window with a gentler spectrum, such as the Hann window. Its spectrum concentrates energy in a narrow central lobe with much smaller side lobes, so the smearing is greatly reduced:

:::{figure}
![The same four-panel layout, but now with a Hann window. The product tapers smoothly to zero at both ends, and the resulting spectrum has far less ripple spreading out from each frequency line.](./assets/fig-windowing.png)

A Hann window has a much cleaner spectrum than the rectangle, so windowing each frame with it substantially reduces spectral leakage.
:::

The effect is visible in the spectrogram itself, where the rectangular window's leakage shows up as vertical smearing that the Hann window cleans away:

:::{figure}
![Two spectrograms of the same recording, side by side. Left, with a rectangular window: horizontal harmonic lines are surrounded by fuzzy vertical smearing. Right, with a Hann window: the same harmonics are crisp and the background is much cleaner.](./assets/fig-spectrogram-window.png)

Spectrograms of the running example with a rectangular window (left) and a Hann window (right). The Hann window's reduced leakage yields a noticeably cleaner picture.
:::

This is also why granular synthesis windowed each grain: the same smoothing that reduces spectral leakage also removes the audible clicks at grain edges. In the STFT, where we window every frame repeatedly, it is especially important.

### Spectral analysis

The spectrogram is a powerful _analysis_ tool. Suppose we are handed the C-D-E-F-G recording from earlier and asked which _pitches_ it contains and when. We can march through the STFT frame by frame, find the loudest frequency in each frame whose energy exceeds some threshold, round it to the nearest musical pitch, and emit a note whenever the detected pitch changes. This turns a {pyquist}`Audio` into a {pyquist}`Score`, a crude form of music {vocab}`transcription`:

:::{interactive}[notebooks/transcription.ipynb]
:::

Transcription in general is a hard problem, especially for _polyphonic_ music where many notes sound at once, but this simple peak-picking approach works well enough for clean, monophonic input like our sine melody.

### The inverse STFT

We have been _computing_ the STFT; now let us _invert_ it. Is the STFT invertible? We already know the DFT is, since $x = \texttt{IDFT}(\texttt{DFT}(x))$. So under a rectangular window at 0% overlap, where the frames tile the signal exactly, the STFT is invertible too: applying the inverse DFT to each frame recovers that frame, and overlap-add stitches the frames back together,

$$\texttt{ISTFT}(\texttt{STFT}(x)) = x.$$

For other windows and overlaps, the same COLA condition from before guarantees perfect reconstruction: as long as the (squared) windows sum to a constant, the inverse DFTs overlap-add back to the original signal. A runnable STFT and inverse STFT are in [code/stft.py](./code/stft.py).

### Spectral processing

The invertibility of the STFT unlocks a whole family of effects. We can transform a sound into the time-frequency domain, _edit_ the spectral coefficients however we like, and transform back, a technique called {vocab}`spectral processing` (the "edit" box in the STFT pipeline diagram). Two quick examples: we can keep each frame's magnitudes but replace its phases with random values, which smears the sound's sharp transients into a wash, or we can perform _cross-synthesis_, combining the magnitudes of one sound with the phases of another:

:::{audio-list}
{audio}`Phase randomized (transients smeared) <./assets/audio-phase-random.wav>`

{audio}`Cross-synthesis (trio's spectrum, noise's phase) <./assets/audio-cross-synth.wav>`

Two spectral-processing effects, both computed by editing the STFT and inverting it.
:::

There is an enormous space of effects to explore here. Try inventing your own by editing the STFT directly:

:::{interactive}[notebooks/spectral-processing.ipynb]
:::

## The phase vocoder

We close with a famous spectral-processing algorithm, the {vocab}`phase vocoder`, which performs high-quality time stretching without pitch shifting. (Despite the name, it is applied to all kinds of audio, not just voice; it is the algorithm behind the "2x speed" button on video sites. It was originally proposed in 1966 as a low-bandwidth way to transmit _speech_, one year after the FFT was invented, and the name stuck.)

Granular synthesis already gave us pitch-preserving time stretching. But we can also frame time stretching as a spectral-processing operation: to slow a sound to half speed, we want an output STFT with twice as many frames, so we simply _interpolate_ between the input frames. For output frame $i$, we blend input frames $j = \lfloor i/2 \rfloor$ and $j+1$:

$$Y[i] = (1 - a)\, X[j] + a\, X[j+1], \qquad a = \tfrac{i}{2} - j.$$

This sounds reasonable, but it has a subtle flaw involving _phase_. Each STFT bin has a phase, and when we interpolate we are implicitly assuming we know how that phase advances from one frame to the next. But the phase is only known modulo $2\pi$: if a bin's phase reads $\pi/4$ in one frame and $5\pi/4$ in the next, did it advance by $\pi$, or by $3\pi$, or by $5\pi$? The sliding-window nature of the STFT makes this genuinely ambiguous, and naive interpolation between ambiguous phases produces a smeared, "phasey" artifact.

:::{figure}
![Two unit circles side by side. The left shows a phasor at angle pi over four; the right shows a phasor at angle five pi over four, half a turn further around. A caption notes the phase could have advanced by pi, or three pi, or five pi.](./assets/fig-phase-ambiguity.png)

The trouble with phase. A bin's phase jumps from $\pi/4$ to $5\pi/4$ between frames, but the true advance could be $\pi$, $3\pi$, $5\pi$, or any of infinitely many possibilities. The STFT alone cannot disambiguate them.
:::

The phase vocoder resolves this by making a reasonable assumption about how phase _should_ evolve. For each bin it computes the _expected_ phase advance per hop (from the bin's center frequency), then compares it to the _observed_ advance and corrects toward the nearest consistent value, accumulating a clean, continuous phase for the output. The details are beyond our scope, but the result is high-quality time stretching:

:::{audio-list}
{audio}`Original <./assets/audio-trio.wav>`

{audio}`Half speed (pitch preserved) <./assets/audio-pv-half.wav>`

{audio}`Double speed (pitch preserved) <./assets/audio-pv-double.wav>`

{audio}`Pitched down an octave (phase vocoder + resampling) <./assets/audio-pv-pitch.wav>`

The phase vocoder stretches time while holding pitch constant, and combined with resampling it gives independent control over both.
:::

## Real-time processing

Frame-based processing has one more role to play, which we will return to in [Chapter 17](../17-realtime): it is how real-time audio works. Suppose we want to synthesize an endless stream of audio _on the fly_, computing each sample $x[n] = x(\tfrac{n}{f_s})$ just in time to be played. We could call our synthesis function once per sample, but function calls have overhead, and at tens of thousands of samples per second that overhead adds up fast. Worse, it is overkill: we cannot physically turn knobs fast enough to need per-sample control anyway.

Instead, real-time systems compute audio in frames, usually called {vocab}`blocks` in this context. We pick a block length $B$, and at each moment $\frac{k \cdot B}{f_s}$ the operating system asks our program for the next $B$ samples. This is exactly frame-based processing with $N_H = N_F = B$. As long as we can compute each block in less than $\frac{B}{f_s}$ seconds, the audio never runs dry and we achieve a real-time stream. We will develop this idea properly when we study real-time, interactive audio.

## Summary

- Frame-based processing operates on music at intermediate, musically intuitive rates by aggregating samples into {vocab}`frames`.
- A frame is $x_k[n] = x[k N_H + n]$, controlled by the {vocab}`frame length` $N_F$ and the {vocab}`hop length` $N_H$. Their ratio sets the overlap.
- {vocab}`Overlap-add` reassembles frames. It is perfect reconstruction when $N_H = N_F$ with rectangular windows, or more generally when windows satisfy {vocab}`constant overlap-add`.
- {vocab}`Granular synthesis` chops sound into {vocab}`grains` and manipulates them (reordering, resizing, respacing) to create textures, and to time-stretch without changing pitch.
- The {vocab}`short-time Fourier transform` takes the DFT of each frame, revealing how frequency content evolves over time. Its magnitude is a {vocab}`spectrogram`.
- The frame length $N_F$ trades time resolution against frequency resolution; the hop length $N_H$ trades time resolution against computation. Windowing each frame reduces {vocab}`spectral leakage`.
- The STFT is invertible, enabling {vocab}`spectral processing`: editing a sound in the time-frequency domain. The {vocab}`phase vocoder` uses this to time-stretch while preserving pitch.
- Real-time audio is frame-based processing with $N_H = N_F = B$, computing one {vocab}`block` at a time.

## Questions for the reader

:::{exercise}
**Frames and time.** A recording at $f_s = 48{,}000$ Hz is processed with frame length $N_F = 2048$ and hop length $N_H = 512$. (a) What is the frame rate in frames per second? (b) What percentage overlap is this? (c) What timestamp, in milliseconds, does frame $k = 20$ correspond to?
:::

:::{exercise}
**Perfect reconstruction.** You extract frames with a rectangular window and reassemble them with overlap-add. For each of $N_H = N_F$, $N_H = 2 N_F$, and $N_H = N_F / 2$, describe what the reconstructed signal looks like compared to the original, and say which (if any) is perfect reconstruction.
:::

:::{exercise}
**Grains versus samples.** Randomizing the order of a sound's _grains_ preserves its overall texture, but randomizing the order of its _samples_ produces only noise. Explain why, in terms of what information a single grain carries that a single sample does not.
:::

:::{exercise}
**Resolution trade-off.** You want to analyze a bass line whose lowest note is $55$ Hz, and you also want to pinpoint the exact moment each note begins. Explain the tension between these two goals in terms of the frame length $N_F$, and suggest a frame length that is a reasonable compromise at $f_s = 44{,}100$ Hz.
:::

:::{exercise}
**Time stretch versus resampling.** Both granular time stretching and resampling can make a recording play back at half speed. How does each affect the _pitch_ of the result, and why? Which would you use to slow down a song for practice without making it sound lower?
:::

:::{exercise}
**Reading a spectrogram.** Sketch (in words) what the spectrogram of a single, sustained trumpet note would look like: where would you see energy, and how would it be arranged on the time and frequency axes? How would it differ from the spectrogram of a snare drum hit?
:::

## Musical examples

Curtis Roads, a pioneer of granular synthesis, composed some of the earliest and most influential music built entirely from grains. His [Eleventh Vortex](https://www.youtube.com/watch?v=XgBjD6_SbOU) is a dense cloud of thousands of tiny sonic particles, exactly the granular textures of this chapter taken to an extreme.

Aphex Twin's "[Equation](https://www.youtube.com/watch?v=M9xMuPWAZW8)" (formally titled with a mathematical equation) hides a visual surprise: near the end of the track, his face is drawn directly into the _spectrogram_. It only becomes visible when you view the sound in the time-frequency domain, a playful demonstration that the spectrogram is a genuine, invertible representation of sound, and that spectral processing runs both ways.
