# Audit trail for agentic runs

Every agentic run leaves a signed, queryable record of what it was, what it was allowed to do
and what it did. The [Agent run audit workflow](../../.github/workflows/agent-audit.yml) builds
that record. It is deterministic: no model is involved.

## What is recorded

The workflow starts when any agentic workflow completes (and can be run by hand for a run id).
It reads the run's artifacts as data, never executing anything from them, and writes one
`agent-run-evidence/v1` JSON record plus a readable summary.

| Evidence | Where it comes from |
|---|---|
| Workflow, run id, attempt, trigger, actor, branch, commit, outcome | The Actions run record |
| Engine, engine version, requested and resolved model, firewall version, allowed domains | `usage/aw_info.json` |
| Prompt hash (SHA-256 of the prompt and of its template), never the prompt text | `activation/aw-prompts/` |
| Tools used: server, tool, call count, failures | `usage/activity/summary.json` (MCP gateway) |
| Safe outputs emitted: type, status, link | `safe-outputs-items/` |
| Token usage: AI Credits, input, output and cache tokens, detection cost | `usage/agent_usage.json`, `detection/detection_usage.json` |
| Firewall: allowed and blocked requests, blocked domains | `usage/activity/summary.json` |
| Threat detection: prompt injection, secret leak, malicious patch | `detection/detection_result.json` |

The record is then checked against the runtime rules in
[runtime.rego](../../policy/rego/runtime.rego): approved engine, approved resolved model, AI
Credits under the budget, no threat detected, only approved safe outputs, and no blocked
network requests. An error finding fails the audit job. The prompt is hashed rather than copied
so the evidence is safe to retain widely, and the hash lets you prove which prompt ran.

## Signed evidence

The evidence file is signed with
[`actions/attest`](https://github.com/actions/attest) using the job's OIDC identity. The
attestation binds the file's digest to this repository, workflow and commit, so a record cannot be
edited later without detection. The [Governance workflow](policy-as-code.md) does the same for
its verdict when `attest: true`.

Verify a downloaded record:

```bash
gh run download <audit-run-id> --repo <owner>/<repo> --name agent-run-evidence-<agentic-run-id>
gh attestation verify evidence-<agentic-run-id>-1.json --repo <owner>/<repo> \
  --predicate-type https://github.com/<owner>/<repo>/agent-run-evidence/v1
```

## Retention

| Item | Retention | Notes |
|---|---|---|
| `agent-run-evidence-*` and `governance-verdict` artifacts | 90 days (set in the workflows) | The upper bound is the repository or organisation setting. Export to long-term storage for longer retention. |
| Attestations | Stored with the repository's attestation records | Verifying needs the artifact; keep the artifact as long as you need to prove the claim. |
| Source artifacts of each agentic run | The repository default | `gh aw audit` needs them, so audit within the retention window. The evidence record outlives them. |
| GitHub audit log | Set by your plan or organisation policy | Stream it to your SIEM for long-term retention (see [enterprise scale](enterprise-scale.md)). |

## Querying

| Question | Command |
|---|---|
| What did this run do, in detail? | `gh aw audit <run-id> --repo <owner>/<repo>` |
| How does this run differ from a good one? | `gh aw audit <good-run-id> <bad-run-id> --repo <owner>/<repo>` |
| Token use and cost across runs of one workflow | `gh aw logs <workflow-id> --start-date -1mo` |
| Which runs breached policy? | `gh run list --workflow agent-audit.yml --status failure` |
| Evidence for one run | `gh run download <audit-run-id> --name agent-run-evidence-<agentic-run-id>` |
| Everything, as JSON, for a report | `gh run download` each evidence artifact, then `jq -s . evidence-*.json` |

The `workflow-id` is the file name of the agentic workflow without `.md`. Add `--artifacts all`
to `gh aw logs` to fetch full agent artifacts.

## Live telemetry

The agentic workflows already export OpenTelemetry through `observability.otlp` in their
frontmatter, to the collector in the `OTLP_ENDPOINT` secret. The evidence record is the durable
audit copy; OTLP gives live dashboards and alerts on the same runs. Alert on the same signals
the runtime policy checks: AI Credits per run, blocked firewall requests, and threat detection.

## Backfill and failure modes

- To rebuild evidence for an older run, dispatch the audit workflow with its run id. It works
  only while the source artifacts still exist; otherwise the record is marked incomplete.
- If a run produced no usage artifact (for example it was cancelled early), the record says so
  under `completeness` and the audit reports a warning instead of inventing values.
- Runs from forks are skipped: nothing from a fork is read in a privileged context.
