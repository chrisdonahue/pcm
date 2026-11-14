# About _Principles of Computer Music_

_Principles of Computer Music_ is a free online textbook that teaches the technical principles and creative practice of musical computing from a computer science perspective in Python.

This textbook was written by [Chris Donahue](https://chrisdonahue.com) as a companion to CMU's Intro to Computer Music Course (15-322/622).

© 2026 Chris Donahue. All rights reserved. **Do not copy or redistribute without permission**. See [LICENSE](license.md) for details.

## Organization

This text is roughly organized into two parts:

- **Part 1: _Foundations_** (Chapters 0-10): Foundational material for computer music.
- **Part 2: _Topics_** (Chapters 11-17): Specific topics that build upon the foundation.

## Status

**This textbook is currently in a "complete rough draft" state**. It is mostly content-complete, but the author intends to do substantial revision passes before stamping a first edition.

Some of the current organization of the textbook reflects practical decisions for the text to accompany the Fall 2026 iteration of the course. After the semester, I plan to spin out the real-time section of Chapter 10 into a standalone chapter. I may also expand the psychoacoustics material in Chapter 15 into a standalone chapter.

## Feedback

We welcome feedback on this book from students and readers. **Share your thoughts through the {{ feedback_form }}**, which includes an optional email field if you would like us to follow up. If you believe you have found an error in the text, please report it the same way. Corrections are tracked on the [Errata](errata.md) page.

## AI disclosure

:::{important}
**AI Disclosure**: This text was written with support from AI, which made it possible to write a complete text within a single semester. **The author contributed all of the organization and high-level content, while AI drafted much of the prose, code, and figures**. The author reviewed and edited every word.
:::

**Human effort**. This book reflects about 150 hours of the author's time, estimated from the timestamps of commits, chapter outlines, and prompts to Claude. Each chapter took roughly 5 to 15 hours, split between writing the outline and revising Claude's drafts. This excludes about 35 hours building supporting software (pyquist, and TA David Liu's contributions of the book's rendering tools), and the years of lecture slides and code from earlier offerings of the course.

**AI assistance**. This book was written with Claude Opus 4.6 through 5.5. The authorship process for each chapter was as follows:

1. (Human) Chris wrote a detailed `OUTLINE.md`, specifying all of the content and organization
1. (Human) Chris added his lecture slides and code from previous years of the course as references
1. (AI) Claude drafted the chapter from the outline, slides, and `AGENTS.md` file
1. (Human) Chris read every word of the draft and made edits and/or left feedback
1. (AI) Claude addressed the feedback
1. Steps 4 and 5 repeated until Chris was satisfied with the chapter

**Provenance**. The original handwritten outlines (`OUTLINE.md`) for each chapter are preserved in the [textbook's GitHub repo](https://github.com/chrisdonahue/pcm), and each handoff between Chris and Claude is a separate commit in its `git` history.


## Acknowledgements

This book was heavily inspired by [Brian McFee](https://brianmcfee.net)'s [_Digital Signals Theory_](https://brianmcfee.net/dstbook-site/content/intro.html), and the formatting builds upon [McFee's executable book project template](https://github.com/bmcfee/dstbook). This book was also inspired by years of reading [Julius Orion Smith's online textbooks and course materials](https://ccrma.stanford.edu/~jos).

David Liu, music technology undergrad at CMU and TA for the course, played a key role in formatting and publishing the textbook content online.

This book would not exist without the efforts of [Roger Dannenberg](https://www.cs.cmu.edu/~rbd/), who carved out a path for computer music at CMU through his research and by creating the original _Introduction to Computer Music_ course and [eponymous textbook](https://compmus.com/icm).

Special thanks to [Tom Cortina](https://www.cs.cmu.edu/~tcortina) for supporting Chris's journey in teaching this course.

## Dedication

_For Jayhee Min_, who found beauty in music.
