#!/usr/bin/env python3
"""Refresh home index pages with molten-gold tokens (EN/RU/ZH/AR)."""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
INDEXES = [
    ROOT / "index.html",
    ROOT / "ru/index.html",
    ROOT / "zh/index.html",
    ROOT / "ar/index.html",
]

OLD_ROOT = re.compile(
    r""":root \{
  --night: #07080c;
  --night-2: #0d1120;
  --tile: #10131f;
  --line: rgba\(212, 175, 90, \.22\);
  --gold: #d4af5a;
  --gold-soft: #ecd9a0;
  --gold-bronze: #8b6914;
  --gold-highlight: #f2e4b8;
  --lapis: #2a4cb3;
  --turquoise: #34b8ac;
  --ivory: #efe8d8;
  --muted: #a39b88;
  --radius: 18px;
  color-scheme: dark;
\}""",
    re.M,
)

NEW_ROOT = """:root {
  --night: #07080c;
  --night-2: #0d1120;
  --tile: #10131f;
  --line: rgba(255, 186, 48, 0.28);
  --gold: #ffc828;
  --gold-soft: #ffe566;
  --gold-deep: #e07810;
  --gold-highlight: #fff6b8;
  --lapis: #2a4cb3;
  --turquoise: #34b8ac;
  --ivory: #f8e9c8;
  --muted: #d4bc7a;
  --radius: 18px;
  color-scheme: dark;
}"""

OLD_MARK = re.compile(
    r"""  background: linear-gradient\(
    168deg,
    var\(--gold-bronze\) 0%,
    #a67c1a 15%,
    #c49a3c 30%,
    var\(--gold-highlight\) 42%,
    var\(--gold-soft\) 50%,
    var\(--gold\) 58%,
    #b8893a 72%,
    #7a5c22 88%,
    var\(--gold-bronze\) 100%
  \);""",
    re.M,
)

NEW_MARK = """  background: linear-gradient(
    168deg,
    #c45a08 0%,
    var(--gold-deep) 14%,
    #ff9f1a 28%,
    var(--gold) 40%,
    var(--gold-highlight) 48%,
    #fffbe6 52%,
    var(--gold-soft) 58%,
    var(--gold) 66%,
    #f09018 80%,
    #c45a08 100%
  );"""

SUBS = [
    ("rgba(212, 175, 90,", "rgba(255, 186, 48,"),
    (
        "radial-gradient(80% 50% at 50% 110%, rgba(212, 175, 90, .10), transparent 70%),",
        "radial-gradient(80% 50% at 50% 110%, rgba(255, 186, 48, .14), transparent 70%),",
    ),
    ("/* Night and gold: a near-black night, Anubis's gold and lapis, ivory text. */",
     "/* Night and molten gold: vivid yellow-gold on near-black, lapis glow. */"),
]


def main() -> None:
    for path in INDEXES:
        text = path.read_text(encoding="utf-8")
        text, n1 = OLD_ROOT.subn(NEW_ROOT, text, count=1)
        text, n2 = OLD_MARK.subn(NEW_MARK, text, count=1)
        for old, new in SUBS:
            text = text.replace(old, new)
        if n1 != 1 or n2 != 1:
            raise SystemExit(f"{path}: root={n1} mark={n2}")
        path.write_text(text, encoding="utf-8")
        print(f"ok {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
