# Custom Markdown directives for this textbook

## Roles

- **Vocab** — introduce a term for the first time (italicizes it and links it to
  the glossary): `` {vocab}`vocabulary` ``.
- **Units** — typeset units in a common form; one argument for a single unit, two
  (numerator, denominator) for a fraction: `` {unit}`radians` ``,
  `` {unit}`cycles,second` ``.

See the template's *Custom roles: vocabulary and units* section.

## Admonitions

Standard MyST admonitions — colored callout boxes. Swap the name for the box you
want: `:::{note}` (a general aside most readers can skip), `:::{tip}` (practical
advice), `:::{warning}` (a common mistake or hazard), or `:::{important}`.

```
:::{warning}
A _warning_ flags common mistakes, e.g., $\sin(\pi) \neq \sin(2\pi)$.
:::
```

See the template's *Admonitions* section (including custom-titled and
collapsible `dropdown` admonitions).

## Definitions and examples

From `sphinx-proof`. Pass the name as the argument and add a `:label:` so it can
be cross-referenced with `` {prf:ref}`label` ``:

```
:::{prf:definition} Periodicity of sinusoid
:label: def-periodicity
The trigonometric function $\sin$ is _periodic_ with period $2\pi$:
$\sin(x) = \sin(x + 2\pi) \;\forall x \in \mathbb{R}$.
:::
```

`:::{prf:example} Name` works the same way. Use it sparingly — most examples are
inline; reserve the block for a longer worked example. See the template's
*Theorems, proofs, and definitions* section.

## Exercises

`:::{exercise}` (optionally with a `:label:` and a matching `:::{solution}`),
collected at the end of a chapter. See the template's *Exercises and solutions*
section.

## Citations

Pull from `references.bib`. Cite with `` {cite}`key` `` → an alpha-style label
like [Dan97], linked to the References page (every citation is collected there
automatically). See the template's *Cross-references and citations* section.

## Figures

Simple form — an image line plus a caption:

```
:::{figure}
![A white-spotted pufferfish swimming near a coral reef](path/to/image.jpg)

A _Arothron stellatus_ (white-spotted pufferfish) photographed in the wild.
:::
```

When you need to size, align, or cross-reference a figure, pass the path as the
argument and add options (`:name:`, `:width:`, `:align:`). See the template's
*Figures and images* section.

## Audio

A book-specific directive (defined in `_ext/icm_audio.py`). A single clip is a
Markdown link plus an optional caption:

```
:::{audio}
[A single frog croak](path/to/clip.wav)

A single croak from a frog, recorded in the wild.
:::
```

For inline clips and side-by-side audio/figure comparisons, use the
`` {audio}`label <url>` `` **role** inside an `audio-figure`, `audio-board`, or
`audio-list` wrapper. See the template's *Audio* section.

## Margin notes

`:::{margin} Optional title` pushes a short aside into the page margin, aligned
with the paragraph that follows it. See the template's *Margin content* section.
