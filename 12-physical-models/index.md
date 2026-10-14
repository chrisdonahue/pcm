---
title: "Chapter 12: Physical Modeling"
---

CLAUDE: at a high-level, need a bit more organizational structure throughout here. also, some sections could be made a bit more concise. no need to go overboard with summarization, it's already _okay_, but just a little long winded and rambly and sometimes redundant at times

# Physical Modeling

CLAUDE: type mismatch? these are not effects of _sound_, they are effects of _acoustics_... exposition here should be more like: we have modeling musical acoustics _indirectly_, synthesizing its emergent properties such as harmonics. now we want to model those acoustics _directly_, which should give rise to these same properties
So far in this book, we have synthesized sound by modeling its _effects_: the properties of musical sounds that we can observe and measure. Additive synthesis builds up a sound from the harmonics that we observe in its spectrum, and an ADSR envelope imitates the shape that we observe in its waveform. In this chapter, we instead model the _causes_ of musical sound: the physical instruments that produce it.

CLAUDE: this is a useless margin note at this point. get rid of it, or move it later once we talk about acoustic systems (open-closed I think?) that it relates to
:::{margin} An early physical model
The singing voice of _Daisy Bell_ (1961), one of the musical examples in [Chapter 4](../04-score-timbre), came from one of the earliest physical models in computer music. John L. Kelly Jr. and Carol Lochbaum simulated the human vocal tract as a chain of tubes.
:::

CLAUDE: Chapter 11 (sampling) is the wrong anchor here. anchor on FM/additive instead
This is the idea behind {vocab}`physical modeling synthesis`: simulating the acoustics of an instrument, and listening to the result. In other words, rather than imitating how an instrument _sounds_, we simulate how it _works_. As we saw in [Chapter 11](../11-sampled-synthesis), imitating the sound of a real instrument property by property is extremely difficult. In a faithful physical model, these properties instead _emerge_ from the simulated physics. Here are a few examples of how realistic physical models can sound:

:::{audio-list}
{audio}`Plucked strings, synthesized on a NeXT computer (1989) <./assets/audio-jos-strings.wav>`

CLAUDE: can you find any more info about what physical modeling system/year this sound came from?
{audio}`An electric guitar, heard through its bass pickup <./assets/audio-jos-electric-guitar.wav>`

{audio}`An oboe and a bassoon, synthesized on the Yamaha VL1 (1994) <./assets/audio-jos-oboe-bassoon.wav>`

Three physical models, from Julius O. Smith III's [collection of sound examples](https://ccrma.stanford.edu/~jos/waveguide/Sound_Examples.html).
:::

Physical models have numerous use cases:

1. **Synthesis** of realistic instruments, or of imaginary instruments that would be impossible to build, like a string a kilometer long.
1. **Analysis** of recorded sound, by estimating the physical parameters of a model that best reproduce a recording.
1. **Instrument design**, by prototyping an instrument in simulation before building it.

CLAUDE: "most famous physical model of all" sounds so sophomoric. frame it as a case study instead: we will explore these techniques within the context of building a model of a plucked string, which formed the basis of early research on physical models.
Physical modeling is a family of techniques that share common building blocks. In this chapter, we will assemble these building blocks into the most famous physical model of all: a plucked string. But to simulate the physics of an instrument, we must first understand that physics.

This chapter is only a cursory overview of a field that has been researched for decades. Readers who want to go further should consult [Julius Smith's _Physical Audio Signal Processing_ {cite}`smith2010physical`](https://ccrma.stanford.edu/~jos/pasp/), a thorough treatment that is freely available online.

## Musical acoustics

Recall from [Chapter 1](../01-sound-audio) that sound is what happens when something in the world moves and disturbs the air around it, like a plucked guitar string. Musical instruments are carefully designed to vibrate in particular ways. In this section, we study the physics of these vibrations, which we will refer to as _musical acoustics_. We focus on waves on a string, which will be the basis of our physical model, and then briefly look at other kinds of instruments.

### Waves in a medium

A wave transfers energy from one point to another through a medium, like a string or the air. As a wave passes by, each particle of the medium is displaced temporarily, and then returns to the same resting position. In other words, it is the _disturbance_ that travels, not the medium itself. For example, when you flick one end of a long rope, a pulse travels down the rope, but the rope itself stays put.
CLAUDE: this is super confusing... doesn't pass a sanity check. the rope doesn't stay put, it moves! I think the point is that it stays put in one dimension but travels in a different one? or that it returns to resting position after deviating? not sure how to phrase it, but regardless, the current phrasing is misleading if not wrong

Three behaviors of waves are critical for musical acoustics:

1. **Propagation.** A wave travels through a medium at a speed $v$, measured in ${unit}`meters,second`$ (m/s), which depends on the properties of the medium. For example, sound travels through air at about $343$ m/s, and waves travel along the strings of a guitar at roughly $100$ to $430$ m/s, depending on its tension.
1. **Superposition.** When two waves traveling in opposite directions meet, they pass through each other undisturbed. While they overlap, the displacement of the medium at each point is simply the sum of the displacements of the two waves. This principle, called {vocab}`superposition`, is a physical example of the _linearity_ that we studied in [Chapter 9](../09-filters).
1. **Reflection.** When a wave reaches a rigid boundary, like the fixed end of a string, it reflects back with opposite polarity: a pulse that displaced the string upward returns displacing it downward. Intuitively, the boundary pushes back on the string with an equal and opposite force, as in Newton's third law.

:::{figure}
![An animation in three rows, each showing a horizontal string. Top: a single bell-shaped pulse travels from left to right along the string. Middle: two pulses travel toward each other from opposite ends, momentarily merge into a single pulse twice as tall, and continue on unchanged, with dashed gray outlines tracing each pulse on its own. Bottom: a pulse travels right toward a fixed end, drawn as a dark vertical bar, and returns traveling left, flipped upside down.](./assets/fig-waves.gif)

Three behaviors of waves on a string: propagation (top), superposition (middle), and reflection (bottom). In the middle row, the dashed gray lines trace each pulse on its own, and the solid line is their sum.
:::

### Standing waves

What happens when we pluck a string that is fixed at both ends, like on a guitar? The pluck sends waves traveling in both directions along the string. The waves reflect off the ends of the string, again and again, so at any moment, the string carries waves traveling both to the right and to the left. By superposition, the shape of the string is the sum of the two.

CLAUDE: just terrible organization. describe and show the standing wave first, then start talking about its wavelength. bottom line up front, then details

CLAUDE: this is really confusing. what does a "sinusoidal wave" mean here? is it referring to the basic sinusoid students will have studied, or some instantiation of it in the physical world? not at all obvious why a sinusoidal wave translates to space, we're only familiar with it oscillating in time so far...
To analyze this sum, let's consider sinusoidal waves. A sinusoidal wave repeats in space as well as in time, and the distance over which it repeats is its {vocab}`wavelength`.

:::{prf:definition} Wavelength
:label: def-wavelength
The _wavelength_ $\lambda$ of a sinusoidal wave is the distance that it travels during one cycle. For a wave with frequency $f$ traveling at speed $v$,

$$\lambda \left[{unit}`meters,cycle`\right] = \frac{v \left[{unit}`meters,second`\right]}{f \left[{unit}`cycles,second`\right]}.$$
:::

A sinusoidal wave with wavelength $\lambda$ and frequency $f$ traveling to the right has displacement $\sin\!\big(2\pi(\tfrac{x}{\lambda} - f t)\big)$ at position $x$ (in meters) and time $t$ (in seconds). Its peaks move to the right at a speed of $\lambda \cdot f = v$, consistent with {prf:ref}`def-wavelength`. The same wave traveling to the left has displacement $\sin\!\big(2\pi(\tfrac{x}{\lambda} + f t)\big)$. Using the identity $\sin a + \sin b = 2 \sin\frac{a + b}{2} \cos\frac{a - b}{2}$, their sum is

$$\sin\!\Big(2\pi\big(\tfrac{x}{\lambda} - f t\big)\Big) + \sin\!\Big(2\pi\big(\tfrac{x}{\lambda} + f t\big)\Big) = 2 \sin\!\Big(\frac{2\pi x}{\lambda}\Big) \cos(2\pi f t).$$

Notice that space and time have separated in the result. The sum is a fixed shape in space, $\sin(2\pi x / \lambda)$, whose amplitude oscillates in time, $\cos(2\pi f t)$. So the sum does not travel at all. Instead, it oscillates in place, and we call it a {vocab}`standing wave`. Wherever $\sin(2\pi x / \lambda) = 0$, which happens every half wavelength, the string never moves. These points are called {vocab}`nodes`. Halfway between the nodes are the {vocab}`antinodes`, where the string oscillates with the largest amplitude:

:::{figure}
![An animation in three rows. Top: a blue sinusoid travels to the right. Middle: an orange sinusoid of the same wavelength travels to the left. Bottom: their purple sum oscillates up and down in place without traveling. It always passes through zero at fixed points marked with black dots, labeled nodes, and swings the most at points marked with gold dots, labeled antinodes, halfway between them.](./assets/fig-standing-wave.gif)

Two sinusoids traveling in opposite directions (top and middle) sum to a standing wave (bottom). The nodes (black) never move, and the antinodes (gold) oscillate with the largest amplitude.
:::

The video below, from acoustician Daniel A. Russell, shows the motion of a plucked string:

<iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/_X72on6CSL0" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

On a string of length $L$ with both ends fixed, the ends cannot move, so they must be nodes. Since nodes occur every half wavelength, a standing wave fits on the string only if the string is a whole number of half wavelengths long:

$$L = i \cdot \frac{\lambda_i}{2}, \qquad \text{so} \qquad \lambda_i = \frac{2L}{i} = \left[2L, L, \tfrac{2L}{3}, \ldots\right] \quad \text{for } i = 1, 2, 3, \ldots$$

What frequencies do these wavelengths correspond to? Rearranging {prf:ref}`def-wavelength`,

$$f_i = \frac{v}{\lambda_i} = i \cdot \frac{v}{2L}.$$

So the lowest frequency is $f_1 = \frac{v}{2L}$, and every other frequency is a whole-number multiple of it, $f_i = i \cdot f_1$. These are exactly the {prf:ref}`harmonics <def-harmonic>` of [Chapter 3](../03-additive-synthesis)! **A string fixed at both ends vibrates at a fundamental frequency $f_1$ and its harmonics.**

:::{figure}
![Three rows, each showing a horizontal string between two fixed black dots, with the outline of a standing wave drawn in dark red. An arrow above the top row marks the length L of the string. Top: a single lobe, labeled lambda 1 equals 2L and f1 equals v over 2L. Middle: two lobes with a node in the middle, labeled lambda 2 equals L and f2 equals 2 f1. Bottom: three lobes with two nodes, labeled lambda 3 equals 2L over 3 and f3 equals 3 f1.](./assets/fig-string-modes.png)

The first three standing waves on a string of length $L$ with both ends fixed. Each fits a whole number of half wavelengths between the ends.
:::

For example, the second-lowest string of a guitar vibrates along a length of about $L = 0.65$ meters, and is tuned to a fundamental frequency of $f_1 = 110$ Hz. So its longest wavelength is $\lambda_1 = 2L = 1.3$ meters, and its waves travel at $v = \lambda_1 \cdot f_1 = 1.3 \cdot 110 = 143$ m/s.

:::{margin}
For an ideal string, $v = \sqrt{\tau / \mu}$, where $\tau$ is the tension of the string in newtons and $\mu$ is its mass per unit length in kilograms per meter. Tuning a guitar adjusts $\tau$, and its lower strings are thicker, so $\mu$ is larger.
:::

This also explains how to play different pitches on a string. A guitarist presses a string against a _fret_ to shorten the vibrating part of the string, which decreases $L$ and raises $f_1$. To change the frequency of a string _without_ changing its length, we can change the speed $v$ instead, by changing the string's tension or its material. Tightening a string raises its pitch, and thicker, heavier strings vibrate at lower pitches.

### Modes of oscillation

Each standing wave that an object supports is called a {vocab}`mode of oscillation`. When we pluck a string, we don't excite just one mode. The string vibrates in many modes at once, each at its own frequency, and by superposition, its motion is the sum of all of them. So a plucked string produces a sum of sinusoids at harmonic frequencies, just like the Fourier series of [Chapter 3](../03-additive-synthesis). In previous chapters, we modeled this sum directly. Now we see where it comes from.

Modes are not always the same as harmonics, though. Consider wind instruments, whose sound comes from a column of air vibrating inside a tube. At an open end of a tube, the air is free to move, so an open end is an antinode. At a closed end, the air cannot move, so a closed end is a node. A tube open at both ends, roughly like a flute, has antinodes at both ends, and supports the same wavelengths as a string, $\lambda_i = \frac{2L}{i}$. But a tube closed at one end, roughly like a clarinet, has a node at one end and an antinode at the other. So its length must be an _odd_ number of quarter wavelengths:

$$L = (2i - 1) \cdot \frac{\lambda_i}{4}, \qquad \text{so} \qquad \lambda_i = \frac{4L}{2i - 1} = \left[4L, \tfrac{4L}{3}, \tfrac{4L}{5}, \ldots\right].$$

Its frequencies are $f_i = (2i - 1) \cdot \frac{v}{4L}$: only the _odd_ harmonics of a fundamental frequency $\frac{v}{4L}$, which is an octave below that of an open tube of the same length.

:::{figure}
![A three-by-three grid. The columns show a string with fixed ends, a tube open at both ends, and a tube closed at its left end. The rows show modes 1 through 3. Each cell outlines a standing wave in dark red, labeled with its wavelength lambda and harmonic number h. The string and the open tube both have wavelengths 2L, L, and 2L over 3, with h equal to 1, 2, and 3, but the string has nodes at its ends while the open tube has antinodes there. The closed tube has a node at its closed end and an antinode at its open end, with wavelengths 4L, 4L over 3, and 4L over 5, and h equal to 1, 3, and 5.](./assets/fig-modes-table.png)

The first three modes of a string and of two kinds of tubes, labeled with their wavelengths $\lambda$ and harmonic numbers $h$. For the tubes, the curves show how far the air moves. The second and third modes of the closed tube are its third and fifth harmonics.
:::

In two dimensions, like a drumhead or a metal plate, modes become more intricate. The frequencies of these modes are generally _not_ whole-number multiples of the lowest one, which is part of why many percussion instruments have a less definite pitch than strings and winds. In the video below, also from Daniel A. Russell, particles sprinkled on a vibrating square plate collect along its _nodal lines_, where the plate stays still, revealing the shape of each mode. These shapes are called _Chladni patterns_, after Ernst Chladni, who studied them in the late 18th century.

<iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/6wmFAwqQB0g" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

Instruments vibrate in three dimensions, too. For example, the wooden body of a guitar has its own modes of oscillation, which help to amplify particular frequencies of the strings' vibrations and radiate them into the air.

:::{seealso}
To learn more about the acoustics of musical instruments, explore Daniel A. Russell's [acoustics and vibration animations](https://www.acs.psu.edu/drussell/demos.html), including the modes of drumheads and guitar bodies.
:::

## Physical modeling

Now that we understand some of the physics of a vibrating string, let's simulate it _in silico_, that is, on a computer. A guitar string is fixed at two ends: the _nut_, near the tuning pegs, and the _bridge_, on the body of the guitar. Rather than simulating the full physics of the string, we will simulate each of its physical properties with a simple synthesis technique that captures its essential behavior:

:::{figure}
![A plucked string, drawn as a black line pulled up into a triangle by a pick near its right end, stretched between the nut on the left and the bridge on the right. A green arrow below marks its length L. Four color-coded callouts each pair a physical property with a simulation. Excitation (the pluck), pointing at the pick, maps to a burst of noise, in blue. Propagation along the string, pointing at the length arrow, maps to delay, in green. Reflection at the ends, pointing at the nut, maps to feedback, in orange. Damping (friction), pointing at the string, maps to a low-pass filter, in purple.](./assets/fig-physical-model-map.png)

A physical model of a plucked string. Each callout pairs a physical property of the string with the synthesis technique that simulates it.
:::

| Physical property | Simulation |
| ----------------- | ---------- |
| Waves take time to travel along the string | A delay line |
| Waves reflect at the ends of the string | Feedback |
| Friction damps the waves, especially at high frequencies | Attenuation and a low-pass filter |
| A pluck excites the string at many frequencies at once | A burst of noise |

In the rest of this section, we build up this model one physical property at a time: (1) propagation and reflection, (2) damping, and (3) excitation. The result will be a classic physical model called the Karplus-Strong algorithm.

(sec-feedback-delay)=

### Propagation via feedback delay

Waves take time to travel. To simulate this, we use one of the simplest filter imaginable, one that simply delays its input. A {vocab}`delay line` of $M$ samples outputs its input $M$ samples later:

$$y[n] = x[n - M].$$

Recall from [Chapter 9](../09-filters) that in signal-flow diagrams, we draw a delay of $M$ samples as a block labeled $z^{-M}$.

How long should the delay line be? Suppose a wave travels $L$ meters at a speed of $v$ m/s, which takes $\frac{L}{v}$ seconds. For example, a wave traveling $L = 1$ meter at $v = 400$ m/s takes $2.5$ ms. To simulate this, we convert seconds to samples. Working through the units,

CLAUDE: expand L and 1/v into additional terms in the product, don't just pack them into one fraction.
$$M \left[{unit}`samples`\right] = \frac{L \left[{unit}`meters`\right]}{v \left[{unit}`meters,second`\right]} \cdot f_s \left[{unit}`samples,second`\right] = \frac{f_s \cdot L}{v}.$$

At $f_s = 44{,}100$ Hz, our example wave takes $M = 44{,}100 \cdot \frac{1}{400} = 110.25$ samples. But a delay line can only delay by a whole number of samples, so we compromise by rounding: $M = \mathrm{round}(\frac{f_s \cdot L}{v}) = 110$. Our simulated wave arrives a quarter of a sample early, as if it traveled about $2$ mm less than it should. As we will see shortly, a shorter trip means a higher pitch.

A delay line alone simulates a wave that travels from one point to another, once. On a string, however, waves reflect at the ends and keep traveling back and forth. To simulate this, we _feed back_ the output of the delay line into its input, where it adds to any new input, just as the reflected waves superimpose on the string:

$$y[n] = x[n] + y[n - M].$$

:::{figure}
![A signal-flow diagram for y[n] = x[n] + y[n - M]. The input x[n] enters a summing junction, whose output is y[n]. The output is tapped and fed back through a block labeled z to the minus M into the summing junction.](./assets/fig-feedback-delay.png)

A feedback delay line. The output $y[n]$ is delayed by $M$ samples and added back into the input.
:::

Each trip around this loop simulates one round trip along the string, from the bridge to the nut and back. Along the way, the wave reflects twice, and each reflection inverts its polarity. So the wave returns with its original polarity, and the feedback simply adds it back in.

How should we choose $M$ to produce a particular fundamental frequency $f$? Recall that a string of length $L$ has a fundamental frequency of $f = \frac{v}{2L}$. Each trip around the loop covers a distance of $2L$, so by the formula above, $M = \frac{f_s \cdot 2L}{v}$. Substituting $f = \frac{v}{2L}$,

$$M = \mathrm{round}\left(\frac{f_s}{f}\right).$$

Again, the units make this clear: $\frac{f_s}{f}$ has units of ${unit}`samples,second` \cdot {unit}`seconds,cycle` = {unit}`samples,cycle`$. **The length of the delay line is simply the fundamental period, in samples.** Notice that the length $L$ and speed $v$ of the string have dropped out entirely. To tune a feedback delay line, we only need the target frequency.

CLAUDE: need to add a subsection on circular buffer sooner rather than later in this section. basically, as early as it can be introduced, as it's not clear at this point why we're calling this a delay _line_, rather than just _delay_. so the flow is: purpose of feedback delay in the context of instrument modeling -> implementation w/ circular buffer -> additional stuff like configuring M.

Rounding has a price, though. A feedback delay line can only produce the frequencies $\frac{f_s}{M}$ for whole numbers $M$. At low frequencies, $M$ is large, and neighboring values of $M$ produce nearly identical frequencies. For example, at $f_s = 44{,}100$ Hz, $M = 100$ produces $441$ Hz and $M = 101$ produces about $436.6$ Hz, so we can tune to $440$ Hz with an error of just $1$ Hz. But at high frequencies, $M$ is small, and the gaps between neighbors grow. For example, $M = 11$ produces about $4009$ Hz and $M = 10$ produces $4410$ Hz, a ratio of $1.1$, or more than one and a half {prf:ref}`steps <def-step>`. **The rounding error grows as frequency increases:**

:::{figure}
![A plot of frequency versus desired frequency, both from 0 to about 8000 Hz. A dashed gray diagonal line shows the desired frequency. A red line, the actual frequency f_s over round of f_s over f, follows the diagonal closely at low frequencies, but becomes a staircase with ever larger steps at higher frequencies.](./assets/fig-delay-quantization.png)

The frequencies that a feedback delay line can produce at $f_s = 44{,}100$ Hz when we round its delay to a whole number of samples (red), compared to the desired frequencies (dashed gray).
:::

:::{margin}
Jaffe and Smith {cite}`jaffe1983extensions` tuned the delay line more precisely with an _all-pass_ filter, which leaves the amplitude of every frequency untouched, but can delay a signal by a fraction of a sample.
:::

CLAUDE: is this actually true? I don't entirely understand the tradeoffs between fractional delay lines and the Jaffe/Smith extensions w/ all pass filters. 

Practical physical models avoid this problem with _fractional_ delays, which interpolate between neighboring samples, much like the wavetables of [Chapter 3](../03-additive-synthesis). In this chapter, we will simply round.

CLAUDE: this can't be just an side. needs to be its own section w/ implementation code example
:::{admonition} Aside: Delay lines as circular buffers
:class: note
The code examples in this chapter store their entire output signal, so they can look up $y[n - M]$ directly. A real-time synthesizer producing an endless stream of audio (as in {ref}`Chapter 10 <sec-realtime-processing>`) can't store its entire output, and it doesn't need to. The feedback only ever needs the last $M$ samples. So in practice, a delay line is implemented as a {vocab}`circular buffer`: an array of $M$ samples, with an index that wraps around it. At each time step, we read the oldest sample in the array, $y[n - M]$, overwrite it with the newest sample, $y[n]$, and advance the index by one, wrapping around to the start of the array at the end. This takes a constant amount of memory, however long the sound.
:::

CLAUDE: need subsection heading here for comb filter

Now, what does a feedback delay line do to a sound? It is a {prf:ref}`recursive filter <def-recursive>`, and therefore LTI, so recall from [Chapter 9](../09-filters) that its impulse response tells us everything about it. Let's feed it a unit impulse $\delta = [1, 0, 0, \ldots]$ and compute the output one sample at a time. For the first $M$ samples, the feedback path contributes nothing, since $y[n - M] = 0$ for $n < M$. After that, each sample repeats the sample $M$ samples earlier:

CLAUDE: would be a bit more intuitive to students to see the second 1 appear here at h[M] (moreso than the equality of h[n] and h[n-M])
$$
\begin{aligned}
h[0] &= \delta[0] = 1, \\
h[n] &= \delta[n] = 0 \quad \text{for } 0 < n < M, \\
h[n] &= \delta[n] + h[n - M] = h[n - M] \quad \text{for } n \geq M.
\end{aligned}
$$

So the impulse response is $1$ at every multiple of $M$, and $0$ everywhere else. It is an impulse train with a period of $M$ samples, which never decays.

What is its frequency response? Recall from {ref}`Chapter 7 <sec-sampling-and-frequency>` that the spectrum of an impulse train is itself an impulse train. An impulse train with a period of $M$ samples, or $\frac{M}{f_s}$ seconds, has spikes in its spectrum every $\frac{f_s}{M}$ Hz. So the feedback delay line boosts the frequencies at whole-number multiples of $\frac{f_s}{M}$, and rejects the frequencies in between. Its magnitude response looks like the teeth of a comb, so it is called a {vocab}`comb filter`:

:::{figure}
![Two plots. Left: the impulse response over 25 milliseconds, red stems of height 1 repeating every 2.27 milliseconds. Right: its magnitude spectrum in decibels from 0 to 4500 Hz, a series of sharp, evenly spaced peaks at multiples of 441 Hz, marked by faint gray vertical lines, with deep valleys in between.](./assets/fig-comb.png)

The impulse response of a feedback delay line with $M = 100$ at $f_s = 44{,}100$ Hz (left) is an impulse train with a period of $100$ samples, about $2.27$ ms. Its spectrum (right, computed from the first $0.25$ seconds of the impulse response) is a comb with teeth at multiples of $\frac{f_s}{M} = 441$ Hz.
:::

CLAUDE: why is this coming in now? maybe we should just talk about this in the next section when we talk about attenuation? for now, don't need to define the feedback comb filter, just focus on the emergence of the harmonics. comb filter can come when we talk about damping
In general, a comb filter can also scale its feedback by a gain $g$, which we will put to use in the next section. So far, $g = 1$.

:::{prf:definition} Feedback comb filter
:label: def-feedback-comb-filter
A _feedback comb filter_ with a delay of $M \in \mathbb{Z}_{>0}$ samples and a gain $g$ is the recursive filter

$$y[n] = x[n] + g \cdot y[n - M].$$
:::

Aside from the tooth at $0$ Hz, the teeth of the comb sit at $\frac{f_s}{M}, \frac{2 f_s}{M}, \frac{3 f_s}{M}, \ldots$, which are exactly the harmonics of the fundamental frequency $\frac{f_s}{M}$ that we tuned the delay line to. **On its own, a feedback delay line resonates at a fundamental frequency and its harmonics, just like a string.** Intuitively, a sinusoid at one of these frequencies fits a whole number of cycles into the loop. So it returns in phase with itself, and adds constructively on every trip. Other frequencies return out of phase, and cancel themselves out. Comb filters appear throughout computer music, and we will meet delay lines again in [Chapter 13](../13-delay-effects).

The code below implements a feedback delay line, tunes it to $220$ Hz, and feeds it a unit impulse. It plots the first $30$ ms of the impulse response, an impulse train, and the spectrum of the impulse response, a comb. Listen for a buzzy, sustained tone at $220.5$ Hz, the closest frequency to $220$ Hz that a whole number of samples allows:

CLAUDE: this is good in scope but should use a basic circular buffer (not a complicated class or something, just define memory of length M and update the pointer as the loop goes). I know it's not necessary for this offline setting, but it's an important pedagogical exercise for students
:::{interactive}[notebooks/feedback-delay.ipynb]
:::

From a single impulse, the feedback delay line produced a sustained, pitched tone. The delay gave us a pitch, and the feedback gave us a harmonic spectrum. But unlike a real string, the tone never decays. That brings us to our next physical property.

### Damping via filters

Real strings don't vibrate forever. On every trip along the string, a wave loses a little energy: to friction with the air, to friction inside the string, and to the body of the instrument, which radiates it into the air as sound. Our feedback delay line, $y[n] = x[n] + y[n - M]$, loses no energy at all. For example, with $M = 2$, its impulse response is $h = [1, 0, 1, 0, 1, 0, \ldots]$, which never decays.

To simulate this loss of energy, we _attenuate_ the signal on every trip around the loop, by multiplying it by a gain $0 < g < 1$:

$$y[n] = x[n] + g \cdot y[n - M].$$

:::{figure}
![A signal-flow diagram for y[n] = x[n] + g times y[n - M]. The input x[n] enters a summing junction, whose output is y[n]. The output is tapped and fed back through a block labeled z to the minus M, then through a triangular gain labeled g, into the summing junction.](./assets/fig-feedback-delay-damped.png)

A feedback delay line with attenuation. On every trip around the loop, the signal is multiplied by a gain $g$.
:::

Now, with $M = 2$, the impulse response is $h = [1, 0, g, 0, g^2, 0, g^3, \ldots]$. In general, $h[kM] = g^k$ for $k = 0, 1, 2, \ldots$, and $h$ is zero everywhere else. As we saw in [Chapter 9](../09-filters), a recursive filter like this one is stable for $|g| < 1$, and its impulse response decays exponentially. In the frequency domain, attenuation changes the _sharpness_ of the comb. The teeth stay at whole-number multiples of $\frac{f_s}{M}$, but the smaller the gain $g$, the wider and shallower they become:

:::{figure}
![Two plots. Left: the impulse response over 50 milliseconds for g = 0.8, red stems every 2.27 milliseconds whose heights decay exponentially, following a dashed gray curve. Right: magnitude spectra in decibels from 0 to 2300 Hz for g = 0.95 in purple, g = 0.8 in red, and g = 0.5 in orange, each with peaks at multiples of 441 Hz. The peaks are sharpest and the valleys deepest for g = 0.95, while the curve for g = 0.5 undulates gently.](./assets/fig-comb-damped.png)

With attenuation, the impulse response of a feedback delay line decays exponentially (left, with $M = 100$ and $g = 0.8$). Its spectrum is still a comb with teeth at multiples of $\frac{f_s}{M} = 441$ Hz, but the teeth widen as $g$ decreases (right).
:::

How should we choose $g$? Musically, we want to control the duration of a note. But the duration depends on both $g$ and $M$, because the signal is attenuated once per trip around the loop, and the number of trips per second depends on $M$. Ideally, we would choose a pitch and a duration independently, and compute $g$ from both.

Technically, an exponentially decaying impulse response never reaches zero, so the duration is infinite for any $g > 0$. But in practice, it becomes inaudible long before then. As in [Chapter 9](../09-filters), we will consider a sound to be over once it has decayed by $60$ dB, to $10^{-60/20} = 10^{-3}$ of its initial amplitude. So what gain $g$ makes the impulse response decay by $60$ dB in $T$ seconds?

After $k$ trips around the loop, the amplitude of the impulse response is $g^k$. How many trips does it make in $T$ seconds? Working through the units,

$$k \left[{unit}`trips`\right] = \frac{T \left[{unit}`seconds`\right] \cdot f_s \left[{unit}`samples,second`\right]}{M \left[{unit}`samples,trip`\right]} = \frac{f_s T}{M}.$$

Setting the amplitude after these $k$ trips to $10^{-3}$ and solving for $g$,

$$g^{f_s T / M} = 10^{-3} \quad \Longrightarrow \quad \frac{f_s T}{M} \cdot \log_{10} g = -3 \quad \Longrightarrow \quad g = 10^{-3M / (f_s T)}.$$

More generally, to decay by $D$ decibels in $T$ seconds (with $D < 0$), replace $-3$ with $\frac{D}{20}$.

Notice that $g$ depends on both the duration $T$ and the pitch, via $M$. For example, at $f_s = 44{,}100$ Hz, a note at $220.5$ Hz has $M = 200$, so it makes $\frac{44{,}100}{200} = 220.5$ trips per second. To decay by $60$ dB in $T = 1$ second, it needs $g = 10^{-3/220.5} \approx 0.969$. A note an octave higher makes twice as many trips per second, so to last just as long, it needs a gain closer to $1$, $g = 10^{-3/441} \approx 0.984$.

The code below puts this to use in an instrument, `pluck_like(pitch, duration)`, which tunes a damped feedback delay line to a pitch, computes $g$ from the duration, and excites the delay line with a unit impulse. We use it to render a short sequence of notes with a {pyquist}`Score`, as in [Chapter 4](../04-score-timbre):

:::{interactive}[notebooks/damping.ipynb]
:::

The notes now decay like plucked strings. But they still sound buzzy and artificial, more like a toy than a guitar.

Why? Multiplying by $g$ is, technically, a filter, $y[n] = g \cdot x[n]$. But it scales every frequency by the same amount, so all of the harmonics decay at the same rate. In a real string, the higher harmonics decay much faster than the lower ones, so a plucked note starts bright and then mellows as it rings.

To simulate this, we can add a low-pass filter to the loop, which attenuates higher frequencies more on every trip. The simplest low-pass filter of all is a two-point average, $\frac{1}{2}(x[n] + x[n - 1])$. This is the first filter that we studied in [Chapter 9](../09-filters), scaled by $\frac{1}{2}$, so it scales a sinusoid at frequency $f$ by $|\cos(\pi f / f_s)|$, from $1$ at $0$ Hz down to $0$ at the Nyquist frequency. Placing it in the loop,

$$y[n] = x[n] + g \cdot \tfrac{1}{2}\big(y[n - M] + y[n - M - 1]\big).$$

CLAUDE: the exact frequency response is too in-the-weeds at this point. the spectrogram and high-level view is enough here
On every trip around the loop, a harmonic at frequency $f$ is now attenuated by $g \cdot |\cos(\pi f / f_s)|$. For low harmonics, $|\cos(\pi f / f_s)|$ is nearly $1$. For example, at $f_s = 44{,}100$ Hz, a harmonic at $110$ Hz is scaled by $0.99997$ per trip. But a harmonic at $4410$ Hz is scaled by about $0.951$ per trip. For a note at $110$ Hz, which makes $110$ trips per second, that adds up to an extra $48$ dB of attenuation every second. So the high harmonics die away quickly, while the low harmonics ring on:

:::{audio-board}
{audio}`Gain only <./assets/audio-pluck-gain.wav>`

{audio}`Gain and low-pass <./assets/audio-pluck-lowpass.wav>`

![Two spectrograms of a 110 Hz pluck over 3 seconds, from 0 to 5 kHz. Left, titled gain only: evenly spaced horizontal lines, one per harmonic, all fade out together at the same rate. Right, titled gain and low-pass: the upper harmonics fade out within a fraction of a second, while the lowest harmonics persist for the full 3 seconds.](./assets/fig-lowpass-decay.png)

Spectrograms of a damped feedback delay line tuned to $110$ Hz and excited by a unit impulse, with a gain alone (left) and with a gain and a two-point average (right). With the low-pass filter in the loop, the higher harmonics decay faster, and the pluck sounds more natural.
:::

CLAUDE: this is too subtle. get rid of it.
There is one subtlety. Averaging $y[n - M]$ and $y[n - M - 1]$ effectively delays the signal by $M + \frac{1}{2}$ samples, halfway between the two. So to tune the loop to a frequency $f$, we set the total delay $M + \frac{1}{2}$ to the period $\frac{f_s}{f}$, i.e., $M = \mathrm{round}\big(\frac{f_s}{f} - \frac{1}{2}\big)$. We will put the low-pass filter into code in the next section, along with the final ingredient of our physical model.

### Excitation via noise

So far, we have excited our physical model with a unit impulse. Is this a good model of a pluck? Consider the first $M$ samples of the output of a feedback delay line. During these samples, the feedback path contributes nothing, since the input has not yet made its first trip around the loop. So $y[n] = x[n]$ for $n < M$. In effect, the first $M$ samples of the input fill the delay line with an initial waveform, which the loop then recirculates, attenuating and smoothing it on every trip.

What should this initial waveform be? A pluck, a strike, or the scrape of a bow is a sudden, chaotic event, which excites the string with energy at many frequencies at once. In general, the sounds of real instruments start out noisy and _broadband_ (containing a broad range of frequencies), and then become periodic and resonant. This suggests filling the delay line with _noise_.

We have casually used noise as a sound source in previous chapters, like in the subtractive synthesis of [Chapter 9](../09-filters). Now let's define it formally.

CLAUDE: a bit confused. does karplus strong actually use Gaussian noise, or does it use uniform noise? I don't really want to introduce both, this section should be pretty short tbh.
:::{prf:definition} White noise
:label: def-white-noise
A random signal $x[n]$ is _white noise_ if its samples are independent and identically distributed, with mean $\mathbb{E}\big[x[n]\big] = 0$ and variance $\mathbb{E}\big[x[n]^2\big] = \sigma^2$.
:::

Here, $\mathbb{E}$ denotes the expected value, the average over many random draws. For example, the code in this chapter draws each sample uniformly at random between $-1$ and $1$, which has variance $\sigma^2 = \frac{1}{3}$. Another common choice is a Gaussian distribution.

Why is it called {vocab}`white noise`? White light contains all visible colors, i.e., all visible frequencies of light, in roughly equal measure. Similarly, white noise contains all frequencies in equal measure, on average:

CLAUDE: don't need to formaly define the spectrum. an empirical plot is fine.
:::{prf:property}
:label: prop-white-noise-spectrum
Let $X[k]$ be the DFT of $N$ samples of white noise with variance $\sigma^2$. Then every frequency bin has the same expected power, $\mathbb{E}\big[|X[k]|^2\big] = N \sigma^2$.
:::

To see why, use the definition of the DFT to write $|X[k]|^2$ as a double sum over pairs of samples $x[n] \cdot x[m]$. When $n \neq m$, the two samples are independent with mean zero, so their product has expectation zero. That leaves only the $N$ pairs with $n = m$, each with expectation $\sigma^2$.

Any single recording of white noise has a jagged spectrum, since every bin is random. But on average, its spectrum is flat:

:::{figure}
![Two plots. Left: 10 milliseconds of white noise, a dense, erratic blue waveform between minus 1 and 1. Right: its magnitude spectrum in decibels from 0 to 22 kHz, a jagged light blue band that fluctuates randomly by tens of decibels, with a flat black line through it showing the average.](./assets/fig-white-noise.png)

Ten milliseconds of white noise, with samples drawn uniformly between $-1$ and $1$ (left), and the magnitude spectrum of one second of it (right). Each bin of the spectrum is random (light blue), but on average (black), the spectrum is flat from $0$ Hz up to the Nyquist frequency.
:::

:::{margin}
Other _colors_ of noise have other spectral shapes. For example, the power of _pink noise_ falls off by $3$ dB per octave, so that every octave contains the same power, and the power of _brown noise_ falls off by $6$ dB per octave.
:::

Now, back to our physical model. To simulate a pluck, we excite the delay line with one period of white noise: $x[n]$ is white noise for $0 \leq n < M$, and $x[n] = 0$ for $n \geq M$. Since white noise contains all frequencies, it excites every tooth of the comb, i.e., every harmonic, at once. From then on, the loop recirculates the noise once per period, so the output becomes periodic, i.e., pitched, right away. On every trip, the low-pass filter smooths the noise a little more, so the sound starts bright and noisy, like the attack of a pluck, and mellows as it decays.

An impulse also contains all frequencies, so why does noise make a better pluck? An impulse excites every harmonic with exactly the same amplitude and phase, which sounds thin and buzzy. Noise excites each harmonic with a random amplitude and phase, which sounds richer and more natural. It also makes every pluck slightly different, just like on a real instrument:

:::{audio-list}
{audio}`Excited by a unit impulse <./assets/audio-excitation-impulse.wav>`

{audio}`Excited by a burst of white noise <./assets/audio-excitation-noise.wav>`

The same feedback delay line, with a gain and a two-point average in its loop, tuned to $196$ Hz and decaying by $60$ dB over $2.5$ seconds. It is excited by a unit impulse (first) and by one period of white noise (second).
:::

CLAUDE: make Karplus-Strong it's own subsection

Putting all of these pieces together yields one of the most famous algorithms in computer music, the {vocab}`Karplus-Strong algorithm`, published by Kevin Karplus and Alex Strong in 1983 {cite}`karplus1983digital`:

:::{figure}
![A signal-flow diagram. A noise burst x[n], drawn as a short jagged waveform followed by silence, enters a summing junction, whose output is y[n]. The output is tapped and fed back into the summing junction through three blocks in sequence: a delay labeled z to the minus M, a low-pass filter labeled one half times the quantity 1 plus z to the minus 1, and a triangular attenuation labeled g.](./assets/fig-karplus-strong.png)

The Karplus-Strong algorithm. A burst of noise excites a feedback delay line, with a low-pass filter and attenuation in its loop.
:::

:::{prf:definition} Karplus-Strong algorithm
:label: def-karplus-strong
The _Karplus-Strong algorithm_ synthesizes a plucked string with fundamental frequency $f$, lasting $T$ seconds at sample rate $f_s$, by computing

$$y[n] = x[n] + g \cdot \tfrac{1}{2}\big(y[n - M] + y[n - M - 1]\big),$$

where

1. the delay $M = \mathrm{round}\big(\frac{f_s}{f} - \frac{1}{2}\big)$ tunes the loop, including the half sample of delay from the two-point average,
1. the gain $g = 10^{-3(M + 1/2) / (f_s T)}$ decays the output by about $60$ dB in $T$ seconds, and
1. the excitation $x[n]$ is white noise for $0 \leq n < M$, and zero otherwise.
:::

Karplus and Strong's original algorithm had no gain, i.e., $g = 1$. Its notes still decay, because of the low-pass filter. In fact, higher notes decay faster, because they make more trips around the loop per second, just like on real strings. David Jaffe and Julius Smith later proposed several extensions to the algorithm {cite}`jaffe1983extensions`, including ways to control its decay time, like our gain $g$.

Karplus and Strong originally described their algorithm as a variation on the {ref}`wavetable synthesis <sec-wavetable-synthesis>` of [Chapter 3](../03-additive-synthesis). The delay line is a wavetable of $M$ samples, initialized with random values, which the algorithm reads in a loop, smoothing the table a little on every pass.

The code below implements the Karplus-Strong algorithm as an instrument, `karplus_strong(pitch, duration)`, and uses it to strum all six strings of a simulated guitar, one string every $40$ ms. Run it a few times: since the excitation is random, every strum sounds slightly different.

:::{interactive}[notebooks/karplus-strong.ipynb]
:::

With just a few lines of code, and a handful of arithmetic operations per audio sample, we have synthesized a convincing plucked string.

## Commuted synthesis

The Karplus-Strong algorithm sounds remarkably like a plucked string, but it leaves us with a mystery. When we studied acoustics, we saw that a vibrating string carries two traveling waves, one moving right and one moving left, which superimpose to form standing waves. Karplus-Strong has only a single delay line, which doesn't seem to correspond to any particular place on the string. So where are the traveling waves? In this section, we will answer this question at a high level, and along the way, learn a key trick (_commuted synthesis_) for making physical models efficient.

### Digital waveguides

A {vocab}`digital waveguide` models the two traveling waves on a string explicitly, using two delay lines that run in opposite directions {cite}`smith1992physical`. Each sample of delay corresponds to a particular point along the string. The upper delay line carries the right-going wave toward the bridge, and the lower one carries the left-going wave toward the nut. At each end, a wave reflects with opposite polarity, so the model multiplies it by $-1$ and feeds it into the other delay line:

:::{figure}
![Top: a plucked string, drawn as a triangle pulled up near its right end, with the caption string displacement equals right-going plus left-going. Below it, two horizontal rows of twelve delay cells. The upper row is labeled right-going wave, with an arrow pointing right, and the lower row is labeled left-going wave, with an arrow pointing left. At the right end, labeled bridge, a curved arrow marked times minus 1 carries the upper row into the lower row. At the left end, labeled nut, another curved arrow marked times minus 1 carries the lower row into the upper row. A purple summing junction taps both rows at the same point along the string, and sends their sum to an output.](./assets/fig-waveguide.png)

A digital waveguide model of a string. Two delay lines carry the right-going and left-going waves, which invert as they reflect at each end. The displacement of the string at any point is the sum of the two waves at that point.
:::

This model has two key advantages:

1. **It models the traveling waves explicitly.** The structure of the simulation mirrors the physics of the string.
1. **We can listen at any point along the string.** By superposition, the displacement of the string at any point is simply the sum of the two delay lines at that point. For example, the pickups of an electric guitar sense the vibrations of its strings at particular points along their length, and the timbre depends on where the pickup is. Listening at the very middle of a string, we would hear none of its even harmonics, which all have nodes there.

### Lumped losses

CLAUDE: gain g should be the same after each delay (just $g$ or $g^3$, not $g_1, g_2, g_3$)
So far, our waveguide is lossless, so its waves would travel back and forth forever. In a real string, energy is lost continuously, all along the length of the string. A faithful simulation would apply a tiny loss after every sample of delay: a gain $g_1$ after the first, $g_2$ after the second, and so on. But this is computationally expensive. A string with a round trip of $M$ samples would need $M$ multiplications for every sample of output.

Fortunately, if we only listen at one point, we can _lump_ these losses together into a single loss, and save almost all of that computation:

:::{figure}
![Two signal chains. Top, labeled distributed: three blocks labeled z to the minus 1, each followed by its own triangular gain, labeled g1, g2, and g3. Bottom, labeled lumped: a single block labeled z to the minus 3, followed by a single triangular gain labeled g1 g2 g3.](./assets/fig-lumped-losses.png)

Distributed losses (top) apply a loss after every sample of delay, while lumped losses (bottom) apply them all at once. Both produce the same output, but the lumped version needs one multiplication instead of three.
:::

Why are these equivalent? Each delay and each loss is an LTI filter, i.e., a convolution with an impulse response. Recall from [Chapter 9](../09-filters) that convolution is {prf:ref}`commutative <prop-conv-commutative>` and {prf:ref}`associative <prop-conv-associative>`. So we can reorder and regroup a chain of filters however we like, without changing its output. Once we move all of the losses next to each other, they combine into a single gain, $g = g_1 \cdot g_2 \cdots$. The catch is that the signals _in between_ the filters do change. So we can only lump losses together between the points where we listen.

:::{margin}
In the research literature, _commuted synthesis_ often refers specifically to commuting the strings of an instrument, like a guitar, with its resonant body. Then, rather than simulating the body, we can excite the strings with a recording of the body's impulse response {cite}`smith2010physical`.
:::

This is the essence of {vocab}`commuted synthesis`: a physical model is a chain of filters, and we can commute them into whatever order is cheapest to compute, even an order that makes no physical sense. The same idea applies to the losses of a real string, which depend on frequency. These losses are low-pass filters rather than gains, but they still lump together into a single low-pass filter.

### Karplus-Strong, fully commuted

We can now solve the mystery of the missing traveling waves. Consider a digital waveguide string with a round trip of $M$ samples, so each delay line holds $\frac{M}{2}$ samples. Suppose we only listen at the bridge, where a guitar string passes its vibrations to the body of the guitar. Then we can commute and lump everything else in the loop:

1. The two delay lines of $\frac{M}{2}$ samples combine into a single delay line of $M$ samples, one full round trip.
1. The two reflections, each multiplying by $-1$, combine into a single multiplication by $(-1) \cdot (-1) = 1$, i.e., no inversion at all.
1. All of the losses along the way combine into a single lumped loss, like the two-point average and gain $g$ of Karplus-Strong.

The result is exactly Karplus-Strong:

:::{figure}
![Two signal-flow diagrams. Top, titled digital waveguide: two delay blocks, each labeled M over 2 samples of delay, with losses, form a loop. At the right end, labeled bridge, a triangular gain of minus 1 carries the output of the upper block into the lower block. At the left end, labeled nut, another gain of minus 1 carries the output of the lower block into the upper block. The output is taken where the upper block meets the bridge. Bottom, titled Karplus-Strong: a single block labeled M samples of delay, whose output loops back into its input through a block labeled g times one half times the quantity 1 plus z to the minus 1, with the caption all of the losses, lumped. The output is taken at the same place as above.](./assets/fig-waveguide-to-ks.png)

Listening only at the bridge, a digital waveguide (top) commutes into Karplus-Strong (bottom). Adapted from a [figure by Julius O. Smith III](https://ccrma.stanford.edu/~jos/Mohonk05/Digital_Waveguide_Interpretation_Karplus_Strong.html).
:::

In other words, **Karplus-Strong is a _fully commuted_ digital waveguide**. The traveling waves are still there, but because we only listen at one point, we can commute them together into a single delay line. This makes Karplus-Strong extremely efficient, at the cost of the flexibility of the full waveguide.

### Going further

We have only scratched the surface of physical modeling. Researchers have spent decades refining these building blocks into models of nearly every kind of instrument, from bowed strings to brass, which are far more realistic than Karplus-Strong. Compared to the sample-based synthesis of [Chapter 11](../11-sampled-synthesis), physical modeling has several advantages:

- **Complex sounds from simple laws**: a few simple physical principles give rise to rich, intricate sounds.
- **Realistic transitions between notes**: a physical model naturally simulates what happens _between_ notes, like re-plucking a string that is still vibrating, while a sampler can only play back the transitions that were recorded.
- **Low memory usage**: a physical model needs only a few parameters and some short delay lines, rather than gigabytes of recordings.
- **Modularity**: building blocks can be recombined into new, hybrid instruments that could never be built in the physical world.

But it also has disadvantages:

- **Less realistic sound**: even sophisticated physical models rarely sound as realistic as recordings of the real instrument.
- **Difficult control**: like real instruments, physical models can be difficult to play. For example, producing a good sound from a model of a violin requires carefully controlling the pressure, speed, and position of the bow, just like a real violin.
- **Computational cost**: simulating vibrations in two or three dimensions, like those of a drumhead or the body of a guitar, can be very expensive.

To dive deeper into the decades of research on physical modeling, see [Julius Smith's _Physical Audio Signal Processing_ {cite}`smith2010physical`](https://ccrma.stanford.edu/~jos/pasp/). To experiment with sophisticated physical models in code, see the [Synthesis ToolKit (STK)](https://ccrma.stanford.edu/software/stk/), an open-source C++ library by Perry Cook and Gary Scavone, which includes physical models of flutes, clarinets, bowed strings, plucked strings, and more.

## Summary

- {vocab}`Physical modeling synthesis` simulates the _causes_ of musical sound, the acoustics of an instrument, rather than imitating its _effects_.
- Waves propagate through a medium at a speed $v$, pass through each other by {vocab}`superposition`, and reflect with opposite polarity at rigid boundaries. A sinusoidal wave has a {vocab}`wavelength` $\lambda = \frac{v}{f}$.
- On a string of length $L$ with fixed ends, waves traveling in opposite directions superimpose into {vocab}`standing waves` with wavelengths $\lambda_i = \frac{2L}{i}$ and frequencies $f_i = i \cdot \frac{v}{2L}$, which are the harmonics of $f_1 = \frac{v}{2L}$.
- Each standing wave is a {vocab}`mode of oscillation`. A tube closed at one end has only odd harmonics, and the modes of two- and three-dimensional objects are generally not harmonic.
- A feedback delay line, $y[n] = x[n] + y[n - M]$, simulates propagation with delay, and reflection with feedback. Tuning it to a frequency $f$ requires $M = \mathrm{round}(\frac{f_s}{f})$, whose rounding error grows with frequency. Its impulse response is an impulse train, so it is a {vocab}`comb filter`, with teeth at multiples of $\frac{f_s}{M}$.
- A gain $g < 1$ in the loop simulates damping. To decay by $60$ dB in $T$ seconds, $g = 10^{-3M/(f_s T)}$. A low-pass filter in the loop, like a two-point average, makes the higher harmonics decay faster, as in real strings.
- {vocab}`White noise` has independent random samples with mean zero, and its expected spectrum is flat. A burst of white noise is a simple model of the broadband excitation of a pluck.
- The {vocab}`Karplus-Strong algorithm` excites a feedback delay line, with a low-pass filter and attenuation in its loop, with a burst of white noise.
- A {vocab}`digital waveguide` models the right-going and left-going waves on a string explicitly, so we can listen at any point along the string. Since delays and losses are LTI filters, we can commute them, and lump the losses together wherever we don't listen. This is the idea behind {vocab}`commuted synthesis`, and Karplus-Strong is a fully commuted digital waveguide.

## Questions for the reader

::::{exercise}
**Modes of a string.** A violin string vibrates along a length of $L = 0.33$ meters, and waves travel along it at $v = 290.4$ m/s.

1. What are the wavelengths of its first three modes?
1. What are their frequencies?
1. Pressing the string against the fingerboard shortens its vibrating length to $\frac{3}{4}$ of the original. What is the new fundamental frequency?

:::{solution}

1. $0.66$ m, $0.33$ m, and $0.22$ m
1. $440$ Hz, $880$ Hz, and $1320$ Hz
1. $\approx 586.7$ Hz

:::
::::

::::{exercise}
**Modes of a tube.** Sound travels through air at $v = 343$ m/s. A tube is $L = 0.5$ meters long.

1. If the tube is open at both ends, what are the frequencies of its first three modes?
1. If the tube is closed at one end, what are the frequencies of its first three modes?

:::{solution}

1. $343$ Hz, $686$ Hz, and $1029$ Hz
1. $171.5$ Hz, $514.5$ Hz, and $857.5$ Hz

:::
::::

::::{exercise}
**Delay from travel time.** A guitar string vibrates along a length of $L = 0.65$ meters, and waves travel along it at $v = 143$ m/s. We simulate it at $f_s = 48{,}000$ Hz.

1. How many samples does it take a wave to travel the length of the string once?
1. To tune a feedback delay line to this string, we set $M$ to the number of samples in a round trip, rounded to the nearest whole number. What is $M$, and what fundamental frequency does the feedback delay line produce?
1. What is the fundamental frequency of the real string?

:::{solution}

1. $\approx 218.18$ samples
1. $M = 436$, which produces $\approx 110.09$ Hz
1. $110$ Hz

:::
::::

::::{exercise}
**Tuning resolution.** At $f_s = 44{,}100$ Hz, what delay $M$ tunes $y[n] = x[n] + y[n - M]$ as closely as possible to each of the following frequencies, and what frequency does it actually produce? By how many steps is each out of tune?

1. A4, at $440$ Hz
1. A7, at $3520$ Hz

:::{solution}

1. $M = 100$, which produces $441$ Hz, $\approx 0.04$ steps sharp
1. $M = 13$, which produces $\approx 3392.3$ Hz, $\approx 0.64$ steps flat

:::
::::

::::{exercise}
**Impulse response of a comb filter.** Consider the comb filter $y[n] = x[n] + 0.5 \cdot y[n - 3]$, at $f_s = 44{,}100$ Hz.

1. Write down the first ten samples of its impulse response.
1. How far apart are the teeth of its comb, in Hz?

:::{solution}

1. $h = [1, 0, 0, 0.5, 0, 0, 0.25, 0, 0, 0.125]$
1. $14{,}700$ Hz

:::
::::

::::{exercise}
**Decay time.** A damped feedback delay line $y[n] = x[n] + g \cdot y[n - M]$ at $f_s = 44{,}100$ Hz is tuned to $441$ Hz.

1. What is $M$?
1. What gain $g$ makes its impulse response decay by $60$ dB in $2$ seconds?
1. Keeping that same gain $g$, we retune the delay line an octave lower, to $220.5$ Hz. How long does its impulse response now take to decay by $60$ dB?

:::{solution}

1. $M = 100$
1. $g \approx 0.9922$
1. $4$ seconds

:::
::::

::::{exercise}
**Tuning Karplus-Strong.** Consider the Karplus-Strong algorithm at $f_s = 44{,}100$ Hz.

1. What delay $M$ tunes it as closely as possible to $440$ Hz, and what frequency does it actually produce?
1. The two-point average in its loop scales a sinusoid at frequency $f$ by $|\cos(\pi f / f_s)|$. By how many decibels does it attenuate a harmonic at $\frac{f_s}{8} = 5512.5$ Hz on each trip around the loop? After $50$ trips?

:::{solution}

1. $M = 100$, which produces $\approx 438.8$ Hz
1. $\approx -0.69$ dB per trip, and $\approx -34.4$ dB after $50$ trips

:::
::::

::::{exercise}
**Lumping losses.** A digital waveguide string has a round trip of $M = 200$ samples, and every sample of delay multiplies the wave by a loss of $0.9999$.

1. If we lump all of these losses into a single gain $g$ per round trip, what is $g$?
1. How many multiplications per sample of output do the distributed losses need? How many do the lumped losses need?

:::{solution}

1. $g \approx 0.9802$
1. $200$ for the distributed losses, and $1$ for the lumped losses

:::
::::

::::{exercise}
**Ordering convolutions.** Directly convolving two signals of lengths $K$ and $N$ takes $K \cdot N$ multiplications, and produces a signal of length $K + N - 1$. You need to compute $h_1 * h_2 * h_3$, where $h_1$, $h_2$, and $h_3$ have lengths $1$, $3$, and $2$. Since convolution is commutative and associative, you may convolve them in any order. Which two should you convolve first to minimize the total number of multiplications, and what is that total?

:::{solution}
Convolve $h_1$ and $h_3$ first, for a total of $8$ multiplications.
:::
::::

## Musical examples

### David A. Jaffe - _Silicon Valley Breakdown_ (1982)

David Jaffe composed this piece at Stanford from plucked-string sounds, synthesized with the extensions to the Karplus-Strong algorithm that he developed with Julius Smith. It shows how far a simple physical model can be pushed, and it was among the first pieces to put the Karplus-Strong algorithm to musical use. This video pairs the piece with a film by George Olczak.

<iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/_p4DGE5t3x0" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

### Don Slepian - _Sonic Test Drive: Yamaha VL1_ (2022)

The Yamaha VL1 (1994) was one of the first commercial synthesizers based on physical modeling, building on digital waveguide research at Stanford. In this video from the Electronic Music Education and Preservation Project, musician Don Slepian takes the instrument for a test drive.

<iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/nxn07L8BUbQ" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
