#!/usr/bin/env python3
"""Render DSM-I cards from conditions/*.md.

Writes cards/dsm-i.png (the whole manual, 4:5) and cards/<code>.png (one card
per condition, 16:9). Needs Google Chrome or Chromium; set CHROME to its path
if it is not found automatically.

    python3 render/render.py
"""

import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONDITIONS = ROOT / "conditions"
CARDS = ROOT / "cards"
CSS = (Path(__file__).resolve().parent / "card.css").read_text()

CHROME_CANDIDATES = [
    os.environ.get("CHROME", ""),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
]

LABELS = {"see also": "See also"}


def chrome():
    for c in CHROME_CANDIDATES:
        if c and (Path(c).exists() or shutil.which(c)):
            return c
    sys.exit("Chrome not found. Set CHROME=/path/to/chrome.")


def parse(path):
    text = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        sys.exit(f"{path.name}: missing frontmatter")
    meta = dict(
        (k.strip(), v.strip())
        for k, v in (line.split(":", 1) for line in m.group(1).splitlines() if ":" in line)
    )
    for key in ("code", "name"):
        if key not in meta:
            sys.exit(f"{path.name}: frontmatter needs '{key}'")
    paras = []
    for block in re.split(r"\n\s*\n", m.group(2).strip()):
        block = " ".join(block.split())
        lm = re.match(r"^\*\*(.+?)\.\*\*\s*(.*)$", block)
        label, body = (lm.group(1), lm.group(2)) if lm else (None, block)
        paras.append((label, body))
    return meta, paras


def inline(text):
    """Escape text; render markdown links as their label, codes in red."""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = html.escape(text)
    return re.sub(r"\b([A-Z]\d{2}(?:\.\d+)?)\b", r'<span class="xref">\1</span>', text)


def entry_html(meta, paras, last=False):
    rows = []
    for label, body in paras:
        lab = f'<span class="label">{html.escape(LABELS.get(label.lower(), label))}</span>' if label else ""
        rows.append(f"<p>{lab}{inline(body)}</p>")
    style = ' style="border-bottom:none"' if last else ""
    return (
        f'<section class="entry"{style}><span class="code">{html.escape(meta["code"])}</span>'
        f'<div><h2>{html.escape(meta["name"])}</h2>{"".join(rows)}</div></section>'
    )


HEADER = """
<header>
  <div class="chapter"><span>DSM-I · Diagnostic and Statistical Manual of Incumbent Disorders</span><span>For clinical use</span></div>
  {title}
</header>"""


def book_html(entries):
    body = HEADER.format(title="""
  <h1>Pathologies of Incumbency</h1>
  <div class="block"><span class="code">R67</span><span class="title">Signs of distress in an incumbent</span><span class="note">Fictional findings.</span></div>""")
    body += "".join(entry_html(m, p, last=i == len(entries) - 1) for i, (m, p) in enumerate(entries))
    body += """
<footer><span class="label">Recording</span><span>A case cites one or more finding codes. Record the date, the words or actions observed, and the source. Mark the doctor’s interpretation as an inference.</span></footer>"""
    return page(body, "book", 1200, 1500)


def single_html(meta, paras):
    body = HEADER.format(title="")
    body += entry_html(meta, paras, last=True)
    body += '<footer><span class="label">R67</span><span>Signs of distress in an incumbent. Fictional findings.</span></footer>'
    return page(body, "single", 1200, 675)


def page(body, kind, w, h):
    return (
        f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><style>{CSS}'
        f"html,body{{width:{w}px;height:{h}px}}</style></head>"
        f'<body class="{kind}">{body}</body></html>'
    )


def shoot(browser, markup, out, w, h):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(markup)
        src = f.name
    try:
        subprocess.run(
            [browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
             "--force-device-scale-factor=2", f"--window-size={w},{h}",
             f"--screenshot={out}", f"file://{src}"],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    finally:
        os.unlink(src)
    print(f"wrote {out.relative_to(ROOT)}")


def code_key(meta):
    return [int(n) if n.isdigit() else n for n in re.split(r"[.]", meta["code"][1:])]


def main():
    browser = chrome()
    CARDS.mkdir(exist_ok=True)
    entries = sorted((parse(p) for p in CONDITIONS.glob("*.md")), key=lambda e: code_key(e[0]))
    shoot(browser, book_html(entries), CARDS / "dsm-i.png", 1200, 1500)
    for meta, paras in entries:
        shoot(browser, single_html(meta, paras), CARDS / f"{meta['code']}.png", 1200, 675)


if __name__ == "__main__":
    main()
