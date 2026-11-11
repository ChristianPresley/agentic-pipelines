# Security Policy

## Reporting a vulnerability

Please report vulnerabilities privately through GitHub's **Report a vulnerability** button
(Security tab → Advisories). Do not open a public issue for an unpatched vulnerability.

We aim to acknowledge reports within 3 business days and to ship a fix or mitigation for confirmed
high/critical issues promptly.

## Supported versions

Only the latest release on `main` is supported.

## Automated findings

Scanner findings (SAST, SCA, DAST, fuzzing, secrets, IaC, container) are triaged by agentic workflows
that open `security-finding` issues. See [README.md](README.md) for the pipeline.
