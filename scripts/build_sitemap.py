#!/usr/bin/env python3
from pathlib import Path
from datetime import date
import subprocess
import re
import xml.sax.saxutils as xmlutils

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://indexresearch.ru"

def lastmod(path: Path) -> str:
    try:
        value = subprocess.check_output(
            ["git", "log", "-1", "--format=%cs", "--", path.name],
            cwd=ROOT,
            text=True,
        ).strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return value
    except Exception:
        pass
    return date.today().isoformat()

pages = []
for path in sorted(ROOT.glob("*.html")):
    text = path.read_text(encoding="utf-8")
    robots = re.search(r'<meta\s+name="robots"\s+content="([^"]+)"', text, re.I)
    if robots and "noindex" in robots.group(1).lower():
        continue
    loc = f"{BASE}/" if path.name == "index.html" else f"{BASE}/{path.name}"
    pages.append((path.name, loc, lastmod(path)))

priority = {"index.html": 0, "ratings.html": 1, "methodology.html": 2}
pages.sort(key=lambda x: (priority.get(x[0], 10), x[0]))

lines = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for _, loc, modified in pages:
    lines.append(f'  <url><loc>{xmlutils.escape(loc)}</loc><lastmod>{modified}</lastmod></url>')
lines.append('</urlset>')
content = "\n".join(lines) + "\n"

target = ROOT / "sitemap.xml"
if not target.exists() or target.read_text(encoding="utf-8") != content:
    target.write_text(content, encoding="utf-8")
    print(f"Updated sitemap.xml with {len(pages)} URLs.")
else:
    print(f"sitemap.xml already current ({len(pages)} URLs).")
