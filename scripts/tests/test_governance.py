import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


govern = load("govern", "scripts/governance/govern.py")
explain = load("explain", "scripts/explain-agentic-workflow.py")

SHA = "3d3c42e5aac5ba805825da76410c181273ba90b1"

LOCK = """\
# gh-aw-metadata: {"compiler_version":"v9","frontmatter_hash":"abcdef0123456789abcdef"}
# gh-aw-manifest: {"secrets":["GITHUB_TOKEN"],"actions":[{"repo":"actions/checkout","sha":"%s","version":"v7"}],"mcp_servers":[{"name":"github","tools":["issue_read"]}]}
name: "Demo Agent"
on:
  workflow_dispatch:
permissions: {}
jobs:
  agent:
    runs-on: ubuntu-26.04
    timeout-minutes: 20
    permissions:
      contents: read
      copilot-requests: write
    env:
      GH_AW_MAX_AI_CREDITS: "500"
    steps:
      - name: Run agent
        env:
          GH_AW_ALLOWED_DOMAINS: "api.example.org,example.org"
          GH_AW_SAFE_OUTPUTS_CONFIG: "{\\"add_comment\\":{\\"max\\":2},\\"noop\\":{\\"max\\":1}}"
        run: echo hi
      - name: Upload agent artifacts
        uses: actions/upload-artifact@%s
        with:
          name: agent
          retention-days: 7
""" % (SHA, SHA)


class GovernFacts(unittest.TestCase):
    def test_classify_use(self):
        self.assertTrue(govern.classify_use(f"actions/checkout@{SHA}")["pinned"])
        self.assertFalse(govern.classify_use("actions/checkout@v4")["pinned"])
        self.assertFalse(govern.classify_use("docker://alpine:3")["pinned"])
        self.assertTrue(govern.classify_use("docker://alpine@sha256:" + "a" * 64)["pinned"])
        self.assertEqual(govern.classify_use("./.github/actions/x")["kind"], "local")

    def test_credits(self):
        self.assertEqual(govern.credits(1000), 1000)
        self.assertEqual(govern.credits("5k"), 5000)
        self.assertIsNone(govern.credits("${{ vars.X }}"))
        self.assertIsNone(govern.credits(True))

    def test_bare_on_key_is_a_trigger(self):
        self.assertEqual(govern.triggers_of({True: {"push": None, "schedule": []}}), ["push", "schedule"])

    def test_bash_without_allowlist_is_unrestricted(self):
        self.assertTrue(govern.bash_facts({"bash": None})["unrestricted"])
        self.assertFalse(govern.bash_facts({"bash": ["ls *"]})["unrestricted"])
        self.assertFalse(govern.bash_facts({})["enabled"])


class Explainer(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.lock = self.tmp / "demo.lock.yml"
        self.lock.write_text(LOCK, encoding="utf-8")

    def test_report_covers_the_review_questions(self):
        text = explain.explain(self.lock)
        for expected in ("## Demo Agent", "workflow_dispatch", "| Token budget per run (AIC) | 500 |",
                         "copilot-requests: write", "`add_comment` | 2", "`issue_read`", "`api.example.org`",
                         "`actions/checkout`", "`agent`"):
            self.assertIn(expected, text)
        self.assertNotIn("`noop`", text.split("### Network")[0].split("### Safe outputs")[1])

    def test_output_is_deterministic(self):
        self.assertEqual(explain.explain(self.lock), explain.explain(self.lock))

    def test_check_detects_drift(self):
        out = self.tmp / "report.md"
        self.assertEqual(explain.main(["--out", str(out), str(self.lock), str(self.lock)]), 0)
        self.assertEqual(explain.main(["--out", str(out), "--check", str(self.lock), str(self.lock)]), 0)
        out.write_text(out.read_text(encoding="utf-8") + "edited\n", encoding="utf-8")
        self.assertEqual(explain.main(["--out", str(out), "--check", str(self.lock), str(self.lock)]), 1)

    def test_real_lock_files_explain_without_error(self):
        for lock in sorted((ROOT / ".github" / "workflows").glob("*.lock.yml")):
            self.assertIn("### Safe outputs", explain.explain(lock))


@unittest.skipUnless(os.environ.get("OPA"), "set OPA to the path of an opa binary to run policy evaluation tests")
class GovernEvaluate(unittest.TestCase):
    def evaluate(self, root: Path, out: Path) -> dict:
        subprocess.run(["python", str(ROOT / "scripts/governance/govern.py"), "evaluate", "--root", str(root),
                        "--policy", str(ROOT / "policy"), "--opa", os.environ["OPA"], "--out-dir", str(out),
                        "--today", "2026-01-01"], check=True, capture_output=True)
        return json.loads((out / "verdict.json").read_text(encoding="utf-8"))

    def test_this_repository_has_no_blocking_violations(self):
        with tempfile.TemporaryDirectory() as tmp:
            verdict = self.evaluate(ROOT, Path(tmp))
        self.assertEqual(verdict["blocking"], [], verdict["blocking"])

    def test_unpinned_action_and_runner_are_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            workflows = root / ".github" / "workflows"
            workflows.mkdir(parents=True)
            (workflows / "bad.yml").write_text(
                "on: push\npermissions: {}\njobs:\n  a:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n",
                encoding="utf-8")
            verdict = self.evaluate(root, Path(tmp) / "out")
        rules = {v["rule"] for v in verdict["blocking"]}
        self.assertTrue({"runner-pin", "action-pin"} <= rules, rules)


if __name__ == "__main__":
    unittest.main()
