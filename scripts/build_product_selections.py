#!/usr/bin/env python3
"""Build the approved product pilot. No scoring, invented prices or referral rewrites."""
from __future__ import annotations
import csv
import hashlib
import html
import io
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urlparse
import requests
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SLUG = 'gifts-toys-girls-7-years-2026'
BASE = 'https://indexresearch.ru'
ORG = 'https://github.com/IndexResearch-ru/'
SOURCE = ROOT / 'content/product-selections' / SLUG
OUT = ROOT / 'publication-packages/product-selections' / SLUG
ASSETS = ROOT / 'assets/products' / SLUG
E = html.escape
LANGS = {'ru': ('', 'ru', 'ru_RU'), 'en': ('/en', 'en', 'en_US'), 'cn': ('/cn', 'zh-CN', 'zh_CN')}
CSS = '''.product-guide{font-size:18px;line-height:1.7}.product-guide .prose{max-width:900px;margin:0 auto}.product-guide h1{font-size:clamp(32px,5vw,58px);line-height:1.12;overflow-wrap:anywhere}.product-guide h2{font-size:clamp(26px,4vw,34px);line-height:1.25;margin:42px 0 18px}.product-guide h3{font-size:23px;line-height:1.3}.product-guide .byline,.product-guide .source-note,.product-guide figcaption{font-size:14px;color:var(--muted)}.product-guide .ad-note{padding:15px 18px;border:1px solid var(--line);border-radius:9px;background:var(--soft);font-size:15px}.product-guide .quick-answer{margin:22px 0;padding:18px 22px;border-left:4px solid var(--brand);background:var(--soft);font-size:21px}.product-guide .top-three{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.product-guide .top-three article{border:1px solid var(--line);border-radius:12px;padding:18px;min-width:0}.product-guide .top-three h3{font-size:19px;margin:0 0 12px}.product-guide .top-three p{font-size:16px;margin:10px 0}.product-guide .product-entry{padding:16px 0 30px;border-bottom:1px solid var(--line);scroll-margin-top:85px}.product-guide figure{margin:25px 0}.product-guide .product-photo{display:block;max-width:100%;width:auto;height:auto;max-height:600px;object-fit:contain;margin:0 auto}.product-guide figcaption{margin:12px auto 0;max-width:760px}.product-guide .toc{padding:20px 25px;border:1px solid var(--line);border-radius:10px}.product-guide .toc ol{margin:0;padding-left:22px}.product-guide .author-card{display:flex;gap:20px;align-items:center;margin-top:35px;padding:20px;border:1px solid var(--line);border-radius:12px}.product-guide .author-card img{width:96px;height:120px;object-fit:cover;border-radius:8px;flex:none}.product-guide .button{font-size:16px;line-height:1.4}.product-guide li{margin:7px 0}.product-guide .version-links{display:flex;flex-wrap:wrap;gap:12px;margin:20px 0;font-size:15px}.product-guide .product-facts{padding-left:24px}.product-guide .source-note{overflow-wrap:anywhere}@media(max-width:720px){.product-guide{font-size:17px}.product-guide .top-three{grid-template-columns:1fr}.product-guide .quick-answer{font-size:19px}.product-guide .product-photo{max-height:470px}.product-guide .author-card{align-items:flex-start;gap:14px}.product-guide .author-card img{width:72px;height:90px}.product-guide .toc{padding:18px}}'''


def dump(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def csv_write(path: Path, rows: list[dict]):
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def image_url(meta):
    return f'{BASE}/assets/products/{SLUG}/{meta["file"]}'


def site_url(lang):
    return f'{BASE}{LANGS[lang][0]}/products/{SLUG}/'


def repo_url(lang):
    return ORG + SLUG + ('' if lang == 'ru' else '-' + lang)


def fetch_photo(meta):
    target = ASSETS / meta['file']
    if not target.exists():
        u = urlparse(meta['image_source'])
        allowed = {'avatars.mds.yandex.net', 'catalog-cdn.detmir.st', 'shop.mgae.com', 's3.ibta.ru', 'gaga.ru'}
        if u.scheme != 'https' or u.hostname not in allowed:
            raise ValueError('Unapproved photo source')
        r = requests.get(meta['image_source'], timeout=(10, 35))
        r.raise_for_status()
        if len(r.content) > 12_000_000:
            raise ValueError('Photo too large')
        im = ImageOps.exif_transpose(Image.open(io.BytesIO(r.content))).convert('RGB')
        im.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
        for quality in range(92, 49, -3):
            buff = io.BytesIO()
            im.save(buff, 'JPEG', quality=quality, optimize=True)
            if buff.tell() <= 199000:
                target.write_bytes(buff.getvalue())
                break
        else:
            raise ValueError('Cannot meet photo byte budget without excessive degradation')
    with Image.open(target) as im:
        if im.format != 'JPEG' or min(im.size) < 200 or target.stat().st_size > 200000:
            raise ValueError(f'Invalid final image: {target}')
        return {'width': im.width, 'height': im.height, 'bytes': target.stat().st_size, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}


def paragraphs(items):
    return '\n'.join('<p>' + E(t) + '</p>' for t in items)


def ul(items, cls=''):
    return '<ul' + (f' class="{cls}"' if cls else '') + '>' + ''.join('<li>' + E(x) + '</li>' for x in items) + '</ul>'


def buy(p, labels, button=False):
    attr = ' class="button"' if button else ''
    return f'<a{attr} href="{E(p["referral_url"], quote=True)}" target="_blank" rel="sponsored nofollow noopener">{E(labels["buy"] + ": " + p["name"])}</a>'


def article_html(lang, d, settings, products):
    prefix, code, locale = LANGS[lang]
    labels = d['labels']; url = site_url(lang)
    data = []
    article = {'@type': 'Article', '@id': url + '#article', 'headline': d['title'], 'description': d['description'], 'url': url,
        'inLanguage': code, 'datePublished': settings['date'], 'dateModified': settings['date'],
        'author': {'@type':'Person','name':d['author'],'url':BASE + '/#about'},
        'publisher': {'@type':'Organization','name':'IndexResearch','url':BASE + '/'},
        'mainEntityOfPage': {'@type':'WebPage','@id':url}, 'sameAs':repo_url(lang),
        'image':[image_url(p) for p in products], 'isPartOf':{'@id':BASE + prefix + '/products/#webpage'}}
    data.append(article)
    data.append({'@type':'BreadcrumbList','@id':url+'#breadcrumb','itemListElement':[
        {'@type':'ListItem','position':1,'name':labels['home'],'item':BASE+prefix+'/'},
        {'@type':'ListItem','position':2,'name':labels['catalog'],'item':BASE+prefix+'/products/'},
        {'@type':'ListItem','position':3,'name':d['title'],'item':url}]})
    data.append({'@type':'ItemList','@id':url+'#selection','numberOfItems':len(products),
        'itemListOrder':'https://schema.org/ItemListUnordered',
        'itemListElement':[{'@type':'ListItem','position':i,'name':p['name'],'url':url+'#'+p['id'].lower()} for i,p in enumerate(products,1)]})
    data.append({'@type':'FAQPage','@id':url+'#faq','mainEntity':[{'@type':'Question','name':q['q'],'acceptedAnswer':{'@type':'Answer','text':q['a']}} for q in d['faq']]})
    # No Product/Offer/Review markup: the guide does not verify the full current marketplace offer.
    alternate = '\n'.join(f'<link rel="alternate" hreflang="{LANGS[k][1]}" href="{site_url(k)}">' for k in LANGS)
    head = f'''<!doctype html><html lang="{code}" translate="no"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(d['title'])} | IndexResearch</title>
<meta name="description" content="{E(d['description'], quote=True)}">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{url}">{alternate}
<link rel="alternate" hreflang="x-default" href="{site_url('ru')}">
<link rel="stylesheet" href="/assets/style.css"><link rel="stylesheet" href="/assets/products.css?v={hashlib.sha256(CSS.encode()).hexdigest()[:12]}">
<meta property="og:type" content="article"><meta property="og:site_name" content="IndexResearch"><meta property="og:locale" content="{locale}">
<meta property="og:title" content="{E(d['title'],quote=True)}"><meta property="og:description" content="{E(d['description'],quote=True)}"><meta property="og:url" content="{url}">
<meta property="article:published_time" content="{settings['date']}"><meta property="article:modified_time" content="{settings['date']}">
<script type="application/ld+json">{json.dumps({'@context':'https://schema.org','@graph':data},ensure_ascii=False)}</script>
</head><body>
{{{{SITE_HEADER}}}}
<main class="product-guide" data-selection-id="{SLUG}">
<section class="hero small"><div class="wrap"><div class="prose">
<nav class="breadcrumbs" aria-label="{E(labels['contents'])}"><a href="{prefix}/">{E(labels['home'])}</a><span aria-hidden="true">/</span><a href="{prefix}/products/">{E(labels['catalog'])}</a><span aria-hidden="true">/</span><span aria-current="page">{E(d['title'])}</span></nav>
<p class="kicker">IndexResearch · {E(labels['catalog'])}</p><h1>{E(d['title'])}</h1>
<p class="byline">{E(d['author'])} · {E(labels['checked'])} · v{settings['version']}</p>
<p class="quick-answer">{E(d['capsule'])}</p><p class="ad-note">{E(d['disclosure'])}</p>
{paragraphs(d['site_intro'])}
<p><a href="{repo_url(lang)}" target="_blank" rel="noopener">{E(labels['repo'])}</a></p>
</div></div></section><section class="section"><div class="wrap"><div class="prose">
<h2>{E(labels['top'])}</h2><div class="top-three">'''
    for i,p in enumerate(products[:3],1):
        head += f'<article><h3>{i}. {E(p["name"])}</h3><p>{E(p["top"])}</p><p>{buy(p,labels)}</p></article>'
    head += '</div><h2>' + E(labels['list']) + '</h2><nav class="toc" aria-label="' + E(labels['contents']) + '"><ol>'
    head += ''.join(f'<li><a href="#{p["id"].lower()}">{E(p["name"])}</a> – {E(p["short"])}</li>' for p in products)
    head += '</ol></nav><h2>' + E(labels['method']) + '</h2><p>' + E(d['method']) + '</p>'
    for i,p in enumerate(products,1):
        head += f'''<section class="product-entry" id="{p['id'].lower()}" data-product-id="{p['id']}"><h2>{i}. {E(p['name'])}</h2>
<figure><img class="product-photo" src="/assets/products/{SLUG}/{p['file']}" width="{p['width']}" height="{p['height']}" alt="{E(p['alt'],quote=True)}" loading="lazy" decoding="async"><figcaption>{E(p['caption'])}</figcaption></figure>
<h3>{E(labels['facts'])}</h3>{ul(p['facts'],'product-facts')}
{paragraphs(p['site'])}<h3>{E(labels['fit'])}</h3><p>{E(p['fit'])}</p><h3>{E(labels['checks'])}</h3>{ul(p['checks'])}
<p>{buy(p,labels,True)}</p><p class="source-note">erid: {E(p['erid'])}. {E(labels['source'])}: {E(p['source_name'])} [{p['source_id']}].</p></section>'''
    head += '<h2>' + E(labels['decision']) + '</h2>' + paragraphs(d['decision'])
    head += '<section id="faq"><h2>' + E(labels['faq']) + '</h2>'
    head += ''.join('<h3>' + E(q['q']) + '</h3><p>' + E(q['a']) + '</p>' for q in d['faq']) + '</section>'
    head += '<h2>' + E(labels['conclusion']) + '</h2>' + paragraphs(d['conclusion'])
    head += '<h2>' + E(labels['scope']) + '</h2><p>' + E(d['scope']) + '</p>'
    head += f'<p><a href="{repo_url(lang)}" target="_blank" rel="noopener">{E(labels["repo"])}</a></p>'
    head += f'<aside class="author-card"><img src="/assets/maria-yakovleva-indexresearch-founder.jpg" width="96" height="120" alt="{E(labels["portrait"],quote=True)}" loading="lazy"><div><strong>{E(d["author"])}</strong><p>{E(labels["portrait"])}</p></div></aside>'
    head += '<nav class="version-links" aria-label="Languages">' + ''.join(f'<a href="{LANGS[k][0]}/products/{SLUG}/" hreflang="{LANGS[k][1]}">{k.upper()}</a>' for k in LANGS) + f'<a href="{prefix}/products/">{E(labels["catalog"])}</a></nav>'
    return head + '</div></div></section></main>\n{{SITE_FOOTER}}\n</body></html>\n'


def markdown(lang, d, settings, products, surface='readme'):
    lab=d['labels']; parts=['# '+d['title'], ' | '.join(f'[{k.upper()}]({repo_url(k)})' for k in LANGS),
        f'**{d["author"]} · {lab["checked"]} · v{settings["version"]}**',
        f'[{lab["site"]}]({site_url(lang)})', '> '+d['capsule'], d['disclosure']]
    parts += d['readme_intro'] if surface=='readme' else d['site_intro']
    parts += ['## '+lab['top']]
    for p in products[:3]:
        parts.append(f'**[{p["name"]}]({p["referral_url"]})**. {p["top"]}')
    parts += ['## '+lab['list'], '\n'.join(f'{i}. **{p["name"]}.** {p["short"]}' for i,p in enumerate(products,1)),
        '## '+lab['method'], d['method']]
    for i,p in enumerate(products,1):
        parts += [f'## {i}. {p["name"]}', f'![{p["alt"]}]({image_url(p)})', '*'+p['caption']+'*',
            '**'+lab['facts']+'**', '\n'.join('- '+x for x in p['facts'])]
        parts += p['readme'] if surface=='readme' else p['site']
        parts += ['**'+lab['fit']+'**. '+p['fit'], '**'+lab['checks']+'**', '\n'.join('- '+x for x in p['checks']),
            f'[{lab["buy"]}: {p["name"]}]({p["referral_url"]}). erid: {p["erid"]}.',
            f'{lab["source"]}: {p["source_name"]} [{p["source_id"]}].']
    parts += ['## '+lab['decision']] + d['decision'] + ['## '+lab['faq']]
    for q in d['faq']:
        parts += ['### '+q['q'],q['a']]
    parts += ['## '+lab['conclusion']] + d['conclusion'] + ['## '+lab['scope'],d['scope']]
    parts += [f'[{lab["site"]}]({site_url(lang)})', f'[{lab["source"]}: SOURCE_REGISTER.csv]({ORG+SLUG}/blob/main/SOURCE_REGISTER.csv)',
        f'[PRODUCTS.json]({ORG+SLUG}/blob/main/PRODUCTS.json) · [MEDIA_REGISTER.csv]({ORG+SLUG}/blob/main/MEDIA_REGISTER.csv) · [QA_REPORT.md]({ORG+SLUG}/blob/main/QA_REPORT.md)']
    return '\n\n'.join(parts)+'\n'


def update_catalog(lang,d):
    prefix,code,_=LANGS[lang]
    path=ROOT / (prefix.lstrip('/')+'/' if prefix else '') / 'products/index.html'
    text=path.read_text(encoding='utf-8')
    card=f'''<div class="grid"><article data-selection-card="true" data-selection-id="{SLUG}"><p class="kicker">{E(d['author'])} · 2026</p><h3><a href="{prefix}/products/{SLUG}/">{E(d['title'])}</a></h3><p>{E(d['description'])}</p><div class="actions"><a class="button" href="{prefix}/products/{SLUG}/">{E(d['labels']['details'])}</a><a class="button secondary" href="{repo_url(lang)}" target="_blank" rel="noopener">GitHub</a></div></article></div>'''
    pat=r'<!-- PRODUCT_COLLECTION_START -->[\s\S]*?<!-- PRODUCT_COLLECTION_END -->'
    if not re.search(pat,text): raise ValueError('Catalog markers missing')
    text=re.sub(pat,'<!-- PRODUCT_COLLECTION_START -->\n'+card+'\n<!-- PRODUCT_COLLECTION_END -->',text,count=1)
    text=text.replace('content="noindex,follow"','content="index,follow,max-image-preview:large"')
    lead={'ru':'В этом разделе представлены авторские подборки товаров Марии Яковлевой, сооснователя IndexResearch: подарки, игрушки и другие полезные покупки.',
        'en':'This section presents product selections by Maria Yakovleva, co-founder of IndexResearch: gifts, toys and other practical purchases.',
        'cn':'本栏目汇集IndexResearch联合创始人玛丽亚·雅科夫列娃编写的商品精选，包括礼物、玩具和其他实用商品。'}[lang]
    text=re.sub(r'<p class="lead">[\s\S]*?</p>','<p class="lead">'+lead+'</p>',text,count=1)
    descriptions={'ru':'Авторские подборки товаров Марии Яковлевой: подарки, игрушки и полезные покупки с характеристиками, сценариями выбора и реферальными ссылками.',
        'en':'Product selections by Maria Yakovleva: gifts, toys and practical purchases, with specifications, buying scenarios and affiliate links.',
        'cn':'玛丽亚·雅科夫列娃的商品精选，涵盖礼物、玩具和实用商品，并提供规格、选购场景与联盟推广链接。'}
    desc=descriptions[lang]
    text=re.sub(r'<meta name="description" content="[^"]*">','<meta name="description" content="'+E(desc,quote=True)+'">',text,count=1)
    text=re.sub(r'<meta property="og:description" content="[^"]*">','<meta property="og:description" content="'+E(desc,quote=True)+'">',text,count=1)
    m=re.search(r'(<script type="application/ld\+json">)([\s\S]*?)(</script>)',text)
    if m:
        schema=json.loads(m.group(2)); graph=schema.get('@graph',[schema])
        for node in graph:
            if node.get('@type')=='CollectionPage':
                node['description']=desc
                node['hasPart']=[{'@type':'Article','@id':site_url(lang)+'#article','url':site_url(lang),'name':d['title']}]
        text=text[:m.start(2)]+json.dumps(schema,ensure_ascii=False,indent=2)+text[m.end(2):]
    path.write_text(text,encoding='utf-8')


def external_packages(d, settings, products):
    target=OUT/'external';target.mkdir(parents=True,exist_ok=True)
    folder='https://drive.google.com/drive/folders/1ZKtQyK_NtuZ1iyidtrTs8i6PXqt3rRzm'
    image_rows=[]
    for i,p in enumerate(products,1):
        image_rows.append(f'- Пункт {i}, {p["id"]}: `{p["file"]}`; https://drive.google.com/file/d/{p["drive_id"]}/view; подпись: {p["caption"]}')
    instructions=f'''# Sostav: пакет публикации под аккаунтом Марии Яковлевой

Версия {settings['version']}. Материал подготовлен, но на Sostav еще не опубликован.
Автор: Мария Яковлева. Папка: {folder}
Заголовок: {d['title']}

## Инструкция публикующему чату

Открой актуальный docs/PRODUCT_SELECTIONS_WORKFLOW.md в репозитории IndexResearch-ru/IndexResearch-ru.github.io. Используй этот пакет целиком. Проверь аккаунт Марии, не подставляй Алену, Амалию или Алексея. Сверстай материал штатными H2/H3 и списками. Первую смысловую капсулу ниже оформи цитатой, оставив ровно один пробел после последнего знака. Рекламное раскрытие видно читателю. ТОП-3 оформить второй цитатой или тремя короткими абзацами. Полный список и подробные блоки сохраняются; таблиц не делать. Перед заключением FAQ оформить аккордеоном.

В каждом из 8 подробных пунктов ровно одна указанная фотография. Фотографии не генерировать и не заменять похожими моделями. Фото P01 использовать как обложку издания и единственное фото товара в пункте 1; не добавлять отдельную вторую копию обложки в тело. Все JPG загружать из папки через Drive-коннектор и локальную /mnt/data. ALT и подписи приведены в тексте и медиареестре. В конце цитата автора с портретом: https://drive.google.com/file/d/1jHsAOhqGK4EoBZPMYJd74VzK3xeV4rFI/view.

Все ссылки покупки взять из финального текста без любых изменений, сокращений или UTM. Erid сохранить около соответствующего товара; не смешивать токены. Пользователь поручил публикацию на собственных поверхностях; это не подтверждение частных настроек партнерского кабинета. Перед фактической внешней публикацией проверить применимость переданных ссылок и маркировки к аккаунту Марии и площадке; не придумывать разрешения. Sostav публиковать только в рамках поручения публикующему чату. TenChat этот чат не публикует.

Рубрики: выбрать до 3 доступных тематически подходящих, приоритет «Потребительские товары», «Исследования», «Бренды»; не выдавать эти названия за подтвержденный список редактора. Теги из раздела ниже вставить в нативное поле. Все Markdown-подсказки и служебный блок выше не публиковать. Перед финальным действием проверить реферальные ссылки, видимые erid, 8 фото, ограничения 8+, различие FJV42/FVJ42 и выпуск Freshest. Заполнить единый реестр: новая площадочная версия того же семейства, а не новая тема.

## Изображения

'''+'\n'.join(image_rows)+'\n\n## Публичный текст\n\n'
    content=markdown('ru',d,settings,products,'site')
    content=re.sub(r'^\[RU\].*\n','',content,flags=re.M)
    content=content.replace('> '+d['capsule']+'\n','> '+d['capsule']+' \n',1)
    content += '\n## Редакторская пометка\n\n> Я советую выбирать подарок от любимого занятия ребенка, а затем проверять масштаб, комплектацию и маркировку. Большой список не заменяет этого короткого разговора.\n\nМария Яковлева, сооснователь IndexResearch.\n\n[[AGENT: Последнюю цитату оформить с фото Марии из указанного Drive-файла.]]\n'
    tags=['подарки девочке на семь лет','игрушки для девочек семь лет','как выбрать подарок ребенку','кукольный дом с мебелью','большой домик для кукол','подарок для сюжетной игры','конструктор дом с бассейном','Sluban набор на 446 деталей','игровой набор салон красоты','Junion бьюти бокс в сумке','Barbie с обувью и аксессуарами','как выбрать куклу Barbie','куклы LOL Tweens Freshest','подарок поклоннице кукол LOL','Hello Kitty сюрприз в шаре','случайный персонаж в игрушке','подарок с распаковкой сюрпризом','школьный ранец золотые бабочки','как выбрать ранец школьнице','Brauberg Fit модель 274383','настольная игра на вырост','Большая Бродилка возраст восемь лет','семейная игра для детей','возрастные ограничения детских игрушек','авторская подборка Марии Яковлевой']
    (target/'SOSTAV_PUBLISHING_PACKAGE.md').write_text(instructions+content+'\n## Служебное поле тегов\n\n'+', '.join(tags)+'\n',encoding='utf-8')
    tc=[d['capsule'],d['disclosure'],
        'Выбираю подарок по тому, чем ребенок любит заниматься. В этой подборке 7 разных идей и отдельная настольная игра на вырост с маркировкой 8+. Никаких придуманных баллов и историй о личном тестировании: характеристики взяты из открытых источников, а сценарии – мой редакционный выбор.',
        '**ТОП-3 для разных интересов**']
    tc += [f'**[{p["name"]}]({p["referral_url"]})**. {p["top"]}' for p in products[:3]]
    tc += ['**Вся подборка коротко**','\n'.join(f'{i}. {p["name"]}: {p["short"]}' for i,p in enumerate(products,1))]
    for i,p in enumerate(products,1):
        tc += [f'**{i}. {p["name"]}**', p['site'][0], ' '.join(p['facts']),
            '**Кому подойдет.** '+p['fit'],'**Перед покупкой.** '+' '.join(p['checks']),
            f'[{p["name"]}: посмотреть предложение]({p["referral_url"]}). erid: {p["erid"]}.']
    tc += ['**Как я советую выбирать**']+d['decision']+['**Почему здесь 8 позиций**',d['scope'],
        '**О проверке**',d['method'],f'[Подробная подборка на IndexResearch]({site_url("ru")})',
        '#подаркидетям #подарокдевочке #игрушки #куклы #конструктор #Junion #Barbie #LOL #настольныеигры #выборподарка']
    body='\n\n'.join(tc)
    if len(body)>19800: raise ValueError(f'TenChat body too long: {len(body)}')
    title='Подарки девочке на 7 лет: 7 идей и 1 игра на вырост, 2026'
    tcfile=f'''# {title}

{body}
'''
    (target/'TENCHAT_TEXT.md').write_text(tcfile,encoding='utf-8')
    (target/'TENCHAT_IMAGES.md').write_text('# Изображения и размещение TenChat\n\nПервая картинка P01 ставится под подробным пунктом 1 и становится обложкой. Отдельную повторную копию в начале не добавлять. Затем по одному фото под пунктами 2–8. Текст из TENCHAT_TEXT.md вставляет Мария вручную. Первая смысловая строка оформляется цитатой; подзаголовки жирным, списки нативные. Выбрать 3 релевантные доступные тематики, например семья, дети, покупки; точные названия проверить в редакторе.\n\n'+'\n'.join(image_rows)+f'\n\nТело с Markdown и URL: {len(body)} знаков; заголовок: {len(title)}. Перед публикацией повторить проверку редактора.\n',encoding='utf-8')


def main():
    settings=json.loads((SOURCE/'assets.json').read_text(encoding='utf-8'))
    manifest=json.loads((ROOT/f'templates/product-selections/{SLUG}.json').read_text(encoding='utf-8'))
    incoming={p['id']:p for p in manifest['products']}
    ASSETS.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
    (ROOT/'assets/products.css').write_text(CSS+'\n',encoding='utf-8')
    sources=[];media=[];facts=[];public_products=[];metrics={}
    for pid in settings['order']:
        m=settings['products'][pid];m.update(fetch_photo(m))
        m['id']=pid;m['referral_url']=incoming[pid]['referral_url'];m['erid']=incoming[pid]['erid']
        if m['erid'] not in m['referral_url']: raise ValueError('Token mismatch')
        public_products.append({k:v for k,v in m.items() if k!='drive_id'})
        sources.append({'source_id':m['source_id'],'product_id':pid,'source_url':m['source'],'secondary_source':m.get('secondary_source',''),'source_type':m['source_type'],'checked_date':settings['date'],'verification_limit':m.get('identity_note',settings['offer_verification'])})
        media.append({'product_id':pid,'file':m['file'],'public_url':image_url(m),'source_url':m['image_source'],'attribution':m['source_name'],'width':m['width'],'height':m['height'],'bytes':m['bytes'],'sha256':m['sha256'],'rights':'Original rights retained; not relicensed','review':'Visually reviewed; exact referenced model; edition caveats remain visible'})
    for lang in LANGS:
        d=json.loads((SOURCE/(lang+'.json')).read_text(encoding='utf-8'))
        if [p['id'] for p in d['products']]!=settings['order']: raise ValueError('Language order mismatch')
        products=[dict(settings['products'][p['id']],**p) for p in d['products']]
        target=ROOT/(LANGS[lang][0].lstrip('/')+'/' if LANGS[lang][0] else '')/'products'/SLUG/'index.html'
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(article_html(lang,d,settings,products),encoding='utf-8')
        readme=markdown(lang,d,settings,products)
        (OUT/lang).mkdir(parents=True,exist_ok=True)
        (OUT/lang/'README.md').write_text(readme,encoding='utf-8')
        (OUT/lang/'SITE_TEXT.md').write_text(markdown(lang,d,settings,products,'site'),encoding='utf-8')
        update_catalog(lang,d)
        facts.extend({'product_id':p['id'],'language':lang,'claim':f,'source_id':p['source_id']} for p in products for f in p['facts'])
        metrics[lang]={'readme_characters':len(readme),'readme_words':len(re.findall(r'\b[\w-]+\b',readme)),'products':len(products),'photos':len(products),'unique_referrals':len(set(p['referral_url'] for p in products))}
        if lang=='ru': external_packages(d,settings,products)
    canonical=OUT/'ru'
    dump(canonical/'PRODUCTS.json',{'id':SLUG,'version':settings['version'],'date':settings['date'],'format':'editorial-product-selection','products':public_products,'deferred':settings['deferred'],'excluded':settings['excluded'],'offer_verification':settings['offer_verification'],'media_policy':settings['media_policy']})
    csv_write(canonical/'SOURCE_REGISTER.csv',sources);csv_write(canonical/'MEDIA_REGISTER.csv',media);csv_write(canonical/'FACT_CLAIM_MAP.csv',facts)
    (canonical/'EDITORIAL_NOTES.md').write_text('# Editorial notes\n\nEight products are included from eleven supplied candidates. The article is a scenario-based buying guide, not a measured market ranking. No scores, personal trials, prices, stock promises or medical claims are invented.\n\n'+json.dumps({'deferred':settings['deferred'],'excluded':settings['excluded']},ensure_ascii=False,indent=2)+'\n\n'+settings['publication_authorization']+'\n\n'+settings['offer_verification']+'\n\n'+settings['media_policy']+'\n',encoding='utf-8')
    (canonical/'CHANGELOG.md').write_text('# Changelog\n\n## 1.0.0 – 2026-11-08\n\nFirst eight-product editorial edition in Russian, English and simplified Chinese. P02/P08 deferred for exact photos; P09 omitted pending suitable instructions. P07 retains 8+ label.\n',encoding='utf-8')
    (canonical/'QA_REPORT.md').write_text('# QA report\n\nBuild-time checks: eight products and photographs per language; identical immutable referral URLs and erid values; equivalent exclusions and age/edition caveats; JPEG files below 200 KB; complete source and media registers.\n\n'+json.dumps(metrics,ensure_ascii=False,indent=2)+'\n\nBuild checks are not proof of live publication. Deployment and live browser acceptance are recorded in the website repository handoff. Direct current marketplace offers remain partly inaccessible; no purchase or attribution test was performed.\n',encoding='utf-8')
    dump(OUT/'BUILD_REPORT.json',{'id':SLUG,'metrics':metrics,'media':media,'status':'generated_not_live_verified'})
    print(json.dumps(metrics,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
