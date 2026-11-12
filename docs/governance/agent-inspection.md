# Inspecting an agent

Reviewers should not have to read a 3,000-line compiled workflow to learn what an agent can do
or did. There are three levels, from a summary to the raw run.

| Level | Question | Where |
|---|---|---|
| 1. Definition | What is this agent allowed to do? | [Generated inspection reports](agent-inspection-reports.md) |
| 2. Run | What did this run actually do? | The run page in the Actions tab, and `gh aw audit` |
| 3. Evidence | Can I prove it later? | The signed [evidence record](audit-trail.md) |

## Level 1: read the definition

`scripts/explain-agentic-workflow.py` parses a compiled `*.lock.yml` (it never executes it) and
prints a report that answers the review questions.

```bash
python scripts/explain-agentic-workflow.py .github/workflows/security-triage.lock.yml
python scripts/explain-agentic-workflow.py --all --out docs/governance/agent-inspection-reports.md
```

| Report section | What it tells you |
|---|---|
| Overview | Who starts it, engine, model, per-run and per-day token budgets |
| Jobs and permissions | Every job, what it needs, where it runs, its timeout and permissions |
| Tools | Each MCP server and the exact tools the agent can call |
| Safe outputs | The only actions it may request, with a per-run cap, and whether threat detection runs |
| Network | The firewall allowlist the agent runs behind |
| Secrets and actions | Secrets referenced and every action with its pinned commit |
| Evidence the run leaves behind | Artifacts uploaded, by which job, with what retention |
| Steps per job | The step names in order, collapsed by default |

The reports for every agentic workflow in this repository are committed in
[agent-inspection-reports.md](agent-inspection-reports.md). CI regenerates them and fails if the
committed copy is stale, so the page you read always matches the lock files. The script has unit
tests in `scripts/tests`.

How to read the "Jobs and permissions" table: the `agent` job holds only `contents: read` style
access plus `copilot-requests: write` for the model token. Anything that writes to the
repository happens afterwards in `safe_outputs`, after `detection` has scanned the agent's
output. The [policy](policy-as-code.md) enforces that split.

## Level 2: click through a run

Pick any run of an agentic workflow in the **Actions** tab and follow this path.

1. **Run summary.** Open the run. The summary shows the job graph: `activation`, `agent`,
   `detection`, `safe_outputs`, `conclusion`. A red or skipped job tells you where it stopped.
2. **Agent job.** Open `agent` and expand the steps. The step names match the "Steps per job"
   section of the generated report. The agent's tool calls, and each denied network request, are
   in the job log.
3. **Detection job.** Open `detection`. It reports whether the output contained a prompt
   injection, a leaked secret or a malicious patch. A positive result blocks the safe outputs.
4. **Safe outputs job.** Open `safe_outputs`. Its log lists each issue, comment, discussion or
   pull request it created, with links. Everything the agent changed is here.
5. **Artifacts.** At the bottom of the run summary, download the artifacts.

   | Artifact | Contents |
   |---|---|
   | `activation` | The prompt as rendered and its template |
   | `usage` | Engine and model, token and AI Credit usage, MCP gateway and firewall activity |
   | `agent` | The agent's output, logs and any patch |
   | `detection` | The threat detection verdict |
   | `safe-outputs-items` | One record per safe output emitted |

6. **Audit summary.** The **Agent run audit** workflow run for the same commit shows the
   [evidence record](audit-trail.md) as a table: model, prompt hash, tools, safe outputs, AI
   Credits, firewall and policy findings.

From the command line, one command does the same analysis:

```bash
gh aw audit <run-id> --repo <owner>/<repo> --parse
```

`--parse` adds `log.md` and `firewall.md`, a readable agent transcript and the firewall decisions.
Pass two run ids to compare a failing run with a good one.

## Level 3: prove it later

Download the signed evidence record and verify its attestation as described in
[audit trail](audit-trail.md#signed-evidence). The record includes the SHA-256 of the prompt, so you
can show which prompt produced which outputs without keeping the prompt text.

## Live view

The agentic workflows export OpenTelemetry through `observability.otlp`. Use your tracing
backend for per-step timing and to follow runs across workflows. Use the evidence records for
the authoritative, signed copy.
