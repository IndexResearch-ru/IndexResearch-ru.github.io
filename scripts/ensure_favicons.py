#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {"templates", ".git", ".github"}

FAVICON_BLOCK = """  <link rel="icon" type="image/png" sizes="192x192" href="/android-chrome-192x192.png">
  <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">"""

ICON_LINK_RE = re.compile(
    r'^\s*<link\b(?=[^>]*\brel=["\'](?:icon|shortcut icon|apple-touch-icon)["\'])[^>]*>\s*\n?',
    re.I | re.M,
)

def public_html_paths():
    return sorted(
        path for path in ROOT.rglob("*.html")
        if not any(part in EXCLUDED_DIRS for part in path.relative_to(ROOT).parts)
    )

def normalize(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    original = text

    text = ICON_LINK_RE.sub("", text)

    stylesheet = re.search(r'^[ \t]*<link\b[^>]*\brel=["\']stylesheet["\'][^>]*>', text, re.I | re.M)
    if stylesheet:
        text = text[:stylesheet.start()] + FAVICON_BLOCK + "\n" + text[stylesheet.start():]
    elif "</head>" in text:
        text = text.replace("</head>", FAVICON_BLOCK + "\n</head>", 1)
    else:
        raise RuntimeError(f"{path.relative_to(ROOT)}: missing </head> and stylesheet marker")

    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False

def main() -> None:
    changed = [path.relative_to(ROOT).as_posix() for path in public_html_paths() if normalize(path)]
    print(f"Favicon metadata normalized on {len(public_html_paths())} public HTML pages.")
    print("Updated:", ", ".join(changed) if changed else "none")

if __name__ == "__main__":
    main()
