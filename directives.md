# List of custom MarkDown directives for this textbook

Uses [CommonMark generic directives proposal](https://talk.commonmark.org/t/generic-directives-plugins-syntax/444).

## Vocab

A :vocab[vocabulary] directive should be use when definining a vocabulary term for the first time, especially if that term should eventually make its way into a global index.

## Units

Units should be used to typeset units in a common form. First argument is numerator, second is denominator. E.g., angle as :unit[radians] or frequency as :unit[cycles,second].

## Admonitions

Admonitions are special container blocks that can contain arbitrary markdown.

:::definition[Periodicity of sinusoid]
A _definition_ is a type of admonition where something is formally defined. It has a primary argument, the name of the definition. For example,

The trigonometric function $\sin$ is _periodic_ with period $2\pi$:

$sin(x) = sin(x + 2\pi) \forall x \in \mathbb{R}$.
:::

:::example[Basic sinusoid]
An _example_ shows a special case of something being defined or discussed. It has a primary argument, the name of the example. E.g.,

$sin(\pi) = sin(3\pi)$

It should be used somewhat sparringly. Most examples will be inline. Mainly used when working through a longer / more complex example to aid understanding.
:::

:::tip
A _tip_ is something of an aside that gives practical advice on a topic. No arguments

Review your trigonometric functions, kids!
:::

:::aside
A general note or aside that most readers can probably skip.
:::

:::warning
A _warning_ flags common mistakes, e.g.,

$sin(\pi) \neq sin(2\pi)$
:::

:::exercise
_Exercises_ appear at the end of a chapter, e.g.,

Does $sin(4\pi) = sin(5\pi)$?
:::

## Citations

In 2017, :citet[donahue2017ddc] introduced _Dance Dance Convolution_ :citep[donahue2017ddc].

## Figures

:::figure
![A white-spotted pufferfish swimming near a coral reef](https://upload.wikimedia.org/wikipedia/commons/d/d2/Arothron_stellatus_R%C3%A9union.jpg)

A _Arothron stellatus_ (white-spotted pufferfish) photographed in the wild.
:::

A figure with no caption:

:::figure
![A white-spotted pufferfish swimming near a coral reef](https://upload.wikimedia.org/wikipedia/commons/d/d2/Arothron_stellatus_R%C3%A9union.jpg)
:::

## Audio

:::audio
[A single frog croak](https://upload.wikimedia.org/wikipedia/commons/9/9f/Single_Frog_Croak.oga)

A single croak from a frog, recorded in the wild.
:::

An audio directive with no caption:

:::audio
[A single frog croak](https://upload.wikimedia.org/wikipedia/commons/9/9f/Single_Frog_Croak.oga)
:::
