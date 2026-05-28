This repository hosts the code for a computer music textbook called _Computer Music Principles_. This is intended to be a technically rigorous textbook used when music is taught in a computer science context.

Logistics:

- The book is written in Markdown with lots of multimedia (LaTeX, code, audio, images)
- By default, the Markdown is typeset to HTML. Rendering is handled by `.render/render.js`, which is a pretty barebones conversion. The render script may handle the multimedia in increasingly custom ways over time
- Chapters are folders in the root directory. Each chapter is a folder w/ `assets` (multimedia) and `code` (Python examples)
- `0-computer-music/index.md` codifies additional guiding design principles of the textbook, always read this first if you haven't already
- `directives.md` defines custom Markdown directives that should be used consistently throughout the book for consistent rendering. Always read this first if you haven't already. Make sure to apply the directives appropriately (but not egregiously) when writing.
- Each chapter should conclude w/ some :::exercise questions for students to complete and turn in to their instructor. Most often, these should be concrete questions that ask students to apply the technical knowledge they've learned from the chapter. Sometimes, these can be open-ended (e.g., for chapter 0). It's rare that I would want these to be coding challenges - these will be addressed in a separate part of the class. Instead, they should be consistent with the types of applied knowledge questions (not memorization) that I might want to ask students about on exams.
- When appropriate, some chapters should also conclude w/ some musical examples (just artist/composer - title) where the techniques in that chapter are explored. Only add these when they're explicitly featured in my input raw material.
- I will prompt you to write a draft most chapters by placing my raw slides and coding examples from last semester into the `raw/` folder for each chapter. These are likely incomplete and will miss some key principles/concepts. Take some editorial license to add principles I may have overlooked, but summarize those additions. Also, the slides will likely make reference to Nyquist, the previous teaching language for the course. Feel free to ignore those references, as we've changed to Python

General stylistic notes (will update w/ preferences as I go along):

- Before making any changes, always reread the file to edit and AGENTS.md, as I will be using a highly iterative workflow of editing your outputs.
- Code
  - Make coding examples standalone scripts. Minimal dependencies. Use vectorized computation in `numpy`. In chapter 2, a library called `pyquist` will be introduced, which is a lightweight library w/ basic computer music utilities. Use `pyquist` audio utilities once the library is introduced, and use raw `numpy` or `soundfile` before that
  - Code should always have typehints. Any function that returns audio should return `pq.Audio`, unless conceptually it's not audio (e.g., `build_wavetable` should return np.ndarray, while `wavetable_synth` should return pq.Audio).
  - Occasionally, it will be useful to inline code into the chapters. In those cases, keep the code as minimal as possible, and link to the verbose code file, but try to keep the inline code as close to a section of the verbose file as possible.
  - Always execute code examples in local virtual environment
  - Never do any `sys.path` modification in any of the code examples, assume dependencies are installed in the execution environment, and altert me if a dependency is needed for code examples that's not available in the environment.
  - Also, use `pathlib` instead of `os.path` whenever needing to reference assets or anything like that
- Figures and sound examples:
  - Figures and sound examples are great! Feel free to write Python code to synthesize audio or plots that can be included. If code is written just to make figures or sound examples rather than for pedagogical purposes of implementation, please store it in `figures/`. Otherwise, code that students should read should be in `code/`
    - Reiterating: do _not_ put code into `code` that is just used to create figures! `code/` is for student eyes, `figures/` is for agent/educator eyes.
  - For audio assets, normalize to -6dBFS unless otherwise specified
  - For plots, prefer wide plots with larger font sizes. Include axis labels but avoid plot titles - the plot will be explained in context or in a caption.
- Mathematical formalisms:
  - I am pretty particular about mathematical formalisms. They should be quite rigorous, but not at the expense of conceptual understanding.
  - Continuous functions should be e.g. $x(t)$, where $t$ is time. For samples and DSP, notation should be $x[n]$, where $n$ is a sample index, and $x[n] = x(n / f_s)$.
  - I like function type signatures where helpful, e.g., $x(t) : \mathbb{R} \to \mathbb{R}$
  - When possible, I don't want students to memorize formula. Instead, let's help them work through the algebra. E.g., if $t_0$ is $[\frac{\text{seconds}}{\text{cycle}}]$ and $f_0$ is $[\frac{\text{cycle}}{\text{second}}]$, then $f_0 = \frac{1}{t_0}$ by the units.
- General writing:
  - Use _italics_ for vocabulary, and **bold for inline key points**.
  - I like em dashes, but use them sparingly
  - Avoid run-on sentences, especially ones with 4 or more clauses
  - Format titles in _Italics and Title Case_. Format song names as Artist - _Title_
  - When typesetting inline itemized lists, use (1) item A, (2) item B, and (3) item C. For actual Markdown itemized lists line-by-line, use 1. for everything and let markdown to the counting, not 1., 2., etc.
