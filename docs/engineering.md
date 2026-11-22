# Engineering

The problems that took the most thought, and how they were solved.

## Real Python and PostgreSQL inside the browser

**Problem.** Grading code on a server means running untrusted code, paying for compute and waiting on
the network. For a learning site with one developer, that was the wrong trade.

**Solution.** The browser does the work. Pyodide (CPython 3.14 compiled to WebAssembly) and PGlite
(PostgreSQL 18 compiled to WebAssembly) each run in a Web Worker, so the page stays responsive and a
runaway loop can be stopped. The first exercise downloads about 10 MB, cached afterwards.

The hard part was **Python talking to PostgreSQL**: lessons such as "SQL from Python" and the FastAPI
modules need `import psycopg`. BeyondPy ships a small `psycopg` written for this purpose, which sends
the PostgreSQL wire protocol from the Pyodide worker straight into PGlite in the same worker. The same
lesson code runs against a real PostgreSQL in CI.

## Simulating tools that cannot exist in a browser

There is no Docker daemon or Git binary in a browser tab. Rather than drop those subjects, BeyondPy
simulates them in pure Python, at the level a learner can observe:

| Simulator | What a student can do |
|---|---|
| Docker | Write Dockerfiles, `build`, `run`, volumes, networks, `docker compose up`, health checks |
| Git | `commit`, `branch`, `merge`, `rebase`, `stash`, `reflog`, remotes and pull requests, in a PowerShell-like shell |
| Redis | A server in memory, with expiration, counters and lists, behind a `redis-py` client |
| Alembic, PyJWT | Migrations and tokens, with the same API as the real libraries |

A simulator is only worth having if it does not teach wrong behavior. That is what the parity checks
are for (below).

## Exercises that test their own tests

**Problem.** An exercise with weak tests accepts wrong answers, and the student learns the wrong thing.

**Solution: mutants.** Every exercise ships with typical wrong answers (an off-by-one, a missing edge
case, a hard-coded output). On every push, CI checks, for each of the 1,033 exercises, that:

1. the reference solution passes;
2. the starter code fails;
3. every mutant fails (2,814 in total).

If a mutant passes, the build fails and the tests get stronger before anyone sees the exercise. A
sample exercise is in [`snippets/`](../snippets/).

## Parity checks: the simulator against the real thing

The same grader runs in two places, so the two must agree. A separate GitHub Actions workflow runs the
same cases on both sides and compares the results:

| Check | Compares |
|---|---|
| Python | `pytest` on CPython 3.12 against Pyodide (CPython 3.14) in Node |
| SQL | PostgreSQL 17 against PGlite |
| Docker | The simulator against Docker Engine, in parallel shards |
| Git | The simulator against real Git, recorded as fixtures |

## About 7,000 tests, with a CI that picks what to run

The full suite takes about 20 minutes, and GitHub Actions minutes are a budget. A small script reads
the files changed in a push and selects only the test groups they can affect: a change to one
module's content runs that module's exercises; a change to the grader runs everything. The parity
workflows run only when the simulator or the grader they cover changes.

## Data isolation per account

**Problem.** Every study table (attempts, views, reviews, notes) belongs to one account. Forgetting a
`WHERE user_id = ...` in one query would leak one person's history to another.

**Solution.** The account is attached to the database session at the start of each request, and a
SQLAlchemy event adds the `user_id` filter to every `SELECT`, `UPDATE` and `DELETE` on those tables
and fills it on every insert. A query written without thinking about accounts is still safe.

## A bilingual site where the source text is the key

Portuguese is the source language. Every interface string stays in Portuguese in the code, wrapped
in a marker function, and the Portuguese text itself is the key of the English file. A test fails
the build if a string has no translation, if a translation is no longer used, or if the `{values}`
inside do not match. Content modules have an `en/` folder with the translated lessons and exercises.

## Security

The site went through a dedicated security review before opening to other people. Highlights:

- Passwords hashed with Argon2; the database stores only a SHA-256 hash of each session token.
- Rate limits on sign-in, sign-up and the attempts API; a cap on concurrent password hashing.
- Same-origin check on every `POST`, a request body size limit, HSTS and strict security headers.
- Cloudflare Turnstile on sign-up; Google sign-in only links accounts whose e-mail Google owns.
- Students can export all their data as JSON and delete their account, which removes everything.

## Performance

- Static files carry a content hash in the URL and are cached for a year.
- Content is cached in memory and refreshed when a file changes on disk.
- Pages are rendered on the server and work before any JavaScript loads; Lighthouse runs guard the
  budget on phone and desktop.
