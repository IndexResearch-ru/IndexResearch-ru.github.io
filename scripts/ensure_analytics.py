#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SHARED = '<script src="/assets/analytics.js" defer></script>'
NOSCRIPT = '''<!-- Yandex.Metrika noscript fallback -->
<noscript><div><img src="https://mc.yandex.ru/watch/112773213" style="position:absolute; left:-9999px;" alt="" /></div></noscript>'''
FAVICONS = '''<!-- IndexResearch favicons -->
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/svg+xml" href="/assets/indexresearch-shield.svg">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="#0E3455">
<meta name="msapplication-TileColor" content="#ffffff">
<meta name="msapplication-TileImage" content="/mstile-150x150.png">
<!-- /IndexResearch favicons -->'''

OLD_SCRIPT_RE = re.compile(
    r'<!-- Yandex\.Metrika counter -->\s*'
    r'<script type="text/javascript">[\s\S]*?</script>\s*(?=</head>)',
    re.MULTILINE,
)
OLD_NOSCRIPT_RE = re.compile(
    r'<noscript><div><img src="https://mc\.yandex\.ru/watch/112773213"[\s\S]*?</div></noscript>\s*'
    r'<!-- /Yandex\.Metrika counter -->\s*',
    re.MULTILINE,
)
NORMALIZED_NOSCRIPT_RE = re.compile(
    r'<!-- Yandex\.Metrika noscript fallback -->\s*'
    r'<noscript><div><img src="https://mc\.yandex\.ru/watch/112773213"[\s\S]*?</div></noscript>\s*',
    re.MULTILINE,
)
ANY_METRIKA_NOSCRIPT_RE = re.compile(
    r'<noscript><div><img src="https://mc\.yandex\.ru/watch/112773213"[\s\S]*?</div></noscript>\s*',
    re.MULTILINE,
)
FAVICON_BLOCK_RE = re.compile(
    r'<!-- IndexResearch favicons -->[\s\S]*?<!-- /IndexResearch favicons -->\s*',
    re.MULTILINE,
)

changed = []
for path in sorted(ROOT.glob("*.html")):
    text = path.read_text(encoding="utf-8")
    original = text

    text = OLD_SCRIPT_RE.sub("", text)
    text = OLD_NOSCRIPT_RE.sub("", text)
    text = NORMALIZED_NOSCRIPT_RE.sub("", text)
    # Remove any orphaned/duplicated fallback left by parallel page generators.
    text = ANY_METRIKA_NOSCRIPT_RE.sub("", text)
    text = re.sub(r'\s*<script src="/assets/analytics\.js" defer></script>\s*', "\n", text)
    text = FAVICON_BLOCK_RE.sub("", text)

    if "</head>" not in text or "<body>" not in text:
        raise SystemExit(f"{path.name}: missing </head> or <body>")

    text = text.replace("</head>", f"  {FAVICONS}\n  {SHARED}\n</head>", 1)
    text = text.replace("<body>", f"<body>\n{NOSCRIPT}", 1)

    if text != original:
        path.write_text(text, encoding="utf-8")
        changed.append(path.name)

if changed:
    print("Analytics normalized:", ", ".join(changed))
else:
    print("Analytics already normalized on all HTML pages.")
