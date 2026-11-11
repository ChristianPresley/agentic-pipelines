#!/usr/bin/env python3
"""Normalize scanner output into a common findings format.

Subcommands
  report  Parse SARIF / PMD / Checkstyle / ZAP / JUnit results, write findings.json,
          render a Markdown step summary and apply a severity gate with a baseline.
  dedupe  Group findings by tool+rule and drop groups that already have an open issue.

Only the Python standard library is used so the script runs on any runner.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import sys
import xml.etree.ElementTree as ET  # nosemgrep
from datetime import date
from pathlib import Path

SEVERITIES = ["critical", "high", "medium", "low", "info"]
RANK = {name: index for index, name in enumerate(SEVERITIES)}
MARKER = "finding-fingerprint"


def parse_xml(path):
    """Parse an XML report, refusing entity declarations (XXE and entity expansion)."""
    data = Path(path).read_bytes()
    if b"<!ENTITY" in data:
        raise ValueError(f"{path}: entity declarations are not allowed")
    return ET.fromstring(data)  # nosemgrep


def fingerprint(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]


def sarif_severity(result: dict, rule: dict) -> str:
    for source in (result.get("properties", {}), rule.get("properties", {})):
        score = source.get("security-severity")
        if score is not None:
            try:
                value = float(score)
            except (TypeError, ValueError):
                continue
            if value >= 9.0:
                return "critical"
            if value >= 7.0:
                return "high"
            if value >= 4.0:
                return "medium"
            return "low"
    level = result.get("level") or rule.get("defaultConfiguration", {}).get("level") or "warning"
    return {"error": "high", "warning": "medium", "note": "low", "none": "info"}.get(level, "medium")


def make_finding(tool, rule_id, severity, title, path, line, message, uri=""):
    path = (path or "").replace("\\", "/")
    for prefix in ("file:///github/workspace/", "file://", "/github/workspace/"):
        if path.startswith(prefix):
            path = path[len(prefix):]
    workspace = os.environ.get("GITHUB_WORKSPACE", "").replace("\\", "/")
    if workspace and path.startswith(workspace + "/"):
        path = path[len(workspace) + 1:]
    return {
        "fingerprint": fingerprint(tool, rule_id, path),
        "group": fingerprint(tool, rule_id),
        "tool": tool,
        "rule_id": rule_id,
        "severity": severity,
        "title": (title or rule_id)[:200],
        "path": path,
        "line": line or 0,
        "message": (message or "")[:500],
        "help_uri": uri or "",
    }


def parse_sarif(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    findings = []
    for run in data.get("runs", []):
        driver = run.get("tool", {}).get("driver", {})
        tool = driver.get("name", path.stem)
        rules = {rule.get("id"): rule for rule in driver.get("rules", [])}
        for result in run.get("results", []):
            if result.get("suppressions"):
                continue
            rule_id = result.get("ruleId") or "unknown"
            rule = rules.get(rule_id, {})
            location = (result.get("locations") or [{}])[0].get("physicalLocation", {})
            uri = location.get("artifactLocation", {}).get("uri", "")
            line = location.get("region", {}).get("startLine", 0)
            message = result.get("message", {}).get("text", "")
            title = rule.get("shortDescription", {}).get("text") or rule.get("name") or rule_id
            findings.append(
                make_finding(tool, rule_id, sarif_severity(result, rule), title, uri, line, message,
                             rule.get("helpUri", ""))
            )
    return findings


def parse_pmd(path: Path) -> list[dict]:
    findings = []
    for file_node in parse_xml(path).iter():
        if not file_node.tag.endswith("file"):
            continue
        for violation in file_node:
            if not violation.tag.endswith("violation"):
                continue
            priority = int(violation.get("priority", "3"))
            severity = "high" if priority <= 2 else "medium" if priority == 3 else "low"
            findings.append(
                make_finding("PMD", violation.get("rule", "unknown"), severity, violation.get("rule"),
                             file_node.get("name"), int(violation.get("beginline", "0")),
                             (violation.text or "").strip(), violation.get("externalInfoUrl", ""))
            )
    return findings


def parse_checkstyle(path: Path) -> list[dict]:
    findings = []
    for file_node in parse_xml(path).iter("file"):
        for error in file_node.iter("error"):
            severity = "medium" if error.get("severity") == "error" else "low"
            rule_id = (error.get("source") or "checkstyle").rsplit(".", 1)[-1]
            findings.append(
                make_finding("Checkstyle", rule_id, severity, rule_id, file_node.get("name"),
                             int(error.get("line", "0")), error.get("message", ""))
            )
    return findings


def parse_zap(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    risk = {"3": "high", "2": "medium", "1": "low", "0": "info"}
    findings = []
    for site in data.get("site", []):
        for alert in site.get("alerts", []):
            instances = alert.get("instances", [])
            target = instances[0].get("uri", site.get("@name", "")) if instances else site.get("@name", "")
            findings.append(
                make_finding("ZAP", str(alert.get("pluginid", alert.get("alertRef", "unknown"))),
                             risk.get(str(alert.get("riskcode", "1")), "medium"), alert.get("name"),
                             target.split("?")[0], 0, f"{alert.get('name')} ({len(instances)} instance(s))")
            )
    return findings


def parse_junit(path: Path, tool: str, severity: str) -> list[dict]:
    findings = []
    for case in parse_xml(path).iter("testcase"):
        for kind in ("failure", "error"):
            node = case.find(kind)
            if node is not None:
                name = f"{case.get('classname', '')}.{case.get('name', '')}".strip(".")
                findings.append(
                    make_finding(tool, name, severity, name, case.get("classname", ""), 0,
                                 (node.get("message") or node.text or "").strip())
                )
    return findings


def collect(inputs: list[str]) -> list[dict]:
    findings: list[dict] = []
    for root in inputs:
        base = Path(root)
        if not base.exists():
            print(f"warning: input path not found: {root}", file=sys.stderr)
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            name = path.name
            try:
                if name.endswith((".sarif", ".sarif.json")) or name == "spotbugsSarif.json":
                    findings += parse_sarif(path)
                elif name == "pmd.xml":
                    findings += parse_pmd(path)
                elif name == "checkstyle-result.xml":
                    findings += parse_checkstyle(path)
                elif name in ("report_json.json", "zap-report.json"):
                    findings += parse_zap(path)
                elif name.startswith("schemathesis") and name.endswith(".xml"):
                    findings += parse_junit(path, "Schemathesis", "medium")
                elif name.startswith("TEST-") and name.endswith(".xml") and "jazzer" in str(path).lower():
                    findings += parse_junit(path, "Jazzer", "high")
            except (ET.ParseError, json.JSONDecodeError, KeyError, ValueError) as error:
                print(f"warning: could not parse {path}: {error}", file=sys.stderr)
    unique = {}
    for finding in findings:
        key = (finding["fingerprint"], finding["line"], finding["message"])
        unique[key] = finding
    return sorted(unique.values(), key=lambda f: (RANK[f["severity"]], f["tool"], f["path"], f["line"]))


def load_suppressions(path: str | None) -> list[dict]:
    if not path or not Path(path).exists():
        return []
    entries = json.loads(Path(path).read_text(encoding="utf-8")).get("suppressions", [])
    today = date.today().isoformat()
    return [entry for entry in entries if not entry.get("expires") or entry["expires"] >= today]


def is_suppressed(finding: dict, suppressions: list[dict]) -> bool:
    for entry in suppressions:
        if entry.get("fingerprint") == finding["fingerprint"]:
            return True
        if entry.get("rule_id") == finding["rule_id"] and entry.get("tool", finding["tool"]) == finding["tool"]:
            pattern = entry.get("path")
            if not pattern or fnmatch.fnmatch(finding["path"], pattern):
                return True
    return False


def escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").replace("<", "&lt;").replace(">", "&gt;")


def render_summary(workflow: str, findings: list[dict], suppressed: list[dict], gate: dict) -> str:
    counts = {name: sum(1 for f in findings if f["severity"] == name) for name in SEVERITIES}
    icon = {"critical": "🟥", "high": "🟧", "medium": "🟨", "low": "🟦", "info": "⬜"}
    lines = [f"## {workflow} security results", ""]
    status = "✅ Passed" if not gate["blocking"] else f"❌ Failed ({len(gate['blocking'])} blocking)"
    lines += [f"**Gate (`fail-on: {gate['fail_on']}`):** {status}", ""]
    lines += ["| Severity | Open | Suppressed |", "| --- | ---: | ---: |"]
    for name in SEVERITIES:
        hidden = sum(1 for f in suppressed if f["severity"] == name)
        lines.append(f"| {icon[name]} {name} | {counts[name]} | {hidden} |")
    by_tool: dict[str, int] = {}
    for finding in findings:
        by_tool[finding["tool"]] = by_tool.get(finding["tool"], 0) + 1
    if by_tool:
        lines += ["", "### By tool", "", "| Tool | Findings |", "| --- | ---: |"]
        lines += [f"| {escape(tool)} | {count} |" for tool, count in sorted(by_tool.items())]
    if findings:
        lines += ["", "### Top findings", "", "| Severity | Tool | Rule | Location | Message |",
                  "| --- | --- | --- | --- | --- |"]
        for finding in findings[:25]:
            location = f"{finding['path']}:{finding['line']}" if finding["line"] else finding["path"]
            lines.append(
                f"| {icon[finding['severity']]} {finding['severity']} | {escape(finding['tool'])} | "
                f"`{escape(finding['rule_id'])}` | `{escape(location)}` | {escape(finding['message'][:140])} |"
            )
        if len(findings) > 25:
            lines.append(f"\n_{len(findings) - 25} more finding(s) in the `findings-{workflow}` artifact._")
    else:
        lines += ["", "No open findings. 🎉"]
    return "\n".join(lines) + "\n"


def command_report(args: argparse.Namespace) -> int:
    findings = collect(args.input)
    suppressions = load_suppressions(args.baseline)
    suppressed = [f for f in findings if is_suppressed(f, suppressions)]
    open_findings = [f for f in findings if not is_suppressed(f, suppressions)]
    threshold = RANK.get(args.fail_on)
    blocking = [] if threshold is None else [f for f in open_findings if RANK[f["severity"]] <= threshold]
    gate = {"fail_on": args.fail_on, "blocking": blocking}

    document = {
        "schema": 1,
        "workflow": args.workflow,
        "run": {
            "id": os.environ.get("GITHUB_RUN_ID", ""),
            "attempt": os.environ.get("GITHUB_RUN_ATTEMPT", ""),
            "sha": os.environ.get("GITHUB_SHA", ""),
            "ref": os.environ.get("GITHUB_REF", ""),
            "repository": os.environ.get("GITHUB_REPOSITORY", ""),
        },
        "counts": {name: sum(1 for f in open_findings if f["severity"] == name) for name in SEVERITIES},
        "suppressed": len(suppressed),
        "blocking": len(blocking),
        "findings": open_findings,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    markdown = render_summary(args.workflow, open_findings, suppressed, gate)
    target = args.summary or os.environ.get("GITHUB_STEP_SUMMARY")
    if target:
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(markdown)
    else:
        print(markdown)
    for finding in blocking[:50]:
        print(f"::error file={finding['path']},line={finding['line'] or 1}::[{finding['tool']}] "
              f"{finding['rule_id']}: {finding['message'][:200]}")
    return 1 if blocking and not args.no_fail else 0


def command_dedupe(args: argparse.Namespace) -> int:
    existing = set()
    titles: list[str] = []
    issues = json.loads(Path(args.issues).read_text(encoding="utf-8")) if Path(args.issues).exists() else []
    for issue in issues:
        body = issue.get("body") or ""
        start = 0
        while (start := body.find(f"{MARKER}:", start)) != -1:
            start += len(MARKER) + 1
            existing.add(body[start:start + 16].strip())
        titles.append(issue.get("title") or "")
    groups: dict[str, dict] = {}
    for path in sorted(Path(args.input).rglob("findings*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        for finding in document.get("findings", []):
            if RANK[finding["severity"]] > RANK[args.min_severity]:
                continue
            group = groups.setdefault(finding["group"], {
                "group_fingerprint": finding["group"], "marker": f"{MARKER}:{finding['group']}",
                "tool": finding["tool"], "rule_id": finding["rule_id"], "title": finding["title"],
                "severity": finding["severity"], "help_uri": finding["help_uri"],
                "source_workflow": document.get("workflow"), "locations": [],
            })
            if RANK[finding["severity"]] < RANK[group["severity"]]:
                group["severity"] = finding["severity"]
            if len(group["locations"]) < 20:
                group["locations"].append({"path": finding["path"], "line": finding["line"],
                                           "message": finding["message"]})
    def tracked(group: dict) -> bool:
        if group["group_fingerprint"] in existing:
            return True
        needle = f"{group['tool']}: {group['rule_id']} ("
        return any(needle in title for title in titles)

    new_groups = [g for g in groups.values() if not tracked(g)]
    new_groups.sort(key=lambda g: (RANK[g["severity"]], g["tool"], g["rule_id"]))
    result = {"total_groups": len(groups), "already_tracked": len(groups) - len(new_groups),
              "new_groups": new_groups[: args.limit], "truncated": max(0, len(new_groups) - args.limit)}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"{result['total_groups']} group(s), {result['already_tracked']} already tracked, "
          f"{len(result['new_groups'])} new")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    report = sub.add_parser("report")
    report.add_argument("--workflow", required=True)
    report.add_argument("--input", action="append", required=True)
    report.add_argument("--out", required=True)
    report.add_argument("--summary")
    report.add_argument("--baseline")
    report.add_argument("--fail-on", default="high", choices=[*SEVERITIES, "none"])
    report.add_argument("--no-fail", action="store_true")
    report.set_defaults(func=command_report)

    dedupe = sub.add_parser("dedupe")
    dedupe.add_argument("--input", required=True)
    dedupe.add_argument("--issues", required=True)
    dedupe.add_argument("--out", required=True)
    dedupe.add_argument("--min-severity", default="medium", choices=SEVERITIES)
    dedupe.add_argument("--limit", type=int, default=10)
    dedupe.set_defaults(func=command_dedupe)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
