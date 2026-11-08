#!/usr/bin/env python3
"""Verify molten-gold theme: token contrast + rendered colors + screenshots."""
from __future__ import annotations

import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ARTIFACTS = pathlib.Path("/opt/cursor/artifacts/gold-theme")
ARTIFACTS.mkdir(parents=True, exist_ok=True)

# Design tokens (must match css/glass.css)
BG = "#07080c"
CARD = "#10131f"
TEXT = "#f8e9c8"
MUTED = "#d4bc7a"
GOLD = "#ffc828"
GOLD_2 = "#ffe566"
GOLD_INK = "#07080c"

PAGES = [
    ("index-en-desktop", "/index.html", 1280, 900),
    ("index-en-mobile", "/index.html", 390, 844),
    ("about-en-desktop", "/about.html", 1280, 900),
    ("about-en-mobile", "/about.html", 390, 844),
    ("plumb-desktop", "/plumb.html", 1280, 900),
    ("ru-about-mobile", "/ru/about.html", 390, 844),
    ("zh-index-mobile", "/zh/index.html", 390, 844),
    ("ar-index-mobile", "/ar/index.html", 390, 844),
    ("iris-terms-desktop", "/iris/terms.html", 1280, 900),
]

RENDER_CHECKS = [
    ("/about.html", ".page-head__title", "color", "rgba(0, 0, 0, 0)", "gradient clip (transparent fill)"),
    ("/about.html", ".page-head__title", "backgroundImage", "linear-gradient", "metallic heading"),
    ("/about.html", ".section__label", "color", GOLD, "section label solid gold", 8),
    ("/about.html", ".brand", "color", GOLD, "nav wordmark gold", 8),
    ("/about.html", "main.policy a", "color", GOLD, "policy link gold", 8),
    ("/about.html", ".nav__links a", "color", GOLD_2, "nav link gold-2", 8),
    ("/plumb.html", ".btn--primary", "color", GOLD_INK, "primary button ink", 8),
    ("/index.html", ".mark", "backgroundImage", "linear-gradient", "home wordmark gradient"),
]


def hex_to_rgb(h: str) -> tuple[float, float, float]:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))


def rel_lum(rgb: tuple[float, float, float]) -> float:
    def chan(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (chan(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    l1, l2 = rel_lum(hex_to_rgb(a)), rel_lum(hex_to_rgb(b))
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def parse_rgb(s: str) -> tuple[int, int, int] | None:
    s = s.strip().lower()
    if s.startswith("#") and len(s) == 7:
        return tuple(int(s[i : i + 2], 16) for i in (1, 3, 5))
    if s.startswith("rgb"):
        nums = [int(float(x)) for x in s.replace("rgba(", "").replace("rgb(", "").replace(")", "").split(",")[:3]]
        return tuple(nums)  # type: ignore
    return None


def rgb_to_hex(t: tuple[int, int, int]) -> str:
    return "#" + "".join(f"{c:02x}" for c in t)


def token_contrast_report() -> list[str]:
    pairs = [
        ("ivory on night", TEXT, BG, 4.5),
        ("muted on night", MUTED, BG, 4.5),
        ("gold on night", GOLD, BG, 4.5),
        ("gold-2 on night", GOLD_2, BG, 4.5),
        ("gold-ink on gold btn", GOLD_INK, GOLD, 4.5),
        ("gold on card", GOLD, CARD, 4.5),
        ("muted on card", MUTED, CARD, 4.5),
    ]
    lines = ["Token contrast (WCAG AA 4.5:1 for normal text):"]
    fails = 0
    for label, fg, bg, need in pairs:
        ratio = contrast(fg, bg)
        ok = ratio >= need
        if not ok:
            fails += 1
        lines.append(f"  {'PASS' if ok else 'FAIL'} {label}: {ratio:.2f}:1 ({fg} on {bg})")
    if fails:
        lines.append(f"{fails} token pair(s) below AA.")
    return lines


def main() -> int:
    lines = token_contrast_report()
    errors: list[str] = []

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        lines.append("Playwright not installed; skipping render checks and screenshots.")
        print("\n".join(lines))
        return 1

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for name, path, w, h in PAGES:
            page = browser.new_page(viewport={"width": w, "height": h})
            url = ROOT.as_uri() + path
            page.goto(url, wait_until="networkidle", timeout=120_000)
            shot = ARTIFACTS / f"{name}.png"
            page.screenshot(path=str(shot), full_page=True)
            lines.append(f"Screenshot: {shot.name} ({w}x{h})")
            page.close()

        page = browser.new_page(viewport={"width": 1280, "height": 900})
        for path, sel, prop, expect, label, *tol in RENDER_CHECKS:
            tolerance = tol[0] if tol else None
            url = ROOT.as_uri() + path
            page.goto(url, wait_until="networkidle", timeout=120_000)
            el = page.locator(sel).first
            el.wait_for(state="visible", timeout=30_000)
            val = el.evaluate(
                f"(e) => getComputedStyle(e).{prop[0].lower()}{prop[1:]}"
            )
            if prop == "color" and tolerance:
                got = parse_rgb(val)
                exp = hex_to_rgb(expect)
                if got is None:
                    errors.append(f"{label}: could not parse color {val!r}")
                    continue
                dist = math.sqrt(sum((a - b * 255) ** 2 for a, b in zip(got, exp)))
                ok = dist <= tolerance
                lines.append(
                    f"  {'PASS' if ok else 'FAIL'} {label}: computed {rgb_to_hex(got)} (Δ≈{dist:.0f})"
                )
                if not ok:
                    errors.append(f"{label}: expected ~{expect}, got {rgb_to_hex(got)}")
            elif prop in ("backgroundImage",):
                ok = expect in (val or "")
                lines.append(f"  {'PASS' if ok else 'FAIL'} {label}: {val[:80] if val else val!r}")
                if not ok:
                    errors.append(f"{label}: expected {expect!r} in {prop}")
            elif prop == "color" and expect.startswith("rgba"):
                ok = val == expect
                lines.append(f"  {'PASS' if ok else 'FAIL'} {label}: {val!r}")
                if not ok:
                    errors.append(f"{label}: expected transparent fill for gradient text")
            else:
                got = parse_rgb(val)
                exp = hex_to_rgb(expect)
                ok = got == tuple(int(c * 255) for c in exp)
                lines.append(
                    f"  {'PASS' if ok else 'FAIL'} {label}: {rgb_to_hex(got) if got else val}"
                )
                if not ok:
                    errors.append(f"{label}: expected {expect}")
        browser.close()

    lines.append("")
    if errors:
        lines.append("Render failures:")
        lines.extend(f"  - {e}" for e in errors)
    else:
        lines.append("All render checks passed.")

    report = ARTIFACTS / "verify-report.txt"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nFull report: {report}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
