"""Offline link and anchor check for the built site (_site)."""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urldefrag, urlparse

ROOT = Path(__file__).resolve().parent.parent / "_site"
BASE = "/agentic-pipelines/"


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links = set(), []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "a" and a.get("name"):
            self.ids.add(a["name"])
        for key in ("href", "src"):
            if a.get(key):
                self.links.append(a[key])


def parse(path):
    p = Page()
    p.feed(path.read_text(encoding="utf-8"))
    return p


pages = {f: parse(f) for f in ROOT.rglob("*.html")}
errors = checked = 0
for f, p in pages.items():
    for link in p.links:
        u = urlparse(link)
        if u.scheme or link.startswith(("//", "mailto:", "data:", "javascript:")):
            continue
        checked += 1
        raw, frag = urldefrag(link)
        if link.startswith("#"):
            target = f
        else:
            rel = unquote(urlparse(raw).path)
            target = ROOT / rel[len(BASE):] if rel.startswith(BASE) else (f.parent / rel if not rel.startswith("/") else ROOT / rel.lstrip("/"))
            if target.is_dir():
                target = target / "index.html"
        if not target.exists():
            print(f"MISSING {f.relative_to(ROOT)} -> {link}")
            errors += 1
        elif frag and target.suffix == ".html" and target in pages and unquote(frag) not in pages[target].ids:
            print(f"ANCHOR  {f.relative_to(ROOT)} -> {link}")
            errors += 1
print(f"checked {checked} local links in {len(pages)} pages; {errors} problems")
sys.exit(1 if errors else 0)
