#!/usr/bin/env python3
"""Focused product QA complements the site's existing checks."""
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
SLUG='gifts-toys-girls-7-years-2026'
settings=json.loads((ROOT/f'content/product-selections/{SLUG}/assets.json').read_text())
manifest=json.loads((ROOT/f'templates/product-selections/{SLUG}.json').read_text())
refs={p['id']:p['referral_url'] for p in manifest['products']}
expected_count=len(refs)
if expected_count!=11 or set(settings['order'])!=set(refs): raise ValueError('Complete eleven-product selection required')
errors=[]
for lang,prefix in [('ru',''),('en','en/'),('cn','cn/')]:
 path=ROOT/f'{prefix}products/{SLUG}/index.html'
 soup=BeautifulSoup(path.read_text(),'html.parser')
 main=soup.find('main')
 if not main: errors.append(f'{lang}: main missing');continue
 entries=main.select('[data-product-id]')
 if [e['data-product-id'] for e in entries]!=settings['order']: errors.append(f'{lang}: order mismatch')
 if len(main.select('img.product-photo'))!=expected_count: errors.append(f'{lang}: must have 8 product photos')
 if len(soup.find_all('h1'))!=1: errors.append(f'{lang}: one H1 required')
 for e in entries:
  pid=e['data-product-id']
  if len(e.select('img.product-photo'))!=1: errors.append(f'{lang}/{pid}: photo count')
  if not any(a.get('href')==refs[pid] for a in e.find_all('a')): errors.append(f'{lang}/{pid}: missing immutable referral')
  if 'erid:' not in e.get_text(): errors.append(f'{lang}/{pid}: missing visible token')
  img=e.select_one('img.product-photo')
  if img:
   file=ROOT/img['src'].lstrip('/')
   if not file.is_file(): errors.append(f'{lang}/{pid}: missing photo')
   else:
    with Image.open(file) as im:
     if im.format!='JPEG' or file.stat().st_size>200000: errors.append(f'{lang}/{pid}: invalid JPG')
 for a in main.find_all('a',href=True):
  if urlparse(a['href']).hostname=='market.yandex.ru':
   if a['href'] not in [refs[p] for p in settings['order']]: errors.append(f'{lang}: unapproved purchase link')
   if not {'sponsored','nofollow','noopener'}.issubset(set(a.get('rel',[]))): errors.append(f'{lang}: affiliate rel missing')
   if a.get('target')!='_blank': errors.append(f'{lang}: external target missing')
 text=main.get_text(' ',strip=True)
 if any(x in text for x in ['[[AGENT','{{SITE_HEADER','{{SITE_FOOTER','БЛОКЕР']): errors.append(f'{lang}: technical placeholder')
 if '8+' not in main.select_one('[data-product-id="P07"]').get_text(): errors.append(f'{lang}: game age warning missing')
 if 'FJV42' not in main.select_one('[data-product-id="P03"]').get_text(): errors.append(f'{lang}: Barbie discrepancy hidden')
 for raw in soup.select('script[type="application/ld+json"]'):
  obj=json.loads(raw.string)
  for node in obj.get('@graph',[obj]):
   if node.get('@type') in ['Dataset','Review','AggregateRating','Offer']: errors.append(f'{lang}: inappropriate schema')
 cat=BeautifulSoup((ROOT/f'{prefix}products/index.html').read_text(),'html.parser')
 if len(cat.select(f'[data-selection-card="true"][data-selection-id="{SLUG}"]'))!=1: errors.append(f'{lang}: catalog card missing/duplicated')
 if 'noindex' in cat.find('meta',attrs={'name':'robots'}).get('content',''): errors.append(f'{lang}: catalog still noindex')
 readme=(ROOT/f'publication-packages/product-selections/{SLUG}/{lang}/README.md').read_text()
 if len(re.findall(r'!\[',readme))!=expected_count: errors.append(f'{lang}: README image count')
 found=set(re.findall(r'https://market\.yandex\.ru/cc/[^\s)<>]+',readme))
 if found!=set(refs[p] for p in settings['order']): errors.append(f'{lang}: README referral set mismatch')
 if 'awaiting_' in readme or 'PREPUBLICATION' in readme: errors.append(f'{lang}: draft marker in article')
if errors:
 print('\n'.join(errors));sys.exit(1)
print('PRODUCT QA PASSED: 3 languages; 11 items/photos; exact referrals and caveats preserved.')
