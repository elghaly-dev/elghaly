#!/usr/bin/env python3
"""Build Iris / Stale / Glance link-card SVGs and 192px WebP thumbs."""

from __future__ import annotations

import io
import os

import cairosvg
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS = os.path.join(ROOT, "assets")

COMMON_HEAD = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192" width="192" height="192">
  <defs>
    <radialGradient id="bg" cx="50%" cy="42%" r="72%">
      <stop offset="0%" stop-color="#3d2588"/>
      <stop offset="55%" stop-color="#12082a"/>
      <stop offset="100%" stop-color="#04030c"/>
    </radialGradient>
    <linearGradient id="wire" x1="8%" y1="6%" x2="92%" y2="94%">
      <stop offset="0%" stop-color="#b388ff"/>
      <stop offset="45%" stop-color="#7c4dff"/>
      <stop offset="100%" stop-color="#40c4ff"/>
    </linearGradient>
    <linearGradient id="name" x1="0%" y1="50%" x2="100%" y2="50%">
      <stop offset="0%" stop-color="#d4cfff"/>
      <stop offset="55%" stop-color="#c9c2ff"/>
      <stop offset="100%" stop-color="#7ae8ff"/>
    </linearGradient>
    <linearGradient id="lock" x1="50%" y1="0%" x2="50%" y2="100%">
      <stop offset="0%" stop-color="#e2deff"/>
      <stop offset="100%" stop-color="#8b7cff"/>
    </linearGradient>
    <filter id="glow" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur stdDeviation="1.6" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="soft" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="0.8"/>
    </filter>
  </defs>
  <rect width="192" height="192" rx="24" fill="url(#bg)"/>
  <g opacity="0.55">
    <circle cx="34" cy="28" r="0.7" fill="#e8e4ff"/>
    <circle cx="148" cy="44" r="0.5" fill="#c9c2ff"/>
    <circle cx="162" cy="118" r="0.6" fill="#ffffff"/>
    <circle cx="52" cy="150" r="0.45" fill="#b9b3e6"/>
  </g>
  <circle cx="96" cy="96" r="78" fill="none" stroke="url(#wire)" stroke-width="1.4" opacity="0.85"/>
  <circle cx="96" cy="96" r="70" fill="none" stroke="#c9c2ff" stroke-width="0.6" stroke-dasharray="2.5 4.5" opacity="0.55"/>
"""

COMMON_TAIL = """
  <g transform="translate(96 152)" filter="url(#glow)">
    <rect x="-11" y="-2" width="22" height="14" rx="4" fill="none" stroke="url(#lock)" stroke-width="2.2"/>
    <path d="M -7 -2 V -7 a 7 7 0 0 1 14 0 V -2" fill="none" stroke="url(#lock)" stroke-width="2.2" stroke-linecap="round"/>
    <circle cy="5" r="2.2" fill="#17123d" stroke="#e2deff" stroke-width="1"/>
  </g>
"""

CRYSTAL = """
  <g stroke="url(#wire)" stroke-width="0.85" fill="none" opacity="0.75" filter="url(#soft)">
    <path d="M96 34 L128 58 L118 98 L74 98 L64 58 Z"/>
    <path d="M96 34 L96 98"/>
    <path d="M64 58 L128 58"/>
    <path d="M74 98 L118 34"/>
    <path d="M118 98 L74 34"/>
    <path d="M96 58 L128 98 L64 98 Z" opacity="0.55"/>
  </g>
"""


def iris_svg() -> str:
    return (
        COMMON_HEAD
        + CRYSTAL
        + """
  <g filter="url(#glow)">
    <ellipse cx="96" cy="88" rx="30" ry="18" fill="none" stroke="url(#name)" stroke-width="2.4"/>
    <circle cx="96" cy="88" r="9" fill="#17123d" stroke="#c9c2ff" stroke-width="1.6"/>
    <circle cx="96" cy="88" r="4.5" fill="#7ae8ff" opacity="0.9"/>
    <path d="M96 70 C78 74 70 88 96 106 C122 88 114 74 96 70 Z" fill="none" stroke="#9b5cff" stroke-width="1.2" opacity="0.65"/>
    <path d="M82 88 H110" stroke="#c9c2ff" stroke-width="0.8" opacity="0.45"/>
    <path d="M96 76 V100" stroke="#c9c2ff" stroke-width="0.8" opacity="0.45"/>
  </g>
  <text x="96" y="128" text-anchor="middle" font-family="Outfit,Segoe UI,sans-serif" font-size="22" font-weight="700"
        fill="url(#name)" letter-spacing="1">IRIS</text>
"""
        + COMMON_TAIL
        + "</svg>\n"
    )


def stale_svg() -> str:
    return (
        COMMON_HEAD
        + CRYSTAL
        + """
  <g filter="url(#glow)">
    <circle cx="96" cy="86" r="26" fill="none" stroke="url(#name)" stroke-width="2.2"/>
    <circle cx="96" cy="86" r="2.2" fill="#c9c2ff"/>
    <path d="M96 86 L96 66" stroke="#e2deff" stroke-width="2.4" stroke-linecap="round"/>
    <path d="M96 86 L112 94" stroke="#7ae8ff" stroke-width="2" stroke-linecap="round" opacity="0.85"/>
    <path d="M96 86 L78 98" stroke="#9b5cff" stroke-width="1.6" stroke-linecap="round" opacity="0.45" stroke-dasharray="3 2"/>
    <path d="M118 72 L126 64 M126 72 L118 64" stroke="#ff8fab" stroke-width="1.8" stroke-linecap="round"/>
    <text x="124" y="68" font-family="Outfit,sans-serif" font-size="8" fill="#ff8fab" font-weight="700">lag</text>
  </g>
  <text x="96" y="128" text-anchor="middle" font-family="Outfit,Segoe UI,sans-serif" font-size="20" font-weight="700"
        fill="url(#name)" letter-spacing="0.5">STALE</text>
"""
        + COMMON_TAIL
        + "</svg>\n"
    )


def glance_svg() -> str:
    return (
        COMMON_HEAD
        + CRYSTAL
        + """
  <g filter="url(#glow)">
    <rect x="68" y="72" width="56" height="34" rx="6" fill="#0d0b1f" stroke="url(#name)" stroke-width="2"/>
    <rect x="74" y="80" width="10" height="18" rx="2" fill="#7be3b0" opacity="0.85"/>
    <rect x="88" y="86" width="10" height="12" rx="2" fill="#c9c2ff" opacity="0.55"/>
    <rect x="102" y="92" width="10" height="6" rx="2" fill="#ff8fab" opacity="0.9"/>
    <path d="M68 92 H124" stroke="#7ae8ff" stroke-width="1.6" opacity="0.9"/>
    <circle cx="124" cy="92" r="3" fill="#7ae8ff"/>
    <path d="M132 78 C126 84 126 100 132 106" fill="none" stroke="#c9c2ff" stroke-width="1.4" opacity="0.7"/>
    <ellipse cx="132" cy="92" rx="5" ry="8" fill="none" stroke="#9b5cff" stroke-width="1.2"/>
  </g>
  <text x="96" y="128" text-anchor="middle" font-family="Outfit,Segoe UI,sans-serif" font-size="19" font-weight="700"
        fill="url(#name)" letter-spacing="0.5">GLANCE</text>
"""
        + COMMON_TAIL
        + "</svg>\n"
    )


def write_webp(svg_path: str, webp_path: str) -> None:
    png = cairosvg.svg2png(url=svg_path, output_width=192, output_height=192)
    img = Image.open(io.BytesIO(png)).convert("RGB")
    img.save(webp_path, "WEBP", quality=86, method=6)


def main() -> None:
    os.makedirs(ASSETS, exist_ok=True)
    specs = (
        ("iris-card.svg", "iris-card-192.webp", iris_svg),
        ("stale-card.svg", "stale-card-192.webp", stale_svg),
        ("glance-card.svg", "glance-card-192.webp", glance_svg),
    )
    for svg_name, webp_name, builder in specs:
        svg_path = os.path.join(ASSETS, svg_name)
        webp_path = os.path.join(ASSETS, webp_name)
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(builder())
        write_webp(svg_path, webp_path)
        print("wrote", svg_name, "and", webp_name)


if __name__ == "__main__":
    main()
