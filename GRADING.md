# Grading: do CPython's maintenance-branch docs keep their own version notes? (run 1)

MV2, Munim, Inc. (mv2@munimtech.com). Graded 2026-11-02 against `PREREG.md`. Made with AI
agents working in MV2's name; every graded row below was read in the rst source by those
agents, not by a human. Code Apache-2.0; text and data CC BY 4.0.

Data run: `branch-version-notes-audit-v1`, 2026-11-02 04:56-05:00 UTC. Heads: 3.12
`3d6d2a6`, 3.13 `42155a0`, 3.14 `1f66a03`, 3.15 `fe47a43`. All 50 final tags were fetched
(`results/run1-summary.json`; commit ids per tag in `results/tags.csv`).

## Verdicts

| | Prediction | Result | Verdict |
|---|---|---|---|
| P0 | gate (known pair found as lost and as future; control clean; >= 2,000 notes per tag; >= 90% of tags) | all five parts true; 50 of 50 tags; 4,390-5,933 notes per tag | **HELD** |
| P1 | >= 3 future notes at the four heads beyond the known pair | 10 | **HELD** |
| P2 | >= 95% of bugfix-release notes survive at the head | 437 of 448 (97.5%) | **HELD** |
| P3 | hand review confirms >= 2 "wrong version on this branch" problems beyond the known pair | 0 under that label | **FAILED** |

P3 failed as pre-registered. The hand review did find **two real problems** beyond the known
pair, but of a kind the labels did not anticipate. In both, a backport copied a `main` note
that describes a 3.15-only change into an older branch, where the behaviour does not exist.
"Wrong version" assumed the behaviour exists on the branch under a wrong number. Here there
is no right number, because the branch never gets the change. These two are reported below
and in `FIXLIST.md`, labelled as found outside the pre-registered category. The runtime
checks (section below) confirm that the behaviour is absent on both branches, so neither
moves into the "wrong version" label and P3 stays failed.

Exploratory: no `next` placeholder was left in the docs at any of the 50 release tags.

## Hand review: the 12 future notes

Each row was read in the rst at the branch head named above.

| Branch | Note | Owner | Reading | Label |
|---|---|---|---|---|
| 3.12 | `deprecated:: 3.14` | `PyLong_AS_LONG` (long.rst:146) | "A soft deprecated alias ... The function is soft deprecated." | intended forward reference (soft-deprecation advice; holds for 3.12 too) |
| 3.13 | `deprecated:: 3.14` x4 | `Py_HUGE_VAL`, `Py_IS_FINITE`, `Py_IS_INFINITY`, `Py_IS_NAN` (float.rst) | "The macro is soft deprecated. Use isfinite / isinf / isnan instead." | intended forward reference (same) |
| 3.13 | `versionchanged:: 3.15` x2 | "Legacy Locking APIs" section and `PyThread_allocate_lock` (c-api/init.rst:2555, 2592) | "These APIs are now a simple wrapper around PyMutex." / "This function now always uses PyMutex. In prior versions, this would use a lock provided by the operating system." | **real problem, outside the P3 label** (see below) |
| 3.14 | `deprecated-removed:: 3.15 3.19` | `PyHash_Func` (hash.rst:150) | "Use one of the built-in hash algorithms instead." | intended forward reference (planned deprecation and removal) |
| 3.14 | `versionadded:: 3.15` x2 | `PyUnstable_ThreadState_Set/ResetStackProtection` | the known pair (gate) | known; not counted |
| 3.14 | `versionchanged:: 3.15` | `datetime.utcfromtimestamp` (datetime.rst:1074) | "Accepts any real number as *timestamp*, not only integer or float." | **real problem, outside the P3 label** (see below) |
| 3.14 | `versionchanged:: 3.15` | `--with-system-libmpdec` (using/configure.rst:986) | "A bundled copy of the library will no longer be selected implicitly ... In Python 3.15 only, it can still be selected explicitly" | intended forward reference (deliberate backport "Defer `--with-system-libmpdec` removal to 3.16", gh-115119, #139347) |

### Problem A: the 3.13 docs describe 3.15's PyMutex-based lock API

- Text at the 3.13 head (`Doc/c-api/init.rst`), live on docs.python.org/3.13 (3.13.18):
  "Changed in version 3.15: These APIs are now a simple wrapper around `PyMutex`" and, under
  `PyThread_allocate_lock`, "Changed in version 3.15: This function now always uses `PyMutex`.
  In prior versions, this would use a lock provided by the operating system."
- Source of the note: the 3.13 backport GH-141955 of "gh-141004: Document missing `PyThread*`
  APIs" (GH-141810), 2025-11-25. Its diff adds both `versionchanged:: 3.15` lines. First tag
  with them: v3.13.10.
- 3.13's code: `Python/thread_pthread.h` at the 3.13 head allocates a `sem_t` (or a
  `pthread_mutex_t` plus condition variable when semaphores are unusable). It does not use
  `PyMutex`. On 3.15 (`Python/thread.c`), `PyThread_allocate_lock` allocates a `PyMutex`.
- Runtime: `sys.thread_info.lock` reports `semaphore` on 3.13.18 and 3.14.10 and `pymutex`
  on 3.15.2 (check `thread_lock`, below).
- The 3.14 docs got the same section without the 3.15 notes (`Doc/c-api/synchronization.rst`
  at the 3.14 head has none), so the 3.13 copy is the odd one out.
- Fixability: 3.13 is now a security-only branch (devguide.python.org/versions), so a docs-only
  fix there is unlikely to be accepted. Recorded for the record, not as a fix request.

### Problem B: the 3.14 docs say `utcfromtimestamp` accepts any real number "in 3.15"

- Text at the 3.14 head (`Doc/library/datetime.rst:1074`), under `datetime.utcfromtimestamp`:
  "Changed in version 3.15: Accepts any real number as *timestamp*, not only integer or float."
- The change is gh-67795 (What's New in 3.15: functions that take timestamp or timeout
  arguments "now accept any real numbers (such as Decimal and Fraction)").
- Source of the note: the 3.14 backport GH-144956 of "Datetime: Tidy up docs" (GH-144720),
  2026-02-18. Its diff adds exactly these two lines and nothing else about timestamps. First
  tag with them: v3.14.4.
- On the same 3.14 page, `datetime.fromtimestamp` and `date.fromtimestamp` carry no such note,
  so only `utcfromtimestamp` got it.
- Runtime: `datetime.datetime.utcfromtimestamp(Fraction(1, 2))` raises `TypeError` on 3.14.10
  (and 3.13.18) and returns `1970-01-01T00:00:00.500000` on 3.15.2 (check
  `utcfromtimestamp_fraction`, below). So the 3.14 docs describe behaviour 3.14 does not have.
- 3.14 is a bugfix branch, so this one can be fixed. A duplicate search (python/cpython issues
  and PRs, "utcfromtimestamp" with "real number" / "3.14 versionchanged") found nothing.

## Hand review: the 11 lost bugfix-release notes

| Branch | Owner | Lost note | Now at head | Reading | Label |
|---|---|---|---|---|---|
| 3.12 | `ConfigParser.read` | versionadded 3.6.1 | versionchanged 3.6.1 | directive corrected from "added" to "changed" | renamed (same version kept) |
| 3.12 | `ipaddress.IPv4Address` | versionchanged 3.8.12 | 3.8, 3.9.5 | a 3.8-branch release number removed from the 3.12 docs | not a 3.12 version; not counted |
| 3.12 | `shutil.which` | versionchanged 3.12.1 (v3.12.1-v3.12.7) | 3.3, 3.8, 3.12 | removed by the 3.12 backport GH-127158 of gh-127001, which rewrote the PATHEXT logic in the same PR | deliberate (behaviour changed again); not counted |
| 3.13 | `shutil.which` | versionchanged 3.12.1 (v3.13.0 only) | same | same change, backported to 3.13 | deliberate; not counted |
| 3.12 | `typing.AsyncContextManager`, `ChainMap`, `Counter`, `Deque` | versionadded 3.5.4 | 3.6.1 / 3.6.2 | 3.5-era notes removed, 3.6 notes kept | not a 3.12 version; not counted |
| 3.13 | `PY_MONITORING_IS_INSTRUMENTED_EVENT` | deprecated 3.13.3 (v3.13.3-v3.13.14) | `soft-deprecated:: 3.13.3` | the note moved to the newer `soft-deprecated` directive, which this audit's vocabulary does not include | renamed directive (parser vocabulary); not counted |
| 3.14 | the known pair | versionadded 3.14.1 | versionadded 3.15 | gate | known |

So no lost note beyond the known pair is a problem. A side observation, not graded: after
GH-127158, the 3.12 and 3.13 docs carry no note at all for the 3.12.8 / 3.13.1 change to
`shutil.which`'s PATHEXT handling.

## Runtime checks (run 2026-11-02)

Job `doc-runtime-checks-v1`, 2026-11-02 07:28-07:31 UTC, python-build-standalone interpreters
3.10.22, 3.11.18, 3.12.16, 3.13.18, 3.14.10, 3.15.2 and 3.16.0a1 (Linux x86-64, via uv
0.13.6). The expected outcome of every graded cell was fixed in `check.py` and `EXPECTED.md`
before the run. **All 18 graded cells matched; 0 mismatches; 7 exploratory cells.** The
checks for this audit:

| Check | 3.13 | 3.14 | 3.15 | 3.16a1 (exploratory) | Expected | Held? |
|---|---|---|---|---|---|---|
| `thread_lock` (`sys.thread_info.lock`) | semaphore | semaphore | pymutex | pymutex | not pymutex / not pymutex / pymutex | yes (3 of 3) |
| `utcfromtimestamp_fraction` | TypeError | TypeError | ok (00:00:00.5) | ok | error / error / ok | yes (3 of 3) |
| `fromtimestamp_fraction` (tz=UTC) | TypeError (exploratory) | TypeError | ok | ok | - / error / ok | yes (2 of 2) |

What this changes: Problems A and B are now confirmed by running the interpreters, not only
by reading the source and What's New. Neither result moves either problem into the
pre-registered "wrong version" label (the behaviour is absent on the branch, so no version
number would be right there), so **P3 stays FAILED at 0 of 2**. The other six checks in the
job belong to munimtechnologies/stdlib-deprecation-ledger and are reported in its GRADING.md.
Limits: one platform (Linux), the latest micro release of each minor, one input (a Fraction).

## Limits

- One run, final tags only. Future notes are counted at the four heads; the per-tag counts in
  `results/run1-summary.json` show when each arrived.
- The audit's directive list did not include `soft-deprecated`, which now exists on the 3.13
  and 3.14 branches (for example `PY_TIMEOUT_T` reads `soft-deprecated:: 3.14.10`). Notes in
  that directive were not scanned.
- "Intended forward reference" is a judgement from reading the note and, where available, the
  commit that added it. The soft-deprecation rows were not traced to their commits.
- The two real problems were found by AI agents and have not been checked by a human or a
  CPython maintainer.

## Prior art, re-checked at grading

python/cpython #159013 (one `main` note), gh-121277 (`next` placeholders) and the one-off fixes
named in `PREREG.md` are still the nearest work. No issue or PR about either problem was found.

## Files

`results/run1-summary.json`, `results/future_notes.csv`, `results/lost_micro.csv`,
`results/gone_micro.csv`, `results/next_at_tags.csv`, `results/tags.csv`; `check.py`,
`test_check.py`, `EXPECTED.md` (runtime checks); `results/runtime-checks.json` (their output).
