#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import html as html_module
import json
import re

from research_topics import load_topic_config

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://indexresearch.ru"
CATALOG_URL = f"{BASE}/ratings/"
CATALOG_ID = f"{CATALOG_URL}#catalog"
CATALOG_PATH = ROOT / "ratings" / "index.html"
ORG_ID = f"{BASE}/#organization"
LOGO_IMAGE = f"{BASE}/assets/indexresearch-logo-horizontal.png"
NON_RESEARCH = {"index.html", "methodology.html", "404.html"}
TOPIC_CONFIG = load_topic_config()
TOPIC_BY_RESEARCH_ID = {
    research_id: topic
    for topic in TOPIC_CONFIG.get("topics", [])
    for research_id in (topic.get("research_ids") or [])
}


def topic_title_for_language(topic: dict, lang: str) -> str:
    if lang == "ru":
        return topic["seo"]["h1"]
    return topic["seo_i18n"][lang]["h1"]

TITLE_OVERRIDES = {
    "antarctica-tours-russia-2026.html": (
        "Туры в Антарктиду под ключ: ТОП-10 организаторов, 2026–2027 | IndexResearch",
        "Туры в Антарктиду под ключ: ТОП-10 организаторов, 2026–2027",
    ),
    "argentina-patagonia-tailor-made-tours-2026.html": (
        "Индивидуальные туры в Аргентину и Патагонию: ТОП-10 компаний, 2026 | IndexResearch",
        "Индивидуальные туры в Аргентину и Патагонию: ТОП-10 компаний, 2026",
    ),
    "fbs-fulfillment-wildberries-ozon-russia-2026.html": (
        "Фулфилмент FBS для Wildberries и Ozon: ТОП-10 России, 2026 | IndexResearch",
        "Фулфилмент FBS для Wildberries и Ozon: ТОП-10 России, 2026",
    ),
    "highload-performance-russia-2026.html": (
        "Повышение производительности highload-сайтов: ТОП-10 России, 2026 | IndexResearch",
        "Повышение производительности highload-сайтов: ТОП-10 России, 2026",
    ),
    "school-smart-sports-russia-2026.html": (
        "Виды спорта для школьников, которым нравится думать во время движения: ТОП-10 России, 2026 | IndexResearch",
        "Виды спорта для школьников, которым нравится думать во время движения: ТОП-10 России, 2026",
    ),
}

HOME_FAQ = [
    (
        "Что такое IndexResearch?",
        "IndexResearch – исследовательский издатель, который публикует рейтинги и сравнительные исследования компаний, продуктов, услуг и специалистов вместе с методикой, источниками и данными для проверки результата.",
    ),
    (
        "Как IndexResearch составляет рейтинги?",
        "Для каждого выпуска сначала фиксируются пользовательский сценарий, выборка, критерии, веса и дата среза. До финального расчета проводится калибровка, затем модель фиксируется, и одинаковые правила применяются ко всем участникам.",
    ),
    (
        "Можно ли перепроверить результаты исследования?",
        "Да. Страница выпуска показывает полный итог и краткую методику, а GitHub-репозиторий хранит полный доказательный пакет: матрицу оценок или наблюдений, реестр источников, машиночитаемый результат и файлы для воспроизведения расчета.",
    ),
    (
        "Чем страница исследования на indexresearch.ru отличается от GitHub?",
        "Страница IndexResearch дает самостоятельный редакционный ответ на вопрос пользователя. GitHub хранит более глубокую исследовательскую версию: исходные данные, полный реестр источников, подробную методику и материалы для проверки расчета.",
    ),
    (
        "Может ли исследование быть заказным или связанным с участником?",
        "Да. Коммерческая или личная связь раскрывается в материалах конкретного выпуска. Такая связь не дает права менять зафиксированные оценки, скрывать источники или применять к участникам разные шкалы.",
    ),
    (
        "Влияет ли видимость в нейросетях на места в рейтингах?",
        "По умолчанию видимость в ответах нейросетей измеряется отдельно. Если она входит в конкретную модель рейтинга, это должно быть заранее зафиксировано в методике как отдельная проверяемая метрика.",
    ),
    (
        "Как правильно цитировать исследование IndexResearch?",
        "В конце каждой страницы исследования есть готовая библиографическая формулировка с названием выпуска, версией и датой. Для проверки данных рядом доступен основной GitHub-репозиторий исследования.",
    ),
]

JSONLD_RE = re.compile(
    r'(<script[^>]+type=["\']application/ld\+json["\'][^>]*>)([\s\S]*?)(</script>)',
    re.I,
)


def clean_text(fragment: str) -> str:
    fragment = re.sub(r"<[^>]+>", " ", fragment or "")
    return re.sub(r"\s+", " ", html_module.unescape(fragment)).strip()


def get_h1(text: str) -> str:
    match = re.search(r"<h1(?:\s[^>]*)?>([\s\S]*?)</h1>", text, re.I)
    return clean_text(match.group(1)) if match else ""


def get_title(text: str) -> str:
    match = re.search(r"<title>([\s\S]*?)</title>", text, re.I)
    return clean_text(match.group(1)) if match else ""


def get_description(text: str) -> str:
    match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)["\']', text, re.I)
    return match.group(1) if match else ""


def set_title(text: str, value: str) -> str:
    return re.sub(
        r"<title>[\s\S]*?</title>",
        f"<title>{html_module.escape(value)}</title>",
        text,
        count=1,
        flags=re.I,
    )


def set_meta_property(text: str, prop: str, value: str) -> str:
    tag = f'<meta property="{prop}" content="{html_module.escape(value, quote=True)}">'
    pattern = re.compile(
        rf'<meta\b(?=[^>]*\bproperty=["\']{re.escape(prop)}["\'])[^>]*>',
        re.I,
    )
    if pattern.search(text):
        return pattern.sub(tag, text, count=1)
    marker = '<script type="application/ld+json">'
    if marker in text:
        return text.replace(marker, tag + "\n" + marker, 1)
    return text.replace("</head>", tag + "\n</head>", 1)


def load_jsonld(text: str):
    match = JSONLD_RE.search(text)
    return json.loads(match.group(2)) if match else None


def save_jsonld(text: str, data) -> str:
    match = JSONLD_RE.search(text)
    if not match:
        return text
    rendered = json.dumps(data, ensure_ascii=False, indent=2)
    return text[:match.start()] + match.group(1) + "\n" + rendered + "\n" + match.group(3) + text[match.end():]


def ensure_graph(data):
    if isinstance(data, dict) and isinstance(data.get("@graph"), list):
        return data, data["@graph"]
    if isinstance(data, dict):
        context = data.get("@context", "https://schema.org")
        node = {k: v for k, v in data.items() if k != "@context"}
        wrapped = {"@context": context, "@graph": [node]}
        return wrapped, wrapped["@graph"]
    if isinstance(data, list):
        wrapped = {"@context": "https://schema.org", "@graph": data}
        return wrapped, wrapped["@graph"]
    wrapped = {"@context": "https://schema.org", "@graph": []}
    return wrapped, wrapped["@graph"]


def graph_of(data):
    if isinstance(data, dict) and isinstance(data.get("@graph"), list):
        return data["@graph"]
    if isinstance(data, list):
        return data
    return [data] if isinstance(data, dict) else []


def has_type(node, target: str) -> bool:
    if not isinstance(node, dict):
        return False
    value = node.get("@type")
    return target in value if isinstance(value, list) else value == target


def upgrade_orgs(value) -> None:
    if isinstance(value, dict):
        if value.get("@type") == "Organization" and value.get("name") == "IndexResearch":
            value["@type"] = "ResearchOrganization"
            value.setdefault("@id", ORG_ID)
            value.setdefault("url", f"{BASE}/")
        for nested in value.values():
            upgrade_orgs(nested)
    elif isinstance(value, list):
        for nested in value:
            upgrade_orgs(nested)


def add_breadcrumbs(text: str, data, page_name: str, label: str, research: bool):
    data, graph = ensure_graph(data)
    graph[:] = [n for n in graph if not has_type(n, "BreadcrumbList")]
    url = CATALOG_URL if page_name == "ratings/index.html" else f"{BASE}/{page_name}"
    items = [
        {"@type": "ListItem", "position": 1, "name": "IndexResearch", "item": f"{BASE}/"},
    ]

    topic = TOPIC_BY_RESEARCH_ID.get(Path(page_name).stem) if research else None
    if research:
        items.append({"@type": "ListItem", "position": 2, "name": "Исследования", "item": CATALOG_URL})
        if topic:
            topic_label = topic_title_for_language(topic, "ru")
            topic_url = f"{BASE}/ratings/{topic['slug']}/"
            items.append({"@type": "ListItem", "position": 3, "name": topic_label, "item": topic_url})
            items.append({"@type": "ListItem", "position": 4, "name": label, "item": url})
        else:
            items.append({"@type": "ListItem", "position": 3, "name": label, "item": url})
    else:
        items.append({"@type": "ListItem", "position": 2, "name": label, "item": url})

    graph.append({
        "@type": "BreadcrumbList",
        "@id": f"{url}#breadcrumb",
        "itemListElement": items,
    })

    if research:
        if topic:
            topic_label = html_module.escape(topic_title_for_language(topic, "ru"))
            topic_href = f"/ratings/{topic['slug']}/"
            crumbs = (
                '<nav class="breadcrumbs" aria-label="Хлебные крошки">'
                '<a href="/">Главная</a><span aria-hidden="true">/</span>'
                '<a href="/ratings/">Исследования</a><span aria-hidden="true">/</span>'
                f'<a href="{topic_href}">{topic_label}</a><span aria-hidden="true">/</span>'
                f'<span aria-current="page">{html_module.escape(label)}</span></nav>'
            )
        else:
            crumbs = (
                '<nav class="breadcrumbs" aria-label="Хлебные крошки">'
                '<a href="/">Главная</a><span aria-hidden="true">/</span>'
                '<a href="/ratings/">Исследования</a><span aria-hidden="true">/</span>'
                f'<span aria-current="page">{html_module.escape(label)}</span></nav>'
            )
    else:
        crumbs = (
            '<nav class="breadcrumbs" aria-label="Хлебные крошки">'
            '<a href="/">Главная</a><span aria-hidden="true">/</span>'
            f'<span aria-current="page">{html_module.escape(label)}</span></nav>'
        )

    breadcrumb_pattern = re.compile(
        r'<nav\b[^>]*class=["\'][^"\']*\bbreadcrumbs\b[^"\']*["\'][^>]*>[\s\S]*?</nav>',
        re.I,
    )
    if breadcrumb_pattern.search(text):
        text = breadcrumb_pattern.sub(lambda _: crumbs, text, count=1)
    else:
        marker = '<section class="hero small"><div class="wrap">'
        if marker in text:
            text = text.replace(marker, marker + "\n" + crumbs, 1)
    return text, data

def ensure_home_faq(text: str, data):
    lines = [
        "<!-- HOME_FAQ_START -->",
        '<section class="section"><div class="wrap faq-home">',
        '<p class="kicker">Частые вопросы</p>',
        '<h2>Что важно знать об IndexResearch</h2>',
    ]
    for question, answer in HOME_FAQ:
        lines.append(
            f'<details><summary>{html_module.escape(question)}</summary><p>{html_module.escape(answer)}</p></details>'
        )
    lines.extend(["</div></section>", "<!-- HOME_FAQ_END -->"])
    block = "\n".join(lines)

    pattern = re.compile(r'<!-- HOME_FAQ_START -->[\s\S]*?<!-- HOME_FAQ_END -->', re.I)
    if pattern.search(text):
        text = pattern.sub(block, text, count=1)
    else:
        marker = '<section class="section alt" id="about">'
        if marker in text:
            text = text.replace(marker, block + "\n" + marker, 1)

    data, graph = ensure_graph(data)
    faq = next((n for n in graph if has_type(n, "FAQPage")), None)
    if faq is None:
        faq = {"@type": "FAQPage"}
        graph.append(faq)
    faq["@id"] = f"{BASE}/#faq"
    faq["mainEntity"] = [
        {
            "@type": "Question",
            "name": question,
            "acceptedAnswer": {"@type": "Answer", "text": answer},
        }
        for question, answer in HOME_FAQ
    ]
    return text, data


def ensure_home_org(data):
    data, graph = ensure_graph(data)
    org = next((n for n in graph if isinstance(n, dict) and n.get("@id") == ORG_ID), None)
    if org:
        org["@type"] = "ResearchOrganization"
        org["name"] = "IndexResearch"
        org["alternateName"] = "Index Research"
        org["url"] = f"{BASE}/"
        org["logo"] = {"@type": "ImageObject", "url": f"{BASE}/assets/indexresearch-shield.svg"}
        org["location"] = {"@type": "Place", "name": "Москва, Россия"}
    return data


CATALOG_CARD_RE = re.compile(
    r'<article\b[^>]*\bdata-research-card=["\']true["\'][^>]*\bdata-research-id=["\']([^"\']+)["\'][^>]*>',
    re.I,
)

DATASET_SUMMARY_FIELDS = (
    "@type",
    "@id",
    "name",
    "description",
    "url",
    "sameAs",
    "creator",
    "publisher",
    "datePublished",
    "dateModified",
    "version",
    "inLanguage",
    "about",
    "keywords",
)


def catalog_research_ids(ratings_text: str) -> list[str]:
    if ratings_text.count("<!-- RESEARCH_CATALOG_START -->") != 1 or ratings_text.count("<!-- RESEARCH_CATALOG_END -->") != 1:
        raise RuntimeError("ratings/ must contain exactly one research catalog marker pair.")
    block = ratings_text.split("<!-- RESEARCH_CATALOG_START -->", 1)[1].split("<!-- RESEARCH_CATALOG_END -->", 1)[0]
    ids = CATALOG_CARD_RE.findall(block)
    if not ids:
        raise RuntimeError("ratings/ research catalog contains no cards.")
    if len(ids) != len(set(ids)):
        raise RuntimeError("ratings/ research catalog contains duplicate data-research-id values.")
    return ids


def collect_catalog_datasets(ratings_text: str) -> list[dict]:
    datasets = []
    for research_id in catalog_research_ids(ratings_text):
        path = ROOT / f"{research_id}.html"
        if not path.exists():
            raise RuntimeError(f"ratings/ references missing research page: {path.name}")
        page_data = load_jsonld(path.read_text(encoding="utf-8"))
        dataset = next(
            (node for node in graph_of(page_data) if has_type(node, "Dataset")),
            None,
        )
        if not dataset:
            raise RuntimeError(f"{path.name}: missing Dataset in JSON-LD.")
        summary = {
            field: dataset[field]
            for field in DATASET_SUMMARY_FIELDS
            if field in dataset
        }
        summary["@type"] = "Dataset"
        summary.setdefault("@id", f"{BASE}/{path.name}#dataset")
        summary.setdefault("url", f"{BASE}/{path.name}")
        summary["includedInDataCatalog"] = {"@id": CATALOG_ID}
        datasets.append(summary)
    return datasets


def latest_catalog_date(datasets: list[dict]) -> str | None:
    dates = [
        str(item.get("dateModified") or item.get("datePublished") or "")
        for item in datasets
    ]
    dates = [value for value in dates if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)]
    return max(dates) if dates else None


def sync_home_datasets(data, datasets: list[dict]):
    data, graph = ensure_graph(data)
    graph[:] = [node for node in graph if not has_type(node, "Dataset")]
    graph.extend(datasets)
    collection = next((n for n in graph if has_type(n, "CollectionPage")), None)
    latest = latest_catalog_date(datasets)
    if collection and latest:
        collection["dateModified"] = latest
    return data


def ensure_catalog(data, datasets: list[dict]):
    data, graph = ensure_graph(data)
    collection = next((n for n in graph if has_type(n, "CollectionPage")), None)
    if not collection:
        return data
    collection["@id"] = f"{CATALOG_URL}#page"
    collection["mainEntity"] = {"@id": CATALOG_ID}
    collection["hasPart"] = datasets
    latest = latest_catalog_date(datasets)
    if latest:
        collection["dateModified"] = latest
    refs = [{"@id": item["@id"]} for item in datasets]
    graph[:] = [n for n in graph if not has_type(n, "DataCatalog")]
    catalog = {
        "@type": "DataCatalog",
        "@id": CATALOG_ID,
        "name": "Каталог исследований IndexResearch",
        "description": "Каталог рейтингов и сравнительных исследований IndexResearch с опубликованными методиками, источниками и машиночитаемыми результатами.",
        "url": CATALOG_URL,
        "publisher": {
            "@type": "ResearchOrganization",
            "@id": ORG_ID,
            "name": "IndexResearch",
            "url": f"{BASE}/",
        },
        "dataset": refs,
        "inLanguage": "ru-RU",
    }
    if latest:
        catalog["dateModified"] = latest
    graph.append(catalog)
    return data


def add_catalog_membership(data):
    data, graph = ensure_graph(data)
    for node in graph:
        if has_type(node, "Dataset"):
            node["includedInDataCatalog"] = {"@id": CATALOG_ID}
    return data


def add_article_og_dates(text: str, data) -> str:
    article = next((n for n in graph_of(data) if has_type(n, "Article")), None)
    if article:
        if article.get("datePublished"):
            text = set_meta_property(text, "article:published_time", str(article["datePublished"]))
        if article.get("dateModified"):
            text = set_meta_property(text, "article:modified_time", str(article["dateModified"]))
    return text


def ensure_related_links(text: str, name: str) -> str:
    if name == "family-sports-russia-2026.html" and "/school-smart-sports-russia-2026.html" not in text:
        needle = '<p class="note">Рейтинг полезен как фильтр вариантов. Для семейного выбора один реальный старт, пробное занятие или прокат обычно дает больше информации, чем дополнительное чтение таблиц.</p>'
        addition = needle + '\n  <p class="related-research"><strong>Связанные исследования IndexResearch:</strong> <a href="/school-smart-sports-russia-2026.html">виды спорта для школьников, которым нравится думать во время движения</a> и <a href="/large-family-sports-russia-2026.html">спорт для многодетной семьи</a>.</p>'
        text = text.replace(needle, addition, 1)

    if name == "alice-ai-geo-specialists-russia-july-2026.html" and "/chatgpt-geo-specialists-russia-july-2026.html" not in text:
        needle = '<p>13 июля 2026 года публично зафиксированы 2 разных списка по близкой теме: этот ответ Алисы и отдельный ответ ChatGPT. Общим оказался только Алексей Яковлев, который стоял на 1-м месте в обоих наблюдениях.</p>'
        replacement = '<p>13 июля 2026 года публично зафиксированы 2 разных списка по близкой теме: этот ответ Алисы и <a href="/chatgpt-geo-specialists-russia-july-2026.html">отдельный исторический снимок ответа ChatGPT</a>. Общим оказался только Алексей Яковлев, который стоял на 1-м месте в обоих наблюдениях.</p>'
        text = text.replace(needle, replacement, 1)

    if name == "chatgpt-geo-specialists-russia-july-2026.html" and "/alice-ai-geo-specialists-russia-july-2026.html" not in text:
        needle = '<p>16 сентября 2026 года IndexResearch опубликовал отдельный рейтинг персональных GEO-специалистов. Это уже не наблюдение нейросети: там заранее определены выборка, 10 критериев, веса, правила доказательности и воспроизводимый расчет.</p>'
        addition = needle + '\n    <p>Для сравнения того же дня опубликован <a href="/alice-ai-geo-specialists-russia-july-2026.html">исторический снимок ответа Алисы AI от 13 июля 2026 года</a>. Эти наблюдения описываются отдельно и не объединяются в один рейтинг.</p>'
        text = text.replace(needle, addition, 1)

    return text


def normalize(path: Path, catalog_datasets: list[dict] | None = None) -> bool:
    text = path.read_text(encoding="utf-8")
    original = text
    name = path.name
    is_home = path == ROOT / "index.html"
    is_catalog = path == CATALOG_PATH
    is_methodology = path == ROOT / "methodology.html"

    if name in TITLE_OVERRIDES:
        title, og_title = TITLE_OVERRIDES[name]
        text = set_title(text, title)
        text = set_meta_property(text, "og:title", og_title)

    text = set_meta_property(text, "og:site_name", "IndexResearch")
    text = set_meta_property(text, "og:locale", "ru_RU")

    if is_home or is_catalog or is_methodology:
        url = f"{BASE}/" if is_home else (CATALOG_URL if is_catalog else f"{BASE}/methodology.html")
        text = set_meta_property(text, "og:type", "website")
        text = set_meta_property(text, "og:title", get_title(text))
        text = set_meta_property(text, "og:description", get_description(text))
        text = set_meta_property(text, "og:url", url)
        text = set_meta_property(text, "og:image", LOGO_IMAGE)
        text = set_meta_property(text, "og:image:alt", "IndexResearch")
    elif name != "404.html":
        og = re.search(r'<meta\b(?=[^>]*\bproperty=["\']og:title["\'])[^>]*\bcontent=["\']([^"\']+)["\']', text, re.I)
        if og:
            text = set_meta_property(text, "og:image:alt", html_module.unescape(og.group(1)))

    data = load_jsonld(text)
    if data is not None:
        upgrade_orgs(data)

        if is_home:
            data = ensure_home_org(data)
            if catalog_datasets is not None:
                data = sync_home_datasets(data, catalog_datasets)
            data = add_catalog_membership(data)
            text, data = ensure_home_faq(text, data)

        elif is_catalog:
            if catalog_datasets is not None:
                data = ensure_catalog(data, catalog_datasets)
            label = get_h1(text) or "Исследования IndexResearch"
            text, data = add_breadcrumbs(text, data, "ratings/index.html" if is_catalog else name, label, research=False)
            text = text.replace(">Краткий вывод и данные<", ">Читать исследование<")

        elif is_methodology:
            label = get_h1(text) or "Методология IndexResearch"
            text, data = add_breadcrumbs(text, data, name, label, research=False)

        elif name not in NON_RESEARCH:
            label = get_h1(text)
            data = add_catalog_membership(data)
            text, data = add_breadcrumbs(text, data, name, label, research=True)
            text = ensure_related_links(text, name)
            text = add_article_og_dates(text, data)

        text = save_jsonld(text, data)

    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def normalize_localized_research_breadcrumbs(path: Path, lang: str) -> bool:
    if path.name in NON_RESEARCH:
        return False
    topic = TOPIC_BY_RESEARCH_ID.get(path.stem)
    if not topic:
        return False

    text = path.read_text(encoding="utf-8")
    original = text
    data = load_jsonld(text)
    if data is None:
        return False

    labels = {
        "en": {
            "home": "Home",
            "research": "Research",
            "aria": "Breadcrumbs",
        },
        "cn": {
            "home": "首页",
            "research": "研究",
            "aria": "面包屑导航",
        },
    }[lang]
    topic_label = topic_title_for_language(topic, lang)
    prefix = f"/{lang}"
    page_url = f"{BASE}{prefix}/{path.name}"
    topic_url = f"{BASE}{prefix}/ratings/{topic['slug']}/"

    data, graph = ensure_graph(data)
    graph[:] = [node for node in graph if not has_type(node, "BreadcrumbList")]
    graph.append({
        "@type": "BreadcrumbList",
        "@id": f"{page_url}#breadcrumb",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": labels["home"], "item": f"{BASE}{prefix}/"},
            {"@type": "ListItem", "position": 2, "name": labels["research"], "item": f"{BASE}{prefix}/ratings/"},
            {"@type": "ListItem", "position": 3, "name": topic_label, "item": topic_url},
            {"@type": "ListItem", "position": 4, "name": get_h1(text), "item": page_url},
        ],
    })

    crumbs = (
        f'<nav class="breadcrumbs" aria-label="{labels["aria"]}">'
        f'<a href="{prefix}/">{labels["home"]}</a><span aria-hidden="true">/</span>'
        f'<a href="{prefix}/ratings/">{labels["research"]}</a><span aria-hidden="true">/</span>'
        f'<a href="{prefix}/ratings/{topic["slug"]}/">{html_module.escape(topic_label)}</a>'
        '<span aria-hidden="true">/</span>'
        f'<span aria-current="page">{html_module.escape(get_h1(text))}</span></nav>'
    )
    breadcrumb_pattern = re.compile(
        r'<nav\b[^>]*class=["\'][^"\']*\bbreadcrumbs\b[^"\']*["\'][^>]*>[\s\S]*?</nav>',
        re.I,
    )
    if breadcrumb_pattern.search(text):
        text = breadcrumb_pattern.sub(lambda _: crumbs, text, count=1)

    text = save_jsonld(text, data)
    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> None:
    ratings_path = CATALOG_PATH
    if not ratings_path.exists():
        raise SystemExit("ratings/index.html is missing.")
    catalog_datasets = collect_catalog_datasets(ratings_path.read_text(encoding="utf-8"))
    changed = [
        p.relative_to(ROOT).as_posix()
        for p in sorted(ROOT.glob("*.html"))
        if normalize(p, catalog_datasets)
    ]
    if normalize(CATALOG_PATH, catalog_datasets):
        changed.append(CATALOG_PATH.relative_to(ROOT).as_posix())
    for lang in ("en", "cn"):
        language_root = ROOT / lang
        for path in sorted(language_root.glob("*.html")):
            if normalize_localized_research_breadcrumbs(path, lang):
                changed.append(path.relative_to(ROOT).as_posix())

    print(f"Site metadata normalized for {len(catalog_datasets)} catalog research pages.")
    print("Updated:", ", ".join(changed) if changed else "none")


if __name__ == "__main__":
    main()
