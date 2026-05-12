---
title: "Chapter 0: Computer Music"
---

# Computer Music

## Why study computer music?

If you have ever been curious about how the music in your headphones is conjured into existence — how a melody is captured, encoded, transformed, and ultimately reconstituted as vibrations in your eardrum — then you are already asking questions in the domain of _computer music_. This book is an invitation to take those questions seriously, and to develop the technical foundation needed to answer them rigorously.

### Music and computation are inextricably linked

Nearly every encounter you have with music today is mediated by computation. When you stream a song on your phone, computers are decoding compressed audio, buffering it across a network, and converting digital samples back into sound. When a producer mixes a track in a digital audio workstation (DAW), they are orchestrating thousands of computations per second to filter, equalize, and combine signals. When a researcher trains a generative model to compose new music, computation becomes the very engine of creation.

Even before the advent of digital computers, music and _computation_ in the broader sense have been deeply entwined. The earliest theories of musical instruments were built on numerical relationships — Pythagorean ratios between string lengths, the mathematics of consonance and dissonance — and the deepest properties of music, such as pitch and rhythm, are fundamentally about _periodicity_: patterns that repeat in time at definable rates. To study music carefully is, almost unavoidably, to study a kind of computation.

If you are interested in better understanding these relationships, then computer music is for you.

### Technology is upstream of musical possibility

Music and technology have always co-evolved. In the hands of musicians, new technologies expand the creative and cultural boundaries of what music can be. A pervasive theme throughout music history is that each major technological development opens up new creative opportunities for artists — opportunities that often could not even be articulated until the technology made them imaginable.

The pianoforte's expressive dynamic range allowed Beethoven to compose his sonatas in a way that would have been impossible on the harpsichord. Multitrack recording gave The Beatles the studio as an instrument, and made an album like _Revolver_ conceivable. Amplification and electricity transformed the electric guitar into Jimi Hendrix's voice. Digital sampling let Kate Bush build the sonic world of _Hounds of Love_ from fragments of real-world sound.

If you are interested in building new computing tools that may expand the possibilities of music, then computer music is for you.

### Inspiration: _FM Synthesis_

To make this concrete, consider one of the most influential episodes in the history of computer music: John Chowning's discovery of _frequency modulation (FM) synthesis_, published in 1976 in the _Computer Music Journal_. Chowning's work is a kind of "full stack" example of what computer music can be, weaving together _acoustics_, _mathematical theory_, _programming_, _instrument design_, and ultimately _musical culture_.

- _Music acoustics_: Real musical sounds are not pure tones. They contain rich mixtures of many time-varying periodic components — partials that fade in, fade out, and shift in relative strength over the duration of a note. Synthesizing such sounds convincingly is challenging, especially with the limited compute available in the 1970s, because each component nominally requires its own oscillator. Consider, for example, the dense spectral fingerprint of a percussive chime instrument:

  <audio src="./assets/fs192645-chime.wav">Orchestral chime. Obtained from Freesound. chimes_f#3_p_1.wav by sgossner -- https://freesound.org/s/192645/ -- License: Attribution 4.0</audio>

- _Mathematical theory_: Working at the Stanford Artificial Intelligence Laboratory (SAIL), Chowning realized that the well-known method of frequency modulation, when applied in the audio range, produces infinitely complex spectra by combining just two simple components in a particular way. The basic FM equation is

  $$x(t) = \sin\left(2 \pi f_c t + I \cdot \sin(2 \pi f_m t)\right),$$

  where $f_c$ is the _carrier_ frequency, $f_m$ is the _modulator_ frequency, and $I$ is the _modulation index_ controlling the depth of modulation. By carefully animating these parameters over time, Chowning showed that a single equation could imitate a striking range of natural musical sounds:

  <audio src="./assets/bell-fm.mp3">FM bell sound synthesized using Csound `fmbell`</audio>

- _Efficient programming_: The mathematical elegance of FM is only useful if it can be _computed_ fast enough — tens of thousands of times per second, in fact, to produce a continuous audio stream. This requires careful, efficient implementations. In Python, a stripped-down FM synthesizer might look something like:

  ```python
  def fm(f_c, f_m, I, f_s, T):
      ...  # uses sine_lookup(phase) for speed, with phase in [0, 2π)
  ```

  where `sine_lookup` precomputes a table of sine values rather than recomputing transcendental functions from scratch. We will return to design choices like this throughout the book.

- _Instrument design_: Yamaha licensed FM as the synthesis engine in the legendary [DX7 synthesizer](https://en.wikipedia.org/wiki/Yamaha_DX7), turning a research result into a piece of hardware that could be played on stage and in the studio.

  <img src="./assets/dx7.png">

- _Music culture_: The DX7 was adopted by thousands of musicians and became, in many ways, _the_ sound of the 1980s. Ironically, while FM had originally been explored as a way to _imitate_ existing acoustic instruments, musicians ended up preferring the synthesizer's ability to create entirely _novel_ sounds — bright, glassy, bell-like timbres that no acoustic instrument could produce. You can hear FM unmistakably in tracks like [A-ha — "Take On Me"](https://www.youtube.com/watch?v=djV11Xbc914) and [Whitney Houston — "Didn't We Almost Have It All"](https://www.youtube.com/watch?v=c0TghfreFok).

A single mathematical insight, refined into an algorithm, embodied in a piece of hardware, became a defining aesthetic of an era. This is the kind of through-line that computer music makes possible.

### Computing is the frontier of music technology

Digital technology is now a key component of music on stage, in the studio, and in your ears. From software synthesizers to streaming codecs to noise-cancelling headphones, computation is no longer an exotic ingredient in music — it is, in most contexts, the substrate on which music is made, distributed, and experienced.

This trend of music and technology co-evolving will almost certainly continue as we venture into new technologies such as artificial intelligence. Like past technological developments — recording, amplification, sampling — these newer technologies will reshape the economic landscape of music, but they will also present new creative opportunities for those who learn to use them thoughtfully. If you are interested in understanding how computers synthesize, manipulate, and ultimately reshape musical sound, then computer music is for you.

## Who is this book for?

At its core, this book on computer music is written from a _computer science_ perspective. It is highly technical, and it is intended to support computer science courses on musical computing, much in the way that established texts support courses on computer graphics. We _will_ assume substantial background experience in programming and mathematics. We will _not_ assume much musical expertise, though musical training will be a helpful bonus for absorbing this material.

You don't need to be an expert in both music and computing to read this text, but there is an unfortunate asymmetry to be aware of:

- Students with a strong music background and weak computing background may struggle, and should study introductory computer science first.
- Students with a strong computing background and weak music background should be fine.

In more detail:

- _Programming_: This book assumes substantial familiarity with Python programming and basic computer science (e.g., data structures, Big O notation). If you are unfamiliar with these, you should learn the basics before proceeding.
- _Math_: You should be reasonably comfortable with trigonometry, basic calculus, and complex numbers. You won't have to do much derivation here, but you'll need to understand these concepts at least at a high level. It's okay if your skills are rusty — it should be possible to brush the dust off as you go through the book.
- _Music_: We aspire to make this book accessible even to those without any formal musical training. However, you will benefit from a basic foundation in musical concepts like pitch, and from an enthusiastic and discerning ear for music.

## What will readers learn from this book?

By the end of this book, you should understand:

- How to program a computer to efficiently store, synthesize, and process musical sound.
- A foundation of digital signal processing and the frequency domain that should transfer readily to many other areas of computing.
- The basics of how sound works in the physical world (acoustics) and how we perceive it (psychoacoustics).
- Exposure to more advanced topics, especially real-time interactive music applications and music AI.

## Why was this book written?

This book was written to support computer music courses taught from a computer science perspective. In the long term, my hope is that _computer music may come to be viewed as a first-class citizen of computer science_, alongside similarly applied domains like computer graphics.

The book was also written to fulfill a perceived gap in the existing computer music literature. It aims to:

- Teach the material in a modern and accessible programming language (Python).
- Maintain the level of technical rigor expected of computer science texts, while keeping the focus empirical and not going _too_ deep into the theory.
- Stay grounded in technical correctness rather than artistic considerations.

This book was heavily inspired by [_Digital Signals Theory_ by Brian McFee](https://brianmcfee.net/dstbook-site/content/intro.html), and it stands on the shoulders of giants more generally. It draws inspiration from the many wonderful texts authored by Curtis Roads, Roger Dannenberg, Julius Orion Smith, Brian McFee, and others. This book is intended to _complement_ those works, not to supersede them.
