"""Build the multi-page GitHub Pages site in docs/ from content/*.md.

    python3 -I build.py            # strict: missing figure/image/video, unlisted link or banned char fails
    python3 -I build.py --draft    # missing parts become visible placeholders

Each content/<slug>.md starts with a JSON front-matter block between lines '---' with keys:
  title, kicker, standfirst, description, hero (img file in docs/img), hero_caption, order (int)
Body markers (each on its own line):
  <!-- FIG:name -->                    templates/figures/name.html (SVG or HTML+JS partial)
  <!-- IMG:file.jpg|caption -->        a photo from docs/img
  <!-- VIDEO:file.mp4|caption -->      docs/media/file.mp4 (+ file.vtt captions, file.jpg poster if present)
  <!-- MOTION:name -->                 alias of FIG for animated partials
Sources: content/<slug>.sources.json = [{"org","title","url","date"}]. Every external link in the page must be listed.
"""
import json, re, sys
from pathlib import Path
import markdown

ROOT = Path(__file__).resolve().parent
C, T, D = ROOT / "content", ROOT / "templates", ROOT / "docs"
DRAFT = "--draft" in sys.argv
BANNED = {"—": "em dash", "–": "en dash"}
BANNED_WORDS = re.compile(r"\b(recorded|recording|my understanding from the tape|transcript)\b", re.I)
DISCLAIMER = ("Written as an attendee. Speaker remarks are paraphrased in my own words. "
              "Educational only, not investment, legal or tax advice. Not affiliated with or endorsed by "
              "Harvard Business School or the HBS ETA Club. Facts as of 15 November 2026.")
OWN = ("https://wilsonwu-ai.github.io/", "https://github.com/wilsonwu-ai/")
LINK_RE = re.compile(r"\]\((https?://[^)\s]+)\)")
MARK = re.compile(r"(?:<p>\s*)?<!-- (FIG|MOTION|IMG|VIDEO):([^>]+?) -->(?:\s*</p>)?")
errors = []

def fail(msg):
    if DRAFT: print("note:", msg)
    else: errors.append(msg)

def load(p):
    raw = p.read_text()
    m = re.match(r"---\n(.*?)\n---\n", raw, re.S)
    if not m: sys.exit(f"{p.name}: missing front matter")
    meta = json.loads(m.group(1)); body = raw[m.end():]
    for ch, lab in BANNED.items():
        if ch in raw: fail(f"{p.name} line {raw[:raw.index(ch)].count(chr(10))+1}: {lab}")
    for mm in BANNED_WORDS.finditer(body):
        fail(f"{p.name}: banned word '{mm.group(0)}' (attended, never recorded)")
    return meta, body

def marker(kind, arg, slug):
    if kind in ("FIG", "MOTION"):
        f = T / "figures" / f"{arg.strip()}.html"
        if not f.exists():
            fail(f"{slug}: figure {arg} missing"); return f'<figure class="fig"><p class="fig-title">[{arg} pending]</p></figure>'
        txt = f.read_text()
        for ch, lab in BANNED.items():
            if ch in txt: fail(f"figure {arg}: {lab}")
        return txt
    file, _, cap = arg.partition("|")
    file = file.strip()
    if kind == "IMG":
        if not (D / "img" / file).exists(): fail(f"{slug}: image {file} missing")
        return f'<figure class="photo"><img src="img/{file}" alt="{cap.strip()}" loading="lazy"><figcaption>{cap.strip()}</figcaption></figure>'
    stem = file.rsplit(".", 1)[0]
    if not (D / "media" / file).exists(): fail(f"{slug}: video {file} missing")
    poster = f' poster="media/{stem}.jpg"' if (D / "media" / f"{stem}.jpg").exists() else ""
    track = f'<track kind="captions" src="media/{stem}.vtt" srclang="en" label="English" default>' if (D / "media" / f"{stem}.vtt").exists() else ""
    return (f'<figure class="video"><video controls preload="metadata" playsinline{poster}>'
            f'<source src="media/{file}" type="video/mp4">{track}</video><figcaption>{cap.strip()}</figcaption></figure>')

def main():
    pages = []
    for p in sorted(C.glob("*.md")):
        meta, body = load(p); meta["slug"] = p.stem; meta["body"] = body; pages.append(meta)
    pages.sort(key=lambda m: m.get("order", 99))
    tpl = (T / "page.html").read_text()
    for pg in pages:
        slug = pg["slug"]; href = "index.html" if slug == "index" else f"{slug}.html"; pg["href"] = href
    for pg in pages:
        slug = pg["slug"]
        srcf = C / f"{slug}.sources.json"
        sources = json.loads(srcf.read_text()) if srcf.exists() else []
        known = {s["url"] for s in sources if s.get("url")}
        for u in LINK_RE.findall(pg["body"]):
            if u not in known and not u.startswith(OWN): fail(f"{slug}: link not in sources: {u}")
        html = markdown.markdown(pg["body"], extensions=["tables", "attr_list", "md_in_html"], output_format="html5")
        html = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', html)
        html = html.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
        html = MARK.sub(lambda m: marker(m.group(1), m.group(2), slug), html)
        nav = "".join(f'<a href="{q["href"]}"{" aria-current=\"page\"" if q is pg else ""}>{q.get("nav", q["title"])}</a>' for q in pages)
        others = "".join(f'<li><a href="{q["href"]}">{q["title"]}</a></li>' for q in pages if q is not pg)
        series = f'<nav class="series" aria-label="More from the conference"><h2>More from the conference</h2><ul>{others}</ul></nav>'
        srcs = "<ol>" + "".join(f'<li>{s.get("org","")}, <a href="{s["url"]}" target="_blank" rel="noopener">{s["title"]}</a>{", " + s["date"] if s.get("date") else ""}.</li>' for s in sources) + "</ol>" if sources else "<p>Speaker remarks from the session itself.</p>"
        hero = ""
        if pg.get("hero"):
            if not (D / "img" / pg["hero"]).exists(): fail(f"{slug}: hero {pg['hero']} missing")
            hero = f'<figure class="hero-img photo portrait"><img src="img/{pg["hero"]}" alt="{pg.get("hero_caption","")}"><figcaption>{pg.get("hero_caption","")}</figcaption></figure>'
        scripts = pg.get("scripts", "")
        out = tpl
        for k, v in {"title": pg["title"], "description": pg.get("description", pg["standfirst"]), "kicker": pg["kicker"],
                     "standfirst": pg["standfirst"], "og_image": pg.get("hero", ""), "nav": nav, "hero": hero, "body": html,
                     "series": series, "sources": srcs, "disclaimer": DISCLAIMER,
                     "scripts": "".join(f'<script src="{s}" defer></script>' for s in pg.get("scripts", []))}.items():
            out = out.replace("{{" + k + "}}", v)
        (D / pg["href"]).write_text(out)
        print(f"built docs/{pg['href']}")
    (D / ".nojekyll").write_text("")
    if errors:
        sys.exit("build FAILED:\n  " + "\n  ".join(errors))

main()
