This repository hosts the code for a computer music textbook called _Computer Music Principles_. This is intended to be a technically rigorous textbook used when music is taught in a computer science context.

Logistics:

- The book is written in Markdown with lots of multimedia (LaTeX, code, audio, images)
- By default, the Markdown is typeset to HTML. Rendering is handled by `.render/render.js`, which is a pretty barebones conversion. The render script may handle the multimedia in increasingly custom ways over time
- Chapters are in `chapter/`. Each chapter is a folder w/ `assets` (multimedia) and `code` (Python examples)
- `chapter/0-computer-music/index.md` codifies additional guiding design principles of the textbook, always read this first if you haven't already
- Each chapter should conclude w/ some questions for students to complete and turn in to their instructor. Most often, these should be concrete questions that ask students to apply the technical knowledge they've learned from the chapter. Sometimes, these can be open-ended (e.g., for chapter 0).
- Each chapter should also conclude w/ some musical examples (just artist/composer - title) where the techniques in that chapter are explored

General stylistic notes (will update w/ preferences as I go along):

- Mathematical formalisms:
  - I am pretty particular about mathematical formalisms. They should be quite rigorous, but not at the expense of conceptual understanding.
- General writing:
  - I like em dashes, but use them sparingly
  - Avoid run-on sentences, especially ones with 4 or more clauses
