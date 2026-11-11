"""Pre-render the Mermaid blocks in docs/*.md to static SVG files in site/diagrams/.

Developer tool, not part of the Pages build: the published site loads only the SVGs, so no
script runs in the browser and the strict CSP stays intact. Re-run after editing a diagram:

    python site/render_diagrams.py path/to/mermaid.min.js

The bundle is mermaid 11.12.0 (cdn.jsdelivr.net/npm/mermaid@11.12.0/dist/mermaid.min.js).
Requires `pip install playwright` and Microsoft Edge (or set CHANNEL).
"""
from __future__ import annotations

import hashlib
import os
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "diagrams"
FENCE = re.compile(r"^```mermaid\n(.*?)^```", re.S | re.M)


def key(source: str) -> str:
    return hashlib.sha256(source.strip().encode("utf-8")).hexdigest()[:12]


def main() -> int:
    bundle = Path(sys.argv[1]).resolve()
    OUT.mkdir(exist_ok=True)
    sources = {}
    for md in sorted((ROOT / "docs").rglob("*.md")):
        for match in FENCE.finditer(md.read_text(encoding="utf-8")):
            sources[key(match.group(1))] = match.group(1).strip()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel=os.environ.get("CHANNEL", "msedge"))
        page = browser.new_page()
        page.set_content("<html><body><div id='out'></div></body></html>")
        page.add_script_tag(path=str(bundle))
        page.evaluate("mermaid.initialize({startOnLoad:false,securityLevel:'strict',theme:'neutral',"
                      "flowchart:{htmlLabels:true,useMaxWidth:false},sequence:{useMaxWidth:false},"
                      "themeVariables:{fontFamily:'Segoe UI, Arial, sans-serif',fontSize:'15px',edgeLabelBackground:'#ffffff'}})")
        for name, source in sources.items():
            svg = page.evaluate("""async ([id, src]) => {
                const holder = document.getElementById('out');
                holder.innerHTML = (await mermaid.render(id, src)).svg;
                const node = holder.querySelector('svg');
                const ctx = document.createElement('canvas').getContext('2d');
                ctx.font = '15px Segoe UI, Arial, sans-serif';
                const wrap = (line, max) => {
                    const out = []; let cur = '';
                    for (const word of line.split(/\\s+/)) {
                        const next = cur ? cur + ' ' + word : word;
                        if (cur && ctx.measureText(next).width > max) { out.push(cur); cur = word; } else cur = next;
                    }
                    out.push(cur); return out;
                };
                // foreignObject HTML labels do not load in <img>; replace them with native SVG text
                for (const fo of [...node.querySelectorAll('foreignObject')]) {
                    const w = parseFloat(fo.getAttribute('width')), h = parseFloat(fo.getAttribute('height'));
                    const div = fo.firstElementChild;
                    if (!div || !w || !h) { fo.remove(); continue; }
                    div.querySelectorAll('br').forEach(b => b.replaceWith('\\n'));
                    const raw = div.textContent.split('\\n').map(s => s.trim()).filter(Boolean);
                    const lines = raw.length * 24 >= h ? raw : raw.flatMap(l => wrap(l, w * 1.05));
                    const span = div.querySelector('span');
                    const fill = (span && span.style.color) || div.style.color || '#000';
                    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                    text.setAttribute('text-anchor', 'middle');
                    text.setAttribute('fill', fill);
                    text.setAttribute('font-size', '15');
                    lines.forEach((l, i) => {
                        const t = document.createElementNS('http://www.w3.org/2000/svg', 'tspan');
                        t.setAttribute('x', w / 2);
                        t.setAttribute('y', h / 2 + (i - (lines.length - 1) / 2) * 22.5);
                        t.setAttribute('dominant-baseline', 'central');
                        t.textContent = l;
                        text.appendChild(t);
                    });
                    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
                    if (fo.closest('.edgeLabel')) {
                        const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                        [['width', w + 8], ['height', h], ['x', -4], ['y', 0], ['fill', '#ffffff']].forEach(([k, v]) => bg.setAttribute(k, v));
                        bg.setAttribute('style', 'fill:#ffffff;opacity:1');
                        g.appendChild(bg);
                    }
                    g.appendChild(text);
                    fo.replaceWith(g);
                }
                node.style.background = '#fff';
                node.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
                return new XMLSerializer().serializeToString(node);
            }""", ["d" + name, source])
            (OUT / f"{name}.svg").write_text(svg, encoding="utf-8")
            print(f"{name}.svg")
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
