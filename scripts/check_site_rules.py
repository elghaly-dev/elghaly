#!/usr/bin/env python3
"""House-rule checks for elghaly.dev HTML (stdlib only)."""
import pathlib
import re
import sys
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent

FOOTER_URLS = [
    'href="https://chatting.elghaly.dev/"',
    'href="/about.html"',
    'href="mailto:support@elghaly.dev"',
    'href="/refund.html"',
    'href="/delivery.html"',
    'href="/terms.html"',
    'href="/privacy.html"',
]

FOOTER_BLOCK = re.compile(r"<footer\b[^>]*>(.*?)</footer>", re.I | re.S)

FORBIDDEN_WORDS = re.compile(r"\b(live|profit|guarantee|audit|launched)\b", re.I)
FORBIDDEN = [
    (re.compile(r"qq\.com", re.I), "qq.com"),
    (re.compile(r"telegram", re.I), "Telegram"),
    (re.compile(r"t\.me/", re.I), "t.me link"),
    (re.compile(r"facebook\.com", re.I), "Facebook"),
]

SKIP = {".git", ".github", "tools", "fonts", "assets"}
EXEMPT_FRAGMENTS = (
    "media/shopify/",
    "tools/site-kit/head.html",
)

CSP_FILE = ROOT / "csp-report-only.txt"
CSP_META = re.compile(
    r'<meta[^>]+http-equiv=["\']Content-Security-Policy-Report-Only["\'][^>]+content="([^"]*)"',
    re.I,
)
SITEMAP_AR = "https://elghaly.dev/ar/"
SATAR_HREF = "https://999.elghaly.dev/"
SATAR_LINE = "Check a forward before you trust it."


def csp_policy_expected() -> str:
    if not CSP_FILE.is_file():
        return ""
    for line in CSP_FILE.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            return s
    return ""


class _VisibleStrip(HTMLParser):
    __slots__ = ("_skip", "out")

    def __init__(self) -> None:
        super().__init__()
        self._skip = 0
        self.out: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() in ("script", "style"):
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self.out.append(data)


def visible_text(raw: str) -> str:
    raw = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    parser = _VisibleStrip()
    parser.feed(raw)
    parser.close()
    return re.sub(r"\s+", " ", " ".join(parser.out))


def is_redirect(raw: str) -> bool:
    head = raw.split("</head>", 1)[0] if re.search(r"</head>", raw, re.I) else raw[:4000]
    return bool(re.search(r'<meta[^>]+http-equiv=["\']refresh["\']', head, re.I))


def is_exempt(path: pathlib.Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    for pref in EXEMPT_FRAGMENTS:
        if rel.startswith(pref) or rel == pref:
            return True
    return False


def is_full_page(path: pathlib.Path, raw: str) -> bool:
    if is_exempt(path):
        return False
    if not re.search(r"<!DOCTYPE\s+html|<html\b", raw, re.I):
        return False
    if is_redirect(raw):
        return False
    return True


def footer_has_llc(raw: str) -> bool:
    block = FOOTER_BLOCK.search(raw)
    if block:
        return "elghaly, LLC" in block.group(1)
    return False


def html_pages():
    for path in sorted(ROOT.rglob("*.html")):
        if any(part in SKIP for part in path.parts):
            continue
        if "site-kit" in path.parts and path.name == "head.html":
            continue
        yield path


def main():
    errors = []
    index = ROOT / "index.html"
    if index.exists():
        text = index.read_text(encoding="utf-8")
        for url in FOOTER_URLS:
            if url not in text:
                errors.append("index.html missing footer link %s" % url)
        vis = visible_text(text)
        for pat, label in FORBIDDEN:
            if pat.search(vis):
                errors.append("index.html: forbidden %s" % label)
        for match in FORBIDDEN_WORDS.finditer(vis):
            errors.append("index.html: forbidden word %r" % match.group(0))
        if 'data-label="Faithful Servant"' not in text:
            errors.append('index.html: AI label must be data-label="Faithful Servant"')
        if SATAR_HREF not in text or SATAR_LINE not in text:
            errors.append("index.html: missing Satar card (999.elghaly.dev + tagline)")

    expected_csp = csp_policy_expected()
    if not expected_csp:
        errors.append("csp-report-only.txt: missing policy line")
    else:
        headers = ROOT / "_headers"
        if not headers.is_file() or expected_csp not in headers.read_text(encoding="utf-8"):
            errors.append("_headers: missing Content-Security-Policy-Report-Only policy")

    sitemap = ROOT / "sitemap.xml"
    if sitemap.is_file():
        sm = sitemap.read_text(encoding="utf-8")
        if f"<loc>{SITEMAP_AR}</loc>" not in sm:
            errors.append("sitemap.xml: missing /ar/ URL")
        if 'hreflang="ar"' not in sm:
            errors.append("sitemap.xml: missing hreflang ar alternate on home")
    else:
        errors.append("sitemap.xml: missing")

    for path in html_pages():
        rel = path.relative_to(ROOT)
        raw = path.read_text(encoding="utf-8")
        if is_full_page(path, raw):
            if not footer_has_llc(raw):
                errors.append("%s: footer missing elghaly, LLC" % rel)
            if expected_csp:
                m = CSP_META.search(raw)
                if not m:
                    errors.append("%s: missing Content-Security-Policy-Report-Only meta" % rel)
                elif m.group(1) != expected_csp:
                    errors.append("%s: CSP report-only meta does not match csp-report-only.txt" % rel)
        if path.name == "index.html" and path.parent.name in ("ar", "ru", "zh"):
            if SATAR_HREF not in raw or SATAR_LINE not in raw:
                errors.append("%s: missing Satar card" % rel)
        if path.name == "index.html" and path.parent == ROOT:
            continue
        if rel.parts[0] in ("ar", "ru", "zh") and len(rel.parts) == 2 and rel.name == "index.html":
            continue
        vis = visible_text(raw)
        for pat, label in FORBIDDEN:
            if pat.search(vis):
                errors.append("%s: forbidden %s" % (rel, label))

    for msg in errors:
        print("FAIL", msg)
    if errors:
        sys.exit(1)
    print("ok: elghaly.dev house rules")


if __name__ == "__main__":
    main()
