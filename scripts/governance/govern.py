#!/usr/bin/env python3
"""Deterministic governance toolkit: fact extraction, policy evaluation and run evidence.

No model is involved. Everything here is reproducible from the repository contents and the
inputs it archives:

  facts      read .github/workflows (sources, compiled lock files, plain workflows) into facts.json
  evaluate   combine facts, policy/policy.yml and policy/waivers.yml, run OPA, write the verdict
  evidence   turn one agentic run's artifacts into an evidence record and check it at runtime

The decision logic lives in policy/rego. This file only extracts facts and renders results.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

SHA40 = re.compile(r"^[0-9a-f]{40}$")
META_SAFE_OUTPUT_KEYS = {"report_incomplete", "report_missing_data", "report_missing_tool",
                         "create_report_incomplete_issue", "noop"}
SCHEMA_FACTS = "governance-facts/v1"
SCHEMA_INPUT = "governance-input/v1"
SCHEMA_VERDICT = "governance-verdict/v1"
SCHEMA_EVIDENCE = "agent-run-evidence/v1"


# ------------------------------------------------------------------ helpers
def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def split_frontmatter(text: str) -> tuple[dict, str]:
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", text, re.S)
    if not match:
        return {}, text
    meta = yaml.safe_load(match.group(1))
    return (meta if isinstance(meta, dict) else {}), match.group(2)


def triggers_of(doc: dict) -> list[str]:
    # YAML 1.1 parses the bare key `on` as boolean True.
    on = doc.get("on", doc.get(True))
    if isinstance(on, str):
        return [on]
    if isinstance(on, (list, dict)):
        return sorted(str(x) for x in on)
    return []


def credits(value: object) -> int | None:
    """Parse an AI Credits budget such as 1000, "5k" or "1M". Expressions and -1 stay unparsed."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        match = re.fullmatch(r"(\d+)([kKmM]?)", value.strip())
        if match:
            return int(match.group(1)) * {"": 1, "k": 1000, "m": 1_000_000}[match.group(2).lower()]
    return None


def perms_of(value: object) -> dict | str | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return {str(k): str(v) for k, v in value.items()}
    return str(value)


def runs_on_of(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return ",".join(str(x) for x in value)
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    return str(value)


def classify_use(ref: str) -> dict:
    if ref.startswith("./"):
        return {"kind": "local", "ref": ref, "pinned": True}
    if ref.startswith("docker://"):
        return {"kind": "docker", "ref": ref, "pinned": "@sha256:" in ref}
    name, _, version = ref.partition("@")
    parts = name.split("/")
    return {"kind": "action", "ref": ref, "owner": parts[0], "repo": "/".join(parts[:2]),
            "pinned": bool(SHA40.match(version))}


def collect_uses(doc: dict) -> list[dict]:
    found = []
    for job_id, job in sorted((doc.get("jobs") or {}).items()):
        if not isinstance(job, dict):
            continue
        refs = []
        if isinstance(job.get("uses"), str):
            refs.append(job["uses"])
        for step in job.get("steps") or []:
            if isinstance(step, dict) and isinstance(step.get("uses"), str):
                refs.append(step["uses"])
        for ref in sorted(set(refs)):
            found.append({"job": str(job_id), **classify_use(ref)})
    runs = doc.get("runs") if isinstance(doc.get("runs"), dict) else {}
    for ref in sorted({s["uses"] for s in runs.get("steps") or [] if isinstance(s, dict) and isinstance(s.get("uses"), str)}):
        found.append({"job": "(composite)", **classify_use(ref)})
    return found


def lock_header(text: str) -> tuple[dict, dict]:
    meta, manifest = {}, {}
    for line in text.splitlines()[:6]:
        for key, target in (("# gh-aw-metadata: ", meta), ("# gh-aw-manifest: ", manifest)):
            if line.startswith(key):
                target.update(json.loads(line[len(key):]))
    return meta, manifest


def safe_output_config(text: str) -> dict:
    match = re.search(r'GH_AW_SAFE_OUTPUTS_CONFIG: (".*")\s*$', text, re.M)
    if not match:
        return {}
    try:
        return json.loads(json.loads(match.group(1)))
    except ValueError:
        return {}


def network_facts(value: object) -> dict:
    if value is None:
        return {"mode": "defaults", "entries": ["defaults"]}
    if isinstance(value, str):
        return {"mode": value, "entries": [value]}
    if isinstance(value, dict):
        entries = [str(x) for x in value.get("allowed") or []]
        return {"mode": "custom" if entries else "none", "entries": entries}
    return {"mode": "unknown", "entries": []}


def bash_facts(tools: dict) -> dict:
    if "bash" not in tools:
        return {"enabled": False, "commands": [], "unrestricted": False}
    value = tools["bash"]
    commands = [] if value in (None, True) else [str(x) for x in (value if isinstance(value, list) else [value])]
    unrestricted = value in (None, True) or any(c in ("*", ":*", "**") for c in commands)
    return {"enabled": True, "commands": commands, "unrestricted": unrestricted}


# ------------------------------------------------------------------ facts
def file_facts(path: Path, root: Path) -> dict:
    doc = load_yaml(path)
    jobs = []
    for job_id, job in sorted((doc.get("jobs") or {}).items()):
        if not isinstance(job, dict):
            continue
        env = job.get("environment")
        jobs.append({"id": str(job_id), "runs_on": runs_on_of(job.get("runs-on")),
                     "permissions": perms_of(job.get("permissions")),
                     "reusable": isinstance(job.get("uses"), str),
                     "environment": env.get("name") if isinstance(env, dict) else env})
    return {"file": path.relative_to(root).as_posix(), "lock": path.name.endswith(".lock.yml"),
            "triggers": triggers_of(doc), "permissions": perms_of(doc.get("permissions")),
            "jobs": jobs, "uses": collect_uses(doc)}


def agentic_facts(md: Path, root: Path) -> dict:
    meta, body = split_frontmatter(md.read_text(encoding="utf-8"))
    lock = md.with_suffix(".lock.yml")
    lock_text = lock.read_text(encoding="utf-8") if lock.exists() else ""
    header, manifest = lock_header(lock_text)
    outputs = {k: {"max": v.get("max") if isinstance(v, dict) else None}
               for k, v in sorted(safe_output_config(lock_text).items()) if k not in META_SAFE_OUTPUT_KEYS}
    engine = meta.get("engine", "copilot")
    safe = meta.get("safe-outputs") if isinstance(meta.get("safe-outputs"), dict) else {}
    detection = safe.get("threat-detection")
    tools = meta.get("tools") if isinstance(meta.get("tools"), dict) else {}
    github = tools.get("github") if isinstance(tools.get("github"), dict) else {}
    observability = meta.get("observability") if isinstance(meta.get("observability"), dict) else {}
    return {
        "id": md.stem, "source": md.relative_to(root).as_posix(),
        "lock": lock.relative_to(root).as_posix() if lock.exists() else None,
        "engine": engine.get("id") if isinstance(engine, dict) else engine,
        "model": engine.get("model") if isinstance(engine, dict) else None,
        "runs_on": runs_on_of(meta.get("runs-on")),
        "timeout_minutes": meta.get("timeout-minutes"),
        "max_ai_credits": credits(meta.get("max-ai-credits")),
        "max_daily_ai_credits": credits(meta.get("max-daily-ai-credits")),
        "permissions": perms_of(meta.get("permissions")),
        "network": network_facts(meta.get("network")),
        "bash": bash_facts(tools),
        "github_toolsets": [str(x) for x in github.get("toolsets") or []],
        "safe_outputs_runs_on": runs_on_of(safe.get("runs-on")),
        "threat_detection_runs_on": runs_on_of(detection.get("runs-on")) if isinstance(detection, dict) else None,
        "threat_detection_enabled": detection is not False,
        "safe_outputs": outputs,
        "mcp_servers": sorted(s.get("name", "") for s in manifest.get("mcp_servers", [])),
        "triggers": triggers_of(meta),
        "otlp": isinstance(observability.get("otlp"), dict),
        "prompt_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "frontmatter_hash": header.get("frontmatter_hash"),
        "compiler_version": header.get("compiler_version"),
    }


def pipeline_facts(root: Path) -> dict:
    path = root / ".github" / "workflows" / "pipeline.yml"
    if not path.exists():
        return {"present": False}
    jobs = load_yaml(path).get("jobs") or {}
    gate = jobs.get("gate") if isinstance(jobs.get("gate"), dict) else None
    needs = (gate or {}).get("needs")
    needs = [needs] if isinstance(needs, str) else [str(x) for x in needs or []]
    return {"present": True, "file": path.relative_to(root).as_posix(),
            "jobs": sorted(str(j) for j in jobs), "gate_present": gate is not None,
            "gate_if": str((gate or {}).get("if", "")), "gate_needs": sorted(needs)}


def collect_facts(root: Path) -> dict:
    workflows = root / ".github" / "workflows"
    files = [file_facts(p, root) for p in sorted(workflows.glob("*.yml"))]
    actions = root / ".github" / "actions"
    if actions.is_dir():
        files += [file_facts(p, root) for p in sorted(actions.glob("*/action.yml"))]
    return {"schema": SCHEMA_FACTS, "files": files,
            "agentic": [agentic_facts(p, root) for p in sorted(workflows.glob("*.md"))],
            "pipeline": pipeline_facts(root)}


# ------------------------------------------------------------------ evaluate
def run_opa(opa: str, rego: Path, query: str, payload: dict) -> dict:
    proc = subprocess.run([opa, "eval", "--format", "json", "--stdin-input", "--data", str(rego), query],
                          input=json.dumps(payload), capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise SystemExit(f"opa failed ({proc.returncode}):\n{proc.stderr}\n{proc.stdout}")
    result = json.loads(proc.stdout).get("result")
    if not result:
        raise SystemExit(f"opa returned no result for {query}")
    return result[0]["expressions"][0]["value"]


def build_input(facts: dict, policy_dir: Path, today: str) -> dict:
    waivers = load_yaml(policy_dir / "waivers.yml").get("waivers") or []
    for waiver in waivers:
        if isinstance(waiver.get("expires"), dt.date):
            waiver["expires"] = waiver["expires"].isoformat()
    return {"schema": SCHEMA_INPUT, "today": today, "policy": load_yaml(policy_dir / "policy.yml"),
            "waivers": waivers, "facts": facts}


def md_table(title: str, head: list[str], rows: list[list[str]]) -> list[str]:
    if not rows:
        return []
    lines = [f"### {title}", "", "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    lines += ["| " + " | ".join(str(c).replace("|", "\\|").replace("\n", " ") for c in row) + " |" for row in rows]
    return lines + [""]


def render_verdict_md(verdict: dict) -> str:
    mode = verdict["mode"]
    status = "PASS" if verdict["pass"] else ("FAIL" if mode == "enforce" else "FAIL (audit mode, not blocking)")
    lines = ["## Governance verdict", "", f"**{status}**", "",
             f"- Policy mode: `{mode}`",
             f"- Evaluated on: `{verdict['today']}`",
             f"- Blocking violations: **{len(verdict['blocking'])}**",
             f"- Warnings: {len(verdict['warnings'])}",
             f"- Waived by an active exception: {len(verdict['waived'])}", ""]
    lines += md_table("Blocking violations", ["Rule", "Subject", "Message"],
                      [[f"`{v['rule']}`", f"`{v['subject']}`", v["message"]] for v in verdict["blocking"]])
    lines += md_table("Warnings", ["Rule", "Subject", "Message"],
                      [[f"`{v['rule']}`", f"`{v['subject']}`", v["message"]] for v in verdict["warnings"]])
    lines += md_table("Waived (needs the exception approval environment)",
                      ["Rule", "Subject", "Waiver", "Expires", "Approved by"],
                      [[f"`{w['violation']['rule']}`", f"`{w['violation']['subject']}`", w["waiver"]["id"],
                        w["waiver"]["expires"], w["waiver"]["approved_by"]] for w in verdict["waived"]])
    stats = verdict["stats"]
    lines.append(f"Checked {stats['files']} workflow files and {stats['agentic']} agentic workflows. "
                 f"Input digest `{verdict['inputs_sha256'][:16]}`. Re-run: "
                 "`python scripts/governance/govern.py evaluate --root . --opa <opa> --out-dir out`.")
    return "\n".join(lines) + "\n"


def write_outputs(path: str | None, values: dict) -> None:
    if path:
        with open(path, "a", encoding="utf-8") as handle:
            handle.writelines(f"{k}={v}\n" for k, v in values.items())


def cmd_facts(args: argparse.Namespace) -> int:
    facts = collect_facts(Path(args.root).resolve())
    Path(args.out).write_text(json.dumps(facts, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"facts: {len(facts['files'])} files, {len(facts['agentic'])} agentic workflows -> {args.out}")
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    policy_dir = Path(args.policy).resolve() if args.policy else root / "policy"
    today = args.today or dt.datetime.now(dt.timezone.utc).date().isoformat()
    facts = collect_facts(root)
    payload = build_input(facts, policy_dir, today)
    mode = args.mode or payload["policy"].get("mode", "enforce")
    report = run_opa(args.opa, policy_dir / "rego", "data.governance.static.report", payload)
    verdict = {"schema": SCHEMA_VERDICT, "today": today, "mode": mode, "pass": report["pass"],
               "blocking": report["blocking"], "warnings": report["warnings"], "waived": report["waived"],
               "stats": {"files": len(facts["files"]), "agentic": len(facts["agentic"])},
               "inputs_sha256": hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()}
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "governance-input.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "verdict.json").write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown = render_verdict_md(verdict)
    (out / "verdict.md").write_text(markdown, encoding="utf-8")
    print(markdown)
    write_outputs(args.github_output, {"blocking": len(verdict["blocking"]), "waived": len(verdict["waived"]),
                                       "mode": mode, "pass": str(verdict["pass"]).lower()})
    return 0


# ------------------------------------------------------------------ evidence
def read_json(path: Path | None) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8")) if path else {}
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def read_jsonl(path: Path | None) -> list[dict]:
    rows = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines() if path else []
    except OSError:
        return rows
    for line in lines:
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def first_existing(root: Path, *patterns: str) -> Path | None:
    for pattern in patterns:
        for candidate in sorted(root.glob(pattern)):
            if candidate.is_file():
                return candidate
    return None


def sha256_file(path: Path | None) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path else None


def build_evidence(run: dict, artifacts: Path) -> dict:
    info = read_json(first_existing(artifacts, "usage/aw_info.json", "activation/aw_info.json", "**/aw_info.json"))
    usage = read_json(first_existing(artifacts, "usage/agent_usage.json", "**/agent_usage.json"))
    detection_usage = read_json(first_existing(artifacts, "detection/detection_usage.json"))
    detection = read_json(first_existing(artifacts, "detection/detection_result.json"))
    activity = read_json(first_existing(artifacts, "usage/activity/summary.json"))
    items = read_jsonl(first_existing(artifacts, "safe-outputs-items/safe-output-items.jsonl"))
    prompt = first_existing(artifacts, "activation/aw-prompts/prompt.txt", "**/aw-prompts/prompt.txt")
    template = first_existing(artifacts, "activation/aw-prompts/prompt-template.txt")
    gateway = activity.get("gateway") or {}
    firewall = activity.get("firewall") or {}
    model_config = info.get("model_config") or {}
    selection = info.get("model_selection") or {}
    tools = sorted(({"server": t.get("server_name"), "tool": t.get("tool_name"), "calls": t.get("call_count", 0),
                     "failed": t.get("failed_calls", 0)} for t in gateway.get("tools") or []),
                   key=lambda t: (str(t["server"]), str(t["tool"])))
    emitted = [{k: item[k] for k in ("type", "status", "url", "number") if k in item} for item in items]
    by_type: dict[str, int] = {}
    for item in emitted:
        by_type[item["type"]] = by_type.get(item["type"], 0) + 1
    actor = run.get("actor")
    return {
        "schema": SCHEMA_EVIDENCE,
        "run": {"id": run.get("databaseId"), "attempt": run.get("attempt"), "url": run.get("url"),
                "workflow": run.get("workflowName") or info.get("workflow_name"), "event": run.get("event"),
                "actor": actor.get("login") if isinstance(actor, dict) else actor,
                "head_sha": run.get("headSha"), "head_branch": run.get("headBranch"),
                "conclusion": run.get("conclusion"), "created_at": run.get("createdAt")},
        "agent": {"engine": info.get("engine_id"), "engine_version": info.get("agent_version"),
                  "requested_model": info.get("requested_model") or selection.get("configured_model"),
                  "resolved_model": selection.get("resolved_model") or usage.get("primary_model") or info.get("model"),
                  "compiler": info.get("cli_version"), "firewall_version": info.get("awf_version"),
                  "allowed_domains": info.get("allowed_domains") or []},
        "prompt": {"sha256": sha256_file(prompt), "template_sha256": sha256_file(template)},
        "tools": tools,
        "safe_outputs": {"emitted": emitted, "by_type": by_type},
        "usage": {"ai_credits": usage.get("ai_credits"), "max_ai_credits": model_config.get("max_ai_credits"),
                  "input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"),
                  "cache_read_tokens": usage.get("cache_read_tokens"), "cache_write_tokens": usage.get("cache_write_tokens"),
                  "detection_ai_credits": detection_usage.get("ai_credits")},
        "firewall": {"allowed_requests": firewall.get("allowed_requests"), "blocked_requests": firewall.get("blocked_requests"),
                     "blocked_domains": firewall.get("blocked_domains") or []},
        "threat_detection": {k: detection[k] for k in ("prompt_injection", "secret_leak", "malicious_patch") if k in detection},
        "integrity_filtered": (activity.get("integrity") or {}).get("total_filtered", 0),
        "completeness": {"aw_info": bool(info), "usage": bool(usage), "activity": bool(activity),
                         "prompt": prompt is not None, "detection": bool(detection)},
    }


def render_evidence_md(evidence: dict) -> str:
    run, agent, usage = evidence["run"], evidence["agent"], evidence["usage"]
    lines = [f"## Agent run evidence: {run['workflow']}", "",
             "| Field | Value |", "|---|---|",
             f"| Run | [{run['id']}]({run['url']}) attempt {run['attempt']} |",
             f"| Trigger | `{run['event']}` by `{run['actor']}` on `{run['head_branch']}` at `{str(run['head_sha'])[:12]}` |",
             f"| Outcome | `{run['conclusion']}` |",
             f"| Engine / model | `{agent['engine']}` {agent['engine_version']} / requested `{agent['requested_model']}`, "
             f"resolved `{agent['resolved_model']}` |",
             f"| Prompt SHA-256 | `{evidence['prompt']['sha256']}` |",
             f"| AI Credits | {usage['ai_credits']} of {usage['max_ai_credits']} (detection: {usage['detection_ai_credits']}) |",
             f"| Tokens | in {usage['input_tokens']}, out {usage['output_tokens']}, cache read {usage['cache_read_tokens']}, "
             f"cache write {usage['cache_write_tokens']} |",
             f"| Firewall | {evidence['firewall']['allowed_requests']} allowed, {evidence['firewall']['blocked_requests']} blocked |",
             f"| Threat detection | `{json.dumps(evidence['threat_detection'], sort_keys=True)}` |",
             f"| Integrity-filtered reads | {evidence['integrity_filtered']} |", ""]
    lines += md_table("Tools used", ["Server", "Tool", "Calls", "Failed"],
                      [[t["server"], f"`{t['tool']}`", t["calls"], t["failed"]] for t in evidence["tools"]])
    lines += md_table("Safe outputs emitted", ["Type", "Status", "Link"],
                      [[f"`{o['type']}`", o.get("status", ""), o.get("url", "")] for o in evidence["safe_outputs"]["emitted"]])
    lines += md_table("Runtime policy findings", ["Rule", "Severity", "Message"],
                      [[f"`{f['rule']}`", f["severity"], f["message"]] for f in evidence.get("policy_findings", [])])
    lines.append("Verify the signature: `gh attestation verify <file> --repo <owner>/<repo>`. "
                 "Inspect the full run: `gh aw audit <run-id>`.")
    return "\n".join(lines) + "\n"


def cmd_evidence(args: argparse.Namespace) -> int:
    evidence = build_evidence(read_json(Path(args.run_json)), Path(args.artifacts))
    if args.opa:
        policy_dir = Path(args.policy).resolve()
        payload = {"policy": load_yaml(policy_dir / "policy.yml"), "evidence": evidence}
        result = run_opa(args.opa, policy_dir / "rego", "data.governance.runtime.report", payload)
        evidence["policy_findings"] = result["flags"]
        evidence["policy_pass"] = result["pass"]
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"evidence-{evidence['run']['id']}-{evidence['run']['attempt']}.json"
    path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown = render_evidence_md(evidence)
    (out / "evidence.md").write_text(markdown, encoding="utf-8")
    print(markdown)
    write_outputs(args.github_output, {"file": path.as_posix(), "policy_pass": str(evidence.get("policy_pass", True)).lower()})
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    facts = sub.add_parser("facts", help="extract workflow facts")
    facts.add_argument("--root", default=".")
    facts.add_argument("--out", default="facts.json")
    facts.set_defaults(func=cmd_facts)
    ev = sub.add_parser("evaluate", help="evaluate static policy")
    ev.add_argument("--root", default=".")
    ev.add_argument("--policy", help="policy directory (default: <root>/policy)")
    ev.add_argument("--opa", required=True)
    ev.add_argument("--out-dir", default="governance-out")
    ev.add_argument("--today", help="override the evaluation date (YYYY-MM-DD) for reproducible runs")
    ev.add_argument("--mode", choices=["enforce", "audit"])
    ev.add_argument("--github-output")
    ev.set_defaults(func=cmd_evaluate)
    evi = sub.add_parser("evidence", help="build a run evidence record")
    evi.add_argument("--run-json", required=True)
    evi.add_argument("--artifacts", required=True)
    evi.add_argument("--out-dir", default="evidence")
    evi.add_argument("--policy", default="policy")
    evi.add_argument("--opa")
    evi.add_argument("--github-output")
    evi.set_defaults(func=cmd_evidence)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
