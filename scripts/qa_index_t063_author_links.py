#!/usr/bin/env python3
"""Check remaining unique author-link HTTP destinations for cinema research."""
import concurrent.futures, json, pathlib, urllib.request, urllib.error, sys, datetime
TARGETS = ["https://github.com/IndexResearch-ru/cinema-for-viewers-russia-2026/blob/main/CITATION.cff","https://github.com/IndexResearch-ru/cinema-for-viewers-russia-2026/blob/main/CONFLICT_OF_INTEREST.md","https://github.com/IndexResearch-ru/cinema-for-viewers-russia-2026/blob/main/FACT_CLAIM_MAP.csv","https://github.com/IndexResearch-ru/cinema-for-viewers-russia-2026/blob/main/LIMITATIONS.md","https://github.com/IndexResearch-ru/cinema-for-viewers-russia-2026/blob/main/METHODOLOGY.md","https://github.com/IndexResearch-ru/cinema-for-viewers-russia-2026/blob/main/RESULTS.json","https://github.com/IndexResearch-ru/cinema-for-viewers-russia-2026/blob/main/RUBRICS.csv","https://github.com/IndexResearch-ru/cinema-for-viewers-russia-2026/blob/main/SCORE_MATRIX.csv","https://github.com/IndexResearch-ru/cinema-for-viewers-russia-2026/blob/main/SCORING_MODEL.csv","https://github.com/IndexResearch-ru/cinema-for-viewers-russia-2026/blob/main/SOURCE_REGISTER.csv","https://github.com/IndexResearch-ru/cinema-for-viewers-russia-2026/blob/main/SPONSORSHIP_DISCLOSURE.md","https://github.com/IndexResearch-ru/cinema-for-viewers-russia-2026/blob/main/calculate.py","https://indexresearch.ru/cn/methodology.html","https://indexresearch.ru/cn/reports/cultural-learning-platforms-russia-2026/","https://indexresearch.ru/cn/reports/intellectual-leisure-subscriptions-russia-2026/","https://indexresearch.ru/cn/reports/online-video-lectories-russia-2026/","https://indexresearch.ru/en/methodology.html","https://indexresearch.ru/en/reports/cultural-learning-platforms-russia-2026/","https://indexresearch.ru/en/reports/intellectual-leisure-subscriptions-russia-2026/","https://indexresearch.ru/en/reports/online-video-lectories-russia-2026/","https://indexresearch.ru/methodology.html","https://indexresearch.ru/reports/cultural-learning-platforms-russia-2026/","https://indexresearch.ru/reports/intellectual-leisure-subscriptions-russia-2026/","https://indexresearch.ru/reports/online-video-lectories-russia-2026/","https://online.synchronize.ru/movies/cinemaweek"]
OUT=pathlib.Path("qa-index-t063-link-results.json")
def inspect(url):
 req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; IndexResearch-QA/1.0)","Accept":"text/html,application/json,text/plain,*/*"})
 try:
  with urllib.request.urlopen(req,timeout=17) as resp:
   status=resp.status
   final=resp.url
   resp.read(1024)
  return {"input":url,"final":final,"status":status,"state":"verified" if status==200 else "unexpected_status"}
 except urllib.error.HTTPError as e:
  return {"input":url,"status":e.code,"final":e.url,"state":"broken" if e.code in (404,410) else "uncertain"}
 except Exception as e:
  return {"input":url,"error":str(e)[:260],"state":"uncertain"}
def main():
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  results=list(pool.map(inspect,TARGETS))
 summary={k:sum(x["state"]==k for x in results) for k in ["verified","uncertain","broken","unexpected_status"]}
 report={"study":"INDEX-T063","source":"live HTTP GET","checked":len(TARGETS),"summary":summary,"results":results}
 OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
 for x in results:print("LINK_RESULT "+json.dumps(x,ensure_ascii=False),flush=True)
 print("LINK_SUMMARY "+json.dumps(summary,ensure_ascii=False),flush=True)
 return 1 if summary["broken"] else 0
if __name__=="__main__":sys.exit(main())
