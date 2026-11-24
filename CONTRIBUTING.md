# Contributing Guidelines

## Commit messages

This repository follows the [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Format

```
<type>(<optional scope>): <short description>
```

- Use the imperative mood: "add", not "added" or "adds".
- Keep the description short (≤ 72 characters), lowercase, with no trailing period.
- Use the scope for the problem category when relevant (e.g. `arrays`, `two-pointers`, `graphs`).

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
| `chore`    | Tooling, dependencies and configuration                 |
| `ci`       | CI/CD configuration (GitHub Actions)                    |

### Examples

```
feat(arrays): solve contains duplicate
perf(arrays): reduce two sum to O(n) with a hash map
test(two-pointers): add edge cases for valid palindrome
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
