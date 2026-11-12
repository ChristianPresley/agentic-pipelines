#!/usr/bin/env python3
"""Render a Markdown build summary (TRX tests, Cobertura coverage, Stryker mutation score) for $GITHUB_STEP_SUMMARY."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from security_report import parse_xml


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def tests(root: Path) -> dict:
    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0, "time": 0.0}
    failed = []
    for path in root.rglob("*.trx"):
        for node in parse_xml(path).iter():
            tag = local(node.tag)
            if tag == "Counters":
                totals["tests"] += int(node.get("total", 0))
                totals["failures"] += int(node.get("failed", 0))
                totals["errors"] += int(node.get("error", 0)) + int(node.get("timeout", 0)) + int(node.get("aborted", 0))
                totals["skipped"] += int(node.get("notExecuted", 0))
            elif tag == "UnitTestResult":
                if node.get("outcome") == "Failed":
                    failed.append(node.get("testName", "unknown"))
                h, m, s = (node.get("duration") or "0:0:0").split(":")[:3]
                totals["time"] += int(h) * 3600 + int(m) * 60 + float(s)
    totals["failed_names"] = failed
    return totals


def coverage(root: Path) -> dict:
    result = {}
    for report in root.rglob("coverage.cobertura.xml"):
        node = parse_xml(report)
        for key, attribute in (("LINE", "line-rate"), ("BRANCH", "branch-rate")):
            if node.get(attribute) is not None:
                pct = 100.0 * float(node.get(attribute))
                result[key] = (0, 0, pct)
    return result


def mutation(root: Path) -> tuple[int, int] | None:
    reports = list(root.rglob("mutation-report.json"))
    if not reports:
        return None
    killed = total = 0
    for report in reports:
        for file_report in json.loads(report.read_text(encoding="utf-8")).get("files", {}).values():
            for mutant in file_report.get("mutants", []):
                if mutant.get("status") in ("Ignored", "CompileError"):
                    continue
                total += 1
                killed += mutant.get("status") in ("Killed", "Timeout")
    return killed, total

def main() -> int:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "artifacts")
    t, c, m = tests(target), coverage(target), mutation(target)
    lines = ["## Build summary", ""]
    status = "✅" if not (t["failures"] or t["errors"]) else "❌"
    lines += ["| Check | Result |", "| --- | --- |",
              f"| {status} Tests | {t['tests']} run, {t['failures']} failed, {t['errors']} errors, "
              f"{t['skipped']} skipped ({t['time']:.1f}s) |"]
    for key, label in (("LINE", "Line coverage"), ("BRANCH", "Branch coverage")):
        if key in c:
            covered, total, pct = c[key]
            lines.append(f"| 📊 {label} | {pct:.1f}% |")
    if m:
        pct = 100.0 * m[0] / m[1] if m[1] else 100.0
        lines.append(f"| 🧬 Mutation score | {pct:.1f}% ({m[0]}/{m[1]} killed) |")
    if t["failed_names"]:
        lines += ["", "### Failing tests", ""] + [f"- `{name}`" for name in t["failed_names"][:30]]
    document = {"tests": {k: v for k, v in t.items() if k != "failed_names"},
                "coverage": {k: round(v[2], 2) for k, v in c.items()},
                "mutation": None if not m else {"killed": m[0], "total": m[1]}}
    (target / "build-summary.json").write_text(json.dumps(document, indent=2), encoding="utf-8")
    output = "\n".join(lines) + "\n"
    destination = os.environ.get("GITHUB_STEP_SUMMARY")
    if destination:
        with open(destination, "a", encoding="utf-8") as handle:
            handle.write(output)
    else:
        print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
