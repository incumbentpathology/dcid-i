#!/usr/bin/env python3
"""Build incumbentpathology.org from the repository's Markdown.

    pip install markdown
    python3 site/build.py            # writes _site/

The site is generated; edit conditions/, cases/ and CONTRIBUTING.md instead.
"""

import html
import json
import re
import shutil
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
SITE = Path(__file__).resolve().parent
OUT = ROOT / "_site"
DOMAIN = "https://incumbentpathology.org"
REPO = "https://github.com/incumbentpathology/dcid-i"

TITLE = "Pathologies of Incumbency"
SUBTITLE = "Diagnostic Criteria for Incumbent Disorders"
MANUAL = "DCID-I"
INSTITUTE = "Institute for the Study of Incumbent Pathologies"
CATEGORY = ("F67", "Early signs of incumbent distress")
DESCRIPTION = "Diagnostic Criteria for Incumbent Disorders, First Edition. A clinical reference for the early signs of incumbent distress."
ART = {"F67.1": "copium", "F67.2": "convulsio", "F67.3": "ave", "F67.4": "delirium"}
FONTS = "https://fonts.googleapis.com/css2?family=Courier+Prime&family=Sorts+Mill+Goudy:ital@0;1&display=swap"


# ---------- parsing ----------

def split_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    return meta, m.group(2)


def code_key(code):
    return [int(n) if n.isdigit() else n for n in code[1:].split(".")]


def strip_md(s):
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    return re.sub(r"[*_`]", "", s)


def load_conditions():
    out = []
    for p in (ROOT / "conditions").glob("*.md"):
        meta, body = split_frontmatter(p.read_text())
        body = re.sub(r"^\s*# .*\n", "", body, count=1)
        body = re.sub(r"^\s*\*Common name:\*.*\n", "", body, count=1)
        features = re.search(r"## \d+\. Diagnostic Features\n\n(.+?)\n", body)
        out.append({
            "code": meta["code"], "name": meta["name"], "common": meta.get("common_name"),
            "file": p.name, "url": f"/{meta['code']}/", "body": body,
            "subcodes": re.findall(r"\*\*(F\d+\.\d{2,}) ([^:*]+?):?\*\*", body),
            "summary": strip_md(features.group(1)) if features else "",
        })
    return sorted(out, key=lambda c: code_key(c["code"]))


def load_cases():
    out = []
    for p in sorted((ROOT / "cases").glob("*.md")):
        if p.name.startswith("_") or p.name == "README.md":
            continue
        meta, body = split_frontmatter(p.read_text())
        body = re.sub(r"^\s*# .*\n", "", body, count=1)
        out.append({
            "file": p.name, "title": meta.get("title", p.stem), "date": meta.get("date_observed", ""),
            "findings": re.findall(r"F\d+(?:\.\d+)?", meta.get("findings", "")),
            "url": f"/cases/{p.stem}/", "body": body,
        })
    return out


# ---------- rendering ----------

def md(text, links):
    """Render Markdown, rewriting repository links to site URLs."""
    def fix(m):
        label, href = m.group(1), m.group(2)
        path, _, frag = href.partition("#")
        name = Path(path).name
        if name in links:
            href = links[name] + (f"#{frag}" if frag else "")
        elif path.endswith((".md", ".yml")) or path == "LICENSE":
            href = f"{REPO}/blob/master/{path.lstrip('./')}"
        return f"[{label}]({href})"
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", fix, text)
    out = markdown.markdown(text, extensions=["tables", "sane_lists", "toc"])
    return re.sub(r"\b(F\d{2}(?:\.\d+)?)\b(?![^<]*>)", r'<span class="code-ref">\1</span>', out)


def page(title, body, path, conditions, here=None, description=DESCRIPTION, image="/cards/dcid-i.png", art=False):
    full = TITLE if title == TITLE else f"{title} · {TITLE}"
    url = DOMAIN + path
    rail = "".join(
        f'<a href="{c["url"]}"{" class=here" if c["code"] == here else ""}>{c["code"]}</a>' for c in conditions
    )
    script = '<script src="/art.js" defer></script>' if art else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(full)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="{TITLE}">
<meta property="og:title" content="{html.escape(full)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{DOMAIN}{image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(full)}">
<meta name="twitter:description" content="{html.escape(description)}">
<meta name="twitter:image" content="{DOMAIN}{image}">
<link rel="icon" href="/seal-600.png"><link rel="apple-touch-icon" href="/seal-600.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="/style.css">
{script}
</head>
<body>
<nav class="rail" aria-label="Conditions"><a href="/"{" class=here" if here == "home" else ""}>F67</a>{rail}<hr><a href="/cases/">Cases</a><a href="/lookup/">Lookup</a></nav>
<main>
{body}
</main>
<footer class="colophon">
  <nav><a href="/">Classification</a><a href="/cases/">Casebook</a><a href="/lookup/">Code lookup</a><a href="/contribute/">Contribute</a><a href="/about/">About</a></nav>
  <p>{INSTITUTE} · {MANUAL}, First Edition. A parody of clinical diagnostic manuals; it diagnoses companies, not people.</p>
</footer>
</body>
</html>
"""


def write(path, content):
    target = OUT / path.strip("/") if path.endswith(".html") else OUT / path.strip("/") / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)


def head(code, name, common=None, cat=None):
    common_html = f'<p class="common">{html.escape(common)}</p>' if common else ""
    cat_html = f'<p class="cat">{cat}</p>' if cat else ""
    code_html = f'<span class="mono">{code}</span>' if code else ""
    return f'<header class="entry-head">{code_html}<h1>{html.escape(name)}</h1>{common_html}{cat_html}</header>'


# ---------- build ----------

def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for f in ("style.css", "art.js", "seal.png", "seal-600.png"):
        shutil.copy(SITE / f, OUT / f)
    shutil.copytree(ROOT / "cards", OUT / "cards")
    (OUT / "CNAME").write_text("incumbentpathology.org\n")

    conditions, cases = load_conditions(), load_cases()
    links = {c["file"]: c["url"] for c in conditions}
    links.update({c["file"]: c["url"] for c in cases})
    links.update({"CONTRIBUTING.md": "/contribute/", "README.md": "/", "_template.md": f"{REPO}/blob/master/cases/_template.md"})
    cited = {}
    for k in cases:
        for f in k["findings"]:
            cited.setdefault(f[:5], []).append(k)
    P = lambda *a, **kw: page(*a, conditions=conditions, **kw)

    # Title page and contents
    toc = "".join(
        f'<a href="{c["url"]}"><span class="mono">{c["code"]}</span><span class="latin">{html.escape(c["name"])}</span>'
        + (f'<span class="common">{html.escape(c["common"])}</span>' if c["common"] else "") + "</a>"
        for c in conditions
    )
    home = f"""
<section class="cover">
  <h1 class="spaced">Pathologies<br>of<br>Incumbency</h1>
  <p class="subtitle">{SUBTITLE}</p>
  <canvas class="art" data-art="copium" aria-hidden="true"></canvas>
  <p class="credits"><img class="seal" src="/seal.png" alt="Seal of the {INSTITUTE}"><br>{INSTITUTE}<br>First Edition · For clinical use</p>
</section>
<section class="contents">
  <p class="category"><span class="mono">{CATEGORY[0]}</span>{CATEGORY[1]}</p>
  <div class="toc">{toc}</div>
  <p class="reserved"><span class="mono">F68–F69</span> &nbsp;Reserved</p>
</section>"""
    write("/", P(TITLE, home, "/", here="home", art=True))

    # Conditions
    for i, c in enumerate(conditions):
        prev_c = conditions[i - 1] if i else None
        next_c = conditions[i + 1] if i + 1 < len(conditions) else None
        listed = "".join(f'<li><a href="{k["url"]}">{html.escape(k["title"])}</a></li>' for k in cited.get(c["code"], []))
        cases_html = f'<section class="cited"><h2>In the casebook</h2><ul>{listed}</ul></section>' if listed else ""
        link = lambda x, arrow_left: (
            f'<a href="{x["url"]}">{"← " if arrow_left else ""}<span class="mono">{x["code"]}</span> <span class="latin">{html.escape(x["name"])}</span>{"" if arrow_left else " →"}</a>'
            if x else "<span></span>")
        body = f"""
<article>
  <canvas class="art" data-art="{ART.get(c["code"], "copium")}" aria-hidden="true"></canvas>
  {head(c["code"], c["name"], c["common"], f'{CATEGORY[0]} · {CATEGORY[1]}')}
  <div class="prose">{md(c["body"], links)}</div>
  {cases_html}
  <nav class="pager">{link(prev_c, True)}{link(next_c, False)}</nav>
</article>"""
        title = f'{c["code"]} {c["name"]}' + (f' ({c["common"]})' if c["common"] else "")
        card = f'/cards/{c["code"]}.png' if (ROOT / "cards" / f'{c["code"]}.png').exists() else "/cards/dcid-i.png"
        write(c["url"], P(title, body, c["url"], here=c["code"], description=c["summary"] or DESCRIPTION, image=card, art=True))

    # Casebook
    items = "".join(
        f'<a href="{k["url"]}"><span class="mono">{" · ".join(k["findings"])}</span><span class="latin">{html.escape(k["title"])}</span><span class="common">Observed {html.escape(k["date"])}</span></a>'
        for k in cases
    )
    casebook = f"""
{head("", "Casebook", None, "Patients are recorded by type, never by name")}
<section class="contents"><div class="toc">{items}</div>
<p class="reserved">To submit a case, see <a href="/contribute/">Contribute</a>.</p></section>"""
    write("/cases/", P("Casebook", casebook, "/cases/"))
    for k in cases:
        body = f'<article>{head(" · ".join(k["findings"]), k["title"], None, "Case report · observed " + html.escape(k["date"]))}<div class="prose">{md(k["body"], links)}</div></article>'
        write(k["url"], P(k["title"], body, k["url"], description=f'Case report citing {", ".join(k["findings"])}.'))

    # Contribute
    _, contrib = split_frontmatter((ROOT / "CONTRIBUTING.md").read_text())
    contrib = re.sub(r"^\s*# .*\n", "", contrib, count=1)
    contrib += f"\n\nSubmissions are received as [issues and pull requests]({REPO}/issues/new/choose).\n"
    write("/contribute/", P("Contribute", f'<article>{head("", "Contribute", None, "Guidance for attending physicians")}<div class="prose">{md(contrib, links)}</div></article>', "/contribute/"))

    # About
    about = f"""
<article>{head("", "About this manual")}
<div class="prose">
<p><em>{TITLE}</em> is the first edition of the {SUBTITLE} ({MANUAL}), issued by the {INSTITUTE} (ISIP).</p>
<h2>Codes</h2>
<p>Codes follow the clinical convention: the category (F67), the condition (F67.3) and, where a coding note applies, a final digit set by the specifier (F67.30, commercial type).</p>
<h2>Forks and local editions</h2>
<p>Fork freely. Conditions added under an existing category take codes ending in <code>.8</code> (“other specified”), e.g. <code>F67.8x</code>, so they do not collide with codes assigned here. An edition for another kind of patient opens its own chapter rather than renumbering F67.</p>
<h2>License</h2>
<p>Text and cards are licensed <a href="{REPO}/blob/master/LICENSE">CC BY 4.0</a>. Reuse, adapt and fork, with attribution to <em>{TITLE} ({MANUAL})</em> and a link to incumbentpathology.org. Source: <a href="{REPO}">{REPO.replace("https://", "")}</a>.</p>
<h2>Notice</h2>
<p><em>{TITLE}</em> is a parody of clinical diagnostic manuals, and the {INSTITUTE} is fictional. The manual diagnoses companies, not people, and is not affiliated with any medical or psychiatric organization. Any resemblance to a company you have been watching is a matter for your own judgment.</p>
</div></article>"""
    write("/about/", P("About", about, "/about/"))

    # Code lookup
    index = {CATEGORY[0]: {"url": "/", "label": CATEGORY[1]}}
    for c in conditions:
        index[c["code"]] = {"url": c["url"], "label": c["name"]}
        for sub, label in c["subcodes"]:
            index[sub] = {"url": c["url"], "label": f'{c["name"]}, {label.strip().lower()}'}
    lookup = f"""
{head("", "Code lookup", None, "Enter a code")}
<form class="lookup" onsubmit="go(event)"><input id="q" autocomplete="off" placeholder="F67.30" aria-label="Code"><button>Consult</button></form>
<p id="result" class="result"></p>
<section class="contents"><div class="toc" id="all"></div></section>
<script>
const CODES = {json.dumps(index)};
function go(e) {{
  e.preventDefault();
  const c = CODES[document.getElementById("q").value.trim().toUpperCase().replace(/\\s+/g, "")];
  if (c) location.href = c.url;
  else document.getElementById("result").textContent = "No such code in this edition. Codes ending in .8 are reserved for local editions.";
}}
document.getElementById("all").innerHTML = Object.entries(CODES).sort().map(([k, v]) =>
  `<a href="${{v.url}}"><span class="mono">${{k}}</span><span class="common">${{v.label}}</span></a>`).join("");
</script>"""
    write("/lookup/", P("Code lookup", lookup, "/lookup/"))

    write("/404.html", P("Not classified", f'<section class="cover">{head("", "Not classified", None, "No entry exists at this address")}<canvas class="art" data-art="delirium" aria-hidden="true"></canvas><p class="credits"><a href="/">Return to the classification</a></p></section>', "/404.html", art=True))

    print(f"built {len(conditions)} conditions, {len(cases)} cases -> {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    build()
