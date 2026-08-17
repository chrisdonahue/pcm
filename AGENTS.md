This repository hosts the code for a computer music textbook called _Computer Music Principles_. This is intended to be a technically rigorous textbook used when music is taught in a computer science context.

Logistics:

- The book is written in Markdown with lots of multimedia (LaTeX, code, audio, images)
- The Markdown will eventually be rendered using a custom fork of the Executable Book Project (EBP) template, which is handled by a different codebase which incorporates this one as a submodule
- `directives.md` defines custom Markdown directives that should be used consistently throughout the book for consistent rendering, which are implemented in our EBP fork. Always read this first if you haven't already. Make sure to apply the directives appropriately (but not egregiously) when writing.
- Chapters are folders in the root directory. Each chapter is a folder w/ `assets` (multimedia) and `code` (Python examples)
  - Eventually, most of the code examples will be embedded in the Markdown and executable in browser via pyodide. However, right now they're mostly decoupled, standalone scripts
- `0-computer-music/index.md` codifies additional guiding design principles of the textbook, always read this first if you haven't already
- Each chapter should conclude w/ some :::{exercise} questions for students to complete and turn in to their instructor. Most often, these should be concrete questions that ask students to apply the technical knowledge they've learned from the chapter. Sometimes, these can be open-ended (e.g., for chapter 0). It's rare that I would want these to be coding challenges - these will be addressed in a separate part of the class. Instead, they should be consistent with the types of applied knowledge questions (not memorization) that I might want to ask students about on exams.
- I will prompt you to write a draft of most chapters by creating an `OUTLINE` and/or placing my raw materials (slides and coding examples from a previous version of the course) into the `raw/` folder for each chapter.
  - If an `OUTLINE` is provided, I will expect that it be followed fairly closely in terms of content. It may be hastily-written though, so please polish the text where needed. Sometimes I will flag sections that I want to be more flshed out than they are in my outline. Also, it's possible that I will skip over some key principles / concepts in my outline, so if it looks like I've missed something obviously critical, please add it and I'll review
  - Sometimes, no `OUTLINE` or a very minimal one will be provided, in which case, do your best to flesh out content based on my raw materials and the topic at hand
  - Also, my raw materials will likely make reference to Nyquist, the previous teaching language for the course. Feel free to ignore those references, as we've changed to Python

General stylistic notes (will update w/ preferences as I go along):

- Before making any changes, always reread the file to edit and AGENTS.md, as I will be using a highly iterative workflow of editing your outputs, and I don't want my work to be overwritten or my updates to AGENTS.md to be ignored.
- General writing:
  - The audience of this book will be CS oriented. Avoid or define music jargon unless strictly necessary or if it's in common vernacular (e.g., "note" is fine, but "chord" is borderline).
  - Use _italics_ to highlight or contrast concepts, and **bold for inline key points**. There is a {vocab}`vocabulary` directive ideally used the first time a vocab term is defined in the book
  - I'm okay with _some_ em dashes, but use them sparingly. Avoid semicolons entirely. When in doubt, just split into two sentences
  - Avoid run-on sentences, especially ones with 4 or more clauses
  - Format titles in _Italics and Title Case_. Format song names as Artist - _Title_
  - When typesetting inline itemized lists, use (1) item A, (2) item B, and (3) item C. For actual Markdown itemized lists line-by-line, use 1. for everything and let markdown to the counting, not 1., 2., etc.
  - On occasion, I like the "inclusive we" pedagogical voice, e.g., "So far, we have studied addition. Now we are going to learn about multipication"
  - Self refer to this as a "book", e.g., "for practical purposes in this book, the Fourier transform is defined as ...". I might use the phrase "in this course" in my outlines, but this is a mistake on my part.
  - The downstream formatting splits each `##`/`###` subsection onto its own page, so a reader may not see adjacent subsections together. Do not refer to figures, equations, or content across subsection boundaries (avoid "the figure above" when the figure is in a different subsection). Keep each figure in the subsection that discusses it, duplicating it if two subsections both need it.
- Mathematical formalisms:
  - I am pretty particular about mathematical formalisms. They should be quite rigorous, but not so detailed as to come at the expense of conceptual understanding
  - Continuous functions should be e.g. $x(t)$, where $t$ is time. For samples and DSP, notation should be $x[n]$, where $n$ is a sample index, and $x[n] = x(n / f_s)$. Frequency domain may be interchangeably expressed as $X(\omega)$ (continuous angular frequency), $X(f)$ (continuous frequency), or $X[m]$ (discrete bin) depending on the situation
  - I like function type signatures where helpful, e.g., $x(t) : \mathbb{R} \to \mathbb{R}$, $X(\omega) : \mathbb{R} \to \mathbb{C}$
  - When possible, I don't want students to memorize formula. Instead, let's help them work through the algebra. E.g., if $t_0$ is {unit}`seconds,cycle` and $f_0$ is {unit}`cycles,second`, then $f_0 = 1 / t_0$ by the units
- Figures and sound examples:
  - Figures and sound examples are great! Feel free to write Python code to synthesize audio or plots that can be included. If code is written just to make figures or sound examples rather than for pedagogical purposes of implementation, please store it in `figures/`. Otherwise, code that students should read should be in `code/`
    - Reiterating: do _not_ put code into `code` that is just used to create figures! `code/` is for student eyes, `figures/` is for agent/educator eyes. Never reference code in `figures` in the chapterr!
  - For audio assets, normalize to -6dBFS unless otherwise specified, to avoid hurting students' ears
  - For plots, prefer wide plots with larger font sizes. Include axis labels but avoid plot titles - the plot will be explained in context or in a caption.
- Code
  - Coding examples should (for now) be standalone scripts. Minimal dependencies. Use vectorized computation in `numpy`. In chapter 2, a library called `pyquist` will be introduced, which is a lightweight library w/ basic computer music utilities. Use `pyquist` audio utilities once the library is introduced, and use raw `numpy` or `soundfile` before that
  - Code should always have typehints, _including_ inline code examples shown in the prose (not just the standalone files in `code/`). Any function that returns audio should return `pq.Audio`, unless conceptually it's not audio (e.g., `build_wavetable` should return np.ndarray, while `wavetable_synth` should return pq.Audio).
  - Occasionally, it will be useful to inline code into the chapters for pedagogical reasons. In those cases, keep the code as minimal as possible, and link to the verbose code file, but try to keep the inline code as close to a section of the verbose file as possible.
  - In other cases, it will be useful pedagogically to embed longer, executable code examples using `pyodide`. Avoid this for now, but we will add it soon.
  - Always execute code examples in local virtual environment
  - Never do any `sys.path` modification in any of the code examples, assume dependencies are installed in the execution environment, and altert me if a dependency is needed for code examples that's not available in the environment.
  - Also, use `pathlib` instead of `os.path` whenever needing to reference assets or anything like that
