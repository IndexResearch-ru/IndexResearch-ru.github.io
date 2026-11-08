#!/usr/bin/env python3
"""Read-only public-source inspection; candidates are never automatically published."""
from __future__ import annotations
import concurrent.futures
import datetime
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = Path('/tmp/product-source-audit')
OUT.mkdir(parents=True, exist_ok=True)
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; IndexResearchProductSourceAudit/1.2)'}


def get_public(url: str) -> requests.Response:
    p = urlparse(url)
    if p.scheme != 'https' or not p.hostname or p.username or p.password:
        raise ValueError('Expected a public HTTPS URL without credentials')
    r = requests.get(url, headers=HEADERS, timeout=(10, 30))
    r.raise_for_status()
    if len(r.content) > 12_000_000:
        raise ValueError('Resource exceeds the 12 MB inspection limit')
    return r


def inspect_image(task: dict) -> dict:
    result = dict(task)
    try:
        if not re.fullmatch(r'[A-Za-z0-9_-]+', task['name']):
            raise ValueError('Invalid local image stem')
        r = get_public(task['url'])
        image = Image.open(io.BytesIO(r.content))
        image.load()
        result.update(status=r.status_code, final_url=r.url, original_format=image.format,
                      width=image.width, height=image.height, source_sha256=hashlib.sha256(r.content).hexdigest())
        if image.width < 100 or image.height < 100:
            raise ValueError('Image too small to inspect as a product photo')
        path = OUT / (task['name'] + '.png')
        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGBA')
        image.save(path)
        result['file'] = path.name
    except Exception as exc:
        result['error'] = type(exc).__name__ + ': ' + str(exc)[:500]
    return result


def inspect_page(task: dict) -> dict:
    result = dict(task)
    try:
        r = get_public(task['url'])
        soup = BeautifulSoup(r.content, 'html.parser')
        result.update(status=r.status_code, final_url=r.url)
        result['title'] = soup.title.get_text(' ', strip=True) if soup.title else ''
        result['h1'] = [n.get_text(' ', strip=True) for n in soup.find_all('h1')][:3]
        result['meta'] = {n.get('property', n.get('name', '')): n.get('content', '') for n in soup.select('meta[property^="og:"],meta[name="description"]')}
        result['images'] = [{'src': urljoin(r.url, n.get('src', '')), 'data_src': n.get('data-src'), 'srcset': n.get('srcset'), 'alt': n.get('alt')} for n in soup.find_all('img')][:160]
        result['image_links'] = [{'url': urljoin(r.url, n.get('href', '')), 'text': n.get_text(' ', strip=True)} for n in soup.find_all('a', href=True) if re.search(r'\.(?:jpg|jpeg|png|webp)(?:\?|$)', n['href'], re.I)][:80]
        result['product_links'] = [{'url': urljoin(r.url, n.get('href', '')), 'text': n.get_text(' ', strip=True)} for n in soup.find_all('a', href=True) if re.search('вилл|villa|208|бьюти|beauty', n.get_text(' ', strip=True) + ' ' + n['href'], re.I)][:40]
        result['jsonld'] = []
        for node in soup.select('script[type="application/ld+json"]')[:12]:
            try:
                result['jsonld'].append(json.loads(node.get_text()))
            except (ValueError, TypeError):
                pass
        for node in soup(['script', 'style', 'nav', 'footer']):
            node.decompose()
        result['visible_text_excerpt'] = re.sub(r'\s+', ' ', soup.get_text(' ', strip=True))[:20000]
        result['access_blocked'] = any(s in (result['title'] + ' ' + result['visible_text_excerpt'][:1200]).lower() for s in ['captcha', 'are you a robot', 'вы не робот', 'подтвердите, что', 'проверка браузера', 'access denied'])
        if result['access_blocked']:
            return result
        # Only inspect a bounded gallery from the explicitly configured source.
        limit = min(max(int(task.get('gallery_limit', 0)), 0), 12)
        candidates = []
        if result['meta'].get('og:image'):
            candidates.append(urljoin(r.url, result['meta']['og:image']))
        candidates += [n['url'] for n in result['image_links']]
        candidates += [urljoin(r.url, n.get('data_src') or n['src']) for n in result['images']]
        photo_filter = task.get('image_url_contains')
        seen = set()
        chosen = []
        for url in candidates:
            if url in seen or not url.startswith('https://') or '.svg' in url:
                continue
            seen.add(url)
            if photo_filter and photo_filter not in url:
                continue
            chosen.append(url)
            if len(chosen) >= limit:
                break
        if limit:
            key = hashlib.sha256(task['url'].encode()).hexdigest()[:6]
            result['gallery_candidates'] = [inspect_image({'product': task['product'], 'url': url,
                'name': task['product'].lower() + '-' + key + '-gallery-' + str(i + 1)})
                for i, url in enumerate(chosen)]
        og = result['meta'].get('og:image')
        if og and not limit and any(x in (urlparse(og).hostname or '').lower() for x in ('detmir', 'mds.yandex')):
            result['og_candidate'] = inspect_image({'product': task['product'], 'url': urljoin(r.url, og), 'name': task['product'].lower() + '-source-og'})
    except Exception as exc:
        result['error'] = type(exc).__name__ + ': ' + str(exc)[:500]
    return result


def export_snapshot() -> None:
    """Public repository files only; excludes Git metadata and hidden directories."""
    suffixes = {'.html', '.py', '.js', '.css', '.json', '.xml', '.md', '.txt', '.png', '.ico'}
    with zipfile.ZipFile(OUT / 'site-snapshot.zip', 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob('*')):
            rel = path.relative_to(ROOT)
            if not path.is_file() or path.is_symlink() or any(p.startswith('.') for p in rel.parts):
                continue
            if path.suffix not in suffixes or path.stat().st_size > 2_000_000:
                continue
            if path.suffix in {'.png', '.ico'} and len(rel.parts) != 1:
                continue
            archive.write(path, rel.as_posix())


def main() -> None:
    data = json.loads((ROOT / 'templates/product-source-audit.json').read_text(encoding='utf-8'))
    pages = data.get('pages', [])
    images = data.get('images', [])
    if len(pages) > 30 or len(images) > 30 or sum(int(p.get('gallery_limit', 0)) for p in pages) > 60:
        raise ValueError('Bounded audit: at most 30 pages, 30 explicit images and 60 gallery candidates')
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        page_results = list(pool.map(inspect_page, pages))
        image_results = list(pool.map(inspect_image, images))
    report = {'selection_id': data['selection_id'], 'checked_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pages': page_results, 'images': image_results}
    (OUT / 'source-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    if data.get('export_public_site_snapshot'):
        export_snapshot()
    for item in page_results + image_results:
        print(json.dumps({k: item.get(k) for k in ('product', 'url', 'status', 'title', 'file', 'width', 'height', 'access_blocked', 'error') if k in item}, ensure_ascii=False))
    print('AUDIT_COMPLETE', len(page_results), 'pages;', len(image_results), 'explicit image candidates')


if __name__ == '__main__':
    main()
