# Repository Governance

This document describes how the repository is protected and how its GitHub settings are managed.

## Settings as code

All GitHub settings live in version control and are applied with a script:

| File | Contents |
|------|----------|
| `.github/settings/repository.json` | Merge strategy, GitHub Actions hardening and security features |
| `.github/rulesets/protect-main.json` | Branch ruleset for `main` |
| `.github/CODEOWNERS` | Code ownership |
| `scripts/repo-settings.sh` | Applies and verifies the settings above |

Editing these files does **not** change GitHub by itself. Only a repository admin can apply them.

### Changing a setting

1. Edit the JSON file in a branch and open a pull request.
2. After it is merged, apply and verify the settings:
   ```bash
   scripts/repo-settings.sh apply
   scripts/repo-settings.sh verify
   ```

### Verifying the settings

```bash
scripts/repo-settings.sh verify      # compares GitHub with the files, exits 1 on drift
scripts/repo-settings.sh test-push   # proves that a direct push to main is rejected
```

`test-push` builds an empty commit in memory and tries to push it to `main`. It does not touch
the working tree or any local branch.

Requirements: `gh` authenticated as a repository admin, and `jq`.

## Branch protection (`main`)

| Rule | Effect |
|------|--------|
| Pull request required | Every change reaches `main` through a pull request |
| Required approvals: 0 | GitHub does not allow approving your own pull requests; the author reviews the diff before merging |
| Squash merge only | Each pull request becomes a single commit; the PR title becomes its message |
| Required status check | `Lint & test (Python)` must pass |
| Up-to-date branches | The branch must contain the latest `main` before merging |
| Resolved conversations | All review comments must be resolved |
| Signed commits | Every commit on `main` must be signed |
| Linear history | No merge commits |
| No force pushes | History on `main` cannot be rewritten |
| No deletion | `main` cannot be deleted |
| No bypass | Not even repository admins can skip these rules |

## Merge settings

| Setting | Value |
|---------|-------|
| Allowed merge methods | Squash only |
| Squash commit message | Pull request title and body |
| Auto-merge | Enabled (`gh pr merge --auto --squash`) |
| Delete branch after merge | Enabled |

## Quality gates

Checks run twice: locally before each commit, and in CI on every push and pull request.

| Check | Local (pre-commit) | CI |
|-------|:------------------:|:--:|
| File checks (whitespace, end of file, YAML, TOML, JSON, merge conflicts, large files) | ✔ | |
| Ruff lint | ✔ | ✔ |
| Ruff format | ✔ | ✔ |
| pytest | ✔ | ✔ |
| README progress dashboard | ✔ (regenerates it) | ✔ (fails if outdated) |
| Conventional Commits message | ✔ | |

Local hooks use the tool versions pinned in `uv.lock`, so they always match CI.

## GitHub Actions hardening

| Setting | Value | Why |
|---------|-------|-----|
| Default `GITHUB_TOKEN` permissions | Read-only | Workflows cannot write to the repository unless a job asks for it explicitly |
| Workflows can approve pull requests | No | Automation cannot approve its own changes |
| Fork pull request workflows | Require approval for all external contributors | Code from forks never runs without review |
| Workflow permissions | `contents: read` declared in `ci.yml` | Least privilege |
| Concurrency | Superseded runs are cancelled | Saves CI minutes |

## Security features

| Feature | Status |
|---------|--------|
| Secret scanning | Enabled |
| Push protection | Enabled: pushes containing credentials are blocked |
| Dependabot alerts | Enabled |
| Dependabot security updates | Enabled |
| Dependabot version updates | Weekly, for GitHub Actions and Python dependencies (`.github/dependabot.yml`) |
| Private vulnerability reporting | Enabled (see [SECURITY.md](../.github/SECURITY.md)) |

## Access and ownership

- The owner is the only collaborator with write access. `verify` fails if anyone else is added.
- `.github/CODEOWNERS` assigns every file to the owner. Code owner review is not required
  while the project has a single maintainer, because GitHub does not allow self-approval.
- If collaborators are added in the future, protect sensitive paths in `CODEOWNERS`
  (`/.github/`, `/scripts/`) and set `require_code_owner_review` to `true` in the ruleset.
