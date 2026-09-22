#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REPLACEMENTS = (
    ("https://indexresearch.ru/en/ratings.html", "https://indexresearch.ru/en/ratings/"),
    ("https://indexresearch.ru/cn/ratings.html", "https://indexresearch.ru/cn/ratings/"),
    ("https://indexresearch.ru/ratings.html", "https://indexresearch.ru/ratings/"),
    ("/en/ratings.html", "/en/ratings/"),
    ("/cn/ratings.html", "/cn/ratings/"),
    ("/ratings.html", "/ratings/"),
)


def main() -> None:
    changed = []
    for path in sorted(ROOT.rglob("*.html")):
        if any(part in {"templates", ".git", ".github"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        original = text
        for old, new in REPLACEMENTS:
            text = text.replace(old, new)
        if text != original:
            path.write_text(text, encoding="utf-8")
            changed.append(path.relative_to(ROOT).as_posix())

    print("Canonical catalog URL normalized to /ratings/ in public HTML.")
    print("Updated:", ", ".join(changed) if changed else "none")


if __name__ == "__main__":
    main()
