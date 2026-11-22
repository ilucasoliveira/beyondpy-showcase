# Code samples

A few files from BeyondPy's private repository, copied as they are (one is an excerpt). They are here
to show how the project is written, not to be run on their own: they import modules that are not part
of this showcase.

| Sample | What it shows |
|---|---|
| [`exercise-pass-or-fail/`](exercise-pass-or-fail/) | One complete exercise: task, tests, solution and mutants |
| [`spaced_review.py`](spaced_review.py) | The spaced review schedule |
| [`git_did_you_mean.py`](git_did_you_mean.py) | A piece of the Git simulator that copies Git's own algorithm |
| [`ci_select_tests.py`](ci_select_tests.py) | How CI picks which of the ~7,000 tests a push needs |

## One complete exercise

[`exercise-pass-or-fail/`](exercise-pass-or-fail/) is the exercise in the
[Python screenshot](../images/exercise-python-light.png), in its English version.

- `exercise.yaml`: the task, the starter code with a blank (`___`) and four hints, from a nudge to
  the answer.
- `tests.py`: seven tests. Each docstring is the line the student reads ("Grade 6 (the limit):
  Passed"), and each failure says what to check next. `run_with_inputs` comes from the grader, which
  runs the student's program with those answers to `input()`.
- `solution.py`: the reference solution, shown only after the exercise is solved.
- `mutants/`: five typical wrong answers. CI fails if any of them passes the tests.

The mutants are the interesting part. Each one is a real mistake a beginner makes, and each one forces
a specific test to exist:

| Mutant | The mistake | Caught by |
|---|---|---|
| `strictly_greater.py` | `>` instead of `>=` | Grade 6 (the limit) |
| `wrong_limit.py` | `>= 7` | Grade 6 (the limit) |
| `only_five_fails.py` | Tests only the example (`!= 5`) | Grades 4 and 0 |
| `always_passes.py` | Prints "Passed" with no `if` | Every grade below 6 |
| `compares_text.py` | Compares text: `"10" >= "6"` is `False` | Grade 10 |

The last one is the subtle case: comparing strings works for one-digit grades, so without the grade-10
test it would pass.

## The spaced review schedule

[`spaced_review.py`](spaced_review.py) is an excerpt of the review service.

- Opening a lesson schedules its cards for the next day, with one `INSERT ... ON CONFLICT DO NOTHING`,
  so opening the lesson again changes nothing.
- A correct answer moves the card one step up the intervals (1, 3, 7 ... 240 days); a miss sends it
  back to day one.
- `due_cards` orders by step first: with a daily limit, the cards from the newest lessons and the ones
  just missed come before mature cards.
- `grade` ignores a card that is not due yet, so a double click or the browser's back button cannot
  move a card forward twice.

There is no `user_id` in these queries. Every query is limited to the current account by a
SQLAlchemy event (see [Engineering](../docs/engineering.md#data-isolation-per-account)).

## The Git simulator's "did you mean"

[`git_did_you_mean.py`](git_did_you_mean.py) reproduces what Git prints for a command it does not
know, such as `git comit`:

```text
git: 'comit' is not a git command. See 'git --help'.

The most similar command is
	commit
```

It follows Git's C source (`help.c` and `levenshtein.c`): the same weighted Levenshtein distance,
the same bonus for common commands that start with what was typed, the same threshold and the same
command list as Git 2.56 for Windows. The simulator is checked against real Git, so a student sees
the same message in the lesson and on their own computer.

## Picking tests in CI

[`ci_select_tests.py`](ci_select_tests.py) reads the list of files a push changed and prints the
GitHub Actions job matrix:

- Only lessons or exercises of some modules changed: run the platform tests plus those modules'
  exercises.
- Only documentation, art or other safe paths changed: run the platform tests.
- Anything else, or no list at all: run everything, in parallel jobs per subject.

When in doubt, everything runs. A test in the main repository checks that the list of files the
exercise tests depend on stays correct.
