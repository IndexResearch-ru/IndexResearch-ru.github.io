#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SHARED = '<script src="/assets/analytics.js" defer></script>'
NOSCRIPT = '''<!-- Yandex.Metrika noscript fallback -->
<noscript><div><img src="https://mc.yandex.ru/watch/112773213" style="position:absolute; left:-9999px;" alt="" /></div></noscript>'''

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

changed = []
for path in sorted(ROOT.glob("*.html")):
    text = path.read_text(encoding="utf-8")
    original = text

    text = OLD_SCRIPT_RE.sub("", text)
    text = OLD_NOSCRIPT_RE.sub("", text)
    text = NORMALIZED_NOSCRIPT_RE.sub("", text)
    text = re.sub(r'\s*<script src="/assets/analytics\.js" defer></script>\s*', "\n", text)

    if "</head>" not in text or "<body>" not in text:
        raise SystemExit(f"{path.name}: missing </head> or <body>")

    text = text.replace("</head>", f"  {SHARED}\n</head>", 1)
    text = text.replace("<body>", f"<body>\n{NOSCRIPT}", 1)

    if text != original:
        path.write_text(text, encoding="utf-8")
        changed.append(path.name)

if changed:
    print("Analytics normalized:", ", ".join(changed))
else:
    print("Analytics already normalized on all HTML pages.")
