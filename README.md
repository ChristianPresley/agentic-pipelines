# agentic-pipelines

A Java 21 / Spring Boot "Hello World" REST API (`GET /api/hello?name=`) wrapped in a security pipeline
of FOSS scanners whose results are read by [GitHub Agentic Workflows](https://github.com/github/gh-aw)
agents. Agents open deduplicated GitHub Issues, comment on PRs, publish Discussions and notify Slack and Teams.

**Documentation site:** <https://christianpresley.github.io/agentic-pipelines/> (pipeline explorer, workflow reference, agents, releases and setup, in English and French). Built by `site/build.py` and deployed by the `Pages` workflow.

## Pipeline

[`pipeline.yml`](.github/workflows/pipeline.yml) is the single entry point. It runs on pull requests, pushes to `main`,
a nightly schedule and manual dispatch, and calls the reusable workflows below (`workflow_call`; they have no
triggers of their own beyond manual dispatch). One commit produces one `Pipeline` run, and a final **Pipeline gate**
job is the single required status check.

| When | Stages |
|---|---|
| Pull request | Plan → lint (only if `.github/` changed), CI build, SAST, SCA + dependency review, secrets/IaC, container, E2E. Docs/site/`*.md`-only changes skip everything but the plan and gate. Runs cancel when superseded. |
| Push to `main` | Same as a PR plus DAST and the GHCR publish with Cosign. |
| Nightly / dispatch | Everything plus PIT mutation testing, dependency freshness and time-boxed Jazzer fuzzing. |
| Weekly | OpenSSF Scorecard (`scorecard.yml`). |

| Workflow | Tools | Output artifacts |
|---|---|---|
| `ci.yml` | Maven verify, Enforcer, JaCoCo (≥80%), Failsafe ITs, PIT mutation (nightly), versions plugin | test/coverage summary |
| `sast.yml` | CodeQL, Semgrep, SpotBugs + FindSecBugs, PMD, Checkstyle | `*-results`, `findings-sast` |
| `sca.yml` | OSV-Scanner, Trivy fs, Dependency Review, CycloneDX + Syft SBOM | `findings-sca` |
| `secrets-iac.yml` | Gitleaks, Hadolint | `findings-secrets-iac` |
| `container.yml` | Buildx, Trivy image, Syft, GHCR publish + Cosign keyless (main) | `findings-container` |
| `dast.yml` | OWASP ZAP API scan, Schemathesis | `findings-dast` |
| `fuzz.yml` | Jazzer (time-boxed fuzzing, nightly) | `findings-fuzz` |
| `scorecard.yml` | OpenSSF Scorecard | SARIF |
| `lint.yml` | actionlint, zizmor, gh-aw lock drift check | |
| `observability-otel.yml` | otel-cicd-action traces for Pipeline, Scorecard and Release (needs `OTLP_ENDPOINT`) | |

Every scanner workflow ends with a summary job: `.github/scripts/security_report.py` normalizes SARIF/XML/JSON
to `findings-<workflow>` artifacts, writes a Markdown step summary, and gates on **new** HIGH/CRITICAL findings
(baseline in `.security/baseline.json`). Summaries always run.

## Agentic workflows (`.github/workflows/*.md`, compiled to `*.lock.yml`)

- `security-triage` – on completion of the `Pipeline` run on `main`: pre-steps download that run's `findings-*`, dedupe against
  existing issues by `<!-- finding-fingerprint:… -->`; the agent opens ≤10 issues (one per rule/CVE, expire 30d),
  and notifies Slack/Teams. Scanner output is treated as untrusted data.
- `security-remediation` – manually dispatched with an issue number: reads a `security-finding` issue, implements a minimal fix with a test, runs `./mvnw verify` and opens a PR (`Closes #n`) for human review.
- `pr-security-reviewer` – one security review comment per PR (forks skipped; docs-only PRs skipped).
- `daily-security-report` – Discussion (category `Security`) plus Slack/Teams.
- `release-readiness` – dispatched by the Release workflow before the approval gate; opens a GO / NO-GO issue
  with gate results, changes since the last release and a reviewer checklist.
- `release-notes` – after a successful Release run, prepends a Highlights section to the GitHub Release notes.
- `pipeline-failure-analyst` – on failed Pipeline or Release runs on `main` or tags (not PRs): classifies the
  root cause and opens one deduplicated `pipeline-failure` issue (or comments on the existing one).

## CI/CD and releases

| Workflow | Purpose |
|---|---|
| `ci.yml` | Build, unit, property, fuzz-regression and integration tests (Failsafe), coverage, static analysis |
| `e2e.yml` | Builds the container image, starts it and runs `HelloApiE2E` against it (reused by Pipeline and Release) |
| `cut-release.yml` | Manual: picks the next semver (patch/minor/major, optional `-rc.N`), tags `main`, dispatches Release |
| `release.yml` | Tag-driven release pipeline (below) |

Release flow for tag `vX.Y.Z` (or `vX.Y.Z-rc.N`, published as a pre-release):

1. **Validate**: semver tag, commit is on `main`, no existing release.
2. **Gates**: the `Pipeline` run for the tagged commit must have passed (CI, SAST, SCA, Secrets and IaC, Container, DAST), and no open `security-finding` issue labelled `severity:critical` or `severity:high` may exist.
3. **Build** with the version stamped from the tag, full `mvn verify`, SHA-512 sums and a CycloneDX SBOM of the jar.
4. **E2E** against the exact image built from the tag.
5. **Readiness agent** posts a go/no-go issue while the run waits.
6. **Approval**: the `production` environment requires a reviewer and only allows `v*` tags.
7. **Publish**: image to GHCR (semver, `major.minor`, `major`, `latest` for stable) with Cosign keyless signature,
   SLSA provenance and SBOM attestations; Maven package to GitHub Packages.
8. **GitHub Release** with the jar, `SHA512SUMS` and SBOM; the release-notes agent then adds Highlights.

Start a release with **Actions → Cut release**, or `git tag -a vX.Y.Z -m "Release vX.Y.Z" && git push origin vX.Y.Z`.
`v*` tags are immutable (repository ruleset: no update or delete).

## Setup

1. `gh extension install github/gh-aw`, then `gh aw compile` after editing any `.md` workflow (CI checks for drift).
2. Copilot auth: the agentic workflows declare `permissions: copilot-requests: write`, so inference uses the
   Actions token (no PAT) when the owner has a Copilot plan with centralized billing. Otherwise remove that
   permission and set `COPILOT_GITHUB_TOKEN` (fine-grained PAT with Copilot Requests) as a fallback.
   Other secrets: `SLACK_WEBHOOK_URL`, `TEAMS_WEBHOOK_URL`, optional `OTLP_ENDPOINT`, `OTLP_TOKEN`, `OTLP_HEADERS`.
3. Enable Discussions and create a `Security` category; create labels `security-finding`, `automated`, `release`,
   `pipeline-failure` and `severity:critical|high|medium|low`.
   Create a `production` environment with required reviewers (deployment tags `v*` only).
4. Enable code scanning, Dependabot alerts, and branch protection requiring CI, SAST, SCA, Secrets and IaC.

## Local build

```
./mvnw verify            # tests, coverage, Checkstyle, PMD, SpotBugs
./mvnw verify -Pmutation # adds PIT
```

### Containers on Windows without Docker (WSLC)

Local container workflows can use [WSL containers](https://learn.microsoft.com/en-us/windows/wsl/wsl-container) (`wslc`, WSL 2.9.3+; update with `wsl --update`). The CLI mirrors Docker's:

```
wslc build -t hello-api .
wslc run -d --name hello-api -p 8080:8080 hello-api
```

`scripts/e2e-local.ps1` builds the image, starts it, waits for readiness and runs the E2E suite (needs a host JDK). Use `-Engine docker` to run it with Docker instead. CI keeps using Docker on the Linux runners (Buildx, Cosign, attestations and the ZAP/Schemathesis containers depend on it).

## Fuzzing design and reports

[![Beyond pass/fail: GitHub Agentic Workflows. CI/CD pipeline with fuzzing stages and evidence gates, plus seven agentic workflows (triage, PR review, daily report, failure analysis, release readiness, release notes, remediation) with safe-output limits and human approval.](docs/visuals/pipeline-overview.svg)](docs/fuzzing-pipeline-explorer.html)

- [Interactive pipeline explorer](docs/fuzzing-pipeline-explorer.html): select
  any of the 23 stage cards to open its details. Product logos show where each
  tool is used. Switch between English and French, or use the stage list,
  display settings, and keyboard controls. Open the HTML file in a browser;
  no build is needed. Keep its local assets with it.
- [French writing and terminology standard](docs/french-technical-style.md):
  controlled vocabulary, technical distinctions, and review rules. The
  explorer includes a bilingual glossary of 36 technical terms.
- [CI/CD pipeline view](docs/fuzzing-pipeline-view.md): stage-based presentation
  with parallel test lanes, quality gates, release approval, and feedback.
- [Dual-surface fuzzing system design](docs/fuzzing-system-design.md): Java/HTTP
  targets, workflow mutation campaigns, replay/corpus strategy, evidence gates,
  reporting contracts, and rollout criteria.
- [Executive baseline report](docs/reports/fuzzing-summary-2026-11-10.md) and
  [technical evidence and connection report](docs/reports/fuzzing-evidence-2026-11-10.md):
  measured CI artifacts, reporting gaps, and Mermaid connection diagrams.

These documents describe the proposed extension and a dated baseline; they do
not deploy new fuzzing infrastructure. Choose the pipeline view for a traditional
CI/CD presentation or the original connection maps for the detailed graph view.

## Notes

- Dependencies and actions are pinned to exact versions or SHAs. The Maven wrapper, Gitleaks and OSV-Scanner
  binaries are verified with SHA-256 because upstream does not publish SHA-512.
- Integration tests use Failsafe + `@SpringBootTest` (no Testcontainers; the app has no external dependencies).
- The Dockerfile and container workflow were not exercised locally (no Docker available during authoring).
