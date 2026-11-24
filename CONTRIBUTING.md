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

1. Add the solution and its tests under `python/<category>/`.
2. Run the checks locally:
   ```bash
   uv run ruff check --fix .
   uv run ruff format .
   uv run pytest
   ```
3. Commit following the convention above. All commits are signed.
