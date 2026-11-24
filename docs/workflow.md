# Development Workflow

Step-by-step commands for working on this repository. `main` is protected, so every change
follows the same path: **branch → commit → pull request → CI → squash merge**.
Every step also has a shortcut: see [Shortcuts (mise tasks)](#shortcuts-mise-tasks).

## One-time setup

```bash
gh repo clone paparici/neetcode-150
cd neetcode-150
uv sync
uv run pre-commit install
```

Commits must be signed. Set up SSH commit signing once, as described in
[GitHub's documentation](https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification).

## Branch names

`<type>/<short-description>`, using the same types as commit messages:

| Change | Example |
|--------|---------|
| New solution | `feat/python-two-sum` |
| Bug fix | `fix/python-valid-anagram-unicode` |
| Documentation | `docs/complexity-notes` |
| CI or repository settings | `ci/codeql-as-code` |
| Tooling or dependencies | `chore/update-pre-commit` |

## Solving a problem

### 1. Start from an up-to-date `main`

```bash
git switch main && git pull
git switch -c feat/python-two-sum
```

### 2. Add the solution and its tests

```bash
# Only when the category is new:
mkdir -p python/neetcode/<category> python/tests/<category>
touch python/neetcode/<category>/__init__.py
```

- Solution: `python/neetcode/<category>/<module>.py`, with a module docstring such as
  `"""1. Two Sum\n\nhttps://leetcode.com/problems/two-sum/\n"""`.
- Tests: `python/tests/<category>/test_<module>.py`.
- Run them while you work: `uv run pytest -k <module>`.

### 3. Register it in the dashboard

Add an entry to `problems.toml` (see the field reference at the top of the file), then:

```bash
uv run python scripts/update_readme.py
```

### 4. Commit

```bash
git add .
git commit -m "feat(python/<category>): solve <problem name> (<leetcode id>)"
```

The pre-commit hooks run file checks, Ruff, pytest and the dashboard update, then validate the
commit message. If a hook modifies files, review the changes and commit again:

```bash
git add -u
git commit -m "feat(python/<category>): solve <problem name> (<leetcode id>)"
```

### 5. Open the pull request

```bash
git push -u origin HEAD
gh pr create --web
```

The browser opens with the pull request template. Make sure the **title follows Conventional
Commits** (it becomes the commit message on `main`; CI validates it), fill in the summary and
the problems table (including time and space complexity), then create the pull request.

Prefer the terminal? Use the last commit message as the title and edit the body later:

```bash
gh pr create --title "$(git log -1 --pretty=%s)" --body-file .github/pull_request_template.md
gh pr edit --body-file <your-filled-template>.md
```

### 6. Merge automatically when CI passes

```bash
gh pr merge --auto --squash --delete-branch
gh pr checks --watch
```

Review the diff before it merges: `gh pr diff` or `gh pr view --web`.

### 7. Clean up

```bash
git switch main && git pull
git branch -D feat/python-two-sum
```

`-D` is required because squash merging creates a new commit, so Git does not see the branch as
merged.

## Keeping a pull request up to date

The ruleset requires branches to contain the latest `main`. If `main` moved after you opened
the pull request:

```bash
gh pr update-branch
```

Or rebase locally (your commits are signed again during the rebase):

```bash
git fetch origin
git rebase origin/main
git push --force-with-lease
```

Force pushing is allowed on your own branches; it is only blocked on `main`.

## Dependabot pull requests

Dependabot opens pull requests every week (`ci(deps): …`, `build(deps): …`) and immediately
for security fixes. They go through the same checks:

```bash
gh pr list --author "app/dependabot"
gh pr diff <number>
gh pr merge <number> --auto --squash
```

## Changing repository settings

Settings live in `.github/settings/repository.json` and `.github/rulesets/protect-main.json`.
Change them through a pull request like any other file, then apply them after merging:

```bash
scripts/repo-settings.sh apply
scripts/repo-settings.sh verify
```

See [repository-governance.md](repository-governance.md) for every rule and setting.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Failed - files were modified by this hook` | A hook fixed formatting or regenerated the README | `git add -u` and commit again |
| `[Bad commit message]` | The message does not follow Conventional Commits | Use `<type>(<scope>): <description>` |
| CI step *Run pre-commit hooks* fails | Commits were made without the hooks (formatting or README dashboard out of date) | `mise run check`, then commit the changes |
| Push to `main` rejected (`GH013`) | `main` only accepts pull requests | Create a branch and open a pull request |
| Pull request cannot be merged | A check failed, the branch is outdated or CodeQL found an alert | `gh pr checks`, then fix or `gh pr update-branch` |
| `Conventional PR title` check fails | The title does not follow Conventional Commits (it becomes the squash commit message) | `gh pr edit --title "<type>(<scope>): <description>"` |

## Cheat sheet

| Task | Command |
|------|---------|
| Start a branch | `git switch main && git pull && git switch -c <type>/<name>` |
| Run all checks | `uv run pre-commit run --all-files` |
| Run one test file | `uv run pytest -k <module>` |
| Regenerate the dashboard | `uv run python scripts/update_readme.py` |
| Open a pull request | `git push -u origin HEAD && gh pr create --web` |
| Auto-merge when green | `gh pr merge --auto --squash --delete-branch` |
| Watch CI | `gh pr checks --watch` |
| Update an outdated branch | `gh pr update-branch` |
| Clean up after merge | `git switch main && git pull && git branch -D <branch>` |
| Verify repository settings | `scripts/repo-settings.sh verify` |

## Shortcuts (mise tasks)

The steps above are wrapped in [mise](https://mise.jdx.dev/) tasks. `mise tasks` lists them.

| Task | What it does |
|------|--------------|
| `mise run new <type>/<name>` | Updates `main` and creates the branch (validates the name) |
| `mise run check` | Runs every pre-commit hook on all files |
| `mise run test` | Runs the test suite |
| `mise run dashboard` | Regenerates the README progress dashboard |
| `mise run pr [title]` | Pushes the branch and opens the pull request in the browser with the template |
| `mise run ship` | Enables squash auto-merge and watches CI |
| `mise run done` | After the merge: switches to an up-to-date `main` and deletes the branch |
| `mise run settings` | Verifies the GitHub settings against the files in `.github/` |

A typical problem from start to finish:

```bash
mise run new feat/python-two-sum
# solve, add tests, register in problems.toml
git add .
git commit -m "feat(python/arrays-hashing): solve two sum (1)"
mise run pr        # fill in the template in the browser and create the pull request
mise run ship      # waits for CI; the pull request merges automatically
mise run done
```

`mise run pr` uses the commit message as the title when the branch has a single commit.
With several commits, pass the title explicitly:
`mise run pr "feat(python/arrays-hashing): solve two sum (1)"`.

Simple tasks are defined in `mise.toml`; the ones with logic are scripts in `.mise/tasks/`.
