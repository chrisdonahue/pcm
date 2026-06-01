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
| Figure     | `{figure} path` | Captioned image (`:alt:`, `:name:` to cross-reference) | §8 |
| Margin     | `{margin} Title` | Short side aside; renders beside the next paragraph | §12 |
| Audio      | `{admonition} 🔊 Listen` / `{grid}` of `<audio>` | Playing a clip, or pairing clips with figures | §5 |

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
