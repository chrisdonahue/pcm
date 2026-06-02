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

| Use        | Directive | When to use | template-md.md |
| ---        | --- | --- | --- |
| Definition | `{prf:definition} Name` | Formally defining something (`:label:` to cross-reference) | §14 |
| Example    | `{prf:example} Name` | A worked special case — sparingly; most examples are inline | §14 |
| Tip        | `{tip}` | A practical-advice aside | §4 |
| Warning    | `{warning}` | Flagging a common mistake | §4 |
| Aside      | `{note}` (add `:class: dropdown` to collapse) | A note most readers can skip | §4 |
| Exercise   | `{exercise}` + `:label:` | End-of-chapter problems | §13 |
| Citation   | `{cite:t}` / `{cite:p}` | Textual / parenthetical, author–year | §10 |
| Figure     | `{figure}` + image body | Captioned image — just an image line + caption; add a path arg + `:name:`/`:width:` only when you need cross-ref/sizing | §8 |
| Margin     | `{margin} Title` | Short side aside; renders beside the next paragraph | §12 |

Everything below is **custom** — it has no native MyST directive, so it's
defined here.

## Audio

Use the `{audio}` directive for a short audio clip with a caption (a recorded
sample, a pre-rendered WAV). Its body is a Markdown link to the clip — the link
text describes it — followed by an optional caption. It renders a 🔊 Listen
callout with an `<audio>` player; the link text becomes the player's
`aria-label` and a download fallback for browsers without `<audio>` support.
Defined in `_ext/icm_audio.py`; see `template-md.md` §5 for the rendered result.

Source:

```
:::{audio}
[A 440 Hz sine tone](./assets/audio-sine-440.wav)

A 440 Hz sine tone, one second long.
:::
```

For a **compact inline** clip — mid-flow or paired with a waveform image — use
the `{audio}` **role** instead: `` {audio}`label <url>` ``. It renders a small
round play/pause button (label → `aria-label`; the visible label is the
surrounding text). To compare several clips under one shared caption, group them
(one paragraph per item; the last paragraph is the caption) in one of three
wrappers — `audio-figure` (each clip has its own waveform image → comparison
grid), `audio-board` (clips share one combined plot → centered button row above a
full-width plot), or `audio-list` (clips + text → wider list). Defined in
`_ext/icm_audio.py` + `_static/audio-chip.js`; see `template-md.md` §5.2.

Source:

```
:::audio-figure
220 Hz sine
{audio}`220 Hz sine <./assets/audio-sine-220.wav>` ![220 Hz sine waveform](./assets/fig-sine-220.png)

330 Hz sine
{audio}`330 Hz sine <./assets/audio-sine-330.wav>` ![330 Hz sine waveform](./assets/fig-sine-330.png)

Two pure tones and their waveforms.
:::
```

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
