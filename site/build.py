#!/usr/bin/env python3
"""Build the GitHub Pages site into _site/ from docs/ and .github/workflows/.

Every link is relative so the site works under /<repository>/ project paths.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import posixpath
import re
import shutil
import sys
from pathlib import Path

import markdown
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chrome  # noqa: E402
ROOT = Path(__file__).resolve().parent.parent
SITE_SRC = ROOT / "site"
DOCS = ROOT / "docs"
WORKFLOWS = ROOT / ".github" / "workflows"
REPO = os.environ.get("GITHUB_REPOSITORY", "ChristianPresley/agentic-pipelines")
BASE_PATH = "/" + REPO.split("/", 1)[1] + "/"
BLOB = f"https://github.com/{REPO}/blob/main/"
ACTIONS = f"https://github.com/{REPO}/actions/workflows/"
OUT = ROOT / "_site"

NBSP = "\u00a0"
NNBSP = "\u202f"
FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%232563eb' "
           "stroke-width='2'%3E%3Crect x='2' y='9' width='6' height='6' rx='1.5'/%3E%3Crect x='16' y='2' width='6' height='6' rx='1.5'/%3E"
           "%3Crect x='16' y='16' width='6' height='6' rx='1.5'/%3E%3Cpath d='M8 12H12V5H16M12 12V19H16'/%3E%3C/svg%3E")


# ---------------------------------------------------------------- text helpers
def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def fix_fr(markup: str) -> str:
    """Apply French typography to text nodes (not tags or code)."""
    parts = re.split(r"(<[^>]+>)", markup)
    depth = 0
    out = []
    for part in parts:
        if part.startswith("<"):
            if re.match(r"<(code|pre)\b", part):
                depth += 1
            elif re.match(r"</(code|pre)>", part):
                depth = max(0, depth - 1)
            out.append(part)
            continue
        if depth == 0:
            part = re.sub(r" ([:%])", NBSP + r"\1", part)
            part = re.sub(r" ([;?!])", NNBSP + r"\1", part)
            part = re.sub(r"« ", "«" + NBSP, part)
            part = re.sub(r" »", NBSP + "»", part)
        out.append(part)
    return "".join(out)


def bi(en: str, fr: str) -> str:
    return f'<span class="l-en" lang="en">{en}</span><span class="l-fr" lang="fr">{fix_fr(fr)}</span>'


def bblock(en: str, fr: str) -> str:
    return f'<div class="l-en" lang="en">{en}</div><div class="l-fr" lang="fr">{fix_fr(fr)}</div>'


def bp(en: str, fr: str, css: str = "") -> str:
    extra = f" {css}" if css else ""
    return (f'<p class="l-en{extra}" lang="en">{en}</p>'
            f'<p class="l-fr{extra}" lang="fr">{fix_fr(fr)}</p>')


def label(en: str, fr: str) -> str:
    return bi(en + ":", fr + " :")


def h2(en: str, fr: str, ident: str = "") -> str:
    attr = f' id="{ident}"' if ident else ""
    return f"<h2{attr}>{bi(en, fr)}</h2>"


def h3(en: str, fr: str) -> str:
    return f"<h3>{bi(en, fr)}</h3>"


def link(href: str, en: str, fr: str | None = None, external: bool = False) -> str:
    label = bi(en, fr) if fr else en
    rel = ' rel="noopener noreferrer"' if external else ""
    return f'<a href="{esc(href)}"{rel}>{label}</a>'


def gh(path: str, en: str = "", fr: str | None = None) -> str:
    return link(BLOB + path, en or path, fr, external=True)


# ------------------------------------------------------------------- layout
NAV = [
    ("home", "", "Home", "Accueil"),
    ("pipeline", "pipeline/", "Pipeline explorer", "Explorateur du pipeline"),
    ("workflows", "workflows/", "Workflows", "Workflows"),
    ("agents", "agents/", "Agentic workflows", "Workflows agentiques"),
    ("release", "release/", "Releases", "Publication"),
    ("setup", "setup/", "Setup", "Configuration"),
]


def rel_root(path: str) -> str:
    depth = path.count("/")
    return "../" * depth


def layout(path: str, key: str, title_en: str, title_fr: str, eyebrow: tuple[str, str],
           lead: tuple[str, str] | None, body: str, extra_main_class: str = "", root: str | None = None) -> str:
    r = root if root is not None else rel_root(path)
    url = page_url(path)
    PAGES[url] = (title_en, title_fr)
    lead_html = f"<p>{bi(*lead)}</p>" if lead else ""
    sha = os.environ.get("GITHUB_SHA", "")[:7]
    built = f" · {sha}" if sha else ""
    crumbs = [f'<li><a href="{r}">{bi("Home", "Accueil")}</a></li>']
    section = next((n for n in NAV if n[0] == key), None)
    if key != "home" and section and url != section[1]:
        crumbs.append(f'<li><a href="{r}{section[1]}">{bi(section[2], section[3])}</a></li>')
    crumbs.append(f'<li><span aria-current="page">{bi(esc(title_en), esc(title_fr))}</span></li>')
    breadcrumb = (f'<nav class="breadcrumb" {chrome.attr("Breadcrumb", "Fil d’Ariane")}><ol>{"".join(crumbs)}</ol></nav>'
                  if key != "home" else "")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <meta http-equiv="Content-Security-Policy" content="{CSP}">
  <link rel="icon" href="{FAVICON}">
  <title data-fr="{esc(fix_fr(title_fr))} | agentic-pipelines">{esc(title_en)} | agentic-pipelines</title>
  <script src="{r}assets/boot.js"></script>
  <link rel="stylesheet" href="{r}pipeline/visuals/pipeline-explorer.css">
  <link rel="stylesheet" href="{r}assets/site.css">
  <script src="{r}assets/site-index.js" defer></script>
  <script src="{r}assets/site.js" defer></script>
</head>
<body data-root="{r}">
  <a class="skip" href="#content">{bi("Skip to content", "Aller au contenu")}</a>
  {chrome.sprite()}
  {chrome.header(r, NAV, key)}
  <div class="app-shell">
    <!--SIDENAV:{url}|{r}-->
    <div class="app-body">
    <div class="hero"><div class="wrap">
      {breadcrumb}
      <div class="eyebrow">{bi(*eyebrow)}</div>
      <h1 class="page-title">{bi(esc(title_en), esc(title_fr))}</h1>
      {lead_html}
    </div></div>
  <main id="content" class="wrap {extra_main_class}" tabindex="-1">
{body}
  </main>
  <footer class="site-footer"><div class="wrap">
    <p>{bi("Generated from the repository sources", "Généré à partir des sources du dépôt")}{built}.
    <a href="https://github.com/{REPO}" rel="noopener noreferrer">{bi("Source repository", "Dépôt source")}</a></p>
  </div></footer>
    </div>
  </div>
  {chrome.dialogs()}
</body>
</html>
"""


CSP = "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; base-uri 'none'; form-action 'none'"
PAGES: dict[str, tuple[str, str]] = {}


def page_url(path: str) -> str:
    return path[: -len("index.html")] if path.endswith("index.html") else path


def sidenav_tree() -> list:
    top = [("", *PAGES.get("", ("Home", "Accueil")))]
    for _, href, en, fr in NAV:
        if href:
            top.append((href, en, fr))
    top = [(u, e, f) for u, e, f in top]
    flows = sorted(((u, *t) for u, t in PAGES.items() if u.startswith("workflows/") and u != "workflows/"), key=lambda x: x[1])
    docs = sorted(((u, *t) for u, t in PAGES.items() if u.startswith("pipeline/") and u != "pipeline/"), key=lambda x: x[1])
    return [(("Site", "Site"), top), (("Workflows", "Workflows"), flows), (("Design documents", "Documents de conception"), docs)]


CHIP_ICONS = {"existing": "check-circle", "proposed": "ring", "measured": "info", "warning": "triangle", "mixed": "triangle"}


def chip_icons(markup: str) -> str:
    """Give every status chip a glyph so state never depends on colour alone."""
    return re.sub(r'(<span class="badge (existing|proposed|measured|warning|mixed)">)(?!<svg)',
                  lambda m: m.group(1) + chrome.icon(CHIP_ICONS[m.group(2)], "icon-16"), markup)


def finish_page(path: str, markup: str) -> str:
    """Fill the contents sidebar once every page title is known."""
    def fill(match: re.Match) -> str:
        url, _, root = match.group(1).partition("|")
        return chrome.sidenav(root, url, sidenav_tree())
    markup = re.sub(r' style="text-align: (left|right|center);"', r' class="align-\1"', markup)
    return chip_icons(re.sub(r"<!--SIDENAV:(.*?)-->", fill, markup, count=1))


def search_index() -> str:
    """Command palette data: pages, workflows and explorer areas with EN/FR titles."""
    items = []
    for url, (en, fr) in sorted(PAGES.items()):
        if url == "404.html":
            continue
        group = ("Workflow", "Workflow") if url.startswith("workflows/") and url != "workflows/" else (
            ("Design document", "Document de conception") if url.startswith("pipeline/") and url != "pipeline/" else ("Page", "Page"))
        items.append({"u": url, "t": [en, fr], "g": list(group), "k": "page"})
    for area, en, fr in EXPLORER_AREAS:
        items.append({"u": f"pipeline/#{area}", "t": [f"Explorer: {en}", f"Explorateur : {fr}"], "g": ["Explorer area", "Zone de l’explorateur"], "k": "page"})
    return "window.SITE_INDEX = " + json.dumps(items, ensure_ascii=False, indent=0) + ";\n"


EXPLORER_AREAS = [
    ("overview", "Overview", "Vue d’ensemble"), ("source-build", "Source and build", "Source et build"),
    ("dotnet", ".NET tests", "Tests .NET"), ("api", "API tests", "Tests d’API"), ("workflows", "Workflow tests", "Tests de workflows"),
    ("evidence", "Test records", "Enregistrements de tests"), ("gates", "Quality gates", "Contrôles qualité"),
    ("release", "Release", "Publication"), ("feedback", "Review and reuse", "Revue et réutilisation"),
    ("reports", "Reports", "Rapports"), ("tools", "Tools and logos", "Outils et logos"),
]


# --------------------------------------------------------- workflow analysis
def load_yaml_file(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".md":
        match = re.match(r"---\r?\n(.*?)\r?\n---\r?\n(.*)", text, re.S)
        data = yaml.safe_load(match.group(1)) if match else {}
        return data or {}, text
    return yaml.safe_load(text) or {}, text


def header_comment(text: str) -> str:
    lines = []
    for line in text.splitlines()[:20]:
        if line.startswith("#"):
            text_line = line.lstrip("# ").rstrip()
            letters = sum(c.isalpha() for c in text_line)
            if text_line and letters < len(text_line) * 0.5:
                continue
            lines.append(text_line)
        elif lines and not line.strip():
            continue
        elif re.match(r"^(on|permissions|jobs|env|concurrency):", line):
            break
    return " ".join(part for part in lines if part)


def fmt_value(value: object) -> str:
    if isinstance(value, (list, tuple)):
        return ", ".join(fmt_value(v) for v in value)
    if isinstance(value, dict):
        return "; ".join(f"{k}: {fmt_value(v)}" for k, v in value.items())
    if value is True:
        return "true"
    if value is False:
        return "false"
    return str(value)


def triggers(data: dict) -> list[tuple[str, str]]:
    on = data.get("on", data.get(True))
    if on is None:
        return []
    if isinstance(on, str):
        return [(on, "")]
    if isinstance(on, list):
        return [(item, "") for item in on]
    rows = []
    for event, detail in on.items():
        if isinstance(detail, dict):
            parts = []
            for key, val in detail.items():
                if key == "inputs" and isinstance(val, dict):
                    parts.append("inputs: " + ", ".join(val))
                elif key == "secrets" and isinstance(val, dict):
                    parts.append("secrets: " + ", ".join(val))
                elif key == "outputs" and isinstance(val, dict):
                    parts.append("outputs: " + ", ".join(val))
                else:
                    parts.append(f"{key}: {fmt_value(val)}")
            rows.append((event, "; ".join(parts)))
        elif isinstance(detail, list):
            rows.append((event, fmt_value(detail)))
        else:
            rows.append((event, "" if detail is None else fmt_value(detail)))
    return rows


def perms(value: object) -> str:
    if value is None:
        return "—"
    if value == {} or value == "{}":
        return "none"
    if isinstance(value, str):
        return value
    return ", ".join(f"{k}: {v}" for k, v in value.items())


def artifact_names(jobs: dict) -> list[str]:
    names = []
    for job in jobs.values():
        for step in (job or {}).get("steps", []) or []:
            if "upload-artifact" in str(step.get("uses", "")):
                name = (step.get("with") or {}).get("name")
                if name:
                    names.append(str(name))
    return sorted(set(names))


def secret_names(text: str) -> list[str]:
    names = set(re.findall(r"secrets\.([A-Za-z_][A-Za-z0-9_]*)", text))
    return sorted(names)


CATEGORIES = {
    "ci": ("Build and test", "Compilation et tests"),
    "e2e": ("Build and test", "Compilation et tests"),
    "lint": ("Build and test", "Compilation et tests"),
    "sast": ("Security scanners", "Analyseurs de sécurité"),
    "sca": ("Security scanners", "Analyseurs de sécurité"),
    "secrets-iac": ("Security scanners", "Analyseurs de sécurité"),
    "container": ("Security scanners", "Analyseurs de sécurité"),
    "dast": ("Security scanners", "Analyseurs de sécurité"),
    "fuzz": ("Security scanners", "Analyseurs de sécurité"),
    "scorecard": ("Security scanners", "Analyseurs de sécurité"),
    "pipeline": ("Build and test", "Compilation et tests"),
    "release": ("Release", "Publication"),
    "cut-release": ("Release", "Publication"),
    "governance": ("Governance", "Gouvernance"),
    "agent-audit": ("Governance", "Gouvernance"),
}


class Workflow:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.agentic = path.suffix == ".md"
        self.stem = path.name.split(".")[0]
        self.data, self.text = load_yaml_file(path)
        self.name = self.data.get("name") or self.stem
        self.description = self.data.get("description") or header_comment(self.text)
        self.jobs = self.data.get("jobs") or {}
        if self.agentic:
            self.category = ("Agentic workflows", "Workflows agentiques")
            self.runs_file = f"{self.stem}.lock.yml"
        else:
            self.category = CATEGORIES.get(self.stem, ("Supporting workflows", "Workflows de support"))
            self.runs_file = path.name

    @property
    def source_rel(self) -> str:
        return f".github/workflows/{self.path.name}"

    def triggers_summary(self) -> str:
        return ", ".join(event for event, _ in triggers(self.data))

    def find_line(self, pattern: str, start: int = 1) -> int:
        """1-based line of the first match at or after `start`; falls back to `start`."""
        rx = re.compile(pattern)
        for number, text in enumerate(self.text.splitlines(), 1):
            if number >= start and rx.search(text):
                return number
        return start

    def src(self, line: int, inner: str, tip: str) -> str:
        href = f"{BLOB}{self.source_rel}#L{line}"
        return f'<a class="src-link" href="{href}" rel="noopener noreferrer" title="{esc(tip)}">{inner}</a>'


def collect_workflows() -> list[Workflow]:
    files = sorted(p for p in WORKFLOWS.iterdir()
                   if p.is_file() and not p.name.endswith(".lock.yml") and p.suffix in (".yml", ".md"))
    return [Workflow(p) for p in files]


def table(headers: list[tuple[str, str]], rows: list[list[str]], caption: tuple[str, str],
          caption_class: str = "") -> str:
    head = "".join(f'<th scope="col">{bi(*h)}</th>' for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    cls = f' class="{caption_class}"' if caption_class else ""
    return (f'<div class="table-scroll" role="region" tabindex="0" aria-label="{esc(caption[0])}">'
            f'<table class="ref-table"><caption{cls}>{bi(*caption)}</caption><thead><tr>{head}</tr></thead>'
            f"<tbody>{body}</tbody></table></div>")


def code(value: object) -> str:
    return f"<code>{esc(value)}</code>"


def workflow_page(wf: Workflow) -> str:
    path = f"workflows/{wf.stem}.html"
    parts = []
    badge_class = "existing" if not wf.agentic else "proposed"
    parts.append(f'<div class="chips"><span class="badge {badge_class}">{bi(*wf.category)}</span></div>')
    if wf.agentic and wf.stem in AGENTS:
        parts.append(bblock(f'<p class="intro">{AGENTS[wf.stem][0]}</p>', f'<p class="intro">{AGENTS[wf.stem][1]}</p>'))
    elif wf.description:
        parts.append(f'<p class="intro" lang="en">{esc(wf.description)}</p>')
    links = [f"<li>{gh(wf.source_rel, 'Source: ' + wf.path.name)}</li>"]
    if wf.agentic:
        links.append(f"<li>{gh('.github/workflows/' + wf.runs_file, 'Compiled lock file')}</li>")
    links.append(f'<li>{link(ACTIONS + wf.runs_file, "Latest runs", "Dernières exécutions", external=True)}</li>')
    parts.append(f'<ul class="links">{"".join(links)}</ul>')

    on_line = wf.find_line(r"^\"?(on|true)\"?\s*:")
    rows = [[wf.src(wf.find_line(rf"^\s+\"?{re.escape(e)}\"?\s*:", on_line), code(e), f"{e} in {wf.path.name}"), esc(d) or "—"]
            for e, d in triggers(wf.data)]
    parts.append(h2("Triggers", "Déclencheurs", "triggers"))
    parts.append(table([("Event", "Événement"), ("Filters and inputs", "Filtres et entrées")], rows,
                       ("Triggers", "Déclencheurs")) if rows else bp("None declared.", "Aucun déclencheur déclaré."))

    parts.append(h2("Permissions", "Autorisations", "permissions"))
    perm_line = wf.find_line(r"^permissions\s*:")
    parts.append(f'<p>{label("Workflow level", "Niveau du workflow")} {wf.src(perm_line, code(perms(wf.data.get("permissions"))), f"permissions in {wf.path.name}")}</p>')
    if wf.jobs:
        job_rows = []
        for jid, job in wf.jobs.items():
            job = job or {}
            needs = job.get("needs")
            jl = wf.find_line(rf"^\s{{2}}\"?{re.escape(str(jid))}\"?\s*:", wf.find_line(r"^jobs\s*:"))

            def at(key: str, inner: str, jl: int = jl, jid: str = jid) -> str:
                return wf.src(wf.find_line(rf"^\s+({key})\s*:", jl + 1) if key else jl, inner, f"{jid} in {wf.path.name}")
            job_rows.append([
                at("", code(jid)),
                at("name", esc(job["name"])) if job.get("name") else "—",
                at("runs-on|uses", code(fmt_value(job.get("runs-on", job.get("uses", "—"))))),
                at("needs", code(fmt_value(needs))) if needs else "—",
                at("permissions", code(perms(job.get("permissions")))),
                at("if", code(job["if"])) if job.get("if") else "—",
            ])
        parts.append(h2("Jobs", "Tâches", "jobs"))
        parts.append(table([("ID", "ID"), ("Name", "Nom"), ("Runs on / reusable", "Exécuteur / réutilisable"),
                            ("Needs", "Dépend de"), ("Permissions", "Autorisations"), ("Condition", "Condition")],
                           job_rows, ("Jobs", "Tâches")))
        outs = []
        for jid, job in wf.jobs.items():
            for out in ((job or {}).get("outputs") or {}):
                jl = wf.find_line(rf"^\s{{2}}\"?{re.escape(str(jid))}\"?\s*:", wf.find_line(r"^jobs\s*:"))
                outs.append([wf.src(jl, code(jid), f"{jid} in {wf.path.name}"),
                             wf.src(wf.find_line(rf"^\s+{re.escape(str(out))}\s*:", jl), code(out), f"{out} in {wf.path.name}")])
        arts = artifact_names(wf.jobs)
        parts.append(h2("Outputs and artifacts", "Sorties et artefacts", "outputs"))
        call = (wf.data.get("on", wf.data.get(True)) or {})
        call_outs = list((((call.get("workflow_call") or {}) if isinstance(call, dict) else {}).get("outputs") or {}))
        if call_outs:
            parts.append(f'<p>{label("Reusable workflow outputs", "Sorties du workflow réutilisable")} {", ".join(code(o) for o in call_outs)}</p>')
        if outs:
            parts.append(table([("Job", "Tâche"), ("Output", "Sortie")], outs, ("Job outputs", "Sorties des tâches")))
        if arts:
            parts.append(f'<p>{label("Uploaded artifacts", "Artefacts téléversés")} {", ".join(code(a) for a in arts)}</p>')
        if not (outs or arts or call_outs):
            parts.append(bp("No job outputs or uploaded artifacts.", "Aucune sortie de tâche ni aucun artefact téléversé."))
    if wf.agentic:
        parts.append(agent_section(wf))
    if wf.stem in TELEMETRY:
        parts.append(telemetry_section(wf))
    secrets = secret_names(wf.text)
    if secrets:
        parts.append(h2("Secrets referenced", "Secrets référencés", "secrets"))
    if secrets:
        parts.append(h2("Secrets referenced", "Secrets référencés", "secrets"))
        parts.append(f'<p>{", ".join(code(s) for s in secrets)}</p>')
        parts.append(bp("Names only. Values stay in repository or organization secrets.",
                        "Noms uniquement. Les valeurs restent dans les secrets du dépôt ou de l’organisation."))
    return layout(path, "workflows", str(wf.name), str(wf.name), ("Workflow reference", "Référence du workflow"),
                  None, "\n".join(parts))


TELEMETRY = {"observability-otel": "exporter", "pipeline": "traced", "scorecard": "traced", "release": "traced"}


def telemetry_section(wf: Workflow) -> str:
    """Document what the observability workflow exports; the site itself collects no visitor data."""
    parts = [h2("Telemetry", "Télémétrie", "telemetry")]
    if TELEMETRY[wf.stem] == "exporter":
        rows = [
            [bi("Trigger", "Déclencheur"), bi("Completion of Pipeline, Scorecard or Release on main or a v* tag", "Fin de Pipeline, Scorecard ou Release sur main ou un tag v*")],
            [bi("Signal", "Signal"), bi("Traces: one span per workflow run, job and step", "Traces : un span par exécution, tâche et étape")],
            [bi("Protocol", "Protocole"), code("OTLP")],
            [bi("Exporter", "Exportateur"), code("corentinmusard/otel-cicd-action v4.2.0")],
            [bi("Endpoint", "Point de terminaison"), bi("Secret " + "<code>OTLP_ENDPOINT</code> (headers in <code>OTLP_HEADERS</code>). Export is skipped when it is not set.",
                                                       "Secret <code>OTLP_ENDPOINT</code> (en-têtes dans <code>OTLP_HEADERS</code>). L’export est ignoré s’il n’est pas défini.")],
            [bi("Permissions", "Autorisations"), code("actions: read, contents: read")],
        ]
        parts.append(table([("Setting", "Paramètre"), ("Value", "Valeur")], rows, ("Trace export", "Export des traces")))
    else:
        parts.append(bp("Runs of this workflow are exported as OpenTelemetry traces by the Observability workflow when an OTLP endpoint is configured.",
                        "Les exécutions de ce workflow sont exportées sous forme de traces OpenTelemetry par le workflow Observability lorsqu’un point de terminaison OTLP est configuré."))
        parts.append(f'<p>{link("observability-otel.html", "Observability (OpenTelemetry)", "Observability (OpenTelemetry)")}</p>')
    parts.append(bp("This site does not collect visitor analytics or send data to third parties; display preferences stay in your browser.",
                    "Ce site ne collecte aucune statistique de visite et n’envoie aucune donnée à des tiers ; les préférences d’affichage restent dans votre navigateur."))
    return "".join(parts)


def agent_section(wf: Workflow) -> str:
    data = wf.data
    parts = [h2("Agent configuration", "Configuration de l’agent", "agent")]
    rows = [[bi("Engine", "Moteur"), code(data.get("engine", "—"))],
            [bi("Network", "Réseau"), code(fmt_value(data.get("network", "—")))],
            [bi("Timeout (minutes)", "Durée maximale (minutes)"), code(data.get("timeout-minutes", "—"))],
            [bi("Agent permissions", "Autorisations de l’agent"), code(perms(data.get("permissions")))],
            [bi("Tools", "Outils"), code(fmt_value(data.get("tools", "—")))]]
    parts.append(table([("Setting", "Paramètre"), ("Value", "Valeur")], rows, ("Agent settings", "Paramètres de l’agent")))
    safe = data.get("safe-outputs") or {}
    imports = data.get("imports") or []
    if safe or imports:
        srows = []
        for kind, cfg in safe.items():
            srows.append([code(kind), esc(fmt_value(cfg)) if cfg else "—"])
        parts.append(h2("Safe outputs", "Sorties sécurisées (safe-outputs)", "safe-outputs"))
        if srows:
            parts.append(table([("Operation", "Opération"), ("Limits", "Limites")], srows,
                               ("Safe outputs", "Sorties sécurisées")))
        if imports:
            parts.append(f'<p>{label("Imports", "Importations")} {", ".join(code(i) for i in imports)}</p>')
    return "".join(parts)


def stat_strip(items: list[tuple], prefix: str = "") -> str:
    """Each card opens a scrollable breakout pane listing the workflows behind its number."""
    cells, templates = [], []
    for index, (n, en, fr, rows) in enumerate(items):
        tid = f"stat-list-{index}"
        entries = "".join(
            f'<li><a href="{prefix}{wf.stem}.html">{esc(wf.name)}</a><span class="stat-note">{note}</span></li>'
            for wf, note in rows)
        templates.append(f'<template id="{tid}"><ul class="stat-list">{entries}</ul></template>')
        label = f'<span class="stat-label">{bi(en, fr)}</span>'
        cells.append(f'<li><button type="button" class="stat" data-stat-list="{tid}" data-title-en="{esc(en)}" data-title-fr="{esc(fix_fr(fr))}" '
                     f'data-count="{n}" aria-haspopup="dialog">{label}<span class="stat-value">{n}</span></button></li>')
    return f'<ul class="stat-strip">{"".join(cells)}</ul>{"".join(templates)}'


def workflow_stats(wfs: list["Workflow"]) -> list[tuple]:
    def plain(wf: "Workflow") -> str:
        return code(wf.path.name)
    scheduled = [wf for wf in wfs if any(event == "schedule" for event, _ in triggers(wf.data))]
    return [
        (len(wfs), "Workflows", "Workflows", [(wf, plain(wf)) for wf in wfs]),
        (sum(1 for wf in wfs if wf.agentic), "Agentic", "Agentiques", [(wf, plain(wf)) for wf in wfs if wf.agentic]),
        (sum(1 for wf in wfs if wf.category[0] == "Security scanners"), "Security scanners", "Analyseurs de sécurité",
         [(wf, plain(wf)) for wf in wfs if wf.category[0] == "Security scanners"]),
        (len(scheduled), "Scheduled", "Planifiés", [(wf, esc(wf.triggers_summary())) for wf in scheduled]),
        (sum(len(wf.jobs) for wf in wfs), "Jobs", "Tâches",
         [(wf, code(str(j))) for wf in wfs for j in wf.jobs]),
    ]


CHART_STYLES = [("solid", "workflow"), ("hatch", "alert"), ("dots", "package"), ("cross", "bot"), ("vert", "wrench")]


def category_chart(groups: dict, order: list[str]) -> str:
    cats = sorted(groups.items(), key=lambda kv: order.index(kv[0][0]) if kv[0][0] in order else len(order))
    total = sum(len(v) for _, v in cats)
    top = max(len(v) for _, v in cats)
    rows, twin, templates = [], [], []
    for idx, ((cat, items), (pat, glyph)) in enumerate(zip(cats, CHART_STYLES)):
        n = len(items)
        tid = f"chart-list-{idx}"
        entries = "".join(f'<li><a href="{wf.stem}.html">{esc(wf.name)}</a><span class="stat-note">{code(wf.path.name)}</span></li>' for wf in items)
        templates.append(f'<template id="{tid}"><ul class="stat-list">{entries}</ul></template>')
        rows.append(f'<li><button type="button" class="chart-row" data-stat-list="{tid}" data-title-en="{esc(cat[0])}" data-title-fr="{esc(fix_fr(cat[1]))}" data-count="{n}" aria-haspopup="dialog">'
                    f'<span class="chart-label">{chrome.icon(glyph, "icon-16")}{bi(*cat)}</span>'
                    f'<span class="chart-track"><span class="chart-bar pat-{pat} w{max(5, round(n * 20 / top) * 5)}" aria-hidden="true"></span><span class="chart-count">{n}<small>{round(n * 100 / total)}%</small>{chrome.icon("chevron-right", "icon-16")}</span></span></button></li>')
        twin.append([bi(*cat), f'<span class="num">{n}</span>', f'<span class="num">{round(n * 100 / total)}%</span>'])
    top_cat = max(cats, key=lambda kv: len(kv[1]))[0]
    summary = bblock(
        f"<p class=\"chart-summary\">{total} workflows in {len(cats)} categories; the largest is {esc(top_cat[0])} with {top}.</p>",
        f"<p class=\"chart-summary\">{total} workflows dans {len(cats)} catégories ; la plus grande est {esc(top_cat[1])} avec {top}.</p>")
    data = table([("Category", "Catégorie"), ("Workflows", "Workflows"), ("Share", "Part")], twin,
                 ("Workflows by category", "Workflows par catégorie"), "sr-only-caption")
    return (f'<figure class="chart"><figcaption>{bi("Workflows by category", "Workflows par catégorie")}</figcaption>'
            f'{summary}<ul class="chart-rows">            {"".join(rows)}</ul>{"".join(templates)}'
            f'<details class="chart-data"><summary>{bi("View as data table", "Voir sous forme de tableau")}</summary>{data}</details></figure>')

def workflows_index(wfs: list[Workflow]) -> str:
    parts = [bblock(
        "<p>One page per workflow, generated from <code>.github/workflows</code>: triggers, jobs, permissions, outputs, a link to the source and a link to the latest runs.</p>",
        "<p>Une page par workflow, générée à partir de <code>.github/workflows</code> : déclencheurs, tâches, autorisations, sorties, lien vers la source et lien vers les dernières exécutions.</p>")]
    groups: dict[tuple[str, str], list[Workflow]] = {}
    for wf in wfs:
        groups.setdefault(wf.category, []).append(wf)
    order = ["Build and test", "Security scanners", "Release", "Governance", "Agentic workflows", "Supporting workflows"]
    parts.append(stat_strip(workflow_stats(wfs)))
    parts.append(category_chart(groups, order))
    for cat, items in sorted(groups.items(), key=lambda kv: order.index(kv[0][0]) if kv[0][0] in order else len(order)):
        rows = []
        for wf in items:
            rows.append([
                f'<a href="{wf.stem}.html">{esc(wf.name)}</a>', code(wf.path.name),
                esc(wf.triggers_summary()) or "—",
                link(ACTIONS + wf.runs_file, "Latest runs", "Dernières exécutions", external=True),
            ])
        parts.append(h2(*cat))
        parts.append(table([("Workflow", "Workflow"), ("File", "Fichier"), ("Triggers", "Déclencheurs"),
                            ("Runs", "Exécutions")], rows, cat, "sr-only-caption"))
    return layout("workflows/index.html", "workflows", "Workflow reference", "Référence des workflows",
                  ("Reference", "Référence"), None, "\n".join(parts))


# ----------------------------------------------------------- prose pages
AGENTS = {
    "security-triage": (
        "Runs after the Pipeline workflow completes on <code>main</code>. Pre-steps download that run’s <code>findings-*</code> artifacts and group new findings. The agent opens at most 10 issues, one per rule or CVE, that expire after 30 days.",
        "S’exécute après la fin du workflow Pipeline sur <code>main</code>. Les étapes préalables téléchargent les artefacts <code>findings-*</code> de cette exécution et regroupent les nouvelles anomalies. L’agent ouvre au plus 10 tickets, un par règle ou CVE, qui expirent après 30 jours."),
    "pr-security-reviewer": (
        "Posts one security review comment on each pull request. Pull requests from forks are skipped.",
        "Publie un commentaire de revue de sécurité par pull request. Les pull requests issues de forks sont ignorées."),
    "daily-security-report": (
        "Publishes a daily Discussion in the <code>Security</code> category and sends a short summary to Slack and Teams.",
        "Publie chaque jour une discussion dans la catégorie <code>Security</code> et envoie un résumé court à Slack et à Teams."),
    "release-readiness": (
        "Dispatched by the Release workflow before the approval gate. Opens a GO / NO-GO issue with gate results, changes since the last release and a reviewer checklist.",
        "Déclenché par le workflow Release avant l’étape d’approbation. Ouvre un ticket GO / NO-GO avec les résultats des contrôles, les changements depuis la dernière version publiée et une liste de vérification pour les relecteurs."),
    "release-notes": (
        "Dispatched by the Release workflow after publication. Prepends a Highlights section to the GitHub Release notes.",
        "Déclenché par le workflow Release après la publication. Ajoute une section Highlights en tête des notes de la version GitHub."),
    "security-remediation": (
        "Run manually with a <code>security-finding</code> issue number. Implements a minimal fix with tests, verifies it with <code>dotnet test</code> and opens a pull request that closes the issue.",
        "Exécuté manuellement avec le numéro d’un ticket <code>security-finding</code>. Implémente un correctif minimal accompagné de tests, le vérifie avec <code>dotnet test</code> et ouvre une pull request qui ferme le ticket."),
    "pipeline-failure-analyst": (
        "Runs when CI, E2E, Container or Release fails on <code>main</code> or on a tag (not on pull requests). Classifies the root cause and opens one deduplicated <code>pipeline-failure</code> issue, or comments on the existing one.",
        "S’exécute lorsque CI, E2E, Container ou Release échoue sur <code>main</code> ou sur un tag (pas sur les pull requests). Classe la cause racine et ouvre un seul ticket <code>pipeline-failure</code> dédupliqué, ou commente le ticket existant."),
}


AGENTIC_VISUALS = {
 "alt": {
  "en": {
   "cmp": "Side-by-side comparison of a legacy deterministic pipeline and GitHub Agentic Workflows in eight areas: failed runs, duplicate findings, explaining findings, fixing, release decision, reporting, release notes, and limits and safety. The table below is the text alternative.",
   "run": "The five steps of one agent run: trigger, prepare, agent, safe outputs and people. It also lists what an agent cannot do. The list below is the text alternative."
  },
  "fr": {
   "cmp": "Comparaison côte à côte d’un pipeline classique déterministe et des GitHub Agentic Workflows dans huit domaines : exécutions en échec, anomalies en double, explication des anomalies, correction, décision de publication, rapports, notes de version, limites et sécurité. Le tableau ci-dessous est l’alternative textuelle.",
   "run": "Les cinq étapes d’une exécution d’agent : déclencheur, préparation, agent, sorties sécurisées et personnes. L’image indique aussi ce qu’un agent ne peut pas faire. La liste ci-dessous est l’alternative textuelle."
  }
},
 "cmp": {
  "en": {
   "title": "Beyond pass/fail: what agents add",
   "sub": "The same events and the same scanners. The difference is what happens after a result arrives.",
   "cols": [
    "LEGACY DETERMINISTIC PIPELINE",
    "GITHUB AGENTIC WORKFLOW"
   ],
   "rows": [
    [
     "Failed run",
     "The step exits non-zero. A person opens the logs and works out why.",
     "The failure analyst reads the failed jobs, names a root-cause class and opens one issue with evidence and a suggested fix."
    ],
    [
     "Duplicate findings",
     "Each run reports again unless dedupe logic is written by hand.",
     "Triage groups findings by rule or CVE and skips any that already have an issue. At most 10 new issues per run."
    ],
    [
     "Explaining a finding",
     "A rule ID, a file and a line from the scanner.",
     "The issue states the impact, lists affected locations and gives remediation steps."
    ],
    [
     "Fixing",
     "A person writes the fix, tests it and opens the pull request.",
     "A person starts the remediation agent. It makes the smallest fix and a test, runs dotnet test and opens one pull request."
    ],
    [
     "Release decision",
     "The gate passes or fails. The approver collects the evidence by hand.",
     "The readiness agent turns gates, changes and open findings into a GO or NO-GO issue. A person still approves production."
    ],
    [
     "Reporting",
     "A pass or fail status for each run.",
     "A daily discussion: findings by severity, scanner health, trend against yesterday, top 5 actions."
    ],
    [
     "Release notes",
     "A generated changelog that lists merged pull requests.",
     "Highlights, security fixes, upgrade notes and verify commands are added above the generated changelog."
    ],
    [
     "Limits and safety",
     "Fixed permissions in YAML. The same behaviour every run.",
     "Read-only agent job. Writes only through declared outputs with maximums and expiry. Untrusted text is data. Network allow-list."
    ]
   ],
   "band_title": "What stays deterministic here",
   "band": [
    [
     "Scanners and tests",
     "They produce the findings the agents read."
    ],
    [
     "Release gates",
     "The gates job blocks on open critical or high findings."
    ],
    [
     "Production approval",
     "A person approves the production environment."
    ],
    [
     "Compiled workflows",
     "Lock files are compiled from the Markdown source."
    ]
   ]
  },
  "fr": {
   "title": "Au-delà de réussi/échoué : l’apport des agents",
   "sub": "Mêmes événements, mêmes analyseurs. La différence : ce qui se passe une fois le résultat connu.",
   "cols": [
    "PIPELINE CLASSIQUE DÉTERMINISTE",
    "WORKFLOW AGENTIQUE GITHUB"
   ],
   "rows": [
    [
     "Exécution en échec",
     "L’étape se termine avec un code d’erreur. Une personne ouvre les journaux et cherche la cause.",
     "L’analyste lit les tâches en échec, nomme une classe de cause racine et ouvre un ticket avec preuves et correctif suggéré."
    ],
    [
     "Anomalies en double",
     "Chaque exécution les signale à nouveau, sauf logique de dédoublonnage écrite à la main.",
     "Le tri regroupe par règle ou CVE et ignore celles qui ont déjà un ticket. 10 nouveaux tickets au plus par exécution."
    ],
    [
     "Expliquer une anomalie",
     "Un identifiant de règle, un fichier et une ligne fournis par l’analyseur.",
     "Le ticket indique l’impact, liste les emplacements touchés et donne les étapes de correction."
    ],
    [
     "Corriger",
     "Une personne écrit le correctif, le teste et ouvre la pull request.",
     "Une personne lance l’agent de correction. Il fait le plus petit correctif et un test, exécute dotnet test et ouvre une pull request."
    ],
    [
     "Décision de publication",
     "Le contrôle réussit ou échoue. L’approbateur réunit les preuves à la main.",
     "L’agent de préparation transforme contrôles, changements et anomalies ouvertes en ticket GO ou NO-GO. Une personne approuve la production."
    ],
    [
     "Rapports",
     "Un statut réussi ou échoué pour chaque exécution.",
     "Une discussion quotidienne : anomalies par gravité, état des analyseurs, tendance par rapport à la veille, 5 actions principales."
    ],
    [
     "Notes de version",
     "Un journal des modifications généré, qui liste les pull requests fusionnées.",
     "Points forts, correctifs de sécurité, notes de mise à niveau et commandes de vérification sont ajoutés au-dessus du journal généré."
    ],
    [
     "Limites et sécurité",
     "Autorisations fixes dans le YAML. Même comportement à chaque exécution.",
     "Tâche de l’agent en lecture seule. Écritures par sorties déclarées, avec maximum et expiration. Texte non fiable traité comme donnée. Réseau en liste autorisée."
    ]
   ],
   "band_title": "Ce qui reste déterministe ici",
   "band": [
    [
     "Analyseurs et tests",
     "Ils produisent les anomalies que les agents lisent."
    ],
    [
     "Contrôles de publication",
     "Le contrôle bloque en cas d’anomalie critique ou haute ouverte."
    ],
    [
     "Approbation de production",
     "Une personne approuve l’environnement de production."
    ],
    [
     "Workflows compilés",
     "Les fichiers de verrouillage sont compilés depuis la source Markdown."
    ]
   ]
  }
},
 "run": {
  "en": {
   "title": "Reasoning agents with hard limits",
   "sub": "Each agent run follows the same five steps. The limits are declared in the workflow file, not left to the agent.",
   "steps": [
    [
     "Trigger",
     "An event starts the run",
     [
      "Pipeline or Release run ends or fails",
      "Pull request opens or updates",
      "Daily schedule",
      "Manual start: remediation, readiness, notes",
      "Forks and docs-only PRs skipped"
     ]
    ],
    [
     "Prepare",
     "Scripts gather the evidence",
     [
      "Download scanner findings",
      "Dedupe against open and closed issues",
      "Collect commits, runs and open findings",
      "Validate tag and issue numbers",
      "Warm a NuGet cache (remediation)"
     ]
    ],
    [
     "Agent",
     "The agent reasons in a sandbox",
     [
      "Copilot engine, 20 minute limit (30 for remediation)",
      "Read-only repository permissions",
      "Allowed network domains only",
      "Logs, issues and PR text are untrusted data",
      "Nothing to do: it calls no-op"
     ]
    ],
    [
     "Safe outputs",
     "Separate jobs apply the writes",
     [
      "Issue, comment, discussion, pull request or release-notes update",
      "A maximum for each type (1 to 10)",
      "Title prefix and labels",
      "Issues and discussions expire after 30 days",
      "Slack and Teams notes through shared jobs"
     ]
    ],
    [
     "People",
     "People decide",
     [
      "Read the issues, comments and discussions",
      "Review and approve the fix pull request",
      "Approve the production environment",
      "Start remediation themselves",
      "No agent merges, approves or releases"
     ]
    ]
   ],
   "cant_title": "An agent cannot",
   "cant": [
    "Write to the repository directly",
    "Create more than its declared maximum",
    "Follow instructions found in logs or issues",
    "Merge or approve anything"
   ],
   "side": [
    [
     "Daily clean-up",
     "Agentic Maintenance closes expired issues and discussions every day."
    ],
    [
     "Traceable runs",
     "OpenTelemetry export is available when an endpoint is configured."
    ]
   ]
  },
  "fr": {
   "title": "Des agents qui raisonnent, des limites strictes",
   "sub": "Chaque exécution suit les mêmes cinq étapes. Les limites sont déclarées dans le fichier du workflow, pas laissées à l’agent.",
   "steps": [
    [
     "Déclencheur",
     "Un événement lance l’exécution",
     [
      "Exécution Pipeline ou Release terminée ou en échec",
      "Pull request ouverte ou mise à jour",
      "Planification quotidienne",
      "Lancement manuel : correction, préparation, notes",
      "Forks et PR de docs seules ignorés"
     ]
    ],
    [
     "Préparation",
     "Des scripts réunissent les preuves",
     [
      "Téléchargement des anomalies des analyseurs",
      "Dédoublonnage avec les tickets ouverts et fermés",
      "Collecte des commits, exécutions et anomalies",
      "Validation des numéros de tag et de ticket",
      "Cache NuGet préparé (correction)"
     ]
    ],
    [
     "Agent",
     "L’agent raisonne dans un bac à sable",
     [
      "Moteur Copilot, limite de 20 min (30 pour la correction)",
      "Autorisations du dépôt en lecture seule",
      "Domaines réseau autorisés seulement",
      "Journaux, tickets et texte des PR : données non fiables",
      "Rien à faire : il appelle no-op"
     ]
    ],
    [
     "Sorties sécurisées",
     "Des tâches distinctes écrivent",
     [
      "Ticket, commentaire, discussion, pull request ou mise à jour des notes",
      "Un maximum par type (de 1 à 10)",
      "Préfixe de titre et étiquettes",
      "Tickets et discussions expirent après 30 jours",
      "Notes Slack et Teams via des tâches partagées"
     ]
    ],
    [
     "Personnes",
     "Les personnes décident",
     [
      "Lisent les tickets, commentaires et discussions",
      "Relisent et approuvent la PR de correction",
      "Approuvent l’environnement de production",
      "Lancent elles-mêmes la correction",
      "Aucun agent ne fusionne, n’approuve ni ne publie"
     ]
    ]
   ],
   "cant_title": "Un agent ne peut pas",
   "cant": [
    "Écrire directement dans le dépôt",
    "Créer plus que son maximum déclaré",
    "Suivre les instructions des journaux ou tickets",
    "Fusionner ou approuver quoi que ce soit"
   ],
   "side": [
    [
     "Nettoyage quotidien",
     "Agentic Maintenance ferme chaque jour les tickets et discussions expirés."
    ],
    [
     "Exécutions traçables",
     "Export OpenTelemetry si un point de terminaison est configuré."
    ]
   ]
  }
}
}


VISUAL_LABELS = {
    "en": {"open": "Open diagram full size", "area": "Area", "cmp_alt": "Text alternative: comparison table",
           "run_alt": "Text alternative: the five steps", "cant": "An agent cannot", "also": "Also"},
    "fr": {"open": "Ouvrir le diagramme en taille réelle", "area": "Domaine", "cmp_alt": "Alternative textuelle : tableau comparatif",
           "run_alt": "Alternative textuelle : les cinq étapes", "cant": "Un agent ne peut pas", "also": "Aussi"},
}


def agentic_figure(name: str, lg: str, alt: str, text_alt_summary: str, text_alt: str) -> str:
    suffix = "" if lg == "en" else "-fr"
    src = f"../pipeline/visuals/{name}{suffix}.svg"
    return (f'<figure class="diagram"><div class="diagram-scroll" tabindex="0" role="group" aria-label="{esc(alt.split(".")[0])}">'
            f'<img src="{src}" alt="{esc(alt)}"></div>'
            f'<p class="diagram-note"><a href="{src}">{VISUAL_LABELS[lg]["open"]}</a></p>'
            f'<details class="chart-data"><summary>{esc(text_alt_summary)}</summary>{text_alt}</details></figure>')


def agentic_visuals() -> str:
    parts = []
    cmp_html, run_html = {}, {}
    for lg in ("en", "fr"):
        lab = VISUAL_LABELS[lg]
        d = AGENTIC_VISUALS["cmp"][lg]
        rows = "".join(f'<tr><th scope="row">{esc(r[0])}</th><td>{esc(r[1])}</td><td>{esc(r[2])}</td></tr>' for r in d["rows"])
        band = "".join(f"<li><strong>{esc(b[0])}.</strong> {esc(b[1])}</li>" for b in d["band"])
        table_html = (f'<div class="table-scroll" role="region" tabindex="0" aria-label="{esc(lab["cmp_alt"])}"><table class="ref-table">'
                      f'<thead><tr><th scope="col">{lab["area"]}</th><th scope="col">{esc(d["cols"][0])}</th><th scope="col">{esc(d["cols"][1])}</th></tr></thead>'
                      f"<tbody>{rows}</tbody></table></div><h4>{esc(d['band_title'])}</h4><ul>{band}</ul>")
        cmp_html[lg] = f"<p>{esc(d['sub'])}</p>" + agentic_figure("agentic-vs-legacy", lg, AGENTIC_VISUALS["alt"][lg]["cmp"], lab["cmp_alt"], table_html)
        d = AGENTIC_VISUALS["run"][lg]
        steps = "".join(f"<li><strong>{esc(s[0])}: {esc(s[1])}.</strong><ul>{''.join(f'<li>{esc(b)}</li>' for b in s[2])}</ul></li>" for s in d["steps"])
        cant = "".join(f"<li>{esc(x)}</li>" for x in d["cant"])
        side = "".join(f"<li><strong>{esc(s[0])}.</strong> {esc(s[1])}</li>" for s in d["side"])
        list_html = f"<ol>{steps}</ol><h4>{esc(lab['cant'])}</h4><ul>{cant}</ul><h4>{esc(lab['also'])}</h4><ul>{side}</ul>"
        run_html[lg] = f"<p>{esc(d['sub'])}</p>" + agentic_figure("agentic-run-guardrails", lg, AGENTIC_VISUALS["alt"][lg]["run"], lab["run_alt"], list_html)
    parts.append(h2("Beyond pass/fail: what agents add", "Au-delà de réussi/échoué : l’apport des agents", "agents-vs-legacy"))
    parts.append(bblock(cmp_html["en"], cmp_html["fr"]))
    parts.append(h2("Reasoning agents with hard limits", "Des agents qui raisonnent, des limites strictes", "guardrails"))
    parts.append(bblock(run_html["en"], run_html["fr"]))
    return "\n".join(parts)


def agents_page(wfs: list[Workflow]) -> str:
    parts = [bblock(
        "<p>Agentic workflows are written in Markdown (<code>.github/workflows/*.md</code>) and compiled with <a href=\"https://github.com/github/gh-aw\" rel=\"noopener noreferrer\">gh-aw</a> to <code>*.lock.yml</code>. Scanners produce normalized findings. Agents read them and act only through declared safe outputs.</p>",
        "<p>Les workflows agentiques sont écrits en Markdown (<code>.github/workflows/*.md</code>) et compilés avec <a href=\"https://github.com/github/gh-aw\" rel=\"noopener noreferrer\">gh-aw</a> en <code>*.lock.yml</code>. Les analyseurs produisent des résultats normalisés. Les agents les lisent et agissent uniquement par des sorties sécurisées déclarées.</p>")]
    parts.append(h2("Agents", "Agents", "agents"))
    items = []
    for wf in wfs:
        if not wf.agentic:
            continue
        en, fr = AGENTS.get(wf.stem, (esc(wf.description), esc(wf.description)))
        safe = ", ".join(code(k) for k in (wf.data.get("safe-outputs") or {}))
        so = f'<p>{label("Safe outputs", "Sorties sécurisées")} {safe or "—"}</p>'
        items.append(f'<li class="card"><h3><a href="../workflows/{wf.stem}.html">{esc(wf.name)}</a></h3>'
                     f'{bblock("<p>" + en + "</p>", "<p>" + fr + "</p>")}{so}</li>')
    parts.append(f'<ul class="card-grid">{"".join(items)}</ul>')
    parts.append(agentic_visuals())
    parts.append(h2("Trust boundary", "Frontière de confiance", "trust-boundary"))
    parts.append(bblock(
        """<ul>
<li>Scanner output and issue text are untrusted data. Agents must not follow instructions found in them.</li>
<li>The agent job has read-only permissions. It cannot write to the repository, issues or pull requests directly.</li>
<li>Writes happen in separate jobs that apply only the declared <code>safe-outputs</code> (for example <code>create-issue</code> with a title prefix, labels and a maximum count).</li>
<li>Pre-steps run deterministic scripts, such as <code>.github/scripts/security_report.py</code>, so the agent receives prepared evidence.</li>
<li>Network access is limited to the allowed domains. Notifications go through the shared <code>chat-notify</code> safe-output jobs.</li>
</ul>""",
        """<ul>
<li>Les résultats des analyseurs et le texte des tickets sont des données non fiables. Les agents ne doivent pas suivre les instructions qu’ils contiennent.</li>
<li>La tâche de l’agent dispose d’autorisations en lecture seule. Elle ne peut pas écrire directement dans le dépôt, les tickets ou les pull requests.</li>
<li>Les écritures ont lieu dans des tâches distinctes qui appliquent uniquement les <code>safe-outputs</code> déclarés (par exemple <code>create-issue</code> avec un préfixe de titre, des étiquettes et un nombre maximal).</li>
<li>Les étapes préalables exécutent des scripts déterministes, comme <code>.github/scripts/security_report.py</code>, afin que l’agent reçoive des éléments de preuve préparés.</li>
<li>L’accès réseau est limité aux domaines autorisés. Les notifications passent par les tâches de sortie sécurisée partagées <code>chat-notify</code>.</li>
</ul>"""))
    parts.append(bblock(
        '<p>After editing a <code>.md</code> workflow, recompile it with <code>gh aw compile</code>. The Workflow lint check fails when a lock file drifts from its source.</p>',
        '<p>Après la modification d’un workflow <code>.md</code>, recompilez-le avec <code>gh aw compile</code>. La vérification Workflow lint échoue lorsqu’un fichier de verrouillage diffère de sa source.</p>'))
    return layout("agents/index.html", "agents", "Agentic workflows", "Workflows agentiques",
                  ("Agents", "Agents"), None, "\n".join(parts))


def release_page() -> str:
    en = """<p>Releases are driven by tags. Push a semver tag (<code>vX.Y.Z</code> or <code>vX.Y.Z-rc.N</code>) on a commit that is already on <code>main</code>, or run the <strong>Cut release</strong> workflow. Tags with <code>-rc.N</code> are published as pre-releases.</p>
<ol>
<li><strong>Validate</strong>: semver tag, commit on <code>main</code>, no existing release.</li>
<li><strong>Gates</strong>: CI, SAST, SCA, Secrets and IaC, Container, DAST and Fuzzing passed for the tagged commit. No open <code>security-finding</code> issue labelled <code>severity:critical</code> or <code>severity:high</code>.</li>
<li><strong>Build</strong> with the version from the tag, full <code>dotnet test</code>, SHA-512 sums and a CycloneDX SBOM.</li>
<li><strong>E2E</strong> against the image built from the tag.</li>
<li><strong>Readiness agent</strong> posts a GO / NO-GO issue while the run waits.</li>
<li><strong>Approval</strong>: the <code>production</code> environment requires a reviewer and allows only <code>v*</code> tags.</li>
<li><strong>Publish</strong>: image to GHCR with Cosign keyless signature, SLSA provenance and SBOM attestations. NuGet package to GitHub Packages.</li>
<li><strong>GitHub Release</strong> with the jar, <code>SHA512SUMS</code> and the SBOM. The release-notes agent then adds Highlights.</li>
</ol>
<pre><code>git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z</code></pre>
<p><code>v*</code> tags are immutable (repository ruleset: no update, no delete).</p>"""
    fr = """<p>Les publications sont pilotées par les tags. Poussez un tag semver (<code>vX.Y.Z</code> ou <code>vX.Y.Z-rc.N</code>) sur un commit déjà présent sur <code>main</code>, ou exécutez le workflow <strong>Cut release</strong>. Les tags <code>-rc.N</code> sont publiés comme préversions.</p>
<ol>
<li><strong>Validation</strong> : tag semver, commit sur <code>main</code>, aucune version publiée existante.</li>
<li><strong>Contrôles</strong> : CI, SAST, SCA, Secrets and IaC, Container, DAST et Fuzzing ont réussi pour le commit du tag. Aucun ticket <code>security-finding</code> ouvert n’a l’étiquette <code>severity:critical</code> ou <code>severity:high</code>.</li>
<li><strong>Compilation</strong> avec la version issue du tag, <code>dotnet test</code> complet, sommes SHA-512 et SBOM CycloneDX.</li>
<li><strong>E2E</strong> sur l’image construite à partir du tag.</li>
<li><strong>Agent de préparation</strong> : il publie un ticket GO / NO-GO pendant que l’exécution attend.</li>
<li><strong>Approbation</strong> : l’environnement <code>production</code> exige un relecteur et n’autorise que les tags <code>v*</code>.</li>
<li><strong>Publication</strong> : image dans GHCR avec signature Cosign sans clé, provenance SLSA et attestations SBOM. Package NuGet dans GitHub Packages.</li>
<li><strong>Version GitHub</strong> avec le jar, <code>SHA512SUMS</code> et le SBOM. L’agent release-notes ajoute ensuite les Highlights.</li>
</ol>
<pre><code>git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z</code></pre>
<p>Les tags <code>v*</code> sont immuables (ruleset du dépôt : ni mise à jour, ni suppression).</p>"""
    body = h2("Release process", "Processus de publication") + bblock(en, fr)
    body += (f'<ul class="links"><li>{link("../workflows/release.html", "Release workflow reference", "Référence du workflow Release")}</li>'
             f'<li>{link("../workflows/cut-release.html", "Cut release workflow reference", "Référence du workflow Cut release")}</li>'
             f'<li>{link(f"https://github.com/{REPO}/releases", "Releases", "Versions publiées", external=True)}</li></ul>')
    return layout("release/index.html", "release", "Release and tag process", "Processus de publication et de tag",
                  ("Releases", "Publication"), None, body)


def setup_page() -> str:
    en = """<ol>
<li>Install the CLI: <code>gh extension install github/gh-aw</code>. Run <code>gh aw compile</code> after editing any <code>.md</code> workflow.</li>
<li>Copilot authentication: the agentic workflows declare <code>copilot-requests: write</code>, so inference uses the Actions token when the owner has a Copilot plan with centralized billing. Otherwise remove that permission and set <code>COPILOT_GITHUB_TOKEN</code>.</li>
<li>Other secrets: <code>SLACK_WEBHOOK_URL</code>, <code>TEAMS_WEBHOOK_URL</code>, and optionally <code>OTLP_ENDPOINT</code>, <code>OTLP_TOKEN</code>, <code>OTLP_HEADERS</code>.</li>
<li>Enable Discussions and create a <code>Security</code> category. Create the labels <code>security-finding</code>, <code>automated</code>, <code>release</code>, <code>pipeline-failure</code> and <code>severity:critical|high|medium|low</code>.</li>
<li>Create a <code>production</code> environment with required reviewers and deployment tags <code>v*</code> only.</li>
<li>Enable code scanning and Dependabot alerts. Add branch protection that requires CI, SAST, SCA, Secrets and IaC.</li>
<li>Pages: set the source to <strong>GitHub Actions</strong> (Settings, Pages). The <code>Pages</code> workflow then publishes this site.</li>
</ol>
<pre><code>dotnet build -warnaserror   # Roslyn analyzers
dotnet format --verify-no-changes
dotnet test --collect:"XPlat Code Coverage"   # coverlet
dotnet stryker              # mutation (Stryker.NET)</code></pre>"""
    fr = """<ol>
<li>Installez la CLI : <code>gh extension install github/gh-aw</code>. Exécutez <code>gh aw compile</code> après chaque modification d’un workflow <code>.md</code>.</li>
<li>Authentification Copilot : les workflows agentiques déclarent <code>copilot-requests: write</code>. L’inférence utilise donc le jeton Actions lorsque le propriétaire a un forfait Copilot avec facturation centralisée. Sinon, supprimez cette autorisation et définissez <code>COPILOT_GITHUB_TOKEN</code>.</li>
<li>Autres secrets : <code>SLACK_WEBHOOK_URL</code>, <code>TEAMS_WEBHOOK_URL</code> et, en option, <code>OTLP_ENDPOINT</code>, <code>OTLP_TOKEN</code>, <code>OTLP_HEADERS</code>.</li>
<li>Activez Discussions et créez une catégorie <code>Security</code>. Créez les étiquettes <code>security-finding</code>, <code>automated</code>, <code>release</code>, <code>pipeline-failure</code> et <code>severity:critical|high|medium|low</code>.</li>
<li>Créez un environnement <code>production</code> avec des relecteurs obligatoires et les seuls tags de déploiement <code>v*</code>.</li>
<li>Activez l’analyse du code et les alertes Dependabot. Ajoutez une protection de branche qui exige CI, SAST, SCA, Secrets and IaC.</li>
<li>Pages : définissez la source sur <strong>GitHub Actions</strong> (Settings, Pages). Le workflow <code>Pages</code> publie ensuite ce site.</li>
</ol>
<pre><code>dotnet build -warnaserror   # Roslyn analyzers
dotnet format --verify-no-changes
dotnet test --collect:"XPlat Code Coverage"   # coverlet
dotnet stryker              # mutation (Stryker.NET)</code></pre>"""
    body = h2("Repository setup", "Configuration du dépôt") + bblock(en, fr)
    return layout("setup/index.html", "setup", "Setup", "Configuration", ("Setup", "Configuration"), None, body)


def home_page(wfs: list[Workflow]) -> str:
    cards = [
        ("pipeline/", "Pipeline explorer", "Explorateur du pipeline",
         "Interactive, bilingual guide to the CI/CD and fuzzing pipeline design.",
         "Guide interactif et bilingue de la conception du pipeline CI/CD et de fuzzing."),
        ("workflows/", "Workflow reference", "Référence des workflows",
         f"{len(wfs)} workflows: triggers, jobs, permissions, outputs, sources and latest runs.",
         f"{len(wfs)} workflows : déclencheurs, tâches, autorisations, sorties, sources et dernières exécutions."),
        ("agents/", "Agentic workflows", "Workflows agentiques",
         "What each agent does, its safe outputs and the trust boundary.",
         "Rôle de chaque agent, sorties sécurisées et frontière de confiance."),
        ("release/", "Release and tag process", "Processus de publication et de tag",
         "From a semver tag to a signed, attested release.",
         "D’un tag semver à une version publiée signée et attestée."),
        ("setup/", "Setup", "Configuration",
         "Secrets, labels, environments and Pages settings.",
         "Secrets, étiquettes, environnements et paramètres de Pages."),
        ("pipeline/governance/policy-as-code.html", "Governance and audit", "Gouvernance et audit",
         "Policy as code, a signed audit trail for every agentic run, agent inspection and the path to enterprise scale.",
         "Politique en tant que code, piste d’audit signée pour chaque exécution agentique, inspection des agents et trajectoire vers l’échelle de l’entreprise."),
        ("pipeline/fuzzing-system-design.html", "System design", "Conception du système",
         "Dual-surface fuzzing design and reports (original language).",
         "Conception du fuzzing à double surface et rapports (langue d’origine)."),
    ]
    items = "".join(
        f'<li class="card card-nav"><h2><a class="card-link" href="{href}">{bi(en, fr)}</a></h2><p>{bi(den, dfr)}</p>'
        f'<span class="card-go" aria-hidden="true">{bi("Open", "Ouvrir")} &rarr;</span></li>'
        for href, en, fr, den, dfr in cards)
    body = bblock(
        "<p>A .NET 11 / ASP.NET Core minimal API (run in WSLC containers locally) wrapped in a security pipeline of open-source scanners. GitHub Agentic Workflows read the results and open deduplicated issues, comments and discussions.</p>",
        "<p>Une API minimale .NET 11 / ASP.NET Core (exécutée localement dans des conteneurs WSLC) entourée d’un pipeline de sécurité composé d’analyseurs open source. Les GitHub Agentic Workflows lisent les résultats et ouvrent des tickets, des commentaires et des discussions dédupliqués.</p>")
    body += stat_strip(workflow_stats(wfs), "workflows/")
    body += f'<ul class="card-grid">{items}</ul>'
    return layout("index.html", "home", "Agentic security pipeline", "Pipeline de sécurité agentique",
                  ("Documentation", "Documentation"),
                  ("Scanners, agents and releases for a .NET service, with the design and workflow reference.",
                   "Analyseurs, agents et publications pour un service .NET, avec la conception et la référence des workflows."),
                  body)


# --------------------------------------------------------- docs rendering
def rewrite_doc_links(markup: str, doc_rel: str) -> str:
    doc_dir = posixpath.dirname(doc_rel)

    def repl(match: re.Match) -> str:
        quote, href = match.group(1), match.group(2)
        if re.match(r"^(?:[a-z][a-z0-9+.-]*:|#|/)", href, re.I):
            return match.group(0)
        target, _, frag = href.partition("#")
        resolved = posixpath.normpath(posixpath.join(doc_dir, target))
        if resolved.startswith(".."):
            repo_path = posixpath.normpath(posixpath.join("docs", doc_dir, target))
            return f'href={quote}{BLOB}{repo_path}{"#" + frag if frag else ""}{quote}'
        if resolved == "fuzzing-pipeline-explorer.html":
            target = posixpath.relpath("index.html", doc_dir or ".")
        elif target.endswith(".md"):
            target = target[:-3] + ".html"
        return f'href={quote}{target}{"#" + frag if frag else ""}{quote}'

    return re.sub(r'href=(["\'])([^"\']*)\1', repl, markup)


def render_diagrams(body: str, doc_rel: str) -> str:
    """Swap Mermaid source blocks for the SVGs pre-rendered by site/render_diagrams.py, keeping the source as a text alternative."""
    import hashlib
    import html as html_lib
    depth = "../" * (doc_rel.count("/") + 1)

    def repl(match: re.Match) -> str:
        source = html_lib.unescape(match.group(1)).strip()
        name = hashlib.sha256(source.encode("utf-8")).hexdigest()[:12]
        if not (SITE_SRC / "diagrams" / f"{name}.svg").exists():
            raise SystemExit(f"Missing diagram {name}.svg in {doc_rel}; run python site/render_diagrams.py")
        kind = source.split(None, 1)[0]
        return (f'<figure class="diagram"><div class="diagram-scroll" tabindex="0" role="group" aria-label="{esc(kind)} diagram">'
                f'<img src="{depth}diagrams/{name}.svg" alt="{esc(kind)} diagram. The Mermaid source below is the text alternative."></div>'
                f'<p class="diagram-note"><a href="{depth}diagrams/{name}.svg">{bi("Open diagram full size", "Ouvrir le diagramme en taille réelle")}</a></p>'
                f'<details class="chart-data"><summary>{bi("View diagram source", "Voir la source du diagramme")}</summary>'
                f'<pre><code>{html_lib.escape(source)}</code></pre></details></figure>')
    return re.sub(r'<pre><code class="language-mermaid">(.*?)</code></pre>', repl, body, flags=re.S)


def render_markdown(md_path: Path) -> str:
    rel = md_path.relative_to(DOCS).as_posix()
    text = md_path.read_text(encoding="utf-8")
    title_match = re.search(r"^#\s+(.+)$", text, re.M)
    title = title_match.group(1).strip() if title_match else md_path.stem
    body = markdown.markdown(text, extensions=["tables", "fenced_code", "toc", "sane_lists"])
    body = re.sub(r"<h1[^>]*>.*?</h1>\s*", "", body, count=1, flags=re.S)
    body = rewrite_doc_links(body, rel)
    body = render_diagrams(body, rel)
    out_path = "pipeline/" + rel[:-3] + ".html"
    note = ""
    src = f'<p>{gh("docs/" + rel, "View source on GitHub", "Voir la source sur GitHub")}</p>'
    return out_path, layout(out_path, "pipeline", title, title, ("Design document", "Document de conception"), None,
                            f'{note}{src}<article class="markdown-body" lang="en">{body}</article>')


def adapt_explorer(source: str) -> str:
    out = rewrite_doc_links(source, "fuzzing-pipeline-explorer.html")
    PAGES["pipeline/"] = ("Pipeline explorer", "Explorateur du pipeline")
    out = re.sub(r'\s*<div class="preferences wrap" data-enhanced>.*?</details>\s*</div>', "", out, count=1, flags=re.S)
    out = out.replace('<link rel="stylesheet" href="visuals/pipeline-explorer.css">',
                      f'<meta http-equiv="Content-Security-Policy" content="{CSP}">\n'
                      '  <script src="../assets/boot.js"></script>\n'
                      '  <link rel="stylesheet" href="visuals/pipeline-explorer.css">\n  <link rel="stylesheet" href="../assets/site.css">\n'
                      f'  <link rel="icon" href="{FAVICON}">\n'
                      '  <script src="../assets/site-index.js" defer></script>', 1)
    out = out.replace('<script src="visuals/pipeline-explorer.js" defer></script>',
                      '<script src="visuals/pipeline-explorer.js" defer></script>\n  <script src="../assets/site.js" defer></script>', 1)
    out = out.replace("<body>", '<body data-root="../">', 1)
    out = re.sub(r'<svg(?![^>]*data-no-translate)', '<svg data-no-translate', out)
    out = out.replace('<img src="visuals/pipeline-overview.svg"', '<img data-no-translate src="visuals/pipeline-overview.svg"')
    out = out.replace('<header class="hero">', '<div class="hero">', 1).replace("</header>", "</div>", 1)
    top = (chrome.sprite() + "\n  " + chrome.header("../", NAV, "pipeline") + '\n  <div class="app-shell">\n        <!--SIDENAV:pipeline/|../-->\n    <div class="app-body">')
    out = re.sub(r'(<a class="skip"[^>]*>[^<]*</a>)', lambda m: m.group(1) + "\n  " + top, out, count=1)
    return out.replace("</body>", "  </div></div>\n  " + chrome.dialogs() + "\n</body>", 1)


def verify_explorer_cards(wfs: list["Workflow"], script: str, page: str) -> None:
    """The explorer's summary cards list workflows by stem: fail the build if a stem or a count drifts from .github/workflows."""
    stems = {wf.stem for wf in wfs}
    agentic = {wf.stem for wf in wfs if wf.agentic}
    listed_agents = re.findall(r'agentItem\("([\w-]+)"', script)
    listed_checks = re.findall(r'checkItem\("([\w-]+)"', script)
    listed_groups = re.findall(r'groupItem\("\w+",\s*"([\w-]+)"', script)
    other = re.findall(r'workflowHref\("([\w-]+)"', script)
    missing = sorted((set(listed_agents) | set(listed_checks) | set(listed_groups) | set(other)) - stems)
    if missing:
        raise SystemExit(f"Explorer cards reference unknown workflows: {', '.join(missing)}")
    if set(listed_agents) != agentic or len(listed_agents) != len(agentic):
        raise SystemExit(f"Explorer agent card lists {sorted(listed_agents)}; agentic workflows are {sorted(agentic)}")
    for key, items in (("agents", listed_agents), ("checks", listed_checks), ("groups", listed_groups)):
        card = re.search(rf'data-stat="{key}"[^>]*><strong>(\d+) ', page)
        if not card or int(card.group(1)) != len(items):
            raise SystemExit(f"Explorer card '{key}' shows {card.group(1) if card else '?'} but lists {len(items)} items")


def adapt_explorer_script(script: str) -> str:
    """Repoint source links held in the explorer script: repository files go to GitHub, docs to the built pages."""
    script = re.sub(r'"\.\./([^"]+)"', lambda m: f'"{BLOB}{m.group(1)}"', script)
    return re.sub(r'"(?!https?:)([\w./-]+)\.md(#[^"]*)?"', lambda m: f'"{m.group(1)}.html{m.group(2) or ""}"', script)


def build(summary: str | None) -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    pages: dict[str, str] = {}
    wfs = collect_workflows()

    shutil.copytree(DOCS / "visuals", OUT / "pipeline" / "visuals")
    script = OUT / "pipeline" / "visuals" / "pipeline-explorer.js"
    script.write_text(adapt_explorer_script(script.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
    dictionary = OUT / "pipeline" / "visuals" / "pipeline-explorer-fr.js"
    text = dictionary.read_text(encoding="utf-8")
    marker = "const messages = {\n"
    if marker not in text:
        raise SystemExit("French dictionary layout changed; update the site bar entries in site/build.py")
    extra = '    "Site": "Site",\n' + "".join(f'    "{en}": "{fr}",\n' for _, _, en, fr in NAV)
    dictionary.write_text(text.replace(marker, marker + extra, 1), encoding="utf-8", newline="\n")
    explorer = DOCS / "fuzzing-pipeline-explorer.html"
    verify_explorer_cards(wfs, (DOCS / "visuals" / "pipeline-explorer.js").read_text(encoding="utf-8"),
                          explorer.read_text(encoding="utf-8"))
    pages["pipeline/index.html"] = adapt_explorer(explorer.read_text(encoding="utf-8"))
    for md in sorted(DOCS.rglob("*.md")):
        out_path, content = render_markdown(md)
        pages[out_path] = content

    pages["index.html"] = home_page(wfs)
    pages["workflows/index.html"] = workflows_index(wfs)
    for wf in wfs:
        pages[f"workflows/{wf.stem}.html"] = workflow_page(wf)
    pages["agents/index.html"] = agents_page(wfs)
    pages["release/index.html"] = release_page()
    pages["setup/index.html"] = setup_page()

    for name, content in pages.items():
        target = OUT / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(finish_page(name, content), encoding="utf-8", newline="\n")
    # Docs pages link to media stored beside them (the Actions run recordings).
    recordings = DOCS / "actions-recordings"
    if recordings.is_dir():
        media_out = OUT / "pipeline" / "actions-recordings"
        media_out.mkdir(parents=True, exist_ok=True)
        for media in sorted(recordings.iterdir()):
            if media.suffix in (".webm", ".png"):
                shutil.copy2(media, media_out / media.name)
    shutil.copytree(SITE_SRC / "assets", OUT / "assets")
    shutil.copytree(SITE_SRC / "diagrams", OUT / "diagrams")
    (OUT / "assets" / "site-index.js").write_text(search_index(), encoding="utf-8", newline="\n")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    (OUT / "404.html").write_text(finish_page("404.html", not_found()), encoding="utf-8", newline="\n")

    lines = ["## Pages build", "", f"- Pages: {len(pages) + 1}",
             f"- Workflows documented: {len(wfs)} ({sum(w.agentic for w in wfs)} agentic)",
             f"- Base path: `{BASE_PATH}`"]
    text = "\n".join(lines) + "\n"
    print(text)
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(text)


def not_found() -> str:
    state = f"""
  <div class="state state-error" role="alert">{chrome.icon("alert")}
    <h2>{bi("This page does not exist", "Cette page n’existe pas")}</h2>
    <p>{bi("The address may be mistyped, or the page was moved.", "L’adresse est peut-être incorrecte, ou la page a été déplacée.")}</p>
    <div class="actions"><a class="btn btn-primary" href="{BASE_PATH}">{bi("Go to the home page", "Retourner à l’accueil")}</a>
    <a class="btn" href="{BASE_PATH}workflows/">{bi("Browse workflows", "Parcourir les workflows")}</a>
    <a class="btn" href="{BASE_PATH}pipeline/">{bi("Open the pipeline explorer", "Ouvrir l’explorateur du pipeline")}</a></div>
    <p class="hint">{bi("Tip: press", "Astuce : appuyez sur")} <kbd>Ctrl</kbd> <kbd>K</kbd> {bi("to search all pages.", "pour rechercher dans toutes les pages.")}</p>
  </div>"""
    return layout("404.html", "", "Page not found", "Page introuvable", ("Error 404", "Erreur 404"), None, state, root=BASE_PATH)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", help="Append a Markdown summary to this file")
    args = parser.parse_args()
    sys.exit(build(args.summary))
