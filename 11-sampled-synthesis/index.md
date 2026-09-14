---
title: "Chapter 11: Sample-based Synthesis"
---

# Sample-based Synthesis

:::{note}
This chapter is planned but not yet written. The section below was moved here from Chapter 7 (Sampling Theory) as a placeholder, to be integrated into the eventual outline.
:::

## Changing playback speed

:::{margin}
**Recap (resampling, from {ref}`Chapter 7 <sec-resampling>`).** _Resampling_ maps one sample vector to another, generally of a different length,

$$\mathbf{x} = [x[0], \ldots, x[N-1]] \;\longrightarrow\; \mathbf{y} = [y[0], \ldots, y[M-1]],$$

by reading the original at fractional positions $p$ via interpolation, $y[m] = \text{Interpolate}(\mathbf{x},\, p)$. Changing the _sample rate_ from $f_s^1$ to $f_s^2$ uses $p = m \cdot f_s^1/f_s^2$ and a new length $M = N\, f_s^2/f_s^1$.
:::

We have actually seen resampling in one other guise already. When wavetable synthesis reads a table faster or slower to change its pitch, that is resampling. The same idea lets us change the _speed_ of a recording, and with it, its pitch.

Here the goal is to change a clip's duration from $T^1$ to $T^2$ while keeping the sample rate fixed. The new length is

$$M = N \cdot \frac{T^2}{T^1},$$

and we read the original at interpolated positions exactly as before, now with the ratio $T^1/T^2$:

$$y[m] = \text{Interpolate}\!\left(\mathbf{x}, \; p = m \cdot \frac{T^1}{T^2}\right).$$

Stretching or squeezing the signal in time shifts every frequency it contains by the factor $T^1/T^2$. Playing a clip at twice the speed halves its duration and raises every frequency by an octave, chipmunk-style.

Notice that changing the sample rate and changing the speed are fundamentally the _same_ operation. The only difference is the ratio used to convert between sample indices, and whether we play the result back at a new sample rate or the original one. In Pyquist, we can change speed by reinterpreting the sample rate and then resampling back:

```python
ratio = 2.0                                       # 2x speed, up an octave
sped_up = pq.Audio(audio.samples, int(audio.sample_rate * ratio))
sped_up = sped_up.resample(audio.sample_rate)
```

:::{audio-list}
{audio}`Original speed <./assets/audio-speed-1.wav>`

{audio}`Half speed (down an octave) <./assets/audio-speed-0p5.wav>`

{audio}`Double speed (up an octave) <./assets/audio-speed-2.wav>`

The same recording played at three speeds. Changing speed also changes pitch, because stretching the signal in time scales all of its frequencies.
:::
