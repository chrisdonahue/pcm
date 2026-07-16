----
title : Psychoacoustics
----
# Psychoacoustics 
Psychoacoustics is the study of how we perceive and process sound—the intersection between the physics of audio and the biology of human hearing. In computer music, understanding psychoacoustics is essential because it bridges the gap between what we can produce as sound waves and what actually reaches the listener's brain. From the logarithmic way we perceive pitch to the remarkable ability our ears have to separate distinct sound sources in a complex mix, psychoacoustics reveals the principles underlying every aspect of musical experience. These perceptual principles directly inform critical decisions in music production and design, such as how to tune instruments, compress audio for efficient storage, create spatial effects, and structure music for specific emotional impact. By understanding psychoacoustics, we understand the human experience of _listening_ to music, which is the ultimate goal of any musical endeavor.

## Frequency Perception
We commonly define the _frequency_ range of human hearing to be 20-20kHz, though as you age, this range begins to diminish. 

There is an interesting relationship between _frequency_ and _pitch_. That is, $ \textrm{Pitch} \propto \log(\textrm{Frequency}) $. 

This proportionality tells us that our **perception** of pitch is logarithmic. This tells us that small changes in low frequencies are much more noticeable than small changes to high frequencies, which creates an information bias toward lower frequencies which provides a better _frequency resolution_. 

:::{dropdown}`Explaining f_s = 44100`
This number comes from two main sources : the range of human hearing, and the mathematical requirements of low-pass filtering. The purpose of sampling is effectively the process of compression-- from infinitely-precise continuous signals to discrete digital representations. We want to balance a lossless representation of audio with practical space efficiency. 

Recall from the Nyquist-Shannon sampling theorem that the sampling rate must be at least twice the highest frequency component in the signal to avoid aliasing. Since the upper limit of human hearing is around 20 kHz, we can safely choose a sampling rate of $f_s >40\text{kHz}$ to avoid any aliasing. 

But what happens if a signal outside our audible range is present in the original analog signal? If we don't properly apply a low-pass filter before sampling, it can cause aliasing, which results in unwanted artifacts in the recording. This is where the extra $4.1\text{kHz}$ comes in-- it allows space for the **transition band** of the low-pass filter to smoothly roll off the frequencies above the audible range.
::: 


### The Octave
The Octave is most easily defined as a **doubling of frequency**. It is the fundamental building block of most tuning systems, basis of intervalic relationships, and is the foundation of our perception of pitch. Mathematically, we get that $2f = f + \text{ an octave}$, $f / 2 = f - \text{ an octave}$, $f \cdot 2^N = f + N \text{ octaves}$. 


:::{dropdown} Why is it called an Octave?
The term "octave" may be confusing since it clearly has the latin prefix for "eight" in it, yet we're only **doubling** the frequency. The term itself comes from the western scale system  where the eighth note in the sequence occurs an octave above the first.
::: 

The octave also arises from the harmonic series, where the frequency of each harmonic is an integer multiple of the fundamental frequency. This is further discussed in {ref}`Tuning Systems`. 

**Pitch Classes** are the set of all pitches that are a whole number of octaves apart. For example, all A notes (A4, A5, A3, etc.) belong to the same pitch class. You can consider an octave to be sort of an [equivalence relation](https://en.wikipedia.org/wiki/Equivalence_relation) on the set of pitches. 

:::{audio-list}
{audio}`Initial Tone : A4 (440 Hz) <./ch10/audio/A4_440Hz.wav> `
{audio}`Octave Above : A5 (880 Hz) <./ch10/audio/A5_880Hz.wav> `
{audio}`Octave Below : A3 (220 Hz) <./ch10/audio/A3_220Hz.wav> `
::: 

### Combining Pitches
When multiple pitches are played simultaneously, they can have different effects based on their differences in frequency, phase, and timbres. Consider playing two pure (sine) tones simultaneously, at frequencies $f_a, $f_b$. 

#### Beating
**Beating** is the effect that occurs when the difference between these frequencies are small (< 10Hz). We call $f_a - f_b$ the **beat frequency**.
    :::{audio-list}`Beating Tones with Beat Frequency of 3 Hz`
{audio}`Tone 1 : 440 Hz <./ch10/audio/A4_440Hz.wav> `
{audio}`Tone 2 : 443 Hz <./ch10/audio/A4_445Hz.wav> `
{audio}`Combined Tones <./ch10/audio/combined_beating.wav> `
:::
Why does this happen? Recall mathematically that 
$$\sin(f_a t) + \sin(f_b t) = 2 \cos\left(\frac{f_a - f_b}{2} t\right) \sin\left(\frac{f_a + f_b}{2} t\right) $$
This shows that we get a ring modulation with sidebands at frequencies $f_a + f_b$ and $|f_a - f_b|$. When tuning a piano, technicians minimize this beating effect to ensure that strings that play the same note are in tune with each other. 

:::{figure} 
![beating-figure](./ch10/images/beating.png)
$f_a = 100$ Hz, $f_b = 101$ Hz, and the resulting beating.
:::


:::{dropdown}`Binaural Beats`
You will find that some people call this phenomenon "binaural beats". This isn't quite accurate, as binaural beats are a specific type of auditory illusion that occurs when two different pure tones are presented **to each ear separately**. When we synthesize two tones together into a single one, we get the beating effect described above, sometimes called "monaural beats".
:::

#### Polyphony
**Polyphony** occurs when two simultaneous pitches are played together that don't have an integer relationship. That is, $\frac{f_a}{f_b} \notin \mathbb{Z}$. This creates distinct basic tones that are perceived separately. 

:::{audio-list}
{audio}`Tone 1 : 440 Hz <./ch10/audio/A4_440Hz.wav> `
{audio}`Tone 2 : 523.25 Hz <./ch10/audio/C5_523.25Hz.wav> `
{audio}`Polyphonic Tones <./ch10/audio/polyphonic.wav> `
:::

#### Timbre
**Timbre** is the "quality" of a sound, which is determined by the harmonic content. Should $\frac{f_a}{f_b} \in \mathbb{Z}$, the two tones will be perceived as a single, more complex tone with a specific timbre. The timbre of a tone is what allows us to distinguish between different instruments playing the same note. The more constituent integer frequencies there are to a tone (i.e., the more harmonics), the more "complex" it's timbre will be.

:::{audio-list}
{audio}`Tone 1 : 440 Hz <./ch10/audio/A4_440Hz.wav> `
{audio}`Tone 2 : 880 Hz <./ch10/audio/C5_523.25Hz.wav> `
{audio}`Tone 3 : 1320 Hz <./ch10/audio/E5_659.25Hz.wav> `
{audio}`Combined Tones <./ch10/audio/added_together.wav> `
:::


### Critical Bands + Masking
Although the human ear can distinguish between different frequencies, it has a limited ability to resolve closely spaced frequencies. This limitation is known as the **critical band**. Within a critical band, the ear cannot distinguish between individual frequencies, and they are perceived as a single, complex tone.
:::{figure}
![critical-band](./ch10/images/critical_band.png)
The critical band is the range of frequencies that the human ear can resolve as separate tones.
:::

This leads to the phenomenon of **masking**, where a strong tone can make it difficult to hear a weaker tone that is close in frequency. We leverage masking to remove imperceptible sounds for compression in the algorithms that power lossy compression like MP3. 

:::{audio}
[Masking Effect](<./ch10/audio/masking.wav>)
The Masking Effect, where (a) makes (b) inaudible.
:::

### Frequency Illusions

One of the most famous illusions is called the **Shepards Tone**. It makes a sound that seems to continuously rise or fall in pitch, even though the actual frequencies are cycling through a fixed range. This is only possible because the sound is made by combining multiple tones which sound like **timbre** instead of **polyphony**. 

:::{audio}
[Shepard's Tone](<./ch10/audio/shepards_tone.wav>)
The Shepard's Tone, an auditory illusion that seems to continuously rise in pitch.
:::

Another illusion is that of the **Missing Fundamental**. This occurs when a complex tone is missing its fundamental frequency, but the brain still perceives the pitch as if the fundamental were present. This is because the brain infers the missing frequency from the harmonic series.

:::{audio}
[Missing Fundamental](<./ch10/audio/missing_fundamental.wav>)
The Missing Fundamental, an illusion where the brain perceives a pitch that is not actually present.
:::


## Loudness
We often talk about the frequency range of human hearing, but what's more impressive is the **dynamic range** of human hearing : the range of loudness that the human ear can perceive, from the quietest sound to the loudest sound. It is commonly defined as $20 \mu P$ (_threshold of hearing_) to $20 P$ (_threshold of pain_).

We also exhibit a logarithmic response to loudness, which can be modeled by $\textit{Loudness} \propto \log(\textit{Amplitude})$. While colloquially used interchangeably, there is a definitional difference between loudness and amplitude. **Loudness** is a subjective measure of the perceived intensity of a sound, while **amplitude** is an objective measure of the physical displacement of the sound wave.


### Decibels (dB)
Just as we use pitch to denote logarithmic differences in frequency, we use **decibels (dB)** to denote logarithmic differences in loudness. A decibel is a _relative_ measurement between two sound levels, where $a$ is the measured amplitude and $a_0$ is the reference amplitude.

$$ dB = 20 \log_{10} ( \frac{a}{a_0} ) $$

[Should I mention how it's derived from power? Don't want to show any unnecessary information]
:::

This lends us to defining different kinds of decibel measurements where we set $a_0$ to different reference values. For example, $\dB_{\text{SPL}}$ (Sound Pressure Level) uses a reference of $20 \mu Pa$, while $\dB_{\text{FS}}$ (Full Scale) is uses a reference where $a_0 = 1$. We mostly use $\dB_{\text{SPL}}$ when discussing human-perceived loudness, and $\dB_{\text{FS}}$ when discussing digital audio levels. 

The decibel is a multiplicative unit for loudness, just as an octave is for frequency. The above equation gives us $a \cdot 1.22 = a + 1dB$, $a \cdot 10 = a + 20dB$, and most importantly, $a \cdot 2 = a + 6dB$, $a / 2 = a - 6dB$.

:::{audio-list}
{audio}`1000 Hz with $a=1.00$ (0dB) <./ch10/audio/0db.wav>`
{audio}`1000 Hz with $a=0.50$ (-6dB) <./ch10/audio/minus6db.wav>`
{audio}`1000 Hz with $a=0.78$ (-1dB) <./ch10/audio/minus1db.wav>`
::: 

:::{dropdown}`Explaining bit depth = 16 bits`
Just like when choosing the sampling rate, we want to balance space efficiency with audio fidelity. Since our dynamic range is quite large, we need a sufficient number of bits to represent the full range of possible amplitudes without introducing significant quantization noise. Since humans are able to perceive a dynamic range of approximately 100 dB, and 16-bit system provides $2^16 = 65,536$ discrete amplitude levels (96 dB), then 16-bit quantization is sufficient for most applications. 
:::

### Loudness Perception 
**Peak amplitude** itself is not a good measure of loudness. Noise with a (normalized) peak amplitude of $1.0$ is perceptually louder than a sine wave with the same peak amplitude. We could instead consider the **average amplitude** of a signal, however any periodic signal will have an average amplitude of zero, making it a poor measure of loudness. 

:::{audio-figure}
{audio}`Noise with a peak amplitude of $1.0$. <./ch10/audio/noise.wav>`
![Noise](./assets/noise.png)
{audio}`Sine wave with a peak amplitude of $1.0$. <./ch10/audio/sine.wav>`
![Sine Wave](./assets/sine.png)
::: 

A metric for loudness better than amplitude itself is the **Root Mean Square (RMS)** amplitude, which takes into account the average power of the signal over time. For some signal $x[t]$ over $N$ samples: 
$$
\text{RMS} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} x_i^2}
$$

:::{figure}
[Root Mean Square (RMS) Amplitude](./assets/rms.png)
:::

:::{dropdown}`What about LUFs?`
Loudness Units Full Scale (LUFs) is a more sophisticated metric for measuring loudness. There are different ways to [calculate LUFs](https://www.itu.int/dms_pubrec/itu-r/rec/bs/R-REC-BS.1770-5-202311-I!!PDF-E.pdf), but the important distinction is that LUFs uses a weighted approach to account for the non-linear response of the human ear to different frequencies.
:::

## Fletcher-Munson Curves
The human ear is not equally sensitive to all frequencies, as some frequencies are louder than others, even when played at the same amplitude. The Fletcher-Munson curves show how the perceived loudness of a sound changes with frequency and amplitude.

:::{figure}
[Fletcher-Munson Curves](./assets/fletcher_munson_curves.png)
:::

The key takeaways from this diagram is that we're most sensitive to the $1000-4000$ Hz range-- not coincidentally the range where most human speech is produced, and least sensitive at the extremes of the audible spectrum. 

:::{dropdown}`The Phon`
The **Phon**  is a unit of loudness level that takes into account the frequency-dependent sensitivity of the human ear. 1 Phon = 1 dB SPL at 1000 Hz. So should a tone of 100 Hz be played at 50 dB SPL, it would be equivalent to 50 Phon. Or, using the Fletcher-Munson curves above, we can determine that a tone at 100 Hz played at 50 dB SPL would be equivalent to 20 Phon.
:::

## Intervals 
An **interval** is the way we describe the distance, or relationship, between two pitches. Since pitch is multiplicative, we can mathematically generalize the concept of an interval as $k \times f_a = f_b, k \in \mathbb{R}$. In english, $k$ is the interval between $f_b$ and $f_a$. Similarly, $k = \frac{f_b}{f_a}$. 

We will often use language such as the interval "above" when $k > 1$, and "below" when $k < 1$.  

### Quick Music Theory
Certain values of $k$ ($\pm \epsilon$) are given names in music theory. We've already seen that when $k=2$, we call this interval an _octave_. When $k= \frac{3}{2}$, we call this interval a _perfect fifth_, $k=\frac{5}{4}$ gives us a _major third_. You will not be expected to memorize all the different ratios and their corresponding names in this class. 


### Integer, Rational, and Irrational Intervals
Since $k$ can be irrational, combining two simple oscillators with an interval of $k$ between them can result in an aperiodic signal. 

![Rational vs Irrational Intervals](./assets/rational_irrational_intervals.png)

### Consonant and Dissonant Intervals
There is a blurry line between physiological and psychological concepts of musical dissonance. This section covers our physiological understanding of dissonance since people around the world disagree on what a dissonant sound is _musically_, as that largely stems from a culture's musical traditions. 

Most real-world instruments and sounds aren't sine wave generators, and therefore have some harmonic complexity (overtones) which affect our perception of consonance and dissonance. Consider playing two complex tones $H_f = \{f, 2f, 3f, \dots\}, H_{kf}= \{kf, 2kf, 3kf, \dots\}$. One way to analyze consonance is through the _harmonic intersection ratio_. For example, when $k=\frac{3/2}$, then $H_{f(3/2)} = \{\frac{3}{2}f, \textbf{3}f, \frac{9}{2}f, \textbf{6}f, \dots\}$. Half of the harmonics in $H_{f(3/2)}$ are also present in $H_f$, and one third of those in $H_f$ are present in $H_{f(3/2)}$, so these two share many frequencies in common. 

What if $k=\frac{9}{8}$? Then $H_{f(9/8)} = \{\frac{9}{8}f, \frac{9}{4}f, \frac{27}{8}f, \dots, \textbf{9}f, \dots\}$. Only $\frac{1}{9}$ of the harmonics in $H_{f(9/8)}$ are also present in $H_f$, and $\frac{1}{8}$ of $H_f$ are in $H_{f(9/8)}$. 

Purely by the harmonic intersection ratio, we consider _simpler_ interval ratios to be more consonant. Now that we've heard seen the math, let's hear the difference! 
:::{audio-list}
{audio}`K = \frac{3}{2} <./assets/K_3_2.mp3>`
{audio}`K = \frac{9}{8} <./assets/K_9_8.mp3>`
:::

When played together some of the overtones aren't shared, but rather exist close enough together to give us {ref}`beating`. Rapid beating is generally unpleasant to the ear and is therefore classified as dissonant. 

:::{dropdown}`Psychological Aspects of Dissonance`
As we mentioned in the introduction, some of our ideas of dissonance are culturally dependent. For example, the tritone interval ($k = \sqrt{2}$) was considered dissonant in the European middle ages (sometimes called the "devil's interval"), but is now widely used in jazz and other musical genres. Some cultures, such as the Javanese gamelan, use {ref}`tuning systems` that are based on intervals that are considered dissonant in western music. 
:::
:::{dropdown}`How Dissonance is Intentionally used in Music`
Dissonance is essential to music, since it provides tension and contrast. Just as in storytelling there needs to be conflict to make a compelling narrative, music needs dissonance to create a compelling journey.  
:::

## Tuning Systems
A **tuning system** is a method for determining the pitch of each note in a musical scale. In this section we will explore the motivation behind different tuning systems, what makes them unique, and how they affect the way we experience music.

### Let's Design a Tuning System
Most tuning systems preserve the fundamental octave, and achieve their scales by subdividing the octave into a certain number of (not necessarily equal) parts. Let's try designing a tuning system, consisting of N notes, in 3 different ways : 

### **Just Intonation**: 
This approach uses simple whole number ratios to determine the frequencies of the notes. For example, a perfect fifth is a 3:2 ratio, and a major third is a 5:4 ratio. This approach is flawed since it is entirely designed around a specific frequency $f_0$, which limits us to playing in a single key center. 
### **Fixed Intervals**
We could simply define a fixed frequency relationship, such as $f_i = f_{i-1} \Delta f$, where $\Delta f$ is a constant frequency difference between adjacent notes. This approach is flawed since it neglects the logarithmic nature of pitch perception, and doesn't preserve the _octave_ relationship. 
### **Equal Temperament**: 
This approach divides the octave into N equal parts, where each step is a fixed ratio. This allows us to play in any key without having to retune the system around a specific key center, and this preserves the octave relationship. However, we lose the harmonicity of the just intonation system. 

The code block below computes an N-tone equal tempered scale and plays the result. Try different values of N, and see how the resulting scale changes.

:::{code-cell}
def play_scale(scale):
    """plays each note of a chromatic scale for 0.25 seconds."""
    import numpy as np
    import pyquist as pq
    osc = lambda f: np.sin(2 * np.pi * f * np.linspace(0, 0.25, int(44100 * 0.25), False))
    buffer = np.array([])
    for f in scale:
        buffer = np.concatenate([buffer, osc(f)])
    pq.play(pq.Audio(buffer, f_s=44100))

def N_equal_temperament(N, f_0 = 440.0):
    return (f_0 * (2 ** (i / N)) for i in range(N))

scale = N_equal_temperament(6)
play_scale(scale)
:::

#### Deriving 12-Tone Equal Temperament (12-TET)
What if we can take the best of all worlds? Something where each note can be easily calculated from the ones preceding, maintain the natural harmonicities of just intonation, and preserve the harmonic flexibility of equal temperament. Maybe if we set N just right we can get really close to _just intonation_ using equal temperament.

Let's consider a set of justly tuned intervals $I_j = \{3:2, 4:3, 5:4, 6:5\}$. Let's try to find an $N$ such that the equal temperament scale approximates these intervals as closely as possible. 

Notice that when $N=12$, we find a local minimum. While $N=\infty$ would give us a perfect approximation of just intonation, we want to find a practical value of $N$ that is small enough where each note is easily distinguishable, but large enough to approximate just intonation.


Although 12-TET is the most common tuning system today, it overly restricts the way we make music. Only some instruments actually require a static tuning system (e.g. piano, guitar, harp), whereas others have the freedom to change their intonation on the fly (e.g. violin, voice, french horn). This means that vocal choirs have the freedom of achieving those _justly tuned intervals_ just by deviating from the 12-TET system slightly. 

:::{dropdown}`Motivating Use of 12-TET`
A famous early work for the 12-tone temperament system was J.S. Bach's "Well-Tempered Clavier", published in 1722, which was a collection of preludes and fugues in _all_ 24 major and minor keys. Without the 12-tone temperament system, it would have been impossible to play in all keys without retuning the instrument, since the further away a key is from the original tuning, the more out of tune it will sound. 

Today, most keyboards, guitars, and other fixed-pitch instruments are tuned to the 12-TET system because it is the most widely used, and allows for modern music where the _tonal center_ changes frequently. 

**Some Nuance:** Bach himself didn't use **equal** temperament, but rather a "well-tempered" system that was more popular at the time. Bach allegedly tuned his instruments to his _own_ liking, though still within a 12-tone _unequal_ temperament system. 
::: 

:::{dropdown}`The Railsback Curve`
Pianos are almost always tuned with the 12-TET system, however since the strings don't produce pure sine waves, the **inharmonicities** (natural deviations from the ideal harmonic series) cause the piano to sound slightly out of tune. At either extreme of the keyboard the inharmonicities become more pronounced, making the piano sound increasingly out of tune. To fix this, technicians will intentionally tune a piano "out of tune" relative to the 12-TET system, but in a way that we perceive as being more in tune. 

The paradoxical way of detuning a piano to make it sound _more_ in tune is known as the **Railsback curve**, shown below. 
:::{figure}
![Railsback Curve](railsback_curve.png)
::: 

::: 



## Identification and Repetition 

### Localization
**Localization** is the ability to perceive the direction and distance of a sound source. Understanding how humans localize sound is important for designing video games, movies, spatial audio systems, and other immersive experiences. 

One way we localize sound is through **interaural time differences (ITD)**, which is the difference in arrival time of a sound at each ear. The human brain implicitly "calculates" the difference in _phase_, at low frequencies and **interaural intensity differences (IID)**, at high frequencies. We can use ITD only at low frequencies since the wavelength of high frequency sounds can be smaller than the distance between our ears, high frequency sounds may have wavelengths shorter than the distance between our ears. We can use IID at high frequencies since the head casts a "shadow" that attenuates the sound reaching the far ear, but low frequency sounds don't get attenuated as much since they diffract around the head. We also use **spectral cues** to localize sound, which are the frequency-dependent changes in the sound caused by the shape of our head and ears. We can also distinguish distances in the _median plane_ (altitude) by relying on these spectral cues. 

:::{dropdown}`The Cone Of Confusion`
When we assume that a head is held stationary, there are certain points in space where the ITD and IID cues are identical, making it difficult to localize sound. This is known as the **cone of confusion**. In reality we use other cues to disambiguate these points, such as head movements and spectral cues, however it is still a weak point in auditory system.
:::

:::{tip}
**Fun Fact!** Our localization is rather weak in the median plane, but some owls have evolved to have _asymmetrical ears_ so they can localize sounds with great accuracy in 3-dimensions. This comes from the fact that one ear is _higher_ than the other, so they use ITD and IID cues to localize sound in the median plane, whereas we can only use spectral cues.
:::

### Scene Analysis 
A remarkable achievement in human evolution that we take for granted is the ability to disambiguate and identify different sound sources in a complex auditory scene, which we call **auditory scene analysis**. Our incredible sensitivity to loudness, and reasonable sensitivity to pitch allows us to use sound features like fundamental frequency, harmonic amplitudes, bandwidth, harmonicity, noisiness, and temporal dynamics to identify and separate different sound sources. 

:::{figure}
![Auditory Scene Analysis](./assets/auditory_scene_analysis.png)
:::

### Repetition
The fundamental building block of (most) music is **repetition**. It is a powerful tool for creating structure, expectation, familiarity, and emotional impact in music. Repetition occurs at many levels temporally, from the repetition of individual notes, to phrases, to entire sections of a piece. 

Repetition on larger scales is often called **form**, where you'll find terms like the "chorus" or "verse" in popular music. On a smaller scale, composers use repetition to create **motifs** (short, recurring musical ideas) which occur throughout a piece. On the flip side, composers also use **variation** to create interest and contrast, by altering a repeated music in some way.

Let's explore the power and purpose of repetition on our perception of music. Below are two random sequences of notes. We will demonstrate how repetition turns randomness into familiarity. 
:::{audio-list}
{audio}`Random Sequence 1 <./ch10/audio/random_sequence_1.wav>`
{audio}`Random Sequence 2 <./ch10/audio/random_sequence_2.wav>`
:::

Here we repeat the first half of `Sequence 1` twice. 
:::{audio}
[Sequence 1 with Repetition](<./ch10/audio/random_sequence_1_repeated.wav>)
:::
Now, we take a quarter of `Sequence 2` and repeat it four times.
:::{audio}
[Sequence 2 with Repetition](<./ch10/audio/random_sequence_2_repeated.wav>)
:::

Already we have turned randomness into something that is more familiar and easier to remember. Finally, we will combine these two modified sequences to create an "ABA" form, meaning we play `Sequence 1` followed by `Sequence 2`, and then repeat `Sequence 1` again.
:::{audio}
[ABA From Random Sequences](<./ch10/audio/ABA_form.wav>)
:::

### Citations : 
Chris' slides
https://web.archive.org/web/20100410235208/http://www.cs.ucc.ie/~ianp/CS2511/HAP.html
https://www.sciencedirect.com/science/chapter/referencework/abs/pii/B9780128093245242673

Jennifer J. Lentz. (2023). Psychoacoustics: Perception of Normal and Impaired Hearing with Audiology Applications, Second Edition. Plural Publishing, Inc.
