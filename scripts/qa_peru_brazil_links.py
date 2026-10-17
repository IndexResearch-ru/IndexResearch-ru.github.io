#!/usr/bin/env python3
"""Public outgoing author-link audit for the 6 Peru–Brazil research surfaces.
Actual hrefs are gathered from rendered Chromium pages, with HTTP redirects
resolved once per distinct target URL. Results stay separate from editorial data.
"""
from collections import Counter
import json
from pathlib import Path
from urllib.parse import urldefrag, urlparse
from playwright.sync_api import sync_playwright

slug="peru-brazil-private-tours-russian-agencies-2026"
base="https://indexresearch.ru"
repo="https://github.com/IndexResearch-ru/"+slug
sites={"SITE":f"{base}/{slug}.html",
       "SITE-EN":f"{base}/en/{slug}.html",
       "SITE-CN":f"{base}/cn/{slug}.html"}
github={"GITHUB":repo,"GITHUB-EN":repo+"-en","GITHUB-CN":repo+"-cn"}
all_surfaces={**sites,**github}
out=Path("qa_artifacts/peru_brazil")
out.mkdir(parents=True,exist_ok=True)
rows=[]
statuses={}
errors=[]
warn=[]
internal_hosts={"indexresearch.ru","www.indexresearch.ru","github.com","raw.githubusercontent.com"}
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
 context=browser.new_context(viewport={"width":1440,"height":900})
 for name,url in all_surfaces.items():
  page=context.new_page()
  try:
   r=page.goto(url,wait_until="domcontentloaded",timeout=60000)
   if not r or r.status!=200:
    errors.append(f"{name}: source HTTP {r.status if r else 'none'}")
    continue
   if name.startswith("SITE"):
    root=page.locator("main")
    nodes=root.locator("a[href]")
   else:
    root=page.locator("#readme .markdown-body")
    if root.count()==0:root=page.locator("article.markdown-body")
    nodes=root.locator("a[href]")
   for k in range(nodes.count()):
    a=nodes.nth(k)
    info=a.evaluate("""a=>({raw:a.getAttribute('href'),abs:a.href,
       text:(a.textContent||a.querySelector('img')?.getAttribute('alt')||'').trim(),
       inCrumbs:!!a.closest('nav.breadcrumbs'),
       isHeading:!!a.closest('h1,h2,h3,h4,h5,h6')&&!!a.classList.contains('anchor'),
       isAutoImageZoom:!!a.querySelector('img') && /\\/assets\\/.*\\.(?:svg|png|jpg|webp)(?:[?#].*)?$/i.test(a.getAttribute('href')||'')})""")
    target=info["abs"] or ""
    if not target.startswith(("http://","https://")) or info["raw"].startswith(("#","mailto:","tel:")) or info["inCrumbs"] or info["isHeading"] or info["isAutoImageZoom"]:
     continue
    normalized=urldefrag(target).url
    rows.append({"surface":name,"seq":k+1,"text":info["text"][:300],
                 "raw_href":info["raw"],"target":normalized})
  except Exception as exc:
   errors.append(f"{name}: DOM link extraction: {type(exc).__name__} {str(exc)[:170]}")
  finally:
   page.close()
 # Use a single APIRequestContext to follow actual redirect responses.
 req=context.request
 distinct=list(dict.fromkeys(x["target"] for x in rows))
 for target in distinct:
  host=urlparse(target).hostname or ""
  if host not in internal_hosts and host not in ("adatours.ru","www.adatours.ru"):
   # External source websites may block automated requests. Still attempt to verify.
   pass
  try:
   resp=req.get(target,timeout=15000,fail_on_status_code=False,max_redirects=7)
   status=resp.status
   final=resp.url
   outcome="OK" if status<400 else ("UNKNOWN_ACCESS" if status in (401,403,406,408,429,451,503) else "BROKEN")
   statuses[target]={"status":status,"final_url":final,"result":outcome}
   if outcome=="UNKNOWN_ACCESS" and status==429 and target.startswith("https://github.com/") and "/blob/main/" in target:
    # GitHub occasionally throttles dozens of automated blob-page GETs.
    # Verify the same Git blob through its public raw content, but do not call
    # this a verification of the GitHub HTML redirect.
    raw=target.replace("https://github.com/","https://raw.githubusercontent.com/",1).replace("/blob/main/","/main/",1)
    try:
     fallback=req.get(raw,timeout=15000,max_redirects=7,fail_on_status_code=False)
     if fallback.status==200:
      outcome="OK_RAW_FALLBACK"
      statuses[target]={"status":429,"final_url":None,"result":outcome,
                         "fallback_http":200,"raw_file":raw}
    except Exception:
     pass
   if outcome=="BROKEN":
    if host in internal_hosts:errors.append(f"Internal link failed: {status} {target} -> {final}")
    else:warn.append(f"External link returned {status}: {target}")
   elif outcome=="UNKNOWN_ACCESS":
    warn.append(f"Access restriction {status}: {target}")
   elif outcome=="OK_RAW_FALLBACK":
    warn.append(f"GitHub page rate-limited but raw Git blob verified: {target}")
  except Exception as exc:
   statuses[target]={"status":None,"final_url":None,"result":"UNKNOWN_TRANSPORT",
                     "error":str(exc)[:180]}
   warn.append(f"Request inconclusive for {target}: {type(exc).__name__}")
 for row in rows:
  row["result"]=statuses[row["target"]]
 browser.close()
counts=Counter(x["surface"] for x in rows)
kinds=Counter(v["result"] for v in statuses.values())
audit={"surfaces":all_surfaces,"occurrence_counts":dict(counts),
       "unique_targets":len(distinct),"result_counts":dict(kinds),
       "errors":errors,"warnings":warn,"links":rows}
(out/"link_audit.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding="utf-8")
print("LINK_QA_SUMMARY="+json.dumps(
 {"occurrences":len(rows),"per_surface":counts,"unique_targets":len(distinct),
  "results":kinds,"errors":errors,"warnings_count":len(warn),
  "warnings":warn[:30]},ensure_ascii=False))
if errors:raise SystemExit(1)
