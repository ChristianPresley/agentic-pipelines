# ADR 0001: Policy engine for governance

Status: accepted

## Context

Enterprise adopters want governance as an enforceable, executable pipeline: organisation
specific policy as code, deterministic, auditable, and reviewable by people who do not write
workflows. The rules must cover agentic workflow definitions (permissions, safe outputs,
network, engine and model, runners, action pinning), token budgets and the repository's
pipeline gate. The evaluator runs in GitHub Actions, in other repositories through a reusable
workflow, and on a developer machine.

## Options considered

| Option | Strengths | Weaknesses |
|---|---|---|
| Open Policy Agent with Rego | Industry standard policy language; built-in unit tests (`opa test`); one static binary; decisions are pure functions of a JSON input; widely understood by platform and security teams | A new language to learn; needs a fact extraction step for YAML |
| Conftest (OPA wrapper) | Parses YAML directly | Another tool to pin and trust; the lock files are too large and too generated to evaluate raw, and our facts need preprocessing anyway |
| CEL or JSON Schema | Simple, embeddable | Weak at cross-document rules (pipeline gate completeness, waivers matching violations); no native test framework |
| Plain Python checks | Fastest to write | Policy is code that only its author can review; no separation between parameters and logic; hard to share across repositories |
| GitHub rulesets and required workflows alone | Enforced by the platform | Cannot inspect gh-aw frontmatter, budgets or safe outputs; complements the choice, does not replace it |

## Decision

Use OPA with Rego for decisions and a small Python program for fact extraction.

- `scripts/governance/govern.py` turns workflows, lock files and frontmatter into a facts
  document. It makes no decisions.
- `policy/policy.yml` holds the organisation's parameters (allowlists, ceilings, limits).
  Changing a number never needs Rego knowledge.
- `policy/rego/*.rego` holds the rules, each with a unit test, in two packages:
  `governance.static` for definitions and `governance.runtime` for evidence from a finished run.
- `policy/waivers.yml` holds time-boxed exceptions, evaluated by the same Rego so that an
  expired waiver is a violation rather than a silent gap.
- The evaluator input (`governance-input.json`) is archived with every verdict. The evaluation
  date is part of the input, so a verdict can be replayed exactly.

OPA is installed as the static Linux binary at an exact version (`1.22.3`) and verified against a
SHA-512 digest before use. The Python dependency is installed with `--require-hashes`, also with
SHA-512 digests.

## Consequences

- Policy is reviewable and testable like any other code, and CODEOWNERS can give the policy
  directory to a separate team.
- The same evaluator and policy run in the pipeline, in the audit trail and locally, so a
  developer sees the verdict before pushing.
- Teams must learn enough Rego to add rules. Parameter changes stay in YAML.
- Bumping OPA is a deliberate change: update the version and digest together in
  `governance.yml`, `agent-audit.yml` and `lint.yml`.
- Moving the policy to a central repository needs no change to the rules, only to the
  `policy-repository` input (see [enterprise scale](../enterprise-scale.md)).
