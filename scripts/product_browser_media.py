#!/usr/bin/env python3
"""One bounded, read-only browser pass. Stop on access challenges; never solve CAPTCHA."""
import asyncio, hashlib, io, json, re
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from PIL import Image
from playwright.async_api import async_playwright

OUT = Path('/tmp/product-source-audit')
TARGETS = [
 ('P02', 'https://market.yandex.ru/card/kukolnyy-domik-villa/4835923444'),
 ('P08', 'https://market.yandex.ru/card/nabor-dlya-risovaniya--208sht-rozovyy/4331309113'),
 ('P02', 'https://www.livemaster.ru/item/33556394-kukly-i-igrushki-kukolnyj-igrovoj-domik-s-gorkoj-dlya-kukol-d'),
 ('P04', 'https://www.detmir.ru/product/index/id/6682237/'),
]

async def main():
 OUT.mkdir(parents=True, exist_ok=True)
 results = []
 async with async_playwright() as p:
  browser = await p.chromium.launch()
  context = await browser.new_context(viewport={'width': 1365, 'height': 1000}, locale='ru-RU')
  for product, url in TARGETS:
   page = await context.new_page()
   result = {'product': product, 'requested_url': url, 'photos': []}
   try:
    response = await page.goto(url, wait_until='domcontentloaded', timeout=45000)
    await page.wait_for_timeout(2500)
    result.update(status=response.status if response else None, final_url=page.url, title=await page.title())
    body = await page.locator('body').inner_text()
    result['text'] = body[:18000]
    result['blocked'] = any(s in (result['title'] + ' ' + body[:1500]).lower() for s in ['вы не робот', 'are you not a robot', 'подтвердите, что', 'access denied'])
    stem = product.lower() + '-' + hashlib.sha256(url.encode()).hexdigest()[:6]
    await page.screenshot(path=str(OUT / (stem + '-page.png')), full_page=False)
    if not result['blocked']:
     images = await page.locator('img').evaluate_all('(nodes) => nodes.map(n => ({src:n.currentSrc || n.src,alt:n.alt,width:n.naturalWidth,height:n.naturalHeight}))')
     result['images'] = images
     seen = set()
     for image in images:
      src = urljoin(page.url, image['src'])
      host = urlparse(src).hostname or ''
      if not src.startswith('https://') or not any(host.endswith(h) for h in ['mds.yandex.net','livemaster.ru','detmir.st']):
       continue
      if image['width'] < 250 or image['height'] < 250 or src in seen:
       continue
      seen.add(src)
      try:
       r = requests.get(src, timeout=20)
       r.raise_for_status()
       if len(r.content)>12000000: continue
       im = Image.open(io.BytesIO(r.content)).convert('RGB')
       im.thumbnail((1600,1600))
       filename = stem + '-candidate-' + str(len(result['photos'])+1) + '.jpg'
       im.save(OUT / filename, quality=91)
       result['photos'].append({'url':src,'file':filename,'alt':image['alt'],'width':im.width,'height':im.height})
       if len(result['photos'])>=8: break
      except Exception as exc:
       result.setdefault('image_errors',[]).append(str(exc)[:200])
   except Exception as exc:
    result['error'] = str(exc)[:500]
   finally:
    await page.close()
   results.append(result)
   print(product, result.get('status'), result.get('title'), 'blocked=',result.get('blocked'), 'photos=',len(result['photos']))
  await browser.close()
 (OUT/'browser-media.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__ == '__main__':
 asyncio.run(main())
