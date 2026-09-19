#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CSS_VERSION = "20260919-1340"
LOCATION = '<span class="footer-location">Москва, Россия</span>'

FOOTER_RE = re.compile(
    r'(<footer>\s*<div class="wrap foot">\s*<span>IndexResearch</span>)',
    re.MULTILINE,
)
STYLE_RE = re.compile(
    r'assets/style\.css(?:\?v=[^"\']*)?'
)

changed = []

for path in sorted(ROOT.glob("*.html")):
    text = path.read_text(encoding="utf-8")
    original = text

    if 'class="footer-location"' not in text:
        text, count = FOOTER_RE.subn(r'\1' + LOCATION, text, count=1)
        if count != 1:
            raise SystemExit(f"{path.name}: canonical footer not found")

    if text.count('class="footer-location"') != 1:
        raise SystemExit(f"{path.name}: footer location must appear exactly once")

    text = STYLE_RE.sub(f"assets/style.css?v={CSS_VERSION}", text)

    if text != original:
        path.write_text(text, encoding="utf-8")
        changed.append(path.name)

if changed:
    print("Footer/location normalized:", ", ".join(changed))
else:
    print("Footer/location already normalized on all HTML pages.")
