# scripts/ci/select_tests.py (BeyondPy). Job names are in Portuguese, as in the CI page.

"""Pick the CI jobs a push needs, from the files it changed (.github/workflows/ci.yml).

Usage: python3 scripts/ci/select_tests.py [changed.txt]
Prints the job matrix as JSON. Without the file (the "Run workflow" button, a new branch, a
history the runner could not fetch), every job runs. When in doubt, everything runs: exercises
are left out only when every changed file is safe (_safe) or inside a module of content/.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PLATFORM = {
    "name": "Plataforma e estilo",
    "lint": True,
    "tests": "--ignore=tests/test_exercises.py",
}
# One job per heavy subject, side by side; the ids are "test[module/slug]", so "[py-" is exact.
# Django in two: its mutants each set up a whole project, and one job passed the 30 minutes.
SUBJECTS = {
    "Python": "[py-",
    "SQL": "[pg-",
    "Django (iniciante)": "[dj-i",
    "Django (intermediário)": "[dj-m",
}
ALL_EXERCISES = [
    *(
        {"name": f"Exercícios de {name}", "tests": f'tests/test_exercises.py -k "{k}"'}
        for name, k in SUBJECTS.items()
    ),
    {
        "name": "Outros exercícios",
        "tests": f'tests/test_exercises.py -k "not ({" or ".join(SUBJECTS.values())})"',
    },
]

# No exercise test reads these; the platform job still checks them.
SAFE = ("scripts/art/", "content/glossary/", ".claude/", "docs/", "migrations/")
# The only parts of app/ the exercise tests load (tests/test_ci_select.py checks this list);
# the rest of app/ is the platform's.
EXERCISE_DEPS = (
    "app/__init__.py",
    "app/assets.py",
    "app/i18n.py",
    "app/grader/",
    "app/services/__init__.py",
    "app/services/content.py",
)


def _safe(path: str) -> bool:
    if path.startswith("app/"):
        return not path.startswith(EXERCISE_DEPS)
    if path.startswith("tests/test_"):
        return path != "tests/test_exercises.py"
    return path.startswith(SAFE) or ("/" not in path and path.endswith(".md"))


def select(changed: list[str] | None) -> list[dict]:
    if changed is None:
        return [PLATFORM, *ALL_EXERCISES]
    modules = set()
    for path in changed:
        parts = path.split("/")
        if _safe(path):
            continue
        if parts[0] == "content" and len(parts) > 2:
            if (ROOT / "content" / parts[1] / "module.yaml").is_file():
                if (ROOT / "content" / parts[1] / "exercises").is_dir():
                    modules.add(parts[1])
                continue
        return [PLATFORM, *ALL_EXERCISES]
    if not modules:
        return [PLATFORM]
    # The test ids are "module/slug", so "py-i1/" never matches py-i10.
    k = " or ".join(f"{module}/" for module in sorted(modules))
    names = ", ".join(sorted(modules))
    return [
        PLATFORM,
        {"name": f"Exercícios de {names}", "tests": f'tests/test_exercises.py -k "{k}"'},
    ]


if __name__ == "__main__":
    file = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    changed = file.read_text().split() if file and file.is_file() else None
    print(json.dumps({"include": select(changed)}))
