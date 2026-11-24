# Security Policy

## Reporting a vulnerability

Please **do not open a public issue** for security problems.

Report them privately through
[GitHub private vulnerability reporting](https://github.com/paparici/neetcode-150/security/advisories/new).
You will get an answer as soon as possible. This is a personal project, so responses are best effort.

## Scope

This repository contains algorithm solutions, tests and the tooling around them (scripts, CI
workflows and repository settings). Reports about the tooling, the CI pipeline or leaked
credentials are especially welcome.

## Security measures in place

- Secret scanning with push protection: pushes that contain credentials are blocked.
- Dependabot alerts and automatic security updates for dependencies and GitHub Actions.
- Signed commits are required on `main`, and every change goes through a pull request.
- GitHub Actions runs with read-only permissions, and workflows from external contributors
  need manual approval.

See [docs/repository-governance.md](../docs/repository-governance.md) for the full configuration.
