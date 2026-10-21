#!/usr/bin/env python3
"""Apply chatting.elghaly.dev sitewide nav, badge, and localized pages."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SITEKIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sitekit.py")

LANGS = ("en", "ar", "ru", "zh")
LANG_LABELS = {
    "en": ("English", "en"),
    "ar": ("العربية", "ar"),
    "ru": ("Русский", "ru"),
    "zh": ("中文", "zh-Hans"),
}

NAV_LABELS = {
    "en": {"products": "Products", "chatting": "Chatting", "plumb": "Plumb", "quay": "QUAY", "contact": "Contact"},
    "ar": {"products": "المنتجات", "chatting": "Chatting", "plumb": "Plumb", "quay": "QUAY", "contact": "تواصل"},
    "ru": {"products": "Продукты", "chatting": "Chatting", "plumb": "Plumb", "quay": "QUAY", "contact": "Контакты"},
    "zh": {"products": "产品", "chatting": "Chatting", "plumb": "Plumb", "quay": "QUAY", "contact": "联系"},
}

SUBPAGES = (
    "about.html",
    "contact.html",
    "delivery.html",
    "refund.html",
    "terms.html",
    "privacy.html",
)

GLASS_PAGES = ("index.html", "chatting.html", "plumb.html", "quay.html", *SUBPAGES)


def lang_prefix(lang: str) -> str:
    return "" if lang == "en" else f"/{lang}"


def lang_href(lang: str, page_file: str | None) -> str:
    """page_file: None for home, else e.g. about.html or chatting."""
    if lang == "en":
        return f"/{page_file}" if page_file else "/"
    if page_file:
        return f"/{lang}/{page_file}"
    return f"/{lang}/"


def nav_html(lang: str, active: str) -> str:
    root = lang_prefix(lang)
    home_href = lang_href(lang, None)
    lab = NAV_LABELS.get(lang, NAV_LABELS["en"])
    links = [
        ("home", lab["products"], f"{home_href}#products"),
        ("chatting", lab["chatting"], "/chatting"),
        ("plumb", lab["plumb"], "/plumb"),
        ("quay", lab["quay"], "/quay"),
        ("contact", lab["contact"], lang_href(lang, "contact.html")),
    ]
    nav_bits = []
    for key, label, href in links:
        cur = ' aria-current="page"' if key == active else ""
        nav_bits.append(f'        <a href="{href}"{cur}>{label}</a>')
    lang_bits = []
    page_suffix = None
    if active not in ("home", "chatting", "plumb", "quay"):
        page_suffix = f"{active}.html" if not active.endswith(".html") else active
    for code in LANGS:
        label, hreflang = LANG_LABELS[code]
        href = lang_href(code, page_suffix)
        if page_suffix or active == "home":
            cur = ' aria-current="page"' if code == lang else ""
        else:
            cur = ""
        lang_bits.append(
            f'        <a class="lang-btn" href="{href}" hreflang="{hreflang}" lang="{hreflang}"{cur}>{label}</a>'
        )
    return f"""  <header class="nav">
    <div class="nav__in">
      <a class="brand" href="{home_href}" aria-label="elghaly home">elghaly</a>
      <a class="nav__badge" href="https://35.elghaly.dev/" rel="noopener noreferrer" title="35 desk"><span class="nav__badge-dot" aria-hidden="true">●</span> 35</a>
      <nav class="nav__links nav__links--always nav__pill" aria-label="Main">
{chr(10).join(nav_bits)}
      </nav>
      <nav class="lang-switch" aria-label="Language">
{chr(10).join(lang_bits)}
      </nav>
    </div>
  </header>"""


def footer_contact() -> str:
    return (
        '<p class="footer__mail">'
        '<a href="mailto:support@elghaly.dev">support@elghaly.dev</a></p>\n'
        "    <p>elghaly, LLC</p>"
    )


def replace_subpage_shell(text: str, lang: str, page: str, title: str, tag: str) -> str:
    active = page.replace(".html", "")
    nav = nav_html(lang, active)
    if 'class="skip"' not in text:
        text = text.replace("<body>", '<body>\n  <a class="skip" href="#main">Skip to content</a>\n', 1)
    hero_pat = re.compile(r"<header class=\"hero\">.*?</header>\s*", re.DOTALL)
    head_block = f"""{nav}

  <div class="page-head">
    <h1 class="page-head__title">{title}</h1>
    <p class="page-head__tag">{tag}</p>
  </div>

"""
    text = hero_pat.sub(head_block, text, count=1)
    text = re.sub(r'<main class="policy">', '<main id="main" class="policy">', text, count=1)
    text = re.sub(
        r'<p class="footer__biz"[^>]*>.*?</p>\s*',
        footer_contact() + "\n    ",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(r'data-theme="solana"\s*', "", text)
    text = re.sub(r'<link rel="stylesheet" href="(?:/)?css/style\.css[^"]*">\s*', "", text, count=1)
    if "css/glass.css" not in text and "inline:css/glass.css" not in text:
        needle = "  <link rel=\"preload\" href=\"/fonts/cinzel-500-wordmark.woff2\""
        insert = (
            '  <!-- inline:css/glass.css — edit css/glass.css, then: '
            f"python3 tools/site-kit/sitekit.py inline {page} css/glass.css -->\n"
            '  <link rel="stylesheet" href="css/glass.css">\n'
        )
        if needle in text:
            text = text.replace(needle, insert + needle, 1)
        else:
            text = text.replace("</head>", insert + "</head>", 1)
    return text


def inline_glass(page_path: str) -> None:
    rel = os.path.relpath(page_path, ROOT).replace(os.sep, "/")
    if not os.path.isfile(page_path):
        return
    # sitekit resolves css beside the page; nested lang/ pages use repo-root css.
    if rel.count("/") > 0:
        css_path = os.path.join(ROOT, "css/glass.css")
        rules = open(css_path, encoding="utf-8").read().rstrip() + "\n"
        text = open(page_path, encoding="utf-8").read()
        start = "<!-- inline:css/glass.css"
        end = "<!-- /inline:css/glass.css -->"
        pat = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
        page_base = os.path.basename(page_path)
        block = (
            f"<!-- inline:css/glass.css — edit css/glass.css, then: "
            f"python3 tools/site-kit/sitekit.py inline {rel} css/glass.css -->\n"
            f"  <style>\n{rules}  </style>\n  {end}"
        )
        if pat.search(text):
            text = pat.sub(lambda _m: block, text, count=1)
        else:
            href = re.compile(r'<link rel="stylesheet" href="(?:\.\./)*css/glass.css"')
            m = href.search(text)
            if m:
                tag = re.search(r"<link\b[^>]*css/glass.css[^>]*>", text)
                if tag:
                    text = text[: tag.start()] + block + text[tag.end() :]
        open(page_path, "w", encoding="utf-8").write(text)
        return
    subprocess.run(
        [sys.executable, SITEKIT, "inline", rel, "css/glass.css"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )


def load_home_translations() -> dict:
    path = os.path.join(os.path.dirname(__file__), "i18n-home.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_english_home_strings() -> dict[str, str]:
    """English defaults keyed like i18n-home.json (from main index data-i18n markers)."""
    try:
        main_html = subprocess.check_output(
            ["git", "show", "main:index.html"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {}
    strings = dict(re.findall(r'data-i18n="([^"]+)"[^>]*>([^<]*)<', main_html))
    strings["prod_h"] = "Products"
    return strings


def apply_home_text_replace(html: str, lang: str, trans: dict) -> str:
    en = load_english_home_strings()
    pairs = sorted(
        ((en[k], v) for k, v in trans[lang].items() if k != "__title" and k in en and en[k]),
        key=lambda p: len(p[0]),
        reverse=True,
    )
    for src, dst in pairs:
        html = html.replace(src, dst)
    return html


def apply_data_i18n(html: str, trans: dict) -> str:
    for key, val in trans.items():
        if key == "__title":
            continue
        html = re.sub(
            rf'(\bdata-i18n="{re.escape(key)}"[^>]*>)([^<]*)(</[^>]+>)',
            lambda m, v=val: m.group(1) + v + m.group(3),
            html,
            count=1,
        )
    html = re.sub(r'\s*data-i18n="[^"]+"', "", html)
    return html


def apply_home_lang(html: str, lang: str, trans: dict) -> str:
    if lang != "en":
        if 'data-i18n="' in html:
            html = apply_data_i18n(html, trans[lang])
        else:
            html = apply_home_text_replace(html, lang, trans)
        hreflang = LANG_LABELS[lang][1]
        html = re.sub(r"<html lang=\"en\">", f'<html lang="{hreflang}">', html, count=1)
        if lang == "ar":
            html = html.replace("<html ", '<html dir="rtl" ', 1)
        title = trans[lang].get("__title", "elghaly")
        html = re.sub(r"<title>[^<]+</title>", f"<title>{title}</title>", html, count=1)
    else:
        html = re.sub(r'\s*data-i18n="[^"]+"', "", html)
    html = re.sub(r"<header class=\"nav\">.*?</header>", nav_html(lang, "home"), html, count=1, flags=re.DOTALL)
    html = re.sub(
        r"<p>elghaly · <a href=\"mailto:support@elghaly\.dev\">support@elghaly\.dev</a></p>",
        footer_contact(),
        html,
        count=1,
    )
    if lang != "en":
        prefix = f"/{lang}"
        for path in (
            "contact.html",
            "about.html",
            "refund.html",
            "delivery.html",
            "terms.html",
            "privacy.html",
        ):
            html = html.replace(f'href="/{path}"', f'href="{prefix}/{path}"')
    html = re.sub(r'<script src="/page-menu.js[^"]*" defer></script>\s*', "", html)
    return html


def strip_home_i18n_script(html: str) -> str:
    return re.sub(
        r"  <script>\s*// Languages for the home page:.*?</script>\s*",
        "",
        html,
        count=1,
        flags=re.DOTALL,
    )


def header_scrub(text: str) -> str:
    """Sitewide nav uses the elghaly brand only; never a Chatting subtitle in <header>."""
    return re.sub(
        r'(<header class="nav">.*?</header>)',
        lambda m: m.group(1).replace("Chatting by elghaly", "elghaly"),
        text,
        count=1,
        flags=re.DOTALL,
    )


CONSENT_LINK_OLD = """    #elghaly-consent .ec-text a {
      color: #ffffff;
      text-underline-offset: 2px;
    }"""
CONSENT_LINK_NEW = """    #elghaly-consent .ec-text a {
      display: inline-flex;
      align-items: center;
      min-height: 44px;
      padding: 0 0.25rem;
      color: #ffffff;
      text-underline-offset: 2px;
    }"""


def patch_consent_tap_targets(text: str) -> str:
    if CONSENT_LINK_OLD in text:
        return text.replace(CONSENT_LINK_OLD, CONSENT_LINK_NEW)
    return text


def legal_scrub(text: str) -> str:
    text = re.sub(
        r"<p class=\"build__text\">These terms are governed by the laws of the United Arab Emirates as applied in the Emirate of Dubai\.</p>\s*",
        "",
        text,
    )
    text = text.replace(
        "Everything we sell is digital. Nothing is shipped, there are no shipping charges, and we deliver to buyers in every country we can legally sell to. ",
        "Everything we sell is digital. Nothing is shipped and there are no shipping charges. ",
    )
    text = text.replace(
        "Everything we sell is digital and delivered by email or transfer, worldwide. ",
        "Everything we sell is digital and delivered by email or transfer. ",
    )
    text = text.replace(
        "If you email us, we keep your message and address to reply to you.",
        "If you email us, we keep your message to reply to you.",
    )
    text = text.replace(
        "which may receive your IP address and browser details when the page loads. ",
        "which may receive connection details when the page loads. ",
    )
    return text


def apply_subpage_translations(html: str, lang: str, page: str, meta: dict) -> str:
    pairs = sorted(meta.get("replace", []), key=lambda p: len(p[0]), reverse=True)
    for en, loc in pairs:
        html = html.replace(en, loc)
    prefix = lang_prefix(lang)
    if prefix:
        for path in SUBPAGES:
            html = html.replace(f'href="/{path}"', f'href="{prefix}/{path}"')
        html = html.replace('href="/"', f'href="{prefix}/"')
    html = re.sub(r"<script src=\"/page-menu.js\" defer></script>\s*", "", html)
    return html


def main() -> None:
    index_path = os.path.join(ROOT, "index.html")
    with open(index_path, encoding="utf-8") as f:
        index_html = f.read()
    trans = load_home_translations()
    index_html = strip_home_i18n_script(index_html)
    index_html = header_scrub(index_html)
    index_en = apply_home_lang(index_html, "en", trans)
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_en)

    for lang in ("ar", "ru", "zh"):
        out_dir = os.path.join(ROOT, lang)
        os.makedirs(out_dir, exist_ok=True)
        localized = apply_home_lang(index_html, lang, trans)
        with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(localized)

    for product in ("chatting", "plumb", "quay"):
        path = os.path.join(ROOT, f"{product}.html")
        with open(path, encoding="utf-8") as f:
            html = f.read()
        html = header_scrub(html)
        html = re.sub(
            r"<header class=\"nav\">.*?</header>",
            nav_html("en", product),
            html,
            count=1,
            flags=re.DOTALL,
        )
        html = re.sub(
            r"<p>elghaly · <a href=\"mailto:support@elghaly\.dev\">support@elghaly\.dev</a></p>",
            footer_contact(),
            html,
            count=1,
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

    sub_titles = {
        "about.html": ("About", "Last updated: October 8, 2026"),
        "contact.html": ("Contact", "Last updated: October 8, 2026"),
        "delivery.html": ("Delivery", "Last updated: October 8, 2026"),
        "refund.html": ("Refunds", "Last updated: October 8, 2026"),
        "terms.html": ("Terms of service", "Last updated: October 8, 2026"),
        "privacy.html": ("Privacy policy", "Last updated: October 8, 2026"),
    }
    sub_trans_path = os.path.join(os.path.dirname(__file__), "i18n-subpages.json")
    sub_trans = {}
    if os.path.isfile(sub_trans_path):
        with open(sub_trans_path, encoding="utf-8") as f:
            sub_trans = json.load(f)

    for page in SUBPAGES:
        path = os.path.join(ROOT, page)
        with open(path, encoding="utf-8") as f:
            html = f.read()
        title, tag = sub_titles[page]
        html = legal_scrub(html)
        html = replace_subpage_shell(html, "en", page, title, tag)
        html = re.sub(r'<script src="/page-menu.js" defer></script>\s*', "", html)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        for lang in ("ar", "ru", "zh"):
            meta = sub_trans.get(lang, {}).get(page)
            if not meta:
                continue
            active = page.replace(".html", "")
            loc = html
            loc = re.sub(
                r"<header class=\"nav\">.*?</header>",
                nav_html(lang, active),
                loc,
                count=1,
                flags=re.DOTALL,
            )
            loc = re.sub(
                r'(<h1 class="page-head__title">)[^<]+(</h1>)',
                r"\1" + meta["title"] + r"\2",
                loc,
                count=1,
            )
            loc = re.sub(
                r'(<p class="page-head__tag">)[^<]*(</p>)',
                r"\1" + meta.get("tag", tag) + r"\2",
                loc,
                count=1,
            )
            loc = apply_subpage_translations(loc, lang, page, meta)
            hreflang = LANG_LABELS[lang][1]
            loc = re.sub(r"<html lang=\"en\">", f'<html lang="{hreflang}">', loc, count=1)
            if lang == "ar":
                loc = loc.replace("<html ", '<html dir="rtl" ', 1)
            out_dir = os.path.join(ROOT, lang)
            os.makedirs(out_dir, exist_ok=True)
            with open(os.path.join(out_dir, page), "w", encoding="utf-8") as f:
                f.write(loc)

    for rel in GLASS_PAGES:
        inline_glass(os.path.join(ROOT, rel))
    for lang in ("ar", "ru", "zh"):
        for name in ("index.html", *SUBPAGES):
            p = os.path.join(ROOT, lang, name)
            if os.path.isfile(p):
                inline_glass(p)

    for rel in (*GLASS_PAGES, "404.html", "consult.html"):
        p = os.path.join(ROOT, rel)
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                html = patch_consent_tap_targets(f.read())
            with open(p, "w", encoding="utf-8") as f:
                f.write(html)
    for lang in ("ar", "ru", "zh"):
        for name in ("index.html", *SUBPAGES):
            p = os.path.join(ROOT, lang, name)
            if os.path.isfile(p):
                with open(p, encoding="utf-8") as f:
                    html = patch_consent_tap_targets(f.read())
                with open(p, "w", encoding="utf-8") as f:
                    f.write(html)
    for product in ("chatting", "plumb", "quay"):
        p = os.path.join(ROOT, f"{product}.html")
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                html = patch_consent_tap_targets(f.read())
            with open(p, "w", encoding="utf-8") as f:
                f.write(html)

    print("Restyle applied.")


if __name__ == "__main__":
    main()
