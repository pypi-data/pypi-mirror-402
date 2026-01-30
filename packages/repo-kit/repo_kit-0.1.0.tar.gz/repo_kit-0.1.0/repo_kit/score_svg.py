from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BadgeSpec:
    label: str
    value: str


def _esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def make_badge_svg(spec: BadgeSpec) -> str:
    """A minimal, dependency-free SVG badge.

    We intentionally avoid color choices; default is neutral gray.
    """
    label = _esc(spec.label)
    value = _esc(spec.value)

    # approximate text widths (monospace-ish, good enough for badges)
    # 7px per char + padding
    label_w = max(40, 7 * len(label) + 20)
    value_w = max(40, 7 * len(value) + 20)
    total_w = label_w + value_w

    return f"""<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{total_w}\" height=\"20\" role=\"img\" aria-label=\"{label}: {value}\">
  <linearGradient id=\"s\" x2=\"0\" y2=\"100%\">
    <stop offset=\"0\" stop-color=\"#bbb\" stop-opacity=\".1\"/>
    <stop offset=\"1\" stop-opacity=\".1\"/>
  </linearGradient>
  <clipPath id=\"r\">
    <rect width=\"{total_w}\" height=\"20\" rx=\"3\" fill=\"#fff\"/>
  </clipPath>
  <g clip-path=\"url(#r)\">
    <rect width=\"{label_w}\" height=\"20\" fill=\"#555\"/>
    <rect x=\"{label_w}\" width=\"{value_w}\" height=\"20\" fill=\"#777\"/>
    <rect width=\"{total_w}\" height=\"20\" fill=\"url(#s)\"/>
  </g>
  <g fill=\"#fff\" text-anchor=\"middle\" font-family=\"Verdana,Geneva,DejaVu Sans,sans-serif\" font-size=\"11\">
    <text x=\"{label_w/2:.1f}\" y=\"14\">{label}</text>
    <text x=\"{label_w + value_w/2:.1f}\" y=\"14\">{value}</text>
  </g>
</svg>"""
