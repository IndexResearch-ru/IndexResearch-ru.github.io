#!/usr/bin/env python3
from pathlib import Path
import hashlib
import re

ROOT = Path(__file__).resolve().parents[1]
HEADER_PATH = ROOT / "templates" / "partials" / "site-header.html"
FOOTER_PATH = ROOT / "templates" / "partials" / "site-footer.html"
STYLE_PATH = ROOT / "assets" / "style.css"

HEADER_START = "<!-- SITE_HEADER_START -->"
HEADER_END = "<!-- SITE_HEADER_END -->"
FOOTER_START = "<!-- SITE_FOOTER_START -->"
FOOTER_END = "<!-- SITE_FOOTER_END -->"

HEADER_BLOCK_RE = re.compile(
    rf"{re.escape(HEADER_START)}[\s\S]*?{re.escape(HEADER_END)}"
)
FOOTER_BLOCK_RE = re.compile(
    rf"{re.escape(FOOTER_START)}[\\s\\S]*?{re.escape(FOOTER_END)}"
)
LEGACY_HEADER_RE = re.compile(r'<header class="top">[\\s\\S]*?</header>', re.I)
LEGACY_FOOTER_RE = re.compile(r'<footer>[\\s\\S]*?</footer>', re.I)
STYLE_RE = re.compile(r'assets/style\\.css(?:\\?v=[^"\\\']*)?')

header = HEADER_PATH.read_text(encoding="utf-8").strip()
footer = FOOTER_PATH.read_text(encoding="utf-8").strip()
style_version = hashlib.sha256(STYLE_PATH.read_bytes()).hexdigest()[:12]

header_block = f"{HEADER_START}\n{header}\n{HEADER_END}"
footer_block = f"{FOOTER_START}\n{footer}\n{FOOTER_END}"

changed = []

for path in sorted(ROOT.glob("*.html")):
    text = path.read_text(encoding="utf-8")
    original = text

    if "{{SITE_HEADER}}" in text:
        text = text.replace("{{SITE_HEADER}}", header_block, 1)
    elif HEADER_START in text or HEADER_END in text:
        text, count = HEADER_BLOCK_RE.subn(header_block, text, count=1)
        if count != 1:
            raise SystemExit(f"{path.name}: invalid shared header markers")
    else:
        text, count = LEGACY_HEADER_RE.subn(header_block, text, count=1)
        if count != 1:
            raise SystemExit(f"{path.name}: canonical header not found")

    if "{{SITE_FOOTER}}" in text:
        text = text.replace("{{SITE_FOOTER}}", footer_block, 1)
    elif FOOTER_START in text or FOOTER_END in text:
        text, count = FOOTER_BLOCK_RE.subn(footer_block, text, count=1)
        if count != 1:
            raise SystemExit(f"{path.name}: invalid shared footer markers")
    else:
        text, count = LEGACY_FOOTER_RE.subn(footer_block, text, count=1)
        if count != 1:
            raise SystemExit(f"{path.name}: canonical footer not found")

    if text.count(HEADER_START) != 1 or text.count(HEADER_END) != 1:
        raise SystemExit(f"{path.name}: shared header must appear exactly once")
    if text.count(FOOTER_START) != 1 or text.count(FOOTER_END) != 1:
        raise SystemExit(f"{path.name}: shared footer must appear exactly once")

    text = STYLE_RE.sub(f"assets/style.css?v={style_version}", text)

    if text != original:
        path.write_text(text, encoding="utf-8")
        changed.append(path.name)

print(f"Shared site chrome synchronized; CSS version {style_version}.")
if changed:
    print("Updated:", ", ".join(changed))
else:
    print("No HTML changes required.")
