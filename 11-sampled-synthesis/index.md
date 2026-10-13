---
title: "Chapter 11: Sample-based Synthesis"
---

# Sample-based Synthesis

This chapter begins the second part of this book. In the first part (Chapters 1 through 10), we studied the fundamental principles of computer music in depth: how sound becomes digital audio, how to synthesize it, how to analyze it in the frequency domain, and how to process it with filters and frames. Now we shift gears. In the second part, we will survey a _breadth_ of computer music topics that build on these principles. We won't study each topic in as much depth as the fundamentals. Instead, the goal is to expose you to many topics, so that you can find the ones that interest you most and go deeper through self-study.

For our first topic, we will examine {vocab}`sampling` and {vocab}`sample-based synthesis`.

:::{admonition} "Sampling" is overloaded
:class: warning
So far in this book, "sampling" has been shorthand for _digital_ sampling, the step of analog-to-digital conversion that measures a signal $f_s$ times per second ({ref}`Chapter 7 <sec-sampling-and-frequency>`). Likewise, a "sample" has referred to a single audio sample $x[n]$.

In this chapter, "sampling" takes on its colloquial meaning: lifting a _clip_ of audio from one source and reusing it in another context, often with some manipulation. Similarly, a "sample" now refers to a clip of audio, not an individual audio sample. When the distinction matters, we will write "audio sample" for $x[n]$.
:::

We will cover two use cases for sampling:

1. **Sampling and sequencing**: extracting samples from recordings and playing them back in new orders and with new timing.
1. **Sample-based synthesis**: combining recorded samples with _repitching_ to create instruments that can play any pitch.

## Sampling

We first define precisely what we mean by a sample: a contiguous chunk of audio samples extracted from some source recording.

:::{prf:definition} Sample
:label: def-sample
Let $\mathbf{x} = [x[0], x[1], \ldots, x[N-1]]$ be source digital audio at sample rate $f_s$ of length $N$ samples. A _sample_ of $\mathbf{x}$ is a contiguous chunk

$$[~x[m], x[m+1], \ldots, x[m+M-1]~]$$

of length $M \leq N$ audio samples, starting at offset $m \in \{0, 1, \ldots, N - M\}$.
:::

In units of seconds, the sample starts $\frac{m}{f_s}$ seconds into the recording and lasts $\frac{M}{f_s}$ seconds.

We have seen operations like this before. When we extracted {ref}`frames <sec-extracting-frames>` for frame-based processing and {ref}`granular synthesis <sec-granular-synthesis>` in [Chapter 10](../10-frame-proc), each frame was also a contiguous chunk of audio samples.

The key difference is _how_ we choose $m$ and $M$. In frame-based processing, they are determined procedurally: the offsets are multiples of the hop length $N_H$, and every frame has the same frame length $N_F$. When sampling, by contrast, a person chooses $m$ and $M$ (the start time and duration of the sample) to capture something musically meaningful, like a single drum hit or a memorable phrase. They typically make this choice _by ear_, or visually by looking at the waveform.

:::{margin} The Amen break
The Amen break is a seven-second drum solo, played by Gregory C. Coleman on The Winstons - _Amen, Brother_ (1969). Starting with hip-hop in the late 1980s, producers sampled it relentlessly, and it became the rhythmic backbone of entire genres like jungle and drum and bass. It is often called the most sampled recording in history, appearing in thousands of tracks.
:::

Try it yourself below, using one of the most famous samples of all time: the _Amen break_. Choose an offset $\frac{m}{f_s}$ and a duration $\frac{M}{f_s}$ (both in seconds), and use the zoom to inspect the waveform up close. The audio card updates whenever you release a slider. Can you isolate a single snare drum hit? How about exactly one bar (four beats) of the break?

:::{interactive}[notebooks/sample-explorer.ipynb]
:::

### Extracting samples in Pyquist

In `pyquist`, extracting a sample is a one-liner. We can work in units of _seconds_ with {pyquist}`Audio.segment`, whose `offset` and `duration` arguments correspond to $\frac{m}{f_s}$ and $\frac{M}{f_s}$. Or we can work in units of _audio samples_ by slicing an {pyquist}`Audio` directly with `audio[m:m + M]`, just like a NumPy array.

Below, we extract the second bar of the Amen break both ways. Each beat of the break lasts about $0.436$ seconds, so the second bar starts $4 \times 0.436 = 1.744$ seconds into the recording and lasts just as long:

:::{interactive}[notebooks/extract-samples.ipynb]
:::

Both approaches extract the same $M = 76{,}910$ audio samples. Use whichever units are more natural for the task at hand: seconds when working by ear, and audio samples when you need exact control.

## Sequencing

What can we do with samples once we have them? A primary use case is {vocab}`sequencing`: playing samples back in different orders, or with different timing, than in their original recordings. Sequencing is a cornerstone of rhythm production in genres like hip-hop and electronic dance music, where producers build new melodies and beats out of fragments of old ones.

CLAUDE: change this to directive to link to `Score` object
Pyquist's scores are a natural fit for sequencing. Recall from {ref}`Chapter 4 <def-render>` that rendering a score calls an _instrument_ function once per event, shifts each result to the event's onset time, and sums them all up. There is no requirement that this function synthesize its output audio from scratch. A function that simply returns a sample is a perfectly good "instrument", so a sequence of samples is just a score. Below, we highlight a couple examples of sequencing using `pyquist` scores.

### Chopping the Amen break

CLAUDE: don't emphasize _chopping_ as vocab, just use it colloquially. also, this is a good time to formally introduce the concept of beats, which we haven't really covered. be succinct about this. a _beat_ (use unit directive) is a symbolic unit of time in music, referring to the underlying pulse (i.e., what you might tap your foot to). beats are particularly expressed in units of beats per minute. here we convert that to seconds per beat. (use unit directives throughout, see section 1.2 for example of the flavor of unit arithmetic I'm expecting to see, no need to do the strikethrough though)

Our first sequencer rearranges the beats of the Amen break, a practice known as _chopping_. The break lasts 16 beats, each about $0.436$ seconds long. We start with an instrument, `amen_sample(offset, duration)`, that extracts a sample of the break with {pyquist}`Audio.segment`, allowing us to control samples with score `Event`s of the form `(2.0, {"offset": 0.0, "duration": 1.0})`. Cutting a sample out of the middle of a recording can leave abrupt edges, which we hear as clicks. So the instrument also applies a very short piecewise-linear envelope, as in [Chapter 4](../04-score-timbre), that fades in over $1$ ms and fades out over $1$ ms.

As a sanity check, a score with one event per beat, each playing that same beat, should reproduce the original break. Then `amen_chop(hits, speed, seed)` builds a new score that plays randomly chosen beats instead, one every $\frac{0.436}{\text{speed}}$ seconds:

:::{interactive}[notebooks/amen-chops.ipynb]
:::

CLAUDE: note that I changed the speed to something more appropriate for jungle, so update this accordingly. remark on the new BPM as well, following the unit overview above
At a speed of $1.5$, a new hit arrives every $0.29$ seconds, so each hit plays only the first two thirds of its beat. Try other seeds, numbers of hits, and speeds. Breakbeats chopped like this, the Amen break above all, are the signature sound of [jungle](https://en.wikipedia.org/wiki/Jungle_music) and [drum and bass](https://en.wikipedia.org/wiki/Drum_and_bass).

### A drum machine

Our second sequencer is a {vocab}`drum machine`. Its interface is a grid of _steps_: each row is a drum sound, each column is a moment in time corresponding to a subdivision of a beat, and the musician switches individual cells on or off.

In the Python example below, we crudely mimic a typical drum machine interface with a few lines of text, where an `X` switches a cell on:

```text
X-X-X-X-X-X-X-X-
----X-------X---
X-------X-------
```

The function `ascii_to_score` turns such a grid into a `Score` object, adding an event at time $j$ for every `X` in column $j$, with the Freesound ID of that row's sound as its only parameter. Our instrument, `freesound(fsid)`, simply fetches and returns the corresponding sound.

CLAUDE: make this consistent w/ the info above about beats. again, concise; don't ramble on at length about beats.
So far, the times in our scores have always been in seconds. A drum machine instead counts time in steps, so we render the score with a {pyquist}`BasicMetronome`, which converts score times to seconds at a fixed tempo measured in beats per minute (BPM). The columns of a drum machine are typically _sixteenth notes_, four steps per beat. So to play our grid at a tempo of $120$ BPM, the metronome must count $4 \times 120 = 480$ steps per minute, or one step every $125$ ms:

CLAUDE: note that I changed the hi hat sound here. may need to cache it? although I think it already cached, can you git add (stage) the correct subset of assets here? i now have more on my local machine than I would need
:::{interactive}[notebooks/drum-machine.ipynb]
:::

Try editing the pattern: move the snare drum, add more kick drums, or change the tempo.

CLAUDE: update this!
Drum sounds from Freesound: hi-hat [332372](https://freesound.org/s/332372/) by soneproject, License: [CC0](http://creativecommons.org/publicdomain/zero/1.0/). Snare drum [46709](https://freesound.org/s/46709/) by boney-man, License: [Attribution 3.0](http://creativecommons.org/licenses/by/3.0/). Kick drum [673512](https://freesound.org/s/673512/) by TheEndOfACycle, License: [CC0](http://creativecommons.org/publicdomain/zero/1.0/).

## Sample-based synthesis

CLAUDE: at a high-level, organization is quite rough here. there are two ideas we want to convey: (1) the idea of recording samples of real instruments as an alternative to computer music synthesis methods, (2) the idea of manipulating those samples if we want to synthesize expressive parameters that we haven't pre-recorded. the transition / connection between them is memory: samples cost memory, and combinatorically more so to record all possible combinations of synthesis parameters (pitch, duration, amplitude, etc.). even w/ memory relatively cheap by modern standards, the combinatorics still make this prohibitively expensive. let's introduce each of those ideas in turn to clean up the exposition here. also, let's include a figure of each. for figure of the first point, compare additive synthesis + envelope recreation of clarinet (see pcm-04-clarinet.ipynb for my attempt, don't include that code just the final audio result) to real clarinet `356904`, w/ expressive parameters pitch=A#5 and duration=6 seconds. include both audio and waveform plots. for second figure, create an image figure with a small 2D grid: rows are durations [1,3,6,9] seconds and columns are pitches w/ A#5 in the middle. cell is either a waveform plot (indicating that we've pre-recorded that combination) or a question mark, indicating that we haven't pre-recorded. put the waveform for the example from the first figure in there, and maybe a couple others, but leave the others as question amrks. point is to emphasize the combinatoric space of possibilities. at some point, explicitly define vocab _sample-based synthesis_: the idea of pre-recording musical material, and applying manipulations on-the-fly to change its expressive parameters

CLAUDE: 
:::{margin} A brief history
Sample-based synthesis predates both digital audio and sampling. Pierre Schaeffer, a pioneer of [_musique concrète_](https://en.wikipedia.org/wiki/Musique_concr%C3%A8te#The_phonog%C3%A8ne), built the _phonogène_, a tape machine whose keyboard changed the playback speed of a tape loop, and with it the pitch. Instruments like the [Mellotron](https://en.wikipedia.org/wiki/Mellotron) later put this idea into mass production. The [Fairlight CMI](https://en.wikipedia.org/wiki/Fairlight_CMI) (1979), the first commercially available digital sampler, was marketed as a way to play realistic sounds, like a piano, that the synthesizers of the day could not produce. Memory was scarce: each voice had just 16 kilobytes for its 8-bit samples, at most about two seconds of audio.
:::

Synthesis techniques like {ref}`frequency modulation <sec-frequency-modulation>` were motivated in part by the goal of producing realistic imitations of musical instruments. This turns out to be extremely difficult! As we saw with the trumpet in [Chapter 6](../06-modulation), the harmonics of real instruments evolve in intricate ways over the course of every note. Decades of synthesis research have produced many compelling instrument sounds, but few that a listener would mistake for the real thing.

With sampling, we can just "cheat": rather than synthesizing an instrument's sound, we can record the instrument and play the recording back! This was prohibitively expensive in the early days of computer music, when computers could store only a few seconds of audio in memory. These days, it's commonplace. Commercial sample-based instruments often span hundreds of gigabytes, consisting of recordings of the world's finest instruments played by top studio musicians in world-class recording studios.

CLAUDE: at this point in the exposition, we should still be emphasizing the idea of changing high-level synthesis parameters like pitch and duration, not just pitch. nix the recorder sample in favor of the clarinet sample for consistency.
The basic idea of sample-based synthesis is to achieve instrument-like control from a single sample:

1. Record an instrument playing a single note.
1. Resample the recording to change its pitch to any other pitch.

For example, here is a single recording of a G5 played on a recorder (the wooden flute familiar from many grade-school music classes), repitched to cover a range of notes:

CLAUDE: move this figure down into the pitch resampling section
:::{audio-board}
{audio}`G4 <./assets/audio-recorder-G4.wav>`

{audio}`C5 <./assets/audio-recorder-C5.wav>`

{audio}`E5 <./assets/audio-recorder-E5.wav>`

{audio}`G5 (the original recording) <./assets/audio-recorder-G5.wav>`

{audio}`C6 <./assets/audio-recorder-C6.wav>`

![A piano keyboard spanning G4 to C6. The G5 key is highlighted in red and labeled as the original. Arrows fan out from a label reading "recording of G5" to the keys G4, C5, E5, and C6, which are highlighted in blue and labeled with their distances from G5 in steps: k = -12, -7, -3, and +5.](./assets/fig-recorder-keyboard.png)

A single recording of G5 on a recorder (red), repitched by $k$ steps to play G4, C5, E5, and C6 (blue). [620964](https://freesound.org/s/620964/) by cdonahueucsd, License: [Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).
:::

If you listen closely, you may notice that the lower notes also last longer, and the higher notes are shorter. We will return to this side effect soon.

CLAUDE: rewrite this w.r.t the adjusted exposition above, if needed

Compared to the other synthesis techniques we have studied, sample-based synthesis has several advantages. It is:

- **Extremely realistic**: the output _is_ a recording of the real instrument.
- **Computationally cheap**: playback is little more than reading numbers from memory. CLAUDE: it's true that it's cheap, but it's misleading to say it's just reading numbers from memory. we're also consdiering the manipulation here as part of the synthesis algorithm
- **Easy to implement**: as we will see, its core is just a few lines of code.
- **Very general**: it works for any tonal sound, from a saxophone to a sung vowel to a car horn.

But it also has disadvantages:

- **High memory usage**: as we will see, convincing instruments require many recordings, often many gigabytes of samples on disk or in memory.
- **Limited ability to modify high-level musical properties**: a recording captures one particular performance of one particular note. Unlike a synthesizer, it has no knobs to turn.

In the rest of this section, we will develop techniques that overcome some of this last limitation, giving us independent control over three musical properties of each note: (1) pitch, (2) duration, and (3) dynamics.

### Changing pitch via resampling

Recall {ref}`wavetable synthesis <sec-wavetable-synthesis>` from [Chapter 3](../03-additive-synthesis), where we stored a single cycle of a waveform in a table. We saw that changing the rate at which we read through the table changes the perceived pitch of the output. We can use the same idea to change the pitch of not just a wavetable, but an entire recorded sample stored on disk! Reading through a recording faster raises its pitch, and reading through it slower lowers it.

CLAUDE: use clarinet instead, from https://freesound.org/people/MTG/packs/20228/.
As a running example for the rest of this chapter, we will use recordings of a soprano saxophone from the Good-sounds dataset, a collection of single notes played by professional musicians on a variety of instruments, recorded by the Music Technology Group (MTG) at Universitat Pompeu Fabra and [available on Freesound](https://freesound.org/people/MTG/packs/20251/). Here is a single recording of C5, shifted up to E5, G5, and C6 by reading it faster:

:::{audio-list}
{audio}`C5 (the original recording) <./assets/audio-sax-repitch-C5.wav>`

{audio}`E5 (4 steps up) <./assets/audio-sax-repitch-E5.wav>`

{audio}`G5 (7 steps up) <./assets/audio-sax-repitch-G5.wav>`

{audio}`C6 (12 steps up) <./assets/audio-sax-repitch-C6.wav>`

A soprano saxophone playing C5, repitched up to E5, G5, and C6 by reading the recording faster. Notice that the higher notes are also shorter. [359646](https://freesound.org/s/359646/) by MTG, License: [Attribution 3.0](http://creativecommons.org/licenses/by/3.0/). For every saxophone recording in this chapter, we trimmed the silence, normalized the level, and fine-tuned the pitch.
:::

Let's make this precise. Recall {ref}`resampling <sec-resampling>` from [Chapter 7](../07-sampling-theory), which maps a vector of $N$ audio samples $\mathbf{x}$ to a new vector of $M$ audio samples $\mathbf{y}$ by reading $\mathbf{x}$ at fractional positions $p$, interpolating between neighboring audio samples. To change the playback speed of a recording from an original duration of $T_1$ seconds to a new duration of $T_2$ seconds, we keep the sample rate fixed, set the new length to $M = N \cdot \frac{T_2}{T_1}$, and read

$$y[m] = \text{Interpolate}\!\left(\mathbf{x},\; p = m \cdot \frac{T_1}{T_2}\right).$$

What does this do to the frequencies in the recording? Suppose the recording contains a component at frequency $f_1$. Each output sample advances $\frac{T_1}{T_2}$ input samples through the recording, so working through the units, the output contains that component at

$$f_2 \left[{unit}`cycles,second`\right] = \frac{f_1}{f_s} \left[{unit}`cycles,input sample`\right] \cdot \frac{T_1}{T_2} \left[{unit}`input samples,output sample`\right] \cdot f_s \left[{unit}`output samples,second`\right] = f_1 \cdot \frac{T_1}{T_2}.$$

Every frequency in the recording is multiplied by the same factor $\frac{T_1}{T_2}$, the ratio of the original duration to the new one.

This raises a key question: **how should we configure the ratio $\frac{T_1}{T_2}$ to change pitch in units of steps?** Recall from {prf:ref}`def-step` in [Chapter 4](../04-score-timbre) that raising a frequency by $k$ steps multiplies it by $2^{k/12}$. Setting $f_2 = f_1 \cdot 2^{k/12}$, we need

$$\frac{T_1}{T_2} = 2^{k/12}, \qquad \text{or equivalently} \qquad T_2 = \frac{T_1}{2^{k/12}}.$$

For example, to shift a recording of C4 up to G4 ($k = 7$ steps), we read it $2^{7/12} \approx 1.498$ times faster than normal. If the C4 recording lasts $2$ seconds, the resulting G4 lasts $\frac{2}{1.498} \approx 1.33$ seconds. To shift a recording _down_, $k$ is negative, so the ratio is less than $1$ and we read the recording slower.

:::{margin}
Recall from [Chapter 7](../07-sampling-theory) that reading a recording faster can also push its highest harmonics past the Nyquist frequency, where they alias. High-quality samplers avoid this by low-pass filtering the recording before reading it faster, much like Pyquist's bandlimited {pyquist}`Audio.resample`.
:::

CLAUDE: say less... instead of these long-winded paragraphs, can just say that outputs get less realistic as $|k|$ gets larger without additional explanation, so in practice, can pre-record a few different frequencies and resample the one closest to the target frequency.
In theory, a single recording can now be shifted to any pitch. In practice, the larger $|k|$ is, the more unrealistic the result sounds. One reason is that resampling scales _every_ frequency in the recording by the same factor, including features of the sound that stay put on a real instrument as its pitch changes, like the resonances of its body. This is why a voice sped up by an octave sounds like a chipmunk, rather than a higher-pitched singer. Another reason is the side effect on duration: shifting by $k$ steps also scales the duration of the recording by $2^{-k/12}$. For example, a note shifted up an octave has an attack twice as fast as the real instrument's.

So in practice, sample-based instruments are built from recordings of several pitches across the range of the instrument, and they shift whichever recording is closest to each requested pitch, keeping $|k|$ small. This practice is called {vocab}`multisampling`, and it is one reason why commercial sample libraries are so large.

The code below implements repitching. The function `resample(x, ratio)` reads `x` at `ratio` times its original speed with linear interpolation, keeping the output sample rate the same. It is just like the wavetable reader of Chapter 3, minus the wraparound. Then, `repitch(x, k)` shifts the pitch of `x` by $k$ steps by resampling it with a ratio of $2^{k/12}$. We use these functions to play an arpeggio in two ways: (1) by repitching a single C5 recording from the middle of the saxophone's range, and (2) by repitching whichever of three recordings (C4, C5, and C6) is closest to each note:

CLAUDE: forget about multisampling in this example. too complicated. simplfiy this example and move it up above the note about multisampling. remove any handling for duration. i _want_ durations to be changed in this example. better for demonstration purposes. remove `cut_off` function. make it a single cell w/ just `resample`, `repitch`, and `clarinet(pitch: str)` function which loads the clarinet sound and calls `repitch` on it. it's okay if notes bleed into one another during playback as a consequence (don't mention the bleeding explicitly to readers).
:::{interactive}[notebooks/repitch.ipynb]
:::

Pay particular attention to the first and last notes of each arpeggio. The multisampled version plays the real C4 and C6 recordings, while the single-recording version must shift C5 a full octave down and up. These functions are also in [code/sampler.py](./code/sampler.py).

Resampling gives us control over pitch. However, there's a catch: duration and pitch are now _coupled_! As the code above shows, shifting the C5 recording down to C4 doubles its duration, and shifting it up to C6 halves it. When we play music, we want to control the duration of each note independently of its pitch, just like for the other synthesis methods we have studied.

### Changing duration via looping

Recall from {ref}`Chapter 4 <sec-envelope-phases>` that the notes of real instruments pass through multiple phases: an attack, a decay, a sustain, and a release. Suppose we have a single recording of a note, repitched or otherwise, that lasts some fixed duration. How can we adjust its duration?

The key insight comes from how these phases behave as duration changes. When the same instrument plays notes of two different durations, the attack, decay, and release are roughly the same in both. Only the sustain is elongated (or shortened). This suggests a strategy: keep the attack and release of the recording as they are, identify a portion of the recorded sustain, and _loop_ it, repeating it as many times as needed to reach the desired duration:

CLAUDE: switch this to clarinet sound for consistency
:::{figure}
![Top: the waveform of the saxophone's C5 note over about 4.4 seconds, with shaded regions marking a brief attack, a long sustain, and a release that begins at 3.3 seconds. An orange band labeled loop marks the last quarter second of the sustain. Bottom: a bar dividing the same timeline into a gray region before the loop labeled plays once (d_A), the orange loop region labeled loops (d_S), and a purple region after the loop labeled plays once (d_R).](./assets/fig-sax-phases.png)

The saxophone's C5 note (top), shaded by phase: a quick attack, a long sustain that slowly fades, and a release. (This note's attack flows directly into its sustain, with no distinct decay.) To play a longer note (bottom), everything before the loop plays once, the loop repeats, and everything after the loop, including the release, plays once.
:::

CLAUDE: these need to be standardized between chapters 4 and here. I like $T, T_A, T_D, T_R$ for full length, attack, duration, release respectively. make that change here and in chapter 4. actually, we don't even need these here. it's confusing to refer to $t_s = T_A$, because $t_s$ includes both the attack, decay, adn part of the sustain potentially. instead, just refer to it as $t_s$. I don't think we have to refer to $T_A, T_D$, etc. at all here, but if we do, make them consistent with those and update chapter 4 anyway. duration should be $T$ not $d$
Let's formalize this. We choose a {vocab}`sustain loop` spanning the time range $[t_s, t_e)$ of a recording that lasts $T$ seconds. This splits the recording into three parts: everything before the loop, lasting $d_A = t_s$ seconds, the loop itself, lasting $d_S = t_e - t_s$ seconds, and everything after the loop, lasting $d_R = T - t_e$ seconds. To play a note of duration $d$, the loop must repeat

$$n = \frac{d - (d_A + d_R)}{d_S}$$

times, which we round to the nearest whole number. For example, our C5 recording lasts $T \approx 4.4$ seconds, and the loop in the figure above spans from $t_s \approx 3.05$ to $t_e = 3.3$ seconds. So $d_A \approx 3.05$, $d_S \approx 0.25$, and $d_R \approx 1.1$ seconds, and a note lasting $d = 8$ seconds needs $n \approx \frac{8 - 4.15}{0.25} = 15.4$, or $15$ repetitions of the loop.

CLAUDE: this is under-emphasizing the key point: that the loop will be in units of _samples_, and the fundamental frequency is unlikely to be an integer number of samples.
CLAUDE: from here on to the end of this subsection should be like two paragraphs at most. just want to very concisely explain the issue of non-integer $f_0$ in units of samples, and the workarounds (selecting multiple periods, crossfading). then, show the the final code example with `clarinet(pitch: str, duration: float)`. crossfading should not be formalized or included in the code example, it's not helpful for building intuition, just explain informally and show a figure of the idea. don't need sound examples.

Where exactly should the loop begin and end? Within the sustain, the waveform is quasi-periodic, repeating at the note's fundamental frequency $f_0$. For the loop to repeat seamlessly, the waveform at its end should flow smoothly back into the waveform at its start. The loop spans

$$c \left[{unit}`cycles`\right] = f_0 \left[{unit}`cycles,second`\right] \cdot (t_e - t_s) \left[{unit}`seconds`\right]$$

cycles of the fundamental. If $c$ is a whole number, the end of the loop lines up with its start. Otherwise, each time the loop wraps around, the waveform's phase jumps by $c - \lfloor c \rfloor$ of a cycle. We accrue this much pitch error with every repetition of the loop, and we hear it as a periodic glitch.

In practice, we choose a loop spanning multiple cycles, and try to get $c$ as close to a whole number as possible. Why not loop a single cycle, like a wavetable? Recall that audio samples are discrete, and a single cycle is rarely a whole number of audio samples. For example, at $f_s = 44{,}100$ Hz, a G4 at $392$ Hz has a period of $\frac{44{,}100}{392} = 112.5$ audio samples, so a single-cycle loop of either $112$ or $113$ audio samples would be off by half a sample. Two cycles, on the other hand, span exactly $225$ audio samples. Longer loops have another benefit: they capture more of the natural variation of the sustain, which makes the repetition less conspicuous.

Even with a whole number of cycles, a small discontinuity usually remains at each wrap. Real sounds are only _quasi_-periodic: their amplitude and timbre drift subtly over time, so the waveform at the end of the loop never exactly matches the waveform at its start. The standard fix is a {vocab}`crossfade`: just before each wrap, we gradually blend the end of the loop into the audio that originally led into the loop's start.

To formalize this, let the loop span from audio sample $s = t_s f_s$ up to (but not including) audio sample $e = t_e f_s$, so that one pass of the loop lasts $d_S = e - s$ audio samples. We choose a crossfade length of $L$ audio samples, where $2 \leq L \leq \min(s, d_S)$. One pass of the crossfaded loop is then

$$\ell[j] = \begin{cases} x[s + j] & \text{if } j < d_S - L, \\[1mm] (1 - w_j) \cdot x[s + j] + w_j \cdot x[s + j - d_S] & \text{otherwise,} \end{cases}$$

for $j \in \{0, 1, \ldots, d_S - 1\}$, where the weight $w_j = \frac{j - (d_S - L)}{L - 1}$ ramps linearly from $0$ to $1$ over the final $L$ audio samples of the loop.

For most of the loop, $\ell[j]$ is just the loop itself. During its final $L$ audio samples, the first term continues the loop, while the second term reads the recording exactly one loop length _earlier_: the stretch of audio just before the loop's start. So as each pass of the loop ends, its tail fades out while the audio that leads into the loop fades in. By the final audio sample of the pass, the output is $x[s - 1]$, the audio sample that immediately precedes $x[s]$ in the recording. Wrapping back to the start of the loop then continues the recording exactly as it originally flowed:

:::{figure}
![A schematic with two rows. The top row, labeled recording, shows a timeline with a loop region between marks t_s and t_e. A gold block labeled pre-start sits just before t_s, and a red block labeled tail occupies the end of the loop just before t_e. The bottom row, labeled one pass of the loop, shows the loop region with its final block crossed by a falling red line and a rising gold line, annotated crossfade: tail out, pre-start in. A gold arrow leads from the pre-start block to the crossfade, and a gray arrow below loops from the end of the pass back to its start, labeled then wrap back to t_s and continue.](./assets/fig-loop-crossfade.png)

Crossfading a loop. During the last $L$ audio samples of each pass, the loop's tail (red) fades out while the $L$ audio samples just before $t_s$ (gold) fade in. Each pass therefore ends on the audio that originally led into $t_s$, so wrapping back to $t_s$ is seamless.
:::

The final pass of the loop is not crossfaded. Instead, it flows directly into the rest of the recording, including the release, exactly as in the original. Here is the effect of each of these refinements on our running example, lengthened from $4.4$ to $7.9$ seconds:

:::{audio-list}
{audio}`The original recording <./assets/audio-loop-original.wav>`

{audio}`A 250 ms loop ($c \approx 130.81$ cycles) <./assets/audio-loop-naive.wav>`

{audio}`A loop of exactly 131 cycles ($\approx 250.36$ ms) <./assets/audio-loop-cycles.wav>`

{audio}`131 cycles with a 30 ms crossfade <./assets/audio-loop-xfade.wav>`

Lengthening the saxophone's C5 by looping its sustain. A loop of exactly $250$ ms spans about $130.81$ cycles, and the resulting phase jump at every wrap produces a regular ticking. A loop of exactly $131$ cycles reduces the jump, and a $30$ ms crossfade smooths over what remains.
:::

In practice, loop points are usually tuned by ear. Sustains are never perfectly periodic, and every recording is different, so the best loop is simply the one that sounds best. Try it yourself below. The loop initially spans exactly $250$ ms, from $3050.0$ to $3300.0$ ms, or about $130.81$ cycles of C5. Listen for the ticking at each wrap, then nudge the loop end until $c$ is within a few hundredths of a whole number (click a slider, then use the arrow keys for steps of $0.1$ ms). Finally, add a crossfade, and watch the wrap smooth out in the bottom panel:

:::{interactive}[notebooks/loop-explorer.ipynb]
:::

What happens if you make the loop only a few cycles long? Even a tiny mismatch then repeats more than a hundred times per second, adding a buzz to the note.

### Changing dynamics

CLAUDE: this should be greatly condensed, down to like two paragraphs. forget about explaining the low pass in detail. organization: (1) want to control loudness from [0, 1] (cut velocity for now since we haven't introduced), simple way is to map [eps, 1] to [-80, 0] dB and then map 0 to -inf dB, (2) show final code example with `clarinet(pitch, duration, loudness)`, (3) mention very briefly at the end that readers can also explore low pass filtering as a function of loudness 

The final musical property we will control is a note's {vocab}`dynamics`: how loudly it is played. Synthesizers typically express dynamics as a {vocab}`velocity` $v \in (0, 1]$, named after the speed with which a key is struck on a keyboard. (We will meet this convention again when we study MIDI in [Chapter 16](../16-compression-midi).) The simplest way to change dynamics is to multiply the note by $v$:

:::{audio-list}
{audio}`$v = 0.2$ <./assets/audio-dyn-gain-20.wav>`

{audio}`$v = 0.5$ <./assets/audio-dyn-gain-50.wav>`

{audio}`$v = 1$ <./assets/audio-dyn-gain-100.wav>`

The saxophone at three velocities, changing only its amplitude.
:::

Something sounds off: the softer notes sound like the same loud note heard from farther away, rather than a saxophonist playing softly. On real instruments, dynamics change timbre as well as loudness. Playing louder disproportionately strengthens the upper harmonics, so loud notes sound brighter and soft notes sound darker. We can imitate this with a low-pass filter whose cutoff frequency increases with velocity. Since our perception of frequency is logarithmic (recall {prf:ref}`def-step`), we raise the cutoff _exponentially_ with velocity, from a dark $f_\text{lo}$ at $v = 0$ to a bright $f_\text{hi}$ at $v = 1$:

$$f_c(v) = f_\text{lo} \cdot \left(\frac{f_\text{hi}}{f_\text{lo}}\right)^{v}.$$

With $f_\text{lo} = 1$ kHz and $f_\text{hi} = 12$ kHz, the cutoff at velocities $0.2$, $0.5$, and $1$ is about $1.6$, $3.5$, and $12$ kHz. For the filter itself, we use the second-order low-pass filter from Robert Bristow-Johnson's Audio EQ Cookbook {cite}`bristowjohnson2016cookbook`, which we used for subtractive synthesis in [Chapter 9](../09-filters):

:::{audio-list}
{audio}`$v = 0.2$ (cutoff 1.6 kHz) <./assets/audio-dyn-filter-20.wav>`

{audio}`$v = 0.5$ (cutoff 3.5 kHz) <./assets/audio-dyn-filter-50.wav>`

{audio}`$v = 1$ (cutoff 12 kHz) <./assets/audio-dyn-filter-100.wav>`

The saxophone at the same three velocities, now changing both its amplitude and its brightness.
:::

:::{figure}
![Overlaid amplitude spectra, in decibels from 0 to 8 kHz, of the saxophone note at velocities 0.2 (blue), 0.5 (orange), and 1.0 (red). All three show harmonic peaks at multiples of about 523 Hz. The softer the velocity, the lower the peaks overall and the faster the upper harmonics fall away: at velocity 0.2 they fade out above about 4 kHz, while at velocity 1.0 they remain visible up to 8 kHz.](./assets/fig-dynamics.png)

Spectra of the saxophone note at three velocities, with both gain and low-pass filtering. Softer notes are quieter overall, and their upper harmonics fall away faster, as on a real instrument played softly.
:::

Putting all three techniques together, [code/sampler.py](./code/sampler.py) implements a complete sample-based saxophone: an instrument function `sax(pitch, duration, velocity)` built from the single C5 recording. For each note, it (1) repitches the recording, (2) loops its sustain to lengthen the note (or fades it out early to shorten it), and (3) applies dynamics. One subtlety is that repitching moves the loop points. After we read the recording $2^{k/12}$ times faster, a loop that started $t_s$ seconds into the original now starts $\frac{t_s}{2^{k/12}}$ seconds into the repitched note. Here is a short phrase played by our sampled saxophone:

:::{audio}
[A phrase played by the sample-based saxophone](./assets/audio-sampler-phrase.wav)

Four notes (G4, C5, E5, and G5) at increasing velocities, with the final note held for six seconds by looping its sustain. Every note comes from the same C5 recording.
:::

## Summary

- In this chapter, "sampling" means lifting a clip of audio, a _sample_, from one recording and reusing it in another context. A sample is a contiguous chunk $[x[m], \ldots, x[m + M - 1]]$ of a recording, whose offset $m \in \{0, \ldots, N - M\}$ and length $M$ are usually chosen by ear rather than procedurally.
- {vocab}`Sequencing` plays samples back in new orders and with new timing. In Pyquist, a sequence of samples is just a {pyquist}`Score` whose instrument returns samples, from a chopped breakbeat to the grid of a {vocab}`drum machine`.
- {vocab}`Sample-based synthesis` turns recordings of an instrument into a playable instrument. It is realistic, cheap to compute, and easy to implement, but it uses a lot of memory and offers limited control over high-level musical properties.
- **Pitch**: resampling a recording by the ratio $\frac{T_1}{T_2} = 2^{k/12}$ shifts its pitch by $k$ steps, but also scales its duration by $2^{-k/12}$. {vocab}`Multisampling` keeps $|k|$ small, for realism.
- **Duration**: a {vocab}`sustain loop` lengthens a note while preserving its attack and release. Good loops span a whole number of cycles, $c = f_0 (t_e - t_s)$, and a {vocab}`crossfade` smooths over the remaining discontinuity at each wrap.
- **Dynamics**: scaling a note by its {vocab}`velocity`, while low-pass filtering it with a cutoff that rises exponentially with velocity, imitates how real instruments brighten as they are played louder.

## Questions for the reader

::::{exercise}
**Extracting a sample.** A recording at $f_s = 48{,}000$ Hz lasts exactly $3$ seconds.

1. How many audio samples $N$ does it contain?
1. You want a sample that starts $1.2$ seconds into the recording and lasts $250$ ms. What are its offset $m$ and length $M$?
1. For this length $M$, what is the largest valid offset $m$? How many seconds into the recording does that sample start?

:::{solution}

1. $N = 144{,}000$
1. $m = 57{,}600$ and $M = 12{,}000$
1. $m = 132{,}000$, which starts $2.75$ seconds into the recording

:::
::::

::::{exercise}
**Repitching.** You have a $2$-second recording of A4 ($440$ Hz), and you want to shift it up $3$ steps to C5.

1. By what factor $\frac{T_1}{T_2}$ must you speed up its playback?
1. What is the fundamental frequency of the result?
1. How long does the result last?

:::{solution}

1. $2^{3/12} \approx 1.189$
1. $\approx 523.3$ Hz
1. $\approx 1.68$ seconds

:::
::::

::::{exercise}
**Multisampling.** A sampled piano records each of its $88$ keys at $4$ different velocities. Each recording lasts $10$ seconds, in stereo, at $f_s = 48{,}000$ Hz, with $24$-bit ($3$-byte) audio samples.

1. How much storage does the library need, in gigabytes?
1. To save space, you instead record every third key (keys $1, 4, 7, \ldots, 88$), and you play each of the other keys by repitching the closest recording. How many keys do you record, how much storage does the library need now, and what is the largest pitch shift $|k|$, in steps, that you will ever need?

:::{solution}

1. $\approx 1.01$ GB
1. $30$ keys, $\approx 0.35$ GB, and $|k| \leq 1$

:::
::::

::::{exercise}
**Counting loops.** A recording of a note lasts $T = 0.65$ seconds, and its sustain loop spans $t_s = 0.15$ to $t_e = 0.40$ seconds. How many times must the loop repeat to play a note lasting $d = 2.4$ seconds?

:::{solution}
$8$ times
:::
::::

::::{exercise}
**Choosing loop points.** A sustained note with a fundamental frequency of $f_0 = 440$ Hz is recorded at $f_s = 44{,}100$ Hz.

1. How many audio samples long is one cycle of the fundamental?
1. What is the shortest loop that spans both a whole number of cycles _and_ a whole number of audio samples? Give its length in cycles, in audio samples, and in milliseconds.

:::{solution}

1. $\approx 100.23$ audio samples
1. $22$ cycles, which is exactly $2{,}205$ audio samples, or $50$ ms

:::
::::

CLAUDE: cut this one
::::{exercise}
**Crossfade constraints.** You place a sustain loop very early in a note, starting at $t_s = 20$ ms, and request a $30$ ms crossfade. Why does the crossfade from this chapter fail? State the condition that the loop start and the crossfade length must satisfy.

:::{solution}
The crossfade blends in the audio just _before_ the loop start, so it needs $30$ ms of audio before $t_s$, but only $20$ ms exists. The loop must start at least one crossfade length into the recording, that is, $s \geq L$.
:::
::::

CLAUDE: make this question standalone. don't make the reader refer back to the drum machine.
::::{exercise}
**Drum machine tempo.** The drum machine from this chapter plays one column per sixteenth note, or four steps per beat.

1. At a tempo of $90$ BPM, how long does each step last?
1. At what time, in seconds, does an `X` in column $12$ play?
1. What value of `bpm` should you pass to {pyquist}`BasicMetronome`?

:::{solution}

1. $\approx 166.7$ ms
1. $2$ seconds
1. $360$

:::
::::

CLAUDE: cut this
:::{exercise}
**Dynamics.** Explain why scaling the amplitude of a recorded note is not enough to convincingly imitate the same note played more softly. What does adding a low-pass filter contribute? Why should its cutoff frequency change _exponentially_, rather than linearly, with velocity?
:::

## Musical examples

### Pierre Schaeffer and Pierre Henry - _Symphonie pour un homme seul_ (1950)

A landmark of _musique concrète_, the movement that first made music by collaging recorded sounds. Schaeffer and Henry built this "symphony for one man alone" from recordings of the human body (breathing, footsteps, voices, and whistling) alongside fragments of instrumental sounds. In this era, sampling and sequencing meant physically manipulating recordings on magnetic tape, decades before digital samplers existed.

<iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/MOYNFu45khQ" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

### Tracklib - _The Most Iconic Hip-Hop Sample of Every Year_ (1973–2023)

Hip-hop artists pioneered the modern practice of sampling and sequencing, beginning with DJs who extended the drum breaks of funk and soul records by looping them on two turntables. This video surveys fifty years of the genre through one iconic sample per year, showing how producers have chopped, looped, and re-sequenced fragments of older recordings into new music.

<iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/hIGNaDk9eIA" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

### The Avalanches - _Frontier Psychiatrist_ (2000)

The Avalanches' debut album, _Since I Left You_, is built almost entirely from samples. The track _Frontier Psychiatrist_ sequences dialogue from a comedy sketch of the same name over an orchestral backing sampled from an Enoch Light record, among [dozens of other sampled fragments](https://www.whosampled.com/The-Avalanches/Frontier-Psychiatrist/samples).

<iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/qLrnkK2YEcE" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

### Herbie Hancock and Quincy Jones - _Fairlight CMI_ (1984)

Watch Herbie Hancock and Quincy Jones experiment with the Fairlight CMI, the earliest commercially available digital sampler. Each key of its keyboard plays back a recorded sample, repitched by changing its playback speed, which is exactly the technique of this chapter.

<iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/n6QsusDS_8A" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

### clipping. - _Williams Mix_ (2014)

The experimental hip-hop group clipping. closes its album _CLPPNG_ with a version of [John Cage's _Williams Mix_](https://en.wikipedia.org/wiki/Williams_Mix) (1952), a pioneering tape piece built from hundreds of fragments of recorded sound, spliced together according to a score that Cage composed with chance operations. Computer musician Tom Erbe, who recreated Cage's piece in software from its original score, realized this version using fragments of the album's own tracks as source material. The result is sampling and sequencing, with the sequence dictated by Cage's score.

<iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/_YmTrYYUVzc" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
