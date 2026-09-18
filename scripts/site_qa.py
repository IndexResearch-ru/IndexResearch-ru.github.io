#!/usr/bin/env python3
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://indexresearch.ru"
errors = []

html_paths = sorted(ROOT.glob("*.html"))
if not html_paths:
    errors.append("No root HTML pages found.")

sitemap_path = ROOT / "sitemap.xml"
sitemap_urls = set()
if sitemap_path.exists():
    try:
        tree = ET.parse(sitemap_path)
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        sitemap_urls = {n.text.strip() for n in tree.findall(".//s:loc", ns) if n.text}
    except Exception as exc:
        errors.append(f"sitemap.xml is invalid XML: {exc}")
else:
    errors.append("sitemap.xml is missing.")

ratings = (ROOT / "ratings.html").read_text(encoding="utf-8") if (ROOT / "ratings.html").exists() else ""
non_research = {"index.html", "ratings.html", "methodology.html"}

for path in html_paths:
    text = path.read_text(encoding="utf-8")
    name = path.name
    expected_url = f"{BASE}/" if name == "index.html" else f"{BASE}/{name}"

    if len(re.findall(r'<script src="/assets/analytics\.js" defer></script>', text)) != 1:
        errors.append(f"{name}: must contain exactly one shared analytics.js include.")
    if "mc.yandex.ru/metrika/tag.js" in text:
        errors.append(f"{name}: contains legacy inline Yandex Metrika loader.")
    if text.count("mc.yandex.ru/watch/112773213") != 1:
        errors.append(f"{name}: must contain exactly one Yandex noscript fallback.")

    if not re.search(r"<title>[^<]{3,}</title>", text, re.I):
        errors.append(f"{name}: missing/non-empty <title>.")
    if not re.search(r'<meta\s+name="description"\s+content="[^"]{20,}"', text, re.I):
        errors.append(f"{name}: missing meta description.")
    canonical = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', text, re.I)
    if not canonical:
        errors.append(f"{name}: missing canonical.")
    elif canonical.group(1) != expected_url:
        errors.append(f"{name}: canonical is {canonical.group(1)!r}, expected {expected_url!r}.")
    if len(re.findall(r"<h1(?:\s[^>]*)?>", text, re.I)) != 1:
        errors.append(f"{name}: must contain exactly one H1.")
    if 'application/ld+json' not in text:
        errors.append(f"{name}: missing Schema.org JSON-LD.")

    robots = re.search(r'<meta\s+name="robots"\s+content="([^"]+)"', text, re.I)
    indexed = not (robots and "noindex" in robots.group(1).lower())
    if indexed and expected_url not in sitemap_urls:
        errors.append(f"{name}: missing from sitemap.xml.")

    if name not in non_research:
        if f'href="/{name}"' not in ratings and f'href="{name}"' not in ratings:
            errors.append(f"{name}: research page is not linked from ratings.html.")

if not (ROOT / "assets" / "analytics.js").exists():
    errors.append("assets/analytics.js is missing.")

robots_path = ROOT / "robots.txt"
if not robots_path.exists():
    errors.append("robots.txt is missing.")
else:
    robots_text = robots_path.read_text(encoding="utf-8")
    if "Sitemap: https://indexresearch.ru/sitemap.xml" not in robots_text:
        errors.append("robots.txt does not declare the canonical sitemap URL.")

if errors:
    print("SITE QA FAILED")
    for err in errors:
        print(f"- {err}")
    sys.exit(1)

print(f"SITE QA PASSED: {len(html_paths)} HTML pages checked.")
