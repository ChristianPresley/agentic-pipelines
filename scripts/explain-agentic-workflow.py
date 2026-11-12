#!/usr/bin/env python3
"""Explain a compiled gh-aw workflow (*.lock.yml) in plain language.

The lock file is generated YAML that runs to thousands of lines. This script reads it with a
YAML parser (never executes anything) and prints what a reviewer actually wants to know: who
can trigger it, which jobs run with which permissions, which tools, network destinations and
safe outputs the agent has, its budgets, and which artifacts it leaves behind.

    python scripts/explain-agentic-workflow.py .github/workflows/security-triage.lock.yml
    python scripts/explain-agentic-workflow.py --all --out docs/governance/agent-inspection-reports.md
    python scripts/explain-agentic-workflow.py --all --out docs/governance/agent-inspection-reports.md --check

Output is deterministic, so `--check` can fail CI when the committed report drifts from the
lock files.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

ECOSYSTEM_NOTE = "ecosystem identifiers (for example `defaults`, `dotnet`) expand to the domain list below"
SAFE_OUTPUT_META = {"report_incomplete", "report_missing_data", "report_missing_tool", "noop"}


def load(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    doc = yaml.safe_load(text)
    if not isinstance(doc, dict) or "jobs" not in doc:
        raise SystemExit(f"{path}: not a workflow file")
    return doc, text


def header(text: str) -> tuple[dict, dict]:
    meta, manifest = {}, {}
    for line in text.splitlines()[:6]:
        if line.startswith("# gh-aw-metadata: "):
            meta = json.loads(line[len("# gh-aw-metadata: "):])
        elif line.startswith("# gh-aw-manifest: "):
            manifest = json.loads(line[len("# gh-aw-manifest: "):])
    return meta, manifest


def triggers(doc: dict) -> list[str]:
    on = doc.get("on", doc.get(True))
    if isinstance(on, str):
        return [on]
    if isinstance(on, list):
        return [str(x) for x in on]
    if isinstance(on, dict):
        out = []
        for name, cfg in on.items():
            detail = ""
            if isinstance(cfg, dict):
                if cfg.get("branches"):
                    detail = f" on {', '.join(map(str, cfg['branches']))}"
                elif cfg.get("workflows"):
                    detail = f" of {', '.join(map(str, cfg['workflows']))}"
                elif cfg.get("types"):
                    detail = f" ({', '.join(map(str, cfg['types']))})"
            out.append(f"{name}{detail}")
        return out
    return []


def perms(value: object) -> str:
    if value in (None, {}):
        return "none"
    if isinstance(value, str):
        return value
    return ", ".join(f"{k}: {v}" for k, v in sorted(value.items()))


def safe_outputs(text: str) -> dict:
    match = re.search(r'GH_AW_SAFE_OUTPUTS_CONFIG: (".*")\s*$', text, re.M)
    if not match:
        return {}
    try:
        return json.loads(json.loads(match.group(1)))
    except ValueError:
        return {}


def first_env(text: str, name: str) -> str | None:
    match = re.search(rf'^\s*{name}: "?([^"\n]*)"?\s*$', text, re.M)
    return match.group(1) if match else None


def budget(text: str) -> dict:
    out: dict = {}
    for key, env in (("max_ai_credits", "GH_AW_MAX_AI_CREDITS"), ("max_daily_ai_credits", "GH_AW_MAX_DAILY_AI_CREDITS")):
        value = first_env(text, env)
        if value and value.isdigit():
            out[key] = int(value)
    return out


def esc(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def table(head: list[str], rows: list[list[object]]) -> list[str]:
    if not rows:
        return ["_None._", ""]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    lines += ["| " + " | ".join(esc(c) for c in row) + " |" for row in rows]
    return lines + [""]


def needs(job: dict) -> str:
    value = job.get("needs") or []
    return ", ".join([value] if isinstance(value, str) else map(str, value)) or "-"


def runs_on(value: object) -> str:
    if isinstance(value, dict):
        return str(value.get("labels") or value.get("group") or value)
    return str(value) if value else "-"


def explain(path: Path, heading: int = 2) -> str:
    doc, text = load(path)
    meta, manifest = header(text)
    h = "#" * heading
    sub = "#" * (heading + 1)
    name = doc.get("name") or path.stem
    jobs: dict = doc["jobs"]
    out = [f"{h} {name}", "",
           f"Source: `{path.as_posix()}`. Compiled by gh-aw `{meta.get('compiler_version', 'unknown')}`, "
           f"frontmatter hash `{str(meta.get('frontmatter_hash', 'unknown'))[:16]}`.", ""]

    out += [f"{sub} Overview", ""]
    engine = first_env(text, "GH_AW_INFO_ENGINE_NAME") or first_env(text, "GH_AW_INFO_ENGINE_ID") or "unknown"
    model = first_env(text, "GH_AW_INFO_MODEL") or "unknown"
    model = "auto (resolved at run time, recorded in the evidence record)" if "|| 'auto'" in model or model.endswith("'auto' }}") else model
    limits = budget(text)
    out += table(["Question", "Answer"], [
        ["Who starts it", "; ".join(triggers(doc)) or "-"],
        ["Engine", engine],
        ["Model", model],
        ["Token budget per run (AIC)", limits.get("max_ai_credits", "not set")],
        ["Token budget per day (AIC)", limits.get("max_daily_ai_credits", "not set")],
        ["Workflow-level permissions", perms(doc.get("permissions"))],
        ["Concurrency", (doc.get("concurrency") or {}).get("group", "-") if isinstance(doc.get("concurrency"), dict) else "-"],
    ])

    out += [f"{sub} Jobs and permissions", "",
            "Read top to bottom: the agent job holds no write scope except the model token; every write to the repository happens later in `safe_outputs`.", ""]
    rows = []
    for job_id, job in jobs.items():
        env = job.get("environment")
        rows.append([f"`{job_id}`", needs(job), runs_on(job.get("runs-on")), job.get("timeout-minutes", "-"),
                     perms(job.get("permissions")), env.get("name") if isinstance(env, dict) else (env or "-"),
                     len(job.get("steps") or [])])
    out += table(["Job", "Needs", "Runs on", "Timeout (min)", "Permissions", "Environment", "Steps"], rows)

    out += [f"{sub} Tools", ""]
    out += table(["MCP server", "Tools exposed"],
                 [[f"`{s.get('name')}`", ", ".join(f"`{t}`" for t in s.get("tools", [])) or "(server default set)"]
                  for s in manifest.get("mcp_servers", [])])

    out += [f"{sub} Safe outputs", "",
            "The only actions the agent may request. Each one is validated, scanned by threat detection and applied by a separate job.", ""]
    cfg = safe_outputs(text)
    out += table(["Output", "Max per run"],
                 [[f"`{k}`", (v.get("max") if isinstance(v, dict) and v.get("max") is not None else "-")]
                  for k, v in sorted(cfg.items()) if k not in SAFE_OUTPUT_META])
    detection = manifest.get("threat_detection")
    out += [f"Threat detection: {'enabled' if jobs.get('detection') else 'not present'}"
            + (f" (`{json.dumps(detection, sort_keys=True)}`)" if detection else "") + ".", ""]

    domains = (first_env(text, "GH_AW_ALLOWED_DOMAINS") or "").split(",")
    domains = sorted(d for d in domains if d)
    out += [f"{sub} Network", "",
            f"The agent runs behind a firewall that denies everything except {len(domains)} destinations; {ECOSYSTEM_NOTE}.", ""]
    out += ["<details><summary>Allowed destinations</summary>", "", ", ".join(f"`{d}`" for d in domains) or "_None._", "", "</details>", ""]

    out += [f"{sub} Secrets and actions", ""]
    out += table(["Secret referenced"], [[f"`{s}`"] for s in sorted(manifest.get("secrets", []))])
    out += table(["Action", "Version", "Commit"],
                 [[f"`{a.get('repo')}`", a.get("version", "-"), f"`{str(a.get('sha', ''))[:12]}`"]
                  for a in sorted(manifest.get("actions", []), key=lambda a: a.get("repo", ""))])

    out += [f"{sub} Evidence the run leaves behind", ""]
    uploads = []
    for job_id, job in jobs.items():
        for step in job.get("steps") or []:
            if "upload-artifact" in str(step.get("uses", "")):
                with_ = step.get("with") or {}
                uploads.append([f"`{job_id}`", step.get("name", ""), f"`{with_.get('name', '(dynamic)')}`", with_.get("retention-days", "default")])
    out += table(["Job", "Step", "Artifact", "Retention (days)"], uploads)

    out += [f"{sub} Steps per job", ""]
    for job_id, job in jobs.items():
        steps = [str(s.get("name") or s.get("uses") or "(unnamed)") for s in job.get("steps") or []]
        if steps:
            out += [f"<details><summary><code>{job_id}</code> ({len(steps)} steps)</summary>", ""]
            out += [f"{i}. {esc(s)}" for i, s in enumerate(steps, 1)] + ["", "</details>", ""]
    return "\n".join(out).rstrip() + "\n"


def report(paths: list[Path]) -> str:
    parts = ["# Agentic workflow inspection reports", "",
             "<!-- Generated by scripts/explain-agentic-workflow.py. Do not edit; CI fails when it drifts from the lock files. -->", "",
             "One section per compiled agentic workflow, generated from its `.lock.yml`. "
             "See [Inspecting an agent](agent-inspection.md) for how to use these next to a live run.", ""]
    parts += [f"- [{(load(p)[0].get('name') or p.stem)}](#{re.sub(r'[^a-z0-9 -]', '', str(load(p)[0].get('name') or p.stem).lower()).replace(' ', '-')})" for p in paths]
    parts.append("")
    for p in paths:
        parts.append(explain(p))
    return "\n".join(parts)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", type=Path, help="lock files to explain")
    ap.add_argument("--all", action="store_true", help="explain every .github/workflows/*.lock.yml")
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, help="write the report here instead of stdout")
    ap.add_argument("--check", action="store_true", help="fail if --out differs from the generated report")
    args = ap.parse_args(argv)

    paths = list(args.files)
    if args.all:
        paths = sorted((args.root / ".github" / "workflows").glob("*.lock.yml"))
    if not paths:
        ap.error("pass lock files or --all")

    text = report(paths) if args.all or len(paths) > 1 else explain(paths[0])
    if args.out and args.check:
        current = args.out.read_text(encoding="utf-8") if args.out.exists() else ""
        if current.replace("\r\n", "\n") != text:
            print(f"{args.out} is stale. Run: python scripts/explain-agentic-workflow.py --all --out {args.out.as_posix()}", file=sys.stderr)
            return 1
        print(f"{args.out} is up to date")
        return 0
    if args.out:
        args.out.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {args.out}")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
