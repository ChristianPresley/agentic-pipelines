import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("security_report.py")

SARIF = {
    "version": "2.1.0",
    "runs": [{
        "tool": {"driver": {"name": "Demo", "rules": [
            {"id": "R1", "shortDescription": {"text": "Rule one"},
             "properties": {"security-severity": "9.8"}},
            {"id": "R2", "defaultConfiguration": {"level": "note"}},
        ]}},
        "results": [
            {"ruleId": "R1", "message": {"text": "bad"}, "locations": [{"physicalLocation": {
                "artifactLocation": {"uri": "src/A.java"}, "region": {"startLine": 3}}}]},
            {"ruleId": "R2", "message": {"text": "meh"}, "locations": [{"physicalLocation": {
                "artifactLocation": {"uri": "src/B.java"}, "region": {"startLine": 7}}}]},
            {"ruleId": "R1", "message": {"text": "hidden"}, "suppressions": [{"kind": "inSource"}]},
        ],
    }],
}


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, check=False)


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "in").mkdir()
        (self.tmp / "in" / "demo.sarif").write_text(json.dumps(SARIF), encoding="utf-8")

    def report(self, *extra):
        return run("report", "--workflow", "t", "--input", str(self.tmp / "in"), "--out",
                   str(self.tmp / "findings.json"), "--summary", str(self.tmp / "summary.md"), *extra)

    def test_critical_blocks_gate_and_suppressed_results_are_skipped(self):
        result = self.report("--fail-on", "high")
        self.assertEqual(result.returncode, 1)
        data = json.loads((self.tmp / "findings.json").read_text(encoding="utf-8"))
        self.assertEqual(data["counts"]["critical"], 1)
        self.assertEqual(data["counts"]["low"], 1)
        self.assertEqual(len(data["findings"]), 2)

    def test_baseline_suppression_clears_gate(self):
        baseline = self.tmp / "baseline.json"
        baseline.write_text(json.dumps({"suppressions": [
            {"tool": "Demo", "rule_id": "R1", "path": "src/*", "reason": "accepted"}]}), encoding="utf-8")
        result = self.report("--fail-on", "high", "--baseline", str(baseline))
        self.assertEqual(result.returncode, 0)
        data = json.loads((self.tmp / "findings.json").read_text(encoding="utf-8"))
        self.assertEqual(data["suppressed"], 1)

    def test_expired_suppression_is_ignored(self):
        baseline = self.tmp / "baseline.json"
        baseline.write_text(json.dumps({"suppressions": [
            {"tool": "Demo", "rule_id": "R1", "expires": "2000-01-01"}]}), encoding="utf-8")
        self.assertEqual(self.report("--baseline", str(baseline)).returncode, 1)

    def test_dedupe_skips_tracked_groups(self):
        self.report("--fail-on", "none")
        (self.tmp / "in2").mkdir()
        (self.tmp / "in2" / "findings-t.json").write_text(
            (self.tmp / "findings.json").read_text(encoding="utf-8"), encoding="utf-8")
        first = run("dedupe", "--input", str(self.tmp / "in2"), "--issues", str(self.tmp / "none.json"),
                    "--out", str(self.tmp / "new.json"), "--min-severity", "low")
        self.assertEqual(first.returncode, 0)
        new = json.loads((self.tmp / "new.json").read_text(encoding="utf-8"))
        self.assertEqual(len(new["new_groups"]), 2)
        marker = new["new_groups"][0]["marker"]
        (self.tmp / "issues.json").write_text(json.dumps([{"body": f"text {marker}"}]), encoding="utf-8")
        run("dedupe", "--input", str(self.tmp / "in2"), "--issues", str(self.tmp / "issues.json"),
            "--out", str(self.tmp / "new2.json"), "--min-severity", "low")
        again = json.loads((self.tmp / "new2.json").read_text(encoding="utf-8"))
        self.assertEqual(again["already_tracked"], 1)
        self.assertEqual(len(again["new_groups"]), 1)
        second = new["new_groups"][1]
        title = f"medium {second['tool']}: {second['rule_id']} (2 locations)"
        (self.tmp / "issues2.json").write_text(
            json.dumps([{"body": f"`{marker}`"}, {"title": title, "body": "no marker"}]), encoding="utf-8")
        run("dedupe", "--input", str(self.tmp / "in2"), "--issues", str(self.tmp / "issues2.json"),
            "--out", str(self.tmp / "new3.json"), "--min-severity", "low")
        titled = json.loads((self.tmp / "new3.json").read_text(encoding="utf-8"))
        self.assertEqual(titled["already_tracked"], 2)
        self.assertEqual(titled["new_groups"], [])


if __name__ == "__main__":
    unittest.main()
