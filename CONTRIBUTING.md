# Contributing Guidelines

## Commit messages

This repository follows the [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Format

```
<type>(<optional scope>): <short description>
```

- Use the imperative mood: "add", not "added" or "adds".
- Keep the description short (≤ 72 characters), lowercase, with no trailing period.
- For solutions, use `<language>/<category>` as the scope (e.g. `python/arrays-hashing`) and end the
  description with the LeetCode number in parentheses, e.g. `(217)`. Avoid `#217`: GitHub turns it
  into a link to issue 217.

### Types

| Type       | When to use it                                          |
|------------|---------------------------------------------------------|
| `feat`     | A new solution or feature                               |
| `fix`      | A bug fix in an existing solution                       |
| `docs`     | Documentation only (README, notes, docstrings)          |
| `test`     | Adding or updating tests                                |
| `refactor` | Code changes that neither fix a bug nor add a feature   |
| `perf`     | Performance improvements (e.g. better time complexity)  |
| `style`    | Formatting only, no logic changes                       |
| `build`    | Dependency updates and build system changes             |
| `chore`    | Tooling, dependencies and configuration                 |
| `ci`       | CI/CD configuration (GitHub Actions)                    |

### Examples

```
feat(python/arrays-hashing): solve contains duplicate (217)
perf(python/arrays-hashing): use a hash map in two sum (1)
test(python/two-pointers): add edge cases for valid palindrome (125)
docs: add complexity notes to README
chore: bump ruff to latest version
ci: run tests on every push
```

## Workflow

1. Add the solution under `python/neetcode/<category>/` and its tests under `python/tests/<category>/`.
2. Run the checks locally:
   ```bash
   uv run ruff check --fix .
   uv run ruff format .
   uv run pytest
   ```
3. Commit following the convention above. All commits are signed.

## Project structure

```
python/
├── neetcode/                 # Solutions (importable package)
│   ├── __init__.py
│   └── <category>/
│       ├── __init__.py
│       └── <problem>.py
└── tests/                    # Tests (mirror the package layout)
    └── <category>/
        └── test_<problem>.py
```

### `__init__.py` rules

| Directory                    | `__init__.py`?        | Why                                              |
|------------------------------|-----------------------|--------------------------------------------------|
| `python/neetcode/` and below | **Yes**, every level  | It is a regular package imported by the tests    |
| `python/tests/` and below    | **No**                | pytest discovers tests (`--import-mode=importlib`) |

- Shared test helpers or fixtures go in a `conftest.py`, never by turning `tests/` into a package.

### Adding a new category

```bash
mkdir -p python/neetcode/<category> python/tests/<category>
touch python/neetcode/<category>/__init__.py
```

Use `snake_case` for category and problem names (e.g. `two_pointers/valid_palindrome.py`).

## Progress dashboard

The progress section in `README.md` is generated from `problems.toml`. After solving a problem:

1. Register it in `problems.toml`:
   ```toml
   [[problems]]
   id = 1
   title = "Two Sum"
   slug = "two-sum"
   category = "arrays_hashing"
   difficulty = "Easy"
   ```
2. Regenerate the dashboard:
   ```bash
   uv run python scripts/update_readme.py
   ```
3. Commit the solution, its tests, `problems.toml` and `README.md` together.

CI fails if `README.md` is out of date.

Optional fields: `module` (when the module name differs from the slug) and `neetcode`
(NeetCode slug, adds a link to its explanation). Solution languages are detected
automatically from the files that exist.

## Local setup

```bash
uv sync
uv run pre-commit install
```

Hooks run automatically on every commit, in this order: file checks, Ruff (lint and format),
pytest and the README progress dashboard. Commit messages are validated afterwards. If a hook
modifies files, review the changes, `git add` them and commit again.

## Pull requests

`main` is protected by the ruleset in `.github/rulesets/protect-main.json`:

- Every change goes through a pull request. Direct pushes, force pushes and deletion are blocked.
- The `Lint & test (Python)` check must pass and the branch must be up to date with `main`.
- All commits must be signed.
- Pull requests are squash-merged. The PR title becomes the commit message, so it must follow
  the commit conventions above.

Branch names follow `<type>/<short-description>`, e.g. `feat/python-two-sum`.

```bash
git switch -c feat/python-two-sum
# solve, test, commit
git push -u origin HEAD
gh pr create --fill
gh pr merge --auto --squash --delete-branch
git switch main && git pull
```
