#!/usr/bin/env python3
"""Normalize Jupyter notebooks to one environment-agnostic format.

Strips everything that running a notebook, or a particular editor or kernel,
leaves behind, and keeps only what is semantic for the book:

- code cells: outputs removed and execution counts cleared
- cell metadata: only the book's `tags` (myst-nb), `interactive`, and
  `animation` keys survive. Colab, VS Code, and timing metadata are dropped.
- cell ids: removed, with nbformat 4.4, so diffs show only real changes
- notebook metadata: a generic Python 3 kernelspec, plus any `mystnb` settings
- formatting: sources as lists of lines, sorted keys, and a one-space indent,
  as Jupyter itself writes notebooks

Usage: python3 tools/clean_notebooks.py [--check] NOTEBOOK ...

Exits 1 if any notebook was cleaned (or, with --check, would be), so that
pre-commit stops the commit and the cleaned files can be re-staged.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

KEEP_CELL_METADATA = ("tags", "interactive", "animation", "format", "raw_mimetype")
KEEP_NOTEBOOK_METADATA = ("mystnb",)
KERNELSPEC = {"display_name": "Python 3", "language": "python", "name": "python3"}


def split_lines(source: str | list[str]) -> list[str]:
    if isinstance(source, list):
        source = "".join(source)
    return source.splitlines(keepends=True)


def clean(nb: dict) -> dict:
    cells = []
    for cell in nb["cells"]:
        out = {
            "cell_type": cell["cell_type"],
            "metadata": {k: v for k, v in cell.get("metadata", {}).items()
                         if k in KEEP_CELL_METADATA},
            "source": split_lines(cell.get("source", "")),
        }
        if "attachments" in cell:
            out["attachments"] = cell["attachments"]
        if cell["cell_type"] == "code":
            out["execution_count"] = None
            out["outputs"] = []
        cells.append(out)
    metadata = {"kernelspec": dict(KERNELSPEC), "language_info": {"name": "python"}}
    metadata.update({k: v for k, v in nb.get("metadata", {}).items()
                     if k in KEEP_NOTEBOOK_METADATA})
    return {"cells": cells, "metadata": metadata, "nbformat": 4, "nbformat_minor": 4}


def dumps(nb: dict) -> str:
    return json.dumps(nb, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def main(args: list[str]) -> int:
    check = "--check" in args
    changed = []
    for path in (Path(a) for a in args if a != "--check"):
        text = path.read_text(encoding="utf-8")
        cleaned = dumps(clean(json.loads(text)))
        if cleaned != text:
            changed.append(path)
            if not check:
                path.write_text(cleaned, encoding="utf-8")
    for path in changed:
        print(f"{'would clean' if check else 'cleaned'} {path}")
    return 1 if changed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
