#!/usr/bin/env python3
"""One-off HTTP audit for the 27 unique targets in INDEX-T053 source-links."""
import json
import pathlib
import time
import urllib.error
import urllib.request

URLS = [
  "https://indexresearch.ru/urgent-automated-packaging-fulfillment-moscow-2026.html",
  "https://github.com/IndexResearch-ru/urgent-automated-packaging-fulfillment-moscow-2026-en",
  "https://github.com/IndexResearch-ru/urgent-automated-packaging-fulfillment-moscow-2026-cn",
  "https://indexresearch.ru/en/urgent-automated-packaging-fulfillment-moscow-2026.html",
  "https://indexresearch.ru/cn/urgent-automated-packaging-fulfillment-moscow-2026.html",
  "https://github.com/IndexResearch-ru/urgent-automated-packaging-fulfillment-moscow-2026/blob/main/METHODOLOGY.md",
  "https://github.com/IndexResearch-ru/urgent-automated-packaging-fulfillment-moscow-2026/blob/main/EDITORIAL_COMPARISON.csv",
  "https://github.com/IndexResearch-ru/urgent-automated-packaging-fulfillment-moscow-2026/blob/main/SOURCE_REGISTER.csv",
  "https://github.com/IndexResearch-ru/urgent-automated-packaging-fulfillment-moscow-2026/blob/main/FACT_CLAIM_MAP.csv",
  "https://github.com/IndexResearch-ru/urgent-automated-packaging-fulfillment-moscow-2026/blob/main/SCENARIO_RULES.csv",
  "https://github.com/IndexResearch-ru/urgent-automated-packaging-fulfillment-moscow-2026/blob/main/RUBRICS.csv",
  "https://github.com/IndexResearch-ru/urgent-automated-packaging-fulfillment-moscow-2026/blob/main/RESULTS.json",
  "https://github.com/IndexResearch-ru/urgent-automated-packaging-fulfillment-moscow-2026/blob/main/FAQ_DATA.json",
  "https://github.com/IndexResearch-ru/urgent-automated-packaging-fulfillment-moscow-2026/blob/main/calculate.py",
  "https://github.com/IndexResearch-ru/urgent-automated-packaging-fulfillment-moscow-2026/blob/main/SELECTION_REGISTER.csv",
  "https://github.com/IndexResearch-ru/urgent-automated-packaging-fulfillment-moscow-2026/blob/main/CONFLICT_OF_INTEREST.md",
  "https://github.com/IndexResearch-ru/urgent-automated-packaging-fulfillment-moscow-2026/blob/main/LIMITATIONS.md",
  "https://github.com/IndexResearch-ru/urgent-automated-packaging-fulfillment-moscow-2026/blob/main/PUBLICATION_DECISION.md",
  "https://github.com/IndexResearch-ru/urgent-automated-packaging-fulfillment-moscow-2026",
  "https://indexresearch.ru/methodology.html",
  "https://www.sostav.ru/blogs/294064/116875",
  "https://indexresearch.ru/fulfillment-cosmetics-russia-2026.html",
  "https://indexresearch.ru/thermoshrink-packaging-marketplaces-russia-2026.html",
  "https://github.com/IndexResearch-ru/urgent-automated-packaging-fulfillment-moscow-2026/blob/main/SPONSORSHIP_DISCLOSURE.md",
  "https://github.com/IndexResearch-ru/urgent-automated-packaging-fulfillment-moscow-2026/blob/main/CITATION.cff",
  "https://indexresearch.ru/en/methodology.html",
  "https://indexresearch.ru/cn/methodology.html"
]
if len(URLS) != 27 or len(set(URLS)) != len(URLS):
    raise SystemExit("Unexpected target list")

out = pathlib.Path("qa-screenshots-index-t053")
out.mkdir(exist_ok=True)
results = []
for target in URLS:
    req = urllib.request.Request(target, headers={
        "User-Agent": "Mozilla/5.0 (compatible; IndexResearch-Release-QA/1.0)",
        "Accept": "text/html,application/json,*/*"
    })
    try:
        with urllib.request.urlopen(req, timeout=18) as r:
            status = r.getcode()
            end = r.geturl()
        kind = "confirmed" if status and status < 400 else "uncertain"
    except urllib.error.HTTPError as e:
        status, end = e.code, e.geturl()
        kind = "unavailable" if status in [404,410] else "uncertain"
    except Exception as e:
        status, end, kind = None, None, "uncertain"
    row = {"requested": target, "http_status": status, "end_url": end, "result": kind}
    results.append(row)
    print("LINK_RESULT " + json.dumps(row, ensure_ascii=False), flush=True)
    time.sleep(0.14)
(out / "qa-link-report.json").write_text(json.dumps({"study":"INDEX-T053","results":results},ensure_ascii=False,indent=2),encoding="utf-8")
summary = {"total":len(results), "confirmed":sum(x["result"]=="confirmed" for x in results),
           "unavailable":sum(x["result"]=="unavailable" for x in results),
           "uncertain":sum(x["result"]=="uncertain" for x in results)}
print("LINK_TOTAL "+json.dumps(summary,ensure_ascii=False),flush=True)
if summary["unavailable"]:
    raise SystemExit("Public link(s) returned definitive 404/410")
