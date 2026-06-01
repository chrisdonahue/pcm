# List of custom Markdown directives for this textbook

This file defines the book's **custom features and house conventions** — the
semantic primitives we commit to, plus the few things we've built ourselves.
For the mechanics of standard MyST directives (full syntax, options, rendered
examples), see the Markdown template page (`template-md.md`); this file does not
repeat them.

We author in MyST. `:::{name}` and ```` ```{name} ```` are equivalent; we use
`:::` throughout.

## Standard primitives

These are stock MyST — use them as-is. This table is the agreed vocabulary and
*when* to reach for each; for *how* they render, see the section noted in
`template-md.md`.

| Use | Directive | When to use | template-md.md |
| --- | --- | --- | --- |
| Definition | `{prf:definition} Name` | Formally defining something (`:label:` to cross-reference) | §13 |
| Example | `{prf:example} Name` | A worked special case — sparingly; most examples are inline | §13 |
| Tip | `{tip}` | A practical-advice aside | §4 |
| Warning | `{warning}` | Flagging a common mistake | §4 |
| Aside | `{note}` (add `:class: dropdown` to collapse) | A note most readers can skip | §4 |
| Exercise | `{exercise}` + `:label:` | End-of-chapter problems | §12 |
| Citation | `{cite:t}` / `{cite:p}` | Textual / parenthetical, author–year | §9 |
| Figure | `{figure} path` | Captioned image (`:alt:`, `:name:` to cross-reference) | §7 |
| Margin | `{margin} Title` | Short side aside; renders beside the next paragraph | §11 |

Everything below is **custom** — it has no native MyST directive, so it's
defined here.

## Vocab

Use the `{vocab}` role when introducing a vocabulary term. It italicizes the
term and links it to its definition in the alphabetically-sorted Glossary, which
serves as the book's single term reference (definitions + global index in one).
A term used with `{vocab}` must be defined in the glossary, or the build warns —
keeping prose and glossary in sync. Defined in `_ext/icm_roles.py`.

Source: `` A signal is {vocab}`periodic` if it repeats. ``

Rendered: A signal is {vocab}`periodic` if it repeats.

## Units

Use the `{unit}` role to typeset units in a common form. One argument renders a
single unit; two render a fraction (numerator, denominator). The numerator and
denominator may be separated by a comma or a slash — `` {unit}`cycles,second` ``
and `` {unit}`cycles/second` `` are equivalent. Defined in `_ext/icm_roles.py`.

| Source | Rendered |
| --- | --- |
| `` {unit}`radians` `` | {unit}`radians` |
| `` {unit}`cycles,second` `` | {unit}`cycles,second` |
| `` {unit}`cycles/second` `` | {unit}`cycles/second` |

## Audio — the `listen` pattern

MyST has no native audio directive, so the book defines one by convention: an
`{admonition}` titled `🔊 Listen` and tagged `:class: note listen`, wrapping a
standard HTML `<audio controls>` player. The book ships CSS for the `listen`
class that suppresses the admonition's default info glyph (the 🔊 in the title
stands in for it), so the block reads as a "Listen" callout rather than a note.

Put the `<audio>` player on the first line of the body; anything after it is the
caption. This mirrors the professor's `:::audio` directive — source first,
caption below — so the two map onto each other directly.

With a caption:

:::{admonition} 🔊 Listen
:class: note listen
<audio controls src="https://upload.wikimedia.org/wikipedia/commons/9/9f/Single_Frog_Croak.oga"></audio>

A single croak from a frog, recorded in the wild.
:::

Without a caption — drop the body text and leave only the player:

:::{admonition} 🔊 Listen
:class: note listen
<audio controls src="https://upload.wikimedia.org/wikipedia/commons/9/9f/Single_Frog_Croak.oga"></audio>
:::

## Inline audio and figures

For compact multimodal content (a series of audio/image pairs under one shared
caption), there is no native directive. The current convention is a `{grid}`
(from `sphinx-design`) of raw `<audio>`/`<img>` pairs followed by one shared
caption.

::::{grid} 1 1 3 3

:::{grid-item}
<audio controls src="https://upload.wikimedia.org/wikipedia/commons/4/4a/Cat_meowing.ogg"></audio>
<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Cat_November_2010-1a.jpg/220px-Cat_November_2010-1a.jpg" alt="A domestic cat" width="100%">
:::

:::{grid-item}
<audio controls src="https://upload.wikimedia.org/wikipedia/commons/c/c9/Barking_of_a_dog.ogg"></audio>
<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/YellowLabradorLooking_new.jpg/220px-YellowLabradorLooking_new.jpg" alt="A domestic dog" width="100%">
:::

:::{grid-item}
<audio controls src="https://upload.wikimedia.org/wikipedia/commons/5/52/Rooster_crowing.ogg"></audio>
<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Male_and_female_chicken_sitting_together.jpg/220px-Male_and_female_chicken_sitting_together.jpg" alt="A rooster" width="100%">
:::

::::

_Three common animal sounds and their sources._

> Open question: this is the least clean mapping. We could keep the `{grid}`
> convention, or define a custom inline-pair directive.
