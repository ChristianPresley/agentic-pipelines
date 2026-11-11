# GitHub Actions recordings

Playwright (Microsoft Edge, headless, 1280x800) recordings of every GitHub Actions run triggered by the push of
`c78923e` to `main` of [ChristianPresley/agentic-pipelines](https://github.com/ChristianPresley/agentic-pipelines).
Each run page was reloaded about every 10 s until the run reached a terminal state (recording cap about 8 min per
video), then held for about 3 s on the final state. Each run also has a final full-page screenshot.
Job logs require a login, so the recordings show the run summary page (job graph, job list, statuses).

Repository Actions tab: [start of session](./actions-tab-start.webm) ([png](./actions-tab-start.png)) ·
[end of session](./actions-tab-end.webm) ([png](./actions-tab-end.png)).

## Runs

| Workflow | Run | Event | Final status | Duration | Recording | Screenshot |
|---|---|---|---|---|---|---|
| Copilot Setup Steps | [43064964683](https://github.com/ChristianPresley/agentic-pipelines/actions/runs/43064964683) | `push` | `success` | 6m 52s | [video](./copilot-setup-steps-43064964683.webm) | [png](./copilot-setup-steps-43064964683.png) |
| Pages | [43064964885](https://github.com/ChristianPresley/agentic-pipelines/actions/runs/43064964885) | `push` | `success` | 8m 27s | [video](./pages-43064964885.webm) | [png](./pages-43064964885.png) |
| Pipeline | [43064965068](https://github.com/ChristianPresley/agentic-pipelines/actions/runs/43064965068) | `push` | `success` | 10m 35s | [video 1 (queued/in progress)](./pipeline-43064965068.webm) · [video 2 (continued)](./pipeline-43064965068-continued.webm) | [png](./pipeline-43064965068-continued.png) |
| Dependabot Updates | [43064974284](https://github.com/ChristianPresley/agentic-pipelines/actions/runs/43064974284) | `dynamic` | `success` | 8m 51s | [video](./dependabot-updates-43064974284.webm) | [png](./dependabot-updates-43064974284.png) |
| Dependabot Updates | [43064974423](https://github.com/ChristianPresley/agentic-pipelines/actions/runs/43064974423) | `dynamic` | `success` | 15m 41s | [video 1 (queued/in progress)](./dependabot-updates-43064974423.webm) · [video 2 (continued)](./dependabot-updates-43064974423-continued.webm) | [png](./dependabot-updates-43064974423-continued.png) |
| Dependabot Updates | [43064975752](https://github.com/ChristianPresley/agentic-pipelines/actions/runs/43064975752) | `dynamic` | `success` | 9m 12s | [video](./dependabot-updates-43064975752.webm) | [png](./dependabot-updates-43064975752.png) |
| Dependabot Updates | [43064980954](https://github.com/ChristianPresley/agentic-pipelines/actions/runs/43064980954) | `dynamic` | `success` | 17m 12s | [video 1 (queued/in progress)](./dependabot-updates-43064980954.webm) · [video 2 (continued)](./dependabot-updates-43064980954-continued.webm) | [png](./dependabot-updates-43064980954-continued.png) |
| Dependabot Updates | [43064982000](https://github.com/ChristianPresley/agentic-pipelines/actions/runs/43064982000) | `dynamic` | `success` | 9m 55s | [video 1 (queued/in progress)](./dependabot-updates-43064982000.webm) · [video 2 (continued)](./dependabot-updates-43064982000-continued.webm) | [png](./dependabot-updates-43064982000-continued.png) |
| Dependabot Updates | [43064982793](https://github.com/ChristianPresley/agentic-pipelines/actions/runs/43064982793) | `dynamic` | `success` | 10m 24s | [video 1 (queued/in progress)](./dependabot-updates-43064982793.webm) · [video 2 (continued)](./dependabot-updates-43064982793-continued.webm) | [png](./dependabot-updates-43064982793-continued.png) |
| Security Finding Triage | [43066730473](https://github.com/ChristianPresley/agentic-pipelines/actions/runs/43066730473) | `workflow_run` | `in_progress` (recording capped) | n/a (still running) | [video](./security-finding-triage-43066730473.webm) | [png](./security-finding-triage-43066730473.png) |
| Pipeline Failure Analyst | [43066730510](https://github.com/ChristianPresley/agentic-pipelines/actions/runs/43066730510) | `workflow_run` | `skipped` | 0m 02s | [video](./pipeline-failure-analyst-43066730510.webm) | [png](./pipeline-failure-analyst-43066730510.png) |
| Observability (OpenTelemetry) | [43066730525](https://github.com/ChristianPresley/agentic-pipelines/actions/runs/43066730525) | `workflow_run` | `success` | 7m 49s | [video](./observability-opentelemetry-43066730525.webm) | [png](./observability-opentelemetry-43066730525.png) |

Durations are the run's own start-to-last-update time as reported by GitHub and include time spent queued. Runs whose first recording hit the
8-minute cap while still queued or in progress have a second "continued" recording that follows them to the end;
the screenshot is taken from the continued recording.

## Overall status

- 12 runs recorded: 10 succeeded, 1 skipped, 0 failed, 1 still running at the end of the session.
- No failures. The six `Dependabot Updates` runs, `Copilot Setup Steps`, `Pages` (Build and check site, Deploy to
  GitHub Pages) and `Observability (OpenTelemetry)` all succeeded.
- `Pipeline` succeeded: `Plan` and `Pipeline gate` passed and every stage job (Secrets and IaC, E2E, SCA, CI, Workflow lint,
  DAST, Container, Fuzzing, SAST) was skipped by the plan.
- `Pipeline Failure Analyst` was skipped (all of its jobs were skipped).
- `Security Finding Triage` was not finished when the session ended (GitHub still listed the run as `queued`; indexed here as
  `in_progress`): `pre_activation`, `activation`, `agent` and `detection` had succeeded, and `safe_outputs` was still queued.

### Jobs per run

- **Copilot Setup Steps 43064964683**: Copilot Setup Steps: success
- **Pages 43064964885**: Build and check site: success, Deploy to GitHub Pages: success
- **Pipeline 43064965068**: Plan: success, Pipeline gate: success, Secrets and IaC: skipped, E2E: skipped, SCA: skipped, CI: skipped, Workflow lint: skipped, DAST: skipped, Container: skipped, Fuzzing: skipped, SAST: skipped
- **Dependabot Updates 43064974284**: Dependabot: success
- **Dependabot Updates 43064974423**: Dependabot: success
- **Dependabot Updates 43064975752**: Dependabot: success
- **Dependabot Updates 43064980954**: Dependabot: success
- **Dependabot Updates 43064982000**: Dependabot: success
- **Dependabot Updates 43064982793**: Dependabot: success
- **Security Finding Triage 43066730473**: pre_activation: success, activation: success, agent: success, detection: success, safe_outputs: queued, teams_notify: skipped, slack_notify: skipped
- **Pipeline Failure Analyst 43066730510**: pre_activation: skipped, activation: skipped, agent: skipped, detection: skipped, slack_notify: skipped, safe_outputs: skipped, teams_notify: skipped, conclusion: skipped
- **Observability (OpenTelemetry) 43066730525**: Export workflow traces: success

## Notes

- Videos were re-encoded to VP9 at 5 fps after capture to keep the total size at 11.5 MiB.
- Long stretches in the videos are queue time, because the runs sat queued before a runner picked them up.
