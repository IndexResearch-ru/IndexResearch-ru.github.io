#!/usr/bin/env python3
"""INDEX-T054: independent HTTP destination audit of all six publication surfaces.
Records source URLs separately from editorial links; 403/429/timeouts are uncertain.
"""
from __future__ import annotations
import csv
import html.parser
import io
import json
import pathlib
import re
import time
import urllib.error
import urllib.parse
import urllib.request

SLUG = "chestny-znak-kiz-fulfillment-moscow-2026"
ROOT = "https://indexresearch.ru/"
GH = "https://github.com/IndexResearch-ru/"
RAW = "https://raw.githubusercontent.com/IndexResearch-ru/"
OUT = pathlib.Path("qa-screenshots-index-t054")
OUT.mkdir(exist_ok=True)

site_urls = [ROOT + ("" if lang == "ru" else lang + "/") + SLUG + ".html"
             for lang in ("ru", "en", "cn")]
repo_urls = [GH + SLUG + ("" if lang == "ru" else "-" + lang)
             for lang in ("ru", "en", "cn")]
readme_urls = [RAW + SLUG + ("" if lang == "ru" else "-" + lang) + "/main/README.md"
               for lang in ("ru", "en", "cn")]
source_csv_url = RAW + SLUG + "/main/SOURCE_REGISTER.csv"

class MainLinks(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.urls = set()
    def handle_starttag(self, tag, attrs):
        if tag == "main":
            self.depth += 1
        if self.depth and tag in ("a", "img"):
            vals = dict(attrs)
            val = vals.get("href") if tag == "a" else vals.get("src")
            if val:
                self.urls.add(val)
    def handle_endtag(self, tag):
        if tag == "main" and self.depth:
            self.depth -= 1

def request(url, max_bytes=1700000):
    req = urllib.request.Request(url, headers={
        "User-Agent":"Mozilla/5.0 (compatible; IndexResearch-Release-QA/1.0)",
        "Accept":"text/html,text/csv,text/plain,image/svg+xml,*/*"
    })
    with urllib.request.urlopen(req, timeout=28) as response:
        return response.status, response.geturl(), response.read(max_bytes)

targets = {}
def add(url, kind):
    if not url or url.startswith(("mailto:", "javascript:", "data:", "#")):
        return
    url = urllib.parse.urldefrag(url).url
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in ("http", "https"):
        return
    targets.setdefault(url, set()).add(kind)

for url in site_urls + repo_urls:
    add(url, "critical_surface")
for url in readme_urls:
    add(url, "critical_readme")
add(source_csv_url, "critical_source_register")

collection_errors = []
for lang, site_url in zip(("ru","en","cn"), site_urls):
    try:
        status, final, body = request(site_url)
        parser = MainLinks()
        parser.feed(body.decode("utf-8", errors="replace"))
        for link in parser.urls:
            add(urllib.parse.urljoin(site_url, link), "editorial_site_" + lang)
    except Exception as exc:
        collection_errors.append("SITE_EXTRACT_" + lang + ": " + str(exc)[:180])

markdown_re = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
html_url_re = re.compile(r"""(?:href|src)=["']([^"']+)["']""")
for lang, url in zip(("ru", "en", "cn"), readme_urls):
    try:
        _, _, body = request(url)
        md = body.decode("utf-8", errors="replace")
        for link in markdown_re.findall(md) + html_url_re.findall(md):
            link = link.replace("&amp;", "&")
            if not link.startswith(("http://","https://")):
                link = urllib.parse.urljoin(repo_urls[("ru","en","cn").index(lang)] + "/blob/main/README.md", link)
            add(link, "editorial_readme_" + lang)
    except Exception as exc:
        collection_errors.append("README_EXTRACT_" + lang + ": " + str(exc)[:180])

source_count=0
try:
    _, _, body = request(source_csv_url)
    sources = list(csv.DictReader(io.StringIO(body.decode("utf-8-sig"))))
    source_count = len(sources)
    if source_count != 31:
        collection_errors.append(f"EXPECTED_31_SOURCES_GOT_{source_count}")
    for row in sources:
        add(row["url"], "evidence_primary_source")
except Exception as exc:
    collection_errors.append("SOURCE_CSV_EXTRACT: "+str(exc)[:180])

results = []
for idx, (url, kinds) in enumerate(sorted(targets.items()), 1):
    status, end, err = None, None, ""
    try:
        status, end, _ = request(url, max_bytes=2048)
    except urllib.error.HTTPError as exc:
        status, end, err = exc.code, exc.geturl(), str(exc)[:160]
    except Exception as exc:
        err = str(exc)[:220]
    outcome = ("confirmed" if status and 200 <= status < 400 else
               "unavailable" if status in (404, 410) else "uncertain")
    item={"url":url,"end_url":end,"http_status":status,"outcome":outcome,
          "kinds":sorted(kinds),"error":err}
    results.append(item)
    print("LINK_RESULT "+json.dumps(item, ensure_ascii=False), flush=True)
    time.sleep(0.06)

is_critical=lambda x:any(k.startswith("critical_") or k.startswith("editorial_site_") or k.startswith("editorial_readme_") for k in x["kinds"])
critical_unavailable=[x["url"] for x in results if x["outcome"]=="unavailable" and is_critical(x)]
critical_uncertain=[x["url"] for x in results if x["outcome"]=="uncertain" and any(k.startswith("critical_") for k in x["kinds"])]
summary={
 "study":"INDEX-T054","source_count":source_count,"total":len(results),
 "confirmed":sum(x["outcome"]=="confirmed" for x in results),
 "unavailable":sum(x["outcome"]=="unavailable" for x in results),
 "uncertain":sum(x["outcome"]=="uncertain" for x in results),
 "critical_unavailable":critical_unavailable,
 "critical_uncertain":critical_uncertain,
 "collection_errors":collection_errors
}
(OUT / "qa-link-report.json").write_text(json.dumps({"summary":summary, "results":results}, ensure_ascii=False, indent=2), encoding="utf-8")
print("LINK_TOTAL "+json.dumps(summary,ensure_ascii=False),flush=True)
if collection_errors or critical_unavailable or critical_uncertain:
    raise SystemExit("Critical publication links or collection checks failed")
