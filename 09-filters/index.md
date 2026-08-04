---
title: "Chapter 9: Filters"
---

# Filters

So far, this book has mostly studied _synthesis_: techniques like additive and modulation synthesis that create sound from scratch. But computer music is as much about _sculpting_ existing sound as it is about creating new sound. In this chapter we study {vocab}`filters`, the tools we use to process a signal we already have, whether it came from a synthesizer, a microphone, or another filter.

This chapter was heavily inspired by the treatment of [convolution in _Digital Signals Theory_ {cite}`mcfee2023digital`](https://brianmcfee.net/dstbook-site/content/ch03-convolution/Convolution.html), and we borrow much of its notation. Filter analysis and design is an extraordinarily deep subject, and we will only take a cursory look here. Readers who want to go further should consult [Julius Smith's _Introduction to Digital Filters_ {cite}`smith2007introduction`](https://ccrma.stanford.edu/~jos/filters), a thorough and audio-focused treatment.

## What do we mean by a filter?

In signal processing, the word _filter_ is remarkably broad. It refers to essentially _any_ function that takes a signal as input and produces another signal as output. Because signals are themselves functions of time, a filter can be viewed as a function _of functions_.

CLAUDE: Realizing my slides are a bit inaccurate here. A filter maps x to y canonically, not samples x[n] to y[n]. Refine the paragraph below and the figure
In this book we study {vocab}`digital filters`: a function $g : x \mapsto y$ that takes $N$ input samples $x \in \mathbb{R}^N$ and produces output samples $y \in \mathbb{R}^N$. Equivalently, thinking of a signal as a function of a sample index, $g$ maps one discrete signal to another.

CLAUDE: I know this was my sugggestion but I think this is just confusing honestly. let's just represent the basic x -> [g] -> y flow in latex, no need for a figure.
:::{figure}
![A block diagram. On the left, the input x[n], labeled as a function x from the naturals to the reals and as an array x in R to the N. An arrow leads into a box labeled g, the filter, itself a map from x to y. An arrow leads out to the output y[n], labeled as a function y from the naturals to the reals and as an array y in R to the N.](./assets/fig-filter-blackbox.png)

A digital filter $g$ maps an input signal $x[n]$ to an output signal $y[n]$. We can view each signal either as a function of a sample index or as an array of $N$ numbers.
:::

This definition is so broad that it covers almost all topics in computer music:

1. The synthesis techniques we have already seen, such as modulation synthesis, which transform one signal into another.
1. Many audio effects you may have encountered outside this book: reverb, delay, distortion, equalization, compression, and so on.

To make progress, we will narrow our attention to an especially important subclass: {vocab}`linear time-invariant` (LTI) filters. LTI filters are so ubiquitous in computer music and digital signal processing that **the word "filter" is shorthand for LTI filters** in colloquial usage. We will define _linear_ and _time-invariant_ precisely later in the chapter. For now, the important thing is their high-level purpose.

**The high-level goal of an LTI filter is to sculpt the frequency-domain content of a sound.** An LTI filter cannot invent new frequencies. It can only boost or attenuate the frequencies already present in its input, each by an amount that depends on the frequency.

CLAUDE: Draw dashed ghost outline of the red filter response on the output subfigure, indicating the new upper bound on the frequency content. Add cdot to output definition. change m to k, consistent w/ DFT chapter
:::{figure}
![Three stacked panels sharing a frequency axis from 0 to f_s over 2. Top: the input spectrum, a set of blue partials whose amplitudes decrease with frequency. Middle: the filter's magnitude response, a smooth red curve that bulges up over a band of low-to-middle frequencies. Bottom: the output spectrum in purple, equal to the input partials each scaled by the filter curve, so the middle partials are emphasized relative to the rest.](./assets/fig-lti-goal.png)

An LTI filter reshapes a sound in the frequency domain. Each partial of the input $|X[m]|$ (blue) is scaled by the filter's response $|H[m]|$ (red), yielding the output $|Y[m]| = |H[m]| \cdot |X[m]|$ (purple). No new partials appear, and the existing ones are only reweighted.
:::

Over the next several sections we will build up several complementary _perspectives_ on LTI filters: difference equations, convolution, impulse responses, frequency-domain multiplication, and signal-flow diagrams. Each perspective illuminates different properties, and a fluent practitioner moves between them freely.

## Difference equations

In a digital signal processing context, a {vocab}`difference equation` defines a filter by expressing each output sample as a formula in terms of the input samples. It is the most direct, hands-on way to specify a filter, and it translates immediately into code.

### A first example

Consider the difference equation

$$y[n] = x[n] + x[n-3].$$

Each output sample is the current input sample plus a _copy of the input delayed by three samples_. Let us feed it a simple square wave with a ten-sample period, $x[n] = [1, 1, 1, 1, 1, -1, -1, -1, -1, -1, \ldots]$.

CLAUDE: Need to emphasize that $x[n-3]$ is a _delayed copy_ of the signal. First time students are encountering this!
To evaluate $x[n-3]$ near the start of the signal, we need values like $x[-1]$, which lie before the signal begins. Throughout this chapter we adopt the standard convention that a signal is _zero_ at any index outside its defined range: $x[n] = 0$ for $n < 0$. The first three output samples therefore see a delayed copy that is still "warming up" with zeros.

:::{figure}
![Three stacked stem plots over sample indices 0 to 31. Top (blue): the input square wave x[n], five samples at plus one then five at minus one, repeating. Middle (red): x[n-3], the same square wave shifted three samples to the right, with the first three samples (shaded) equal to zero. Bottom (purple): the sum y[n], which is plus two or minus two where the two copies agree and zero where they disagree, after an initial warm-up region equal to the input.](./assets/fig-diffeq-delay.png)

The filter $y[n] = x[n] + x[n-3]$ applied to a square wave. The delayed copy $x[n-3]$ (red) is the input shifted right by three samples, with zeros assumed before $n = 0$ (shaded). Summing it with $x[n]$ gives $y[n]$ (purple).
:::

Comparing $y[n]$ to $x[n]$, three things stand out: (1) the output has a _different peak amplitude_ ($\max|y| \ne \max|x|$), (2) it has a different _shape_, and (3) there is an initial "warm-up" period before it settles into cyclical behavior. Even for this very simple filter, the output is not trivial to predict by inspection. You can experiment with this filter in code, including listening to the input and output, in the following example:

:::{interactive}[notebooks/difference-equations.ipynb]
:::

### A second example

Now consider a slightly different difference equation,

$$y[n] = \tfrac{1}{2}\,x[n] - \tfrac{1}{2}\,x[n-1].$$

This one uses a shorter delay of a single sample, scales both terms by one half, and _subtracts_ rather than adds. Applied to the same square wave, its behavior is quite different:

:::{figure}
![Three stacked stem plots over sample indices 0 to 31. Top (blue): one half times x[n], a square wave between plus and minus one half. Middle (red): minus one half times x[n-1], the inverted square wave delayed by one sample, with the first sample shaded as a warm-up zero. Bottom (purple): the sum y[n], which is zero across the flat stretches of the square wave and spikes to plus or minus one only at the transitions.](./assets/fig-diffeq-difference.png)

The filter $y[n] = \tfrac{1}{2}x[n] - \tfrac{1}{2}x[n-1]$ applied to the same square wave. Scaling by one half adjusts the amplitude, and the subtraction inverts the phase of the delayed term. The output is zero wherever the input is constant and spikes only at the input's transitions.
:::

The takeaways here are different: (1) the one-half factors adjust the amplitude, (2) the subtraction of a delayed copy makes the filter respond only to _changes_ in the input, so the output is zero across the flat stretches and spikes at the edges, and (3) there is again a brief warm-up period. This filter is, in effect, a crude edge detector.

### What do these filters do to sound?

Difference equations are trivial to implement, but as the two examples show, it can be difficult to predict their effect just by reading the formula. The clearest way to build intuition is to _listen_. Below are the same two filters applied to an audible square-wave tone (a richer square than our ten-sample toy, so more harmonics are in play), alongside the amplitude spectrum of each result:

CLAUDE: Something seems off here... the high-level filter shapes are not clearly coming through visually in the spectrogram. what's wrong? maybe we need to change the examples up stream to more clearly highlight a basic low / high pass? but I also want to preserve other things in those pedagogical examples such as a warm up period and overal change in amplitude
:::{audio-board}
{audio}`Input square wave $x[n]$ <./assets/audio-diffeq-input.wav>`

{audio}`$y_1[n] = x[n] + x[n-3]$ <./assets/audio-diffeq-y1.wav>`

{audio}`$y_2[n] = \frac{1}{2}x[n] - \frac{1}{2}x[n-1]$ <./assets/audio-diffeq-y2.wav>`

![Three amplitude spectra in decibels over 0 to 10 kHz. Left: the input square wave, showing evenly spaced odd harmonics that fall off gently with frequency. Middle: the first filter's output, whose harmonics are reshaped with a deep notch near 7 kHz. Right: the second filter's output, whose harmonics are lifted so the spectrum is nearly flat, emphasizing the higher frequencies.](./assets/fig-diffeq-spectra.png)

The same two difference equations applied to an audible square-wave tone. The first filter (middle) carves a deep notch into the spectrum near 7 kHz. The second (right) tilts energy toward higher frequencies, brightening the tone.
:::

Even these two-term filters produce clearly audible changes in timbre by reshaping the spectrum. The first, a sum of delayed copies, imposes a series of peaks and notches called a _comb_ pattern. The second, a difference, acts like a treble boost. The rest of this chapter is largely about developing the tools to _predict_ and _design_ such frequency-domain effects, rather than discovering them by trial and error.

(sec-convolution)=

## Convolution

CLAUDE: Restate the filters y*1[n] and y_2[n] as difference equations before expanding the terms below. My rendering pipeline breaks things up into different pages at `##` headings.
We have now seen two distinct difference equations with quite different behaviors. How might we \_generalize* the idea? The trick is to write both filters in a single common format. Padding each with explicit zero coefficients,

$$
\begin{aligned}
y_1[n] &= 1 \cdot x[n] + 0 \cdot x[n-1] + 0 \cdot x[n-2] + 1 \cdot x[n-3], \\
y_2[n] &= \tfrac{1}{2} \cdot x[n] - \tfrac{1}{2} \cdot x[n-1] + 0 \cdot x[n-2] + 0 \cdot x[n-3].
\end{aligned}
$$

The pattern is now clear. Each filter is a weighted sum of delayed copies of the input, and a filter is fully specified by its list of weights: $[1, 0, 0, 1]$ for the first and $[\tfrac{1}{2}, -\tfrac{1}{2}, 0, 0]$ for the second. Collecting the weights into a sequence $h[k]$, every filter of this form can be written in a common format known as _convolution_.

:::{prf:definition} Convolution
:label: def-convolution
The {vocab}`convolution` of a length-$K$ filter coefficients $\red{h}$ with a length-$N$ signal $\blue{x}$ is the signal

$$\purple{y[n]} = \sum_{k=0}^{K-1} \red{h[k]} \cdot \blue{x[n-k]}.$$

This operation is so common that it has its own notation, an asterisk:

$$\purple{y} = \red{h} * \blue{x}.$$
:::

### An example of convolution

Let us work a small example by hand. Take a short input $\blue{x} = [1, 1, 1]$ (length $N = 3$) and a short filter $\red{h} = [3, 2, 1]$ (length $K = 3$). Applying the definition, each output sample is a sum of products, remembering that any out-of-range sample of $x$ is zero:

CLAUDE: missing color coding on h/x

$$
\begin{aligned}
\purple{y[0]} &= h[0]x[0] = 3, \\
\purple{y[1]} &= h[0]x[1] + h[1]x[0] = 3 + 2 = 5, \\
\purple{y[2]} &= h[0]x[2] + h[1]x[1] + h[2]x[0] = 3 + 2 + 1 = 6, \\
\purple{y[3]} &= h[1]x[2] + h[2]x[1] = 2 + 1 = 3, \\
\purple{y[4]} &= h[2]x[2] = 1.
\end{aligned}
$$

:::{figure}
![Three stem plots. Left (blue): x[n] equal to [1,1,1] at indices 0,1,2. Middle (red): h[n] equal to [3,2,1] at indices 0,1,2. Right (purple): the convolution y equal to [3,5,6,3,1] at indices 0 through 4, forming a peak in the middle.](./assets/fig-convolution-example.png)

Convolving $\blue{x} = [1,1,1]$ with $\red{h} = [3,2,1]$ yields $\purple{y} = [3,5,6,3,1]$. The output has five nonzero samples.
:::

Notice that the output $\purple{y} = [3, 5, 6, 3, 1]$ is _longer_ than either input. In general, convolving a length-$N$ signal with a length-$K$ filter produces an output with $N + K - 1$ nonzero samples. The convolution "spreads" the input out by the length of the filter.

You can watch convolution unfold as a sliding operation in the animation below, where a longer input signal is convolved with a filter. The filter slides across the input one sample at a time, and at each position the output sample is the sum of the overlapping products. (Because of a subtlety we will prove next, the filter appears _reversed_ as it slides.)

CLAUDE: change x in this figure to be more pulse-train like, to show the spreading effect more clearly. not a pure pulse train, just more like that than the current x. also, the x axis is a bit messed up here... make it integers starting at -3 so can see the effect of h operating on x[<0] when computing y[0]. finally, in the caption don't relate the 'reversing' to the commutativity proof below, just state it as a matter of fact: it falls out of the definition of convolution of multiplying h[n] by x[n-k]
:::{figure}
![An animation of convolution as a sliding operation. A fixed input signal x, drawn as blue stems, spans the top. A short reversed filter h, drawn as red stems, slides across it from left to right. At each position, the overlapping samples are multiplied and summed to produce one output sample of y, drawn as a growing purple stem plot below.](./assets/fig-convolution-sliding.gif)

Convolution as a sliding sum. The reversed filter $\red{h}$ slides across the input $\blue{x}$ one sample at a time. At each position, the overlapping products are summed to produce one output sample of $\purple{y}$.
:::

### Commutativity of convolution

What happens if we swap the roles of $\red{h}$ and $\blue{x}$, convolving $\blue{x} * \red{h}$ instead of $\red{h} * \blue{x}$? Reworking the same example with the roles reversed gives

CLAUDE: do the full example, not just the first two samples

$$
\begin{aligned}
\purple{y[0]} &= x[0]h[0] = 1 \cdot 3 = 3, \\
\purple{y[1]} &= x[0]h[1] + x[1]h[0] = 2 + 3 = 5, \\
&\;\;\vdots
\end{aligned}
$$

which produces exactly the same output $[3, 5, 6, 3, 1]$. This is no accident. Convolution is {vocab}`commutative`:

$$\red{h} * \blue{x} = \blue{x} * \red{h}.$$

CLAUDE: confusing to reference commutativity for explaining the reversing. see above
In other words, it does not matter which signal we call the "filter" and which the "input". This is also the reason the filter appears reversed in the sliding animation. Substituting $m = n - k$ into the definition re-expresses the sum with the roles of the two signals exchanged, which flips the direction one of them is indexed.

### Other properties of convolution

Beyond commutativity, convolution has two more essential algebraic properties. We state them here and leave their proofs (a matter of manipulating the summation) as exercises.

:::{important}
Convolution is **commutative**: $\;a * b = b * a$.
:::

:::{important}
Convolution is **associative**: $\;a * (b * c) = (a * b) * c$.
:::

:::{important}
Convolution is **distributive** over addition: $\;a * (b + c) = a * b + a * c$.
:::

Associativity and commutativity have a practical consequence worth scrutinizing further. For a chain of convolutions like $a * b * c$, computing in _any order_ gives the same result, but _some orders require far less work than others_.

To see this, note that convolving a length-$K$ filter with a length-$N$ signal costs at least $K \cdot N$ multiplications. Suppose $a$, $b$, and $c$ have lengths $A < B < C$. Then:

1. Computing $a * (b * c)$ first convolves $b * c$ (cost $BC$, length $B + C - 1$), then convolves $a$ with the result (cost $A(B + C - 1)$). The total is $BC + AB + AC - A$.
1. Computing $(a * b) * c$ first convolves $a * b$ (cost $AB$, length $A + B - 1$), then convolves with $c$ (cost $(A + B - 1)C$). The total is $AB + AC + BC - C$.

The two totals differ only in their final term: $-A$ versus $-C$. Since $C > A$, the second ordering subtracts more and therefore costs less. The lesson is that when convolving several signals, it pays to combine the _shorter_ ones first.

### Implementing convolution

Convolution translates directly into code. A literal transcription of the definition uses two nested loops, one over the output index $n$ and one over the filter index $k$:

```python
def convolve(x: np.ndarray, h: np.ndarray) -> np.ndarray:
    N, K = len(x), len(h)
    y = np.zeros(N + K - 1)
    for n in range(N + K - 1):
        for k in range(K):
            if 0 <= n - k < N:      # samples outside x are zero
                y[n] += h[k] * x[n - k]
    return y
```

The full runnable version, checked against NumPy's `np.convolve`, is in [code/convolve.py](./code/convolve.py). The two nested loops make the cost plain: producing $N + K - 1$ outputs, each a sum of up to $K$ products, is an $O(NK)$ computation. This is perfectly fine for the short filters behind simple difference equations. But as the filter length $K$ grows (sometimes _hundreds of thousands_ of samples long in practical scenarios), the quadratic cost becomes a serious problem. We will return to this shortly with a dramatically faster approach.

(sec-convolution-theorem)=

## The convolution theorem

We have defined convolution and seen that it generalizes difference equations, but it is not yet obvious that we have made progress toward our stated goal of _sculpting content in the frequency domain_. So far everything has happened in the time domain. The bridge between the two is one of the most important results in all of signal processing.

Change these to $[k]$ consistent w/ DFT chapter
:::{prf:theorem} The convolution theorem
:label: thm-convolution
Convolution in the time domain corresponds to _multiplication_ in the frequency domain. If $\purple{y} = \red{h} * \blue{x}$, then their DFTs satisfy

$$\purple{Y[m]} = \red{H[m]} \cdot \blue{X[m]}$$

at every frequency bin $m$.
:::

CLAUDE: Always use \cdot in this type of definition!
A proof is beyond the scope of this book (see {cite}`smith2007introduction` or {cite}`mcfee2023digital`), but the consequence is exactly what we were after. Convolving with a filter $h$ multiplies the spectrum of the input by $H$, the spectrum of the filter. So to boost or attenuate particular frequencies, we simply design a filter whose spectrum $H$ has the desired shape. This is precisely the frequency-sculpting picture from the start of the chapter, now made concrete: $|Y[m]| = |H[m]| \cdot |X[m]|$.

Let's draw an analogy to something we have already seen. Back in [Chapter 4](../04-score-timbre) we shaped a sound's loudness _over time_ by multiplying it by an amplitude envelope. The convolution theorem says that a filter is, in effect, an _envelope applied in the frequency domain_: $H$ is a shape we multiply the spectrum by, sculpting which frequencies come through, exactly as an amplitude envelope sculpts which moments in time come through.

The theorem also has a _dual_, obtained by swapping the roles of the two domains:

:::{prf:theorem} The convolution theorem (dual)
:label: thm-convolution-dual
Multiplication in the time domain corresponds to convolution in the frequency domain. Multiplying two signals sample-by-sample convolves their spectra.
:::

This dual form connects to several phenomena we have already encountered, each an instance of "multiplying in time smears in frequency":

1. In [Chapter 7](../07-sampling-theory), sampling was modeled as multiplying a signal by an impulse train in time. In frequency, this convolves the spectrum with an impulse train, producing the spectral copies that lead to _aliasing_.
1. In [Chapter 8](../08-dft), windowing a signal to a finite length meant multiplying by a rectangular window in time. In frequency, this convolves the spectrum with the window's spectrum, producing _spectral leakage_.
1. In [Chapter 6](../06-modulation), ring modulation multiplied one sinusoid by another in time. In frequency, this convolves their spectra, creating the _sidebands_ at sum and difference frequencies.

Seen this way, three seemingly different effects from three different chapters are all consquences of the convolution theorem.

### Leveraging the convolution theorem

The convolution theorem is not just conceptually satisfying, it is also enormously _practical_. Recall that directly convolving two signals of length $N$ costs $O(N^2)$ operations. The theorem offers a shortcut. Since convolution in time equals multiplication in frequency, we can convolve by transforming to the frequency domain, multiplying, and transforming back:

$$
\begin{aligned}
\red{h} * \blue{x} &= \texttt{IDFT}\big(\texttt{DFT}(\red{h}) \cdot \texttt{DFT}(\blue{x})\big) \\
                   &= \texttt{IFFT}\big(\texttt{FFT}(\red{h}) \cdot \texttt{FFT}(\blue{x})\big).
\end{aligned}
$$

The first line is just the convolution theorem read backwards, using the invertibility of the DFT from [Chapter 8](../08-dft). The second line swaps in the _fast_ Fourier transform (and its equally fast inverse) for the same result. Now count the cost: two forward FFTs and one inverse FFT are each $O(N \log N)$, and the sample-by-sample multiplication in between is only $O(N)$. The total is

$$O(N \log N) + O(N \log N) + O(N \log N) = O(N \log N),$$

a massive improvement over the $O(N^2)$ of direct convolution.

:::{note}
The constant factors still favor direct time-domain convolution for _short_ filters, but frequency-domain convolution wins as the filter grows, and for long filters it wins by a landslide. In practice, for a filter of length $K$ and a signal of length $N$, we first zero-pad both to a common length of at least $N + K - 1$ (so the circular wraparound of the DFT does not corrupt the result), rounded up to the nearest power of two so the FFT is maximally efficient.
:::

## Impulse response

Convolution is closely tied to a concept called the _impulse response_, which gives us yet another way to think about filters.

At the start of the chapter we defined a filter as a function $g : x \mapsto y$. Convolution by a fixed filter $h$ is one such function: it takes an input $x$ and returns $h * x$. Let us name it $g_h$, so that

$$g_h(x) = \red{h} * \blue{x}.$$

Now let's ask a simple question: what does this filter do to one very special input, the {vocab}`unit impulse`

$$\delta = [1, 0, 0, 0, \ldots],$$

a single one followed by infinitely many zeros? Conceptually, the unit impulse is silence everywhere except for an infinitesimally brief spike at time zero. A perfect impulse does not exist in the real world, but a balloon pop or a hand clap is not far off.

The {vocab}`impulse response` of a filter is simply its output when fed the unit impulse, namely $g(\delta)$. Let us compute it for $g_h$. Applying the convolution sum with $x = \delta$, and remembering that $\delta[n - k]$ is one only when $k = n$ and zero otherwise:

CLAUDE: Using red/blue color coding here to make this more clear

$$
\begin{aligned}
g_h(\delta)[0] &= h[0]\delta[0] + h[1]\delta[-1] + \cdots = h[0] \cdot 1 = h[0], \\
g_h(\delta)[1] &= h[0]\delta[1] + h[1]\delta[0] + \cdots = h[1] \cdot 1 = h[1], \\
g_h(\delta)[2] &= h[0]\delta[2] + h[1]\delta[1] + h[2]\delta[0] + \cdots = h[2], \\
&\;\;\vdots
\end{aligned}
$$

The punch line here is simple:

$$g_h(\delta) = \red{h}.$$

**The impulse response of the "convolve by $h$" filter is just $h$ itself.** The unit impulse "picks out" the coefficients of $h$ one at a time. This is why the $h$ coefficients are referred to as an _impulse response_: it is literally the filter's response to an impulse. It also establishes a clean one-to-one correspondence: a difference equation's coefficients _are_ its impulse response, so we can translate freely between the two views.

### Designing impulse responses

Because a filter is completely characterized by its impulse response, and because the same convolution operation implements _any_ impulse response, we can _design_ filters with specific time-domain behaviors just by choosing the numbers in $h$. Here are a few useful ones:

:::{list-table}
:header-rows: 1
:name: tbl-impulse-designs

- - Desired behavior
  - Impulse response $h$
- - Delay the signal by 3 samples
  - $[0, 0, 0, 1]$
- - Apply a gain of 5 (no delay)
  - $[5]$
- - Mix the signal with a 1-sample-delayed copy
  - $[1, 1]$
- - Pass the signal through unchanged (identity)
    - $[1]$
      :::

The last one is worth a remark. The impulse response $h = [1] = \delta$ leaves the signal untouched, because $\delta * x = x$. The unit impulse is the _identity element_ for convolution, playing the same role that $1$ plays for ordinary multiplication.

### Real-world impulse responses

The impulse response also gives us a way to _reverse engineer_ a filter we did not design. Suppose someone hands you a mysterious black box that filters audio, and you want to know what it does. Just feed it an impulse and record the output. That output _is_ the impulse response, and (for an LTI filter) it tells you everything about the box: to reproduce the box's effect on any other signal, you convolve that signal with the recorded impulse response.

This idea is the basis of {vocab}`convolution reverb`. The acoustics of a physical space (a concert hall, a stairwell, a cathedral) act as an LTI filter: the space delays, attenuates, and mixes together countless reflections of whatever sound is produced in it. We can capture that entire acoustic signature by recording the space's impulse response, approximated by popping a balloon or firing a starter pistol and recording the reverberant decay. Convolving any dry recording with that impulse response makes it sound as though it were played in that space.

CLAUDE: can we just incorporate the gif exactly from mcfee? I would rather grab that gif and embed it cleanly here with an attribution to DST book, then make a copy of it that could be viewed as attempting to subvert plagiarism detection
:::{figure}
![An animation of a room shown from above, with a sound source at one point and a microphone at another. A sound emitted at the source spreads outward and bounces off the walls, and the direct path plus each reflected path arrives at the microphone at a different delay and amplitude, building up the room's impulse response over time.](./assets/fig-room-ir.gif)

A room's impulse response is built up from the direct sound plus a growing collection of delayed, attenuated reflections off the walls, floor, and ceiling. Convolving a dry signal with this response simulates playing the signal in the room. Animation after {cite}`mcfee2023digital`.
:::

With a recorded impulse response in hand, applying convolution reverb is just a single convolution. The example below convolves a dry marimba loop with the recorded impulse response of a real church (resampling the dry sound to match the impulse response's sample rate first). Listen for the way the marimba suddenly acquires the long, echoing tail of the space:

:::{interactive}[notebooks/convolution-reverb.ipynb]
:::

:::{note}
Dry sound: [Marimba loop 3](https://freesound.org/s/522193/) by BrickDeveloper171, License: [CC0](http://creativecommons.org/publicdomain/zero/1.0/). Impulse response: [IR_Church_01](https://freesound.org/s/474296/) by snapssound, License: [Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).
:::

(sec-lti)=

## Linear, time-invariant filters

We have been calling convolution an _LTI_ filter without justifying the name. Now we can. LTI stands for two properties, _linearity_ and _time-invariance_, and convolution has both.

A filter is {vocab}`linear` if it respects scaling and addition:

1. **Consistency over gain.** Scaling the input scales the output by the same factor: $\;h * (A \cdot x) = A \cdot (h * x)$ for any constant $A$.
1. **Consistency over mixtures.** The response to a sum of inputs is the sum of the responses: $\;h * (x_1 + x_2) = h * x_1 + h * x_2$.

A filter is {vocab}`time-invariant` if delaying the input merely delays the output by the same amount, without otherwise changing it. Writing $\Delta_d = [0, 0, \ldots, 0, 1]$ for the impulse response that delays by $d$ samples,

$$h * (\Delta_d * x) = \Delta_d * (h * x) \quad \text{for all } d \ge 0.$$

In words, it makes no difference whether you delay first and then filter, or filter first and then delay. Both properties follow directly from the algebra of the convolution sum (linearity from the fact that the sum is built from multiplication and addition, time-invariance from the fact that the coefficients $h[k]$ do not depend on $n$).

CLAUDE: Is the converse really true? Wouldn't we need to qualify this statement: that the impulse response may need to be of infinite length?
**Convolution is therefore a linear, time-invariant filter.** In fact, the converse is also true, though we will not prove it: _every_ LTI filter can be written as a convolution with some impulse response. This is a remarkably strong statement. It means the humble convolution sum captures the entire universe of LTI filters, and it is why the impulse response is such a powerful tool.

CLAUDE: This needs to be emphasized more strongly. it's the main reason we care about this
The defining feature of LTI filters, and the reason they are so convenient for computer music, **is that LTI filters _cannot_ add new frequency content**. They only boost or attenuate the frequencies already present.

## Recursive filters

CHRIS: BOOKMARK!!

Every filter we have seen so far computes its output purely from the _input_. But there is no reason a difference equation cannot also refer to _past outputs_. Filters that do are called {vocab}`recursive filters`, and they open up a large and powerful new class of behaviors.

### Signal-flow diagrams

Recursive filters are often best understood visually, as a {vocab}`signal-flow diagram`. This is yet another perspective on filters, complementing difference equations, convolution, and impulse responses. The diagrams are built from three elements: wires that carry a signal, a summing junction (drawn as a circled plus) that adds signals together, and a _delay block_ labeled $z^{-1}$, which delays its input by exactly one sample, mapping $x[n]$ to $x[n-1]$.

:::{margin}
The notation $z^{-1}$ comes from the _z-transform_, a generalization of the DFT that is the standard tool for analyzing recursive filters. We won't cover the z-transform in this course, but we will still adopt the conventional $z^{-N}$ notation in signal flow diagrams for a delay of $N$ sample. Note that delaying by one sample is itself just convolution with the impulse response $\color{red}{h} = [0, 1]$.
:::

CLAUDE: Could you make the font size a bit larger here? Also, the centering is way off in this figure. Look at the image and try again. Also, for the recursive, change to Recursive (feedback only) and draw out y[n] = x[n] + y[n-1], that way the contrast between feedforward and feedback is more clear.
:::{figure}
![Two signal-flow diagrams side by side. Left, labeled ordinary: the input x[n] splits, one path going straight to a summing junction and another passing through a z-to-the-minus-one delay block before reaching the junction, whose output is y[n]; the equation is y[n] = x[n] + x[n-1]. Right, labeled recursive: the same feedforward structure, but the output y[n] is also tapped and fed back through a second z-to-the-minus-one block into the summing junction; the equation is y[n] = x[n] + x[n-1] + y[n-1].](./assets/fig-recursive-signalflow.png)

Left: an ordinary (feedforward) filter, $y[n] = x[n] + x[n-1]$, whose output depends only on the input. Right: a recursive filter, $y[n] = x[n] + x[n-1] + y[n-1]$, which adds a _feedback_ path from the output back into the sum.
:::

The left diagram is an ordinary filter: the input flows forward through delays and sums to the output. The right diagram adds a _feedback_ loop, tapping the output, delaying it, and feeding it back in. This feedback is what makes the filter recursive.

### Feedforward and feedback

We can generalize the difference equation to include both past inputs and past outputs.

CLAUDE: split the sum into two lines to avoid it being too long horizontally. change label for first term of sum to feedfoward (convolution). update caption accordingly, mentioning succinctly that the $b_i$ coefficients are the same as $\red{h}$ and are referred to as $b$ by convention in the context of recursive filters. also mention $M$ and $L$ explicitly here, since we use them below. finally, note the absence of $a_0$, as $y[n]$ cannot depend on $y[n]$ itself
:::{prf:definition} General recursive difference equation
:label: def-recursive
A recursive filter is defined by

$$y[n] = \underbrace{b_0\,x[n] + b_1\,x[n-1] + \cdots + b_M\,x[n-M]}_{\text{feedforward}} + \underbrace{a_1\,y[n-1] + \cdots + a_L\,y[n-L]}_{\text{feedback}}.$$

The constants $b_i$ are the {vocab}`feedforward coefficients` and the $a_j$ are the {vocab}`feedback coefficients`. Together they are the filter's _coefficients_.
:::

CLAUDE: this is confusing... $M$ and $L$ are sort of undefined until now. add them to the caption above
Two facts about this general form are worth committing to memory. First, **every filter of this form is LTI**, feedback and all. Second, the {vocab}`order` of the filter is the largest delay it uses, $\max(M, L)$. For example, $y[n] = x[n] + x[n-1] + \tfrac{1}{3}y[n-2]$ has $M = 1$ and $L = 2$, so it is a second-order filter.

Recursive filters are commonplace in computer music because they can achieve higher-quality frequency responses with very few coefficients (and thus very little computation) compared to the equivalent non-recursive filter. More on "higher-quality" frequency responses in the next section!

### Finite and infinite impulse responses

Feedback has a striking consequence for the impulse response. Consider the simplest recursive filter,

$$y[n] = x[n] + y[n-1].$$

CLAUDE: Spell this out more clearly in a latex block rather than inline prose, defining y[0] = x[0] + y[-1] = 1 + 0, then y[1] = x[1] + y[0] = 0 + 1, then y[2] = x[2] + y[1] = 0 + x, then ...
What is its response to the unit impulse $\delta = [1, 0, 0, \ldots]$? The output at $n = 0$ is $1$. At $n = 1$ the input is zero, but the filter adds the previous output, giving $y[1] = 0 + 1 = 1$. The same happens forever: the impulse response is $[1, 1, 1, 1, \ldots]$, _infinitely long_. This filter accumulates a running sum of its input.

This distinguishes two families of filters:

1. A filter with only feedforward coefficients has a {vocab}`finite impulse response` (FIR) equal to the coefficients themselves. Its impulse response has as many nonzero samples as it has coefficients, and then stops.
1. A recursive filter (with feedback) generally has an {vocab}`infinite impulse response` (IIR). The feedback keeps the response going forever.

With feedback comes a new danger: an IIR filter can be {vocab}`unstable`. Compare two filters. The filter $y[n] = x[n] + 0.9\,y[n-1]$ is _stable_: each pass through the loop shrinks the signal by a factor of $0.9$, so its impulse response $[1, 0.9, 0.81, \ldots]$ decays toward zero. But $y[n] = x[n] + 1.1\,y[n-1]$ is _unstable_: each pass _amplifies_ the signal by $1.1$, so its impulse response $[1, 1.1, 1.21, \ldots]$ grows without bound and quickly explodes into a deafening blowup. Designing stable recursive filters is a central concern of filter design.

For implementation, an IIR filter must generally be run as a difference equation, computing each output from previous outputs, rather than as a direct convolution (its impulse response is infinite, so we cannot convolve with all of it). That said, the impulse response of a _stable_ IIR filter decays, so in practice we can approximate it by a finite one: run the impulse response until it has decayed below some threshold (say $60$ dB down, $|y[n]| \le 0.001$), truncate it there, and convolve with the result.

CLAUDE: Add an interactive code example here. filter is $y[n] = x[n] + 0.95 y[n-100]$. compute its impulse response and the point at which it hits -60dB. plot result and cutoff threshold

## Filter types

CLAUDE: Oh whoops it looks like I totally forgot to give you my 07B slides, so this is missing a lot. in particular, let's start w/ idealized filter anatomy 2x2 from slide 20, highlighting passband/stopband/bandwidth/f*C for all. forget about f_H and f_L in those figures, just put f_C in middle of bandpass/stop. next, do a 2x1 figure just showing more real-world filters, showing a low pass filter w/ -6dB horizontal line (intersecting w/ cutoff frequency) and -60dB line creating a "transition band" (see slide 22). finally, show a band pass filter w/ higher quality, highlighting f_L and f_H as intersection points w/ -6dB to highlight the bandwidth. similar to 23 but band pass instead of resonant LP. define \_quality* of a filter as well

LTI filters are often categorized by the _shape_ of their frequency response, that is, by which bands of frequencies they pass and which they reject. A handful of shapes are so common that they have standard names.

:::{figure}
![Four idealized magnitude responses, each a plot of the gain from 0 to f_s over 2. Low pass: gain near one at low frequencies, rolling off to zero above a cutoff, with the passband, stopband, and cutoff labeled. High pass: the mirror image, zero at low frequencies rising to one above the cutoff. Band pass: gain near one only within a band between two cutoffs, zero outside. Band stop or notch: gain near one everywhere except a rejected band between two cutoffs.](./assets/fig-filter-types.png)

The four canonical filter shapes, drawn as idealized magnitude responses. The {vocab}`passband` (shaded) is the range of frequencies that pass through with little attenuation, the {vocab}`stopband` is the range that is rejected, and the {vocab}`cutoff frequency` $f_c$ marks the boundary between them.
:::

1. A {vocab}`low-pass` filter passes low frequencies and attenuates those above its cutoff. Rolling off a sound's treble to make it darker or muffled is a low-pass.
1. A {vocab}`high-pass` filter does the opposite, passing high frequencies and attenuating those below its cutoff. Removing low-frequency rumble is a high-pass.
1. A {vocab}`band-pass` filter passes a band of frequencies around a center frequency and attenuates everything else. A telephone or a "lo-fi" effect is roughly band-pass.
1. A {vocab}`band-stop` filter, also called a {vocab}`notch`, is the inverse: it rejects a narrow band and passes everything else. Removing a single offending hum frequency is a notch.

Real filters cannot achieve the perfectly sharp "brick wall" edges drawn above. Every practical filter has a gradual _transition band_ between passband and stopband, and the steepness of that transition is one of the main things filter design trades off against cost.

## Analyzing filters

We have looked at filters both in their low-level _implementation_ (difference equations, convolution) and in their high-level _behavior_ (sculpting in frequency domain, convolution theorem). But how might we connect the two? We have two directions to worry about. Given a filter (its difference equation or impulse response), how do _analyze_ its frequency response, to know what it will do to a sound? And conversely, given a desired frequency response, how do we _desing_ a filter that achieves it? There are entire textbooks written on these questions. In this book, we will consider filter design as explicitly out of scope, and present just a cursory empirical view of filter analysis here.

CLAUDE: Take another crack at this section now that you have slides 28/29. start w/ my revised intro paragraph above. then continue by walking students through manual testing of a difference equation at 0 Hz, f_s/4, and f_s/2, which is enough to suggest a behavior among the canonical types. Then, show the code example of more exhaustive empirical testing, highlighting the inter-sample peak amplitue issue that can cause the empirical method to undershoot the analytical.

The empirical idea is simple and follows directly from what an LTI filter does: it scales each frequency by some amount. So to measure the response at a given frequency, we _feed the filter a pure sinusoid at that frequency and measure how much the output amplitude changed_. Sweeping the test frequency from $0$ up to the Nyquist frequency traces out the filter's whole {vocab}`frequency response`. The figure below does this for the two-tap averager $y[n] = x[n] + x[n-1]$:

:::{figure}
![A plot of output amplitude versus frequency from 0 to the Nyquist frequency, about 24 kHz. Blue stems mark the measured output amplitude at forty probe frequencies, starting near 2 at low frequencies and falling smoothly to 0 at Nyquist. A red curve, the analytical response two times the absolute value of cosine of pi f over f_s, passes exactly through every measured point.](./assets/fig-frequency-response.png)

The empirically measured frequency response of $y[n] = x[n] + x[n-1]$ (blue stems), obtained by probing with sinusoids, matches the analytical response $2\,|\cos(\pi f / f_s)|$ (red). Summing a signal with a one-sample-delayed copy is a gentle low-pass filter: it passes low frequencies at nearly double amplitude and fully cancels the Nyquist frequency.
:::

The measured points fall exactly on the curve $2\,|\cos(\pi f / f_s)|$. This closed form can be derived analytically rather than measured, but the derivation is beyond our scope. Interested readers can find it worked through in {cite}`smith2007introduction`. The empirical method, by contrast, requires no derivation at all and works for any filter you can run. You can measure the response of your own filters, including ones you invent, in the following example:

:::{interactive}[notebooks/frequency-response.ipynb]
:::

:::{note}
We have only measured the _amplitude_ response, how much each frequency is scaled. LTI filters also affect _phase_, shifting each frequency in time, described by the filter's _phase response_ $\angle H(\omega)$. Phase matters whenever filtered signals are mixed back together, where it governs constructive and destructive interference, and it can be manipulated creatively (a guitar "phaser" is one example). An {vocab}`all-pass` filter is designed to leave every amplitude untouched while altering only the phase.
:::

## Subtractive synthesis

We opened this chapter by contrasting synthesis with processing, but filters can be a _synthesis_ tool in their own right. {vocab}`Subtractive synthesis` starts from a harmonically rich source (often noise or a buzzy waveform like a sawtooth) and _carves away_ frequencies with filters to shape a timbre. It is the founding principle of the classic analog synthesizer, and the complement of the additive synthesis from [Chapter 3](../03-additive-synthesis): rather than building a sound up from sinusoids, we start with everything and subtract.

CLAUDE: include somthing like the diagram I have on slide 26.

For these examples we use a small library of ready-made filter designs, `rbj.py`, which implements Robert Bristow-Johnson's widely used ["Audio EQ Cookbook"](https://www.musicdsp.org/en/latest/_downloads/3e1dc886e7849251d6747b194d482272/Audio-EQ-Cookbook.txt) formulas {cite}`bristowjohnson2016cookbook`. Each function returns the feedforward and feedback coefficients ($b$ and $a$) of a second-order recursive filter (a _biquad_), ready to apply with SciPy's `lfilter`.

Our first example filters white noise, whose spectrum is flat (equal energy at all frequencies) and therefore a perfect raw material. A low-pass version keeps only the lows for a soft "thump", and a high-pass version keeps only the highs for a crisp "tick". Arranging the two with a {pyquist}`Score` produces a simple drum-like rhythm:

:::{interactive}[notebooks/subtractive-noise.ipynb]
:::

Our second example is the sound most associated with subtractive synthesis: a _resonant filter sweep_. We start with a bright sawtooth-like tone and pass it through a resonant low-pass filter (one with a pronounced peak at its cutoff), then _move the cutoff frequency over time_. As the cutoff sweeps up and down, it emphasizes different harmonics in turn.

:::{interactive}[notebooks/subtractive-sweep.ipynb]
:::

## Summary

- A {vocab}`filter` is any function that maps an input signal to an output signal. We focused on {vocab}`linear time-invariant` (LTI) filters, which sculpt a sound in the frequency domain without adding new frequencies.
- A {vocab}`difference equation` defines a filter by writing each output sample as a weighted sum of past input (and possibly output) samples. It is trivial to implement but hard to predict by inspection.
- {vocab}`Convolution`, $y = h * x = \sum_k h[k]\,x[n-k]$, generalizes the (non-recursive) difference equation. It is commutative, associative, and distributive, and produces an output of length $N + K - 1$.
- The {vocab}`convolution theorem` states that convolution in time equals multiplication in frequency, $Y[m] = H[m]\,X[m]$. This is how filters sculpt the spectrum, and (via the FFT) it lets us convolve in $O(N \log N)$ instead of $O(N^2)$.
- The {vocab}`impulse response` $h$ is a filter's output to a unit impulse. It fully characterizes an LTI filter, and every LTI filter is a convolution with its impulse response.
- {vocab}`Recursive filters` feed past outputs back into the sum. They are efficient but can have an {vocab}`infinite impulse response` and can be {vocab}`unstable`.
- Filters are categorized by response shape ({vocab}`low-pass`, {vocab}`high-pass`, {vocab}`band-pass`, {vocab}`band-stop`), and a filter's frequency response can be measured empirically by probing it with sinusoids.
- {vocab}`Subtractive synthesis` uses filters as a synthesis tool, carving a timbre out of a harmonically rich source.
- Filtering can be viewed in many equivalent forms: a difference equation, a convolution, an impulse response, a signal-flow diagram, or a multiplication in the frequency domain.

## Questions for the reader

:::{exercise}
**Impulse response from a difference equation.** A filter is defined by $y[n] = \tfrac{1}{3}x[n] + x[n-2]$. Write down its impulse response $h$, and state its length $K$.
:::

:::{exercise}
**Difference equation from an impulse response.** A filter has impulse response $h = [1, 0, -1]$. Write down the difference equation for $y[n]$. Is this filter FIR or IIR, and why?
:::

:::{exercise}
**Signal-flow diagrams.** Draw a signal-flow diagram (using $z^{-1}$ delay blocks and a summing junction) for the filter $y[n] = x[n] - \tfrac{1}{2}x[n-1] + \tfrac{1}{4}y[n-1]$. Label the feedforward and feedback paths, and state the filter's order.
:::

:::{exercise}
**Proving the properties of convolution.** Starting from the summation definition $\,(h * x)[n] = \sum_k h[k]\,x[n-k]$, prove that convolution is (a) commutative and (b) distributive over addition. For commutativity, the substitution $m = n - k$ is helpful.
:::

:::{exercise}
**Ordering a chain of convolutions.** You must compute $a * b * c$, where $a$, $b$, and $c$ have lengths $2$, $10$, and $1000$. Using the multiplication count $KN$ for convolving a length-$K$ filter with a length-$N$ signal, compute the total cost of $(a * b) * c$ versus $a * (b * c)$. Which ordering is cheaper, and does it agree with the "combine the shortest first" rule of thumb?
:::

:::{exercise}
**Stability.** For the recursive filter $y[n] = x[n] + a\,y[n-1]$, write out the first five samples of the impulse response in terms of $a$. For which values of $a$ does the impulse response decay to zero, and for which does it grow without bound?
:::

:::{exercise}
**Identifying a filter's type.** The two-tap averager $y[n] = x[n] + x[n-1]$ has frequency response $2\,|\cos(\pi f / f_s)|$. Evaluate the response at $f = 0$ and at the Nyquist frequency $f = f_s/2$. Based on these two values, is this a low-pass or a high-pass filter?
:::

## Musical examples

Filtering is not merely a technical tool. It is a core expressive device across a century of music.

Alvin Lucier - _I Am Sitting in a Room_ (1969) is the quintessential demonstration of filtering, feedback, and room acoustics. Lucier recorded himself speaking, then played the recording back into the room and re-recorded it, and repeated this cycle dozens of times. Each pass convolves the sound with the room's impulse response once more. The frequencies the room emphasizes grow louder with every iteration and the rest fade away, until the intelligible speech dissolves into the pure resonant tones of the room itself. It is the convolution reverb of this chapter, applied over and over until the filter's frequency response is all that remains.

Daft Punk - _Voyager_ (2001) is a showcase of subtractive synthesis in popular music. Nearly every part leans on filtering for its character: gentle low-pass and high-pass motion opens and closes the pads, and a resonant low-pass sweep gives the bassline its vocal, funky "wah". It is a compact tour of the filter types and the resonant sweep from this chapter, deployed for groove.
