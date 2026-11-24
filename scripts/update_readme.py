"""Generate the progress dashboard in README.md from problems.toml.

Usage:
    uv run python scripts/update_readme.py           # update README.md
    uv run python scripts/update_readme.py --check   # fail if README.md is outdated (CI)
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "problems.toml"
README = ROOT / "README.md"

START_MARKER = "<!-- progress:start -->"
END_MARKER = "<!-- progress:end -->"

NEETCODE_URL = "https://neetcode.io/problems/{slug}/question?list=neetcode150"

# Where each language keeps its solutions and tests. Placeholders:
#   {category}   folder name, e.g. "arrays_hashing"
#   {module}     snake_case name, e.g. "contains_duplicate"
#   {class_name} PascalCase name, e.g. "ContainsDuplicate" (for Java, Go types, etc.)
# Languages are detected automatically: a problem counts as solved in a language
# when its solution file exists. Add a new entry here when you start a new language.
LANGUAGES: dict[str, tuple[str, str]] = {
    "Python": (
        "python/neetcode/{category}/{module}.py",
        "python/tests/{category}/test_{module}.py",
    ),
}

# NeetCode 150 categories: folder name -> (display name, number of problems).
CATEGORIES: dict[str, tuple[str, int]] = {
    "arrays_hashing": ("Arrays & Hashing", 9),
    "two_pointers": ("Two Pointers", 5),
    "sliding_window": ("Sliding Window", 6),
    "stack": ("Stack", 7),
    "binary_search": ("Binary Search", 7),
    "linked_list": ("Linked List", 11),
    "trees": ("Trees", 15),
    "tries": ("Tries", 3),
    "heap_priority_queue": ("Heap / Priority Queue", 7),
    "backtracking": ("Backtracking", 9),
    "graphs": ("Graphs", 13),
    "advanced_graphs": ("Advanced Graphs", 6),
    "dp_1d": ("1-D Dynamic Programming", 12),
    "dp_2d": ("2-D Dynamic Programming", 11),
    "greedy": ("Greedy", 8),
    "intervals": ("Intervals", 6),
    "math_geometry": ("Math & Geometry", 8),
    "bit_manipulation": ("Bit Manipulation", 7),
}
TOTAL = sum(total for _, total in CATEGORIES.values())

DIFFICULTIES: dict[str, tuple[str, str]] = {
    "Easy": ("🟢", "brightgreen"),
    "Medium": ("🟡", "orange"),
    "Hard": ("🔴", "red"),
}


@dataclass(frozen=True)
class Problem:
    leetcode_id: int
    title: str
    slug: str
    category: str
    difficulty: str
    module: str
    neetcode: str | None
    solutions: dict[str, Path]

    @property
    def url(self) -> str:
        return f"https://leetcode.com/problems/{self.slug}/"


def language_paths(language: str, category: str, module: str) -> tuple[Path, Path]:
    solution, test = LANGUAGES[language]
    class_name = "".join(part.capitalize() for part in module.split("_"))
    values = {"category": category, "module": module, "class_name": class_name}
    return Path(solution.format(**values)), Path(test.format(**values))


def load_problems() -> list[Problem]:
    data = tomllib.loads(CATALOG.read_text(encoding="utf-8"))
    problems: list[Problem] = []
    errors: list[str] = []
    seen_ids: set[int] = set()

    for entry in data.get("problems", []):
        leetcode_id = entry.get("id")
        title = entry.get("title", "")
        slug = entry.get("slug", "")
        category = entry.get("category", "")
        difficulty = entry.get("difficulty", "")
        module = entry.get("module", slug.replace("-", "_"))
        label = title or slug or "<unnamed>"

        if not isinstance(leetcode_id, int) or leetcode_id <= 0:
            errors.append(f"{label}: 'id' must be the LeetCode problem number")
        elif leetcode_id in seen_ids:
            errors.append(f"{label}: duplicate id {leetcode_id}")
        if not title or not slug:
            errors.append(f"{label}: 'title' and 'slug' are required")
        if category not in CATEGORIES:
            errors.append(f"{label}: unknown category '{category}'")
        if difficulty not in DIFFICULTIES:
            errors.append(f"{label}: difficulty must be one of {', '.join(DIFFICULTIES)}")

        solutions: dict[str, Path] = {}
        for language in LANGUAGES:
            solution, test = language_paths(language, category, module)
            if (ROOT / solution).is_file():
                solutions[language] = solution
                if not (ROOT / test).is_file():
                    errors.append(f"{label}: missing {language} test file {test}")
        if not solutions:
            errors.append(f"{label}: no solution file found in any language")

        if isinstance(leetcode_id, int):
            seen_ids.add(leetcode_id)
        problems.append(
            Problem(
                leetcode_id=leetcode_id if isinstance(leetcode_id, int) else 0,
                title=title,
                slug=slug,
                category=category,
                difficulty=difficulty,
                module=module,
                neetcode=entry.get("neetcode"),
                solutions=solutions,
            )
        )

    if errors:
        sys.exit("problems.toml has errors:\n  - " + "\n  - ".join(errors))
    return problems


def progress_bar(done: int, total: int, width: int = 20) -> str:
    filled = round(width * done / total) if total else 0
    return "█" * filled + "░" * (width - filled)


def badge(label: str, message: str, color: str) -> str:
    def escape(text: str) -> str:
        return text.replace("-", "--").replace(" ", "%20").replace("/", "%2F")

    return f"![{label}](https://img.shields.io/badge/{escape(label)}-{escape(message)}-{color})"


def render(problems: list[Problem]) -> str:
    solved = len(problems)
    by_difficulty = {name: 0 for name in DIFFICULTIES}
    by_category = {key: 0 for key in CATEGORIES}
    by_language = {name: 0 for name in LANGUAGES}
    for problem in problems:
        by_difficulty[problem.difficulty] += 1
        by_category[problem.category] += 1
        for language in problem.solutions:
            by_language[language] += 1

    lines = [
        " ".join(
            [
                badge("solved", f"{solved}/{TOTAL}", "blue"),
                *(
                    badge(name.lower(), str(by_difficulty[name]), color)
                    for name, (_, color) in DIFFICULTIES.items()
                ),
            ]
        ),
        "",
        f"`{progress_bar(solved, TOTAL)}` **{solved}/{TOTAL}** ({solved / TOTAL:.1%})",
        "",
        "| Difficulty | Solved |",
        "|------------|-------:|",
    ]
    for name, (icon, _) in DIFFICULTIES.items():
        lines.append(f"| {icon} {name} | {by_difficulty[name]} |")

    lines += ["", "| Language | Solved |", "|----------|-------:|"]
    for name, count in by_language.items():
        lines.append(f"| {name} | {count} |")

    lines += [
        "",
        "### By category",
        "",
        "| Category | Progress | Solved |",
        "|----------|----------|-------:|",
    ]
    for key, (name, total) in CATEGORIES.items():
        done = by_category[key]
        lines.append(f"| {name} | `{progress_bar(done, total, width=10)}` | {done}/{total} |")

    lines += [
        "",
        "### Solved problems",
        "",
        "<details>",
        f"<summary>Show all ({solved})</summary>",
        "",
        "| LeetCode | Problem | Difficulty | Category | Solutions |",
        "|---------:|---------|------------|----------|-----------|",
    ]
    category_order = list(CATEGORIES)
    ordered = sorted(problems, key=lambda p: (category_order.index(p.category), p.leetcode_id))
    for problem in ordered:
        icon, _ = DIFFICULTIES[problem.difficulty]
        category_name, _ = CATEGORIES[problem.category]
        title = f"[{problem.title}]({problem.url})"
        if problem.neetcode:
            title += f" · [NeetCode]({NEETCODE_URL.format(slug=problem.neetcode)})"
        solutions = " · ".join(
            f"[{language}]({path.as_posix()})" for language, path in problem.solutions.items()
        )
        lines.append(
            f"| {problem.leetcode_id} | {title} | {icon} {problem.difficulty} "
            f"| {category_name} | {solutions} |"
        )
    lines += ["", "</details>"]
    return "\n".join(lines)


def update(readme: str, dashboard: str) -> str:
    start = readme.find(START_MARKER)
    end = readme.find(END_MARKER)
    if start == -1 or end == -1 or end < start:
        sys.exit(f"README.md must contain '{START_MARKER}' followed by '{END_MARKER}'")
    before = readme[: start + len(START_MARKER)]
    after = readme[end:]
    return f"{before}\n{dashboard}\n{after}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check", action="store_true", help="exit with an error if README.md is outdated"
    )
    args = parser.parse_args()

    current = README.read_text(encoding="utf-8")
    updated = update(current, render(load_problems()))

    if args.check:
        if updated != current:
            sys.exit(
                "README.md progress is outdated. "
                "Run 'uv run python scripts/update_readme.py' and commit the result."
            )
        print("README.md progress is up to date.")
        return

    README.write_text(updated, encoding="utf-8")
    print("README.md progress updated.")


if __name__ == "__main__":
    main()
