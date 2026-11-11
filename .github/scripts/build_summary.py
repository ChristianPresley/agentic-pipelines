#!/usr/bin/env python3
"""Render a Markdown build summary (tests, coverage, mutation score) for $GITHUB_STEP_SUMMARY."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from security_report import parse_xml


def tests(root: Path) -> dict:
    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0, "time": 0.0}
    failed = []
    for path in list(root.glob("surefire-reports/TEST-*.xml")) + list(root.glob("failsafe-reports/TEST-*.xml")):
        suite = parse_xml(path)
        for key in ("tests", "failures", "errors", "skipped"):
            totals[key] += int(suite.get(key, 0))
        totals["time"] += float(suite.get("time", 0))
        for case in suite.iter("testcase"):
            if case.find("failure") is not None or case.find("error") is not None:
                failed.append(f"{case.get('classname')}.{case.get('name')}")
    totals["failed_names"] = failed
    return totals


def coverage(root: Path) -> dict:
    report = root / "site" / "jacoco" / "jacoco.xml"
    if not report.exists():
        return {}
    result = {}
    for counter in parse_xml(report).findall("counter"):
        covered, missed = int(counter.get("covered")), int(counter.get("missed"))
        total = covered + missed
        result[counter.get("type")] = (covered, total, 100.0 * covered / total if total else 100.0)
    return result


def mutation(root: Path) -> tuple[int, int] | None:
    report = root / "pit-reports" / "mutations.xml"
    if not report.exists():
        return None
    killed = total = 0
    for node in parse_xml(report).iter("mutation"):
        total += 1
        killed += node.get("status") == "KILLED"
    return killed, total


def main() -> int:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "target")
    t, c, m = tests(target), coverage(target), mutation(target)
    lines = ["## Build summary", ""]
    status = "✅" if not (t["failures"] or t["errors"]) else "❌"
    lines += ["| Check | Result |", "| --- | --- |",
              f"| {status} Tests | {t['tests']} run, {t['failures']} failed, {t['errors']} errors, "
              f"{t['skipped']} skipped ({t['time']:.1f}s) |"]
    for key, label in (("LINE", "Line coverage"), ("BRANCH", "Branch coverage")):
        if key in c:
            covered, total, pct = c[key]
            lines.append(f"| 📊 {label} | {pct:.1f}% ({covered}/{total}) |")
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
