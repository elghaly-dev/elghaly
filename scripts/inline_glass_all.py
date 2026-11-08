#!/usr/bin/env python3
"""Inline css/glass.css into every page that already has an inline block."""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITEKIT = ROOT / "tools/site-kit/sitekit.py"
RULES = (ROOT / "css/glass.css").read_text(encoding="utf-8").rstrip() + "\n"
START_TPL = "<!-- inline:css/glass.css"
END = "<!-- /inline:css/glass.css -->"


def inline_page(path: pathlib.Path) -> None:
    text = path.read_text(encoding="utf-8")
    if START_TPL not in text:
        return
    page = path.relative_to(ROOT).as_posix()
    start_line = START_TPL + f" — edit css/glass.css, then: python3 tools/site-kit/sitekit.py inline {page} css/glass.css -->"
    block = f"{start_line}\n  <style>\n{RULES}  </style>\n  {END}"
    pattern = re.compile(re.escape(START_TPL) + r".*?" + re.escape(END), re.S)
    new, n = pattern.subn(lambda _m: block, text, count=1)
    if n != 1:
        raise SystemExit(f"{page}: could not replace inline block ({n})")
    if new != text:
        path.write_text(new, encoding="utf-8")
        print(f"   +  {page}")


def main() -> None:
    for html in sorted(ROOT.rglob("*.html")):
        if ".git" in html.parts:
            continue
        inline_page(html)


if __name__ == "__main__":
    main()
