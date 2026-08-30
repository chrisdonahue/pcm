---
title: "Chapter 0: Motivating Computer Music"
---

# Motivating Computer Music

Welcome to _Principles of Computer Music_! Before we dive into the principles themselves, we'll begin by providing some general motivation for the study of computer music. Perhaps the strongest argument: technology has always expanded the boundaries of creative possibilites in music, and computer music continues to define the forefront of music technology.

:::{seealso}
For a general overview of _Principles of Computer Music_, see the [textbook frontmatter](../index.md).
:::

## Why study computer music?

Have you ever wondered how sound and music are stored on and processed by computers? Or how any song can be efficiently streamed to your phone over the network? Or how plugins in your digital audio workstation are working behind the scenes? If so, then you are already asking questions in the domain of _computer music_. This book is an invitation to take those questions seriously, and to develop the **technical principles** needed to answer them rigorously.

### Music and computation are inextricably linked

Computing has become ubiquitous within everyday music practice. When you stream a song on your phone, computers are compressing audio, buffering it across a network, and converting digital samples back into sound. When a producer mixes a track in a digital audio workstation (DAW), they are orchestrating thousands of computations per second to filter, equalize, and combine signals. When you attend a live show, digital mixing consoles route, equalize, and apply effects to every signal coming off the stage in real time, while in-ear monitor systems compute a personalized mix for each performer.

Even before the advent of digital computers, music and _computation_ in the broader sense have been deeply entwined. The earliest theories of musical instruments were built on numerical relationships: Pythagorean ratios between string lengths, the mathematics of consonance and dissonance. Some of the deepest properties of music, such as pitch and rhythm, are fundamentally about _periodicity_: patterns that repeat in time at definable rates. To study music carefully is, almost unavoidably, to study computation and mathematics.

If you are interested in better understanding these relationships, then computer music is for you.

### Technology is upstream of musical possibility

Music and technology have always co-evolved. In the hands of musicians, new technologies expand the creative and cultural boundaries of what music can be. A pervasive theme throughout music history is that each major technological development opens up new creative opportunities for artists, opportunities that often could not even be articulated until the technology made them imaginable.

The pianoforte's expressive dynamic range allowed Beethoven to compose his [sonatas](https://www.youtube.com/watch?v=4Tr0otuiQuU) in a way that would have been impossible on the harpsichord. The Beatles wielded the entire studio as an instrument, using multitrack recording technology to make an album like [_Revolver_](https://www.youtube.com/watch?v=UVgJLy_aJwI) conceivable. Amplification and electricity transformed the electric guitar into [Jimi Hendrix's voice](https://www.youtube.com/watch?v=qFfnlYbFEiE). Digital sampling let Kate Bush build the sonic world of [_Hounds of Love_](https://www.youtube.com/watch?v=wp43OdtAAkM) from fragments of real-world sound.

If you are interested in building new computing tools that may expand the possibilities of music, then computer music is for you.

(sec-fm-inspiration)=

### Inspiration: _FM Synthesis_

To make this concrete, consider one of the most influential episodes in the history of computer music: John Chowning's invention of _frequency modulation (FM) synthesis_ {cite}`chowning1973synthesis`. Chowning's work is a kind of "full stack" example of what computer music can be, weaving together _acoustics_, _mathematical theory_, _programming_, _instrument design_, and ultimately _musical culture_.

- _Music acoustics_: Real musical sounds are not pure tones. They contain rich mixtures of many time-varying periodic components that fade in, fade out, and shift in relative strength over the duration of a note. Synthesizing such sounds convincingly is challenging, especially with the limited compute available in the 1970s, because each component nominally requires its own oscillator. Consider, for example, the dense spectral fingerprint of a percussive chime instrument:

  :::{audio}
  [Orchestral chime](./assets/fs192645-chime.wav)

  Orchestral chime. [chimes_f#3_p_1.wav](https://freesound.org/s/192645/) by sgossner, License: [Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).
  :::

:::{margin} SAIL
The Stanford Artificial Intelligence Laboratory (1963–1980) was a pioneering AI research center where foundational work in robotics and computer music synthesis emerged.
:::

- _Mathematical theory_: Working at the Stanford Artificial Intelligence Laboratory (SAIL), Chowning realized that the well-known method of frequency modulation, when applied in the audio range, produces infinitely complex spectra by chaining just two simple sinusoidal components together in a particular way. The basic FM equation is

  $$x(t) = \sin\left(2 \pi f_c t + I \sin(2 \pi f_m t)\right).$$

If this doesn't mean much to you now, no worries - you'll learn more about this equation and its parameters when we {ref}`study FM in detail <sec-frequency-modulation>` later in this text. Focus for now on the high level: Chowning showed that, by carefully controlling these parameters over time, this single equation could imitate a striking range of natural musical sounds:

:::{audio}
[FM bell sound](./assets/bell-fm.mp3)

FM bell sound synthesized using Csound `fmbell`.
:::

- _Efficient programming_: The mathematical elegance of FM is only useful if it can be _computed_ fast enough (tens of thousands of times per second) to produce a continuous audio stream. This requires careful, efficient implementations, bringing an _algorithmic_ perspective to computer music. In Python, an efficient FM synthesizer might look something like:

```python
def fm(f_c, f_m, I, f_s, T):
    audio = [0.0] * int(f_s * T)  # audio buffer
    p_c, p_m = 0.0, 0.0  # carrier/modulator phase in radians
    d_c, d_m = (2.0 * math.pi * f / f_s for f in (f_c, f_m))  # radians per sample
    for i in range(len(audio)):
        audio[i] = sin_fast(p_c + I * sin_fast(p_m))
        p_c, p_m = p_c + d_c, p_m + d_m
    return audio
```

Observe a few high-level changes from the formula above: (1) we're using discrete computation instead of continuous math, (2) we're pre-computing some operations outside of the for loop, and (3) we're calling `sin_fast` which uses a pre-computed lookup table (see the [full example here](./code/fm.py)). These were essential optimizations in 1973, and remain useful today, e.g., for running many FM synthesizers in parallel in your DAW.

:::{margin} DX7
Released in 1983 at roughly \$2,000, the DX7 sold over 200,000 units and was the synth that made FM mainstream. The patent on FM was [one of the most lucrative in Stanford's history](https://ccrma.stanford.edu/news/father-of-digital-synthesizer).
:::

- _Instrument design_: Yamaha licensed FM as the synthesis engine in the legendary [DX7 synthesizer](https://en.wikipedia.org/wiki/Yamaha_DX7), turning a research result into a piece of hardware that could be played on stage and in the studio.

  :::{figure}
  ![Photo of a Yamaha DX7 synthesizer](./assets/dx7.png)

  The Yamaha DX7 (1983), the first commercially successful digital synthesizer, brought Chowning's FM synthesis to musicians worldwide.
  :::

- _Music culture_: The DX7 was adopted by thousands of musicians and became, in many ways, _the_ sound of the 1980s. Ironically, while FM had originally been explored as a way to _imitate_ existing acoustic instruments, musicians ended up preferring the synthesizer's ability to create entirely _novel_ sounds that no acoustic instrument could produce. You can hear the DX7 unmistakably in tracks like [A-ha — "Take On Me"](https://www.youtube.com/watch?v=djV11Xbc914) and [Whitney Houston — "Didn't We Almost Have It All"](https://www.youtube.com/watch?v=c0TghfreFok).

A mathematical insight, inspired by acoustics, refined into an algorithm, embodied in a piece of hardware, became a defining aesthetic of an era. This is the kind of impact that computer music makes possible.

Try FM synthesis yourself below: the same equation, with sliders for its three parameters.

:::{interactive}[notebooks/fm-playground.ipynb]
:::

### Computing is the frontier of music technology

Computation is now a key component of music on stage, in the studio, and in your ears. From software synthesizers to streaming codecs to noise-cancelling headphones, computation is increasingly synonymous with music. It is, in most contexts, the mechanism through which music is made, distributed, and experienced.

This trend of music and technology co-evolving will almost certainly continue as we venture into new technologies such as artificial intelligence. Like past technological developments (recording, amplification, sampling) these newer technologies will likely reshape the economic landscape of music, but they will also present new creative opportunities for those who learn to use them thoughtfully. If you are interested in understanding how computers synthesize, manipulate, and ultimately reshape musical sound, then computer music is for you.

## Who is this book for?

At its core, this book on computer music is written from a _computer science_ perspective. It is highly technical, and it is intended to support computer science courses on musical computing, much in the way that established texts support courses on computer graphics. We _will_ assume substantial background experience in programming and mathematics. We will _not_ assume much musical expertise, though musical training will be a helpful bonus for absorbing this material.

You don't need to be an expert in both music and computing to read this text, but there is an unfortunate asymmetry to be aware of:

- Students with a strong music background and weak computing background may struggle, and should study introductory computer science and programming first.
- Students with a strong computing background and weak music background should be fine.

In more detail:

- _Programming_: This book assumes substantial familiarity with Python programming and basic computer science (e.g., data structures, Big O notation). If you are unfamiliar with these, you should learn the basics before proceeding.
- _Math_: You should be reasonably comfortable with trigonometry, basic calculus, and complex numbers. You won't have to do much derivation here, but you'll need to understand these concepts at least at a high level. It's okay if your skills are rusty — it should be possible to brush the dust off as you go through the book.
- _Music_: We aspire to make this book accessible even to those without any formal musical training. However, you will benefit from a basic foundation in musical concepts like pitch, and from an enthusiastic and discerning ear for music.

## What will readers learn from this book?

By the end of this book, you should understand:

- How to program a computer to efficiently store, synthesize, and process musical sound.
- The foundational principles of sampling, digital signal processing, and the frequency domain that should transfer readily to many other areas of computing.
- Exposure to a breadth of specific computer music topics (sampling, physical modeling, music AI, etc.) that build on these foundational principles.

## Why was this book written?

This book was written to support computer music courses taught from a computer science perspective. In the long term, the author's hope is that _computer music may come to be viewed as a first-class citizen of computer science_, alongside similarly applied domains like computer graphics.

The book was also written to fulfill a perceived gap in the existing computer music literature. It aims to:

- Teach the material in a modern and accessible programming language (Python).
- Maintain the level of technical rigor expected of computer science texts, while keeping the focus empirical and not going _too_ deep into the theory.
- Stay grounded in technical correctness while also touching on creative practice.

This book was heavily inspired by _Digital Signals Theory_ by {cite}`mcfee2023digital`. More broadly, it stands on the shoulders of giants, drawing inspiration from other texts like {cite}`roads1996computer`, {cite}`dannenberg2024intro`, {cite}`smith2007mathematics`, among others. This book is intended to _complement_ those works, not to supersede them.

## Musical examples

### a-ha - _Take On Me_ (1985)

The song's instantly recognizable synth hook is a Yamaha DX7 riff, an archetypal example of FM synthesis defining the sound of 1980s pop. The DX7 could produce novel timbres that earlier analog synthesizers could not, and this track puts them front and center.

<iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/djV11Xbc914" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

### Whitney Houston - _Saving All My Love for You_ (1985)

The DX7's famous "E.PIANO 1" patch was prominently featured in the instrumental backing track of many Whitney Houston recordings.

<iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/ewxmv2tyeRs" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
