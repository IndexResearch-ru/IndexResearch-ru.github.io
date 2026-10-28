#!/usr/bin/env python3
"""Public live QA for the six Amazon editorial research surfaces. No writes."""
import json, re
from pathlib import Path
from collections import Counter
from urllib.parse import urldefrag, urlparse
from playwright.sync_api import sync_playwright

SLUG="amazon-private-tours-brazil-dmc-2026"
BASE="https://indexresearch.ru"
GH="https://github.com/IndexResearch-ru/"
SITES={"ru":f"{BASE}/{SLUG}.html","en":f"{BASE}/en/{SLUG}.html","cn":f"{BASE}/cn/{SLUG}.html"}
READMES={k:GH+SLUG+("" if k=="ru" else "-"+k) for k in SITES}
OUT=Path("qa_artifacts/amazon");OUT.mkdir(parents=True,exist_ok=True)
results=[];links=[];errors=[];warnings=[];statuses={}
def check(cond,reason):
 if not cond: errors.append(reason)
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
 for kind,urls in (("site",SITES),("github",READMES)):
  for lang,url in urls.items():
   for width in ([360,390,412,1440] if kind=="site" else [1440]):
    page=browser.new_page(viewport={"width":width,"height":900},device_scale_factor=1)
    label=f"{kind}/{lang}/{width}"
    try:
     response=page.goto(url,wait_until="domcontentloaded",timeout=60000)
     status=response.status if response else None
     check(status==200,f"{label} HTTP {status}")
     if status!=200: continue
     root=page.locator("main") if kind=="site" else page.locator("#readme .markdown-body")
     if kind=="github" and root.count()==0: root=page.locator("article.markdown-body")
     check(root.count()>0,f"{label}: no content root")
     content=root.inner_text() if root.count() else ""
     check("Ada Tours" in content,f"{label}: Ada Tours missing")
     check("15" in content,f"{label}: participant count missing")
     check("28" in content,f"{label}: source count missing")
     if kind=="site":
      check(page.locator("main h1").count()==1,f"{label}: H1 count")
      check(page.locator("main details").count()==8,f"{label}: FAQ count")
      check(page.locator("main article").count()==15,f"{label}: participant profiles count")
      check(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 2"),f"{label}: horizontal page overflow")
      page.screenshot(path=str(OUT/f"{lang}-{width}.png"),full_page=False)
     if width==1440 and root.count():
      anchors=root.locator("a[href]")
      for i in range(anchors.count()):
       info=anchors.nth(i).evaluate("""a=>({raw:a.getAttribute('href'),abs:a.href,
       text:(a.textContent||a.querySelector('img')?.getAttribute('alt')||'').trim(),
       inCrumbs:!!a.closest('nav.breadcrumbs'),
       autoAnchor:!!a.classList.contains('anchor')})""")
       raw=info["raw"] or "";target=info["abs"] or ""
       if not target.startswith(("http://","https://")) or raw.startswith(("#","mailto:","tel:")) or info["inCrumbs"] or info["autoAnchor"]:continue
       links.append({"surface":kind+"/"+lang,"seq":len([x for x in links if x["surface"]==kind+"/"+lang])+1,
                     "anchor":info["text"][:250],"href_as_rendered":raw,"target":urldefrag(target).url})
     results.append({"surface":label,"status":status,"title":page.title(),"content_chars":len(content)})
    except Exception as e:errors.append(f"{label}: {type(e).__name__}: {str(e)[:180]}")
    finally:page.close()
 context=browser.new_context()
 distinct=list(dict.fromkeys(x["target"] for x in links))
 for target in distinct:
  try:
   response=context.request.get(target,timeout=15000,max_redirects=7,fail_on_status_code=False)
   code=response.status;final=response.url
   state="OK" if code<400 else ("ACCESS_LIMIT" if code in (401,403,406,408,429,451,503) else "BROKEN")
   statuses[target]={"status":code,"final":final,"state":state}
   if state=="BROKEN" and (urlparse(target).hostname or "") in ("indexresearch.ru","github.com","raw.githubusercontent.com"):errors.append(f"Broken internal link {code}: {target}")
   elif state!="OK":warnings.append(f"{state} {code}: {target}")
  except Exception as e:
   statuses[target]={"status":None,"final":None,"state":"UNKNOWN_TRANSPORT"}
   warnings.append(f"Transport unknown: {target} {type(e).__name__}")
 for row in links:row["verification"]=statuses[row["target"]]
 context.close();browser.close()
report={"surfaces":results,"occurrence_counts":dict(Counter(x["surface"] for x in links)),"unique_targets":len(distinct),"status_counts":dict(Counter(v["state"] for v in statuses.values())),"links":links,"errors":errors,"warnings":warnings}
(OUT/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("AMAZON_LIVE_QA="+json.dumps({k:report[k] for k in ("occurrence_counts","unique_targets","status_counts","errors","warnings")},ensure_ascii=False))
if errors:raise SystemExit(1)
