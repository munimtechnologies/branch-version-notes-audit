# branch-version-notes-audit

Do CPython's maintenance-branch docs keep their own version notes? This is a pre-registered
audit by MV2 of Munim, Inc., made with AI agents working in his name.

Each branch builds its own docs (docs.python.org/3.14 comes from the `3.14` branch), and
doc changes are backported from `main`. This audit reads every version note (`versionadded`,
`versionchanged`, `versionremoved`, `deprecated`, `deprecated-removed`) at the heads of the
3.12-3.15 branches and at all 50 of their final release tags. It reports:

- **future notes:** the 3.Y docs give a later version (for example "Added in version 3.15"
  in the 3.14 docs);
- **lost bugfix-release notes:** a note such as "Added in version 3.14.1" that an earlier
  3.14 release carried and the branch no longer has.

What prompted it: in the 3.14 docs, `PyUnstable_ThreadState_SetStackProtection()` and
`PyUnstable_ThreadState_ResetStackProtection()` say "Added in version 3.15". Both shipped in
3.14.1, which is what the 3.14.1-3.14.3 docs said. Those docs also warned that extensions
using them are incompatible with 3.14.0. The note and the warning changed when the C API
init page was split up for 3.14.4. See `PREREG.md`.

## Results (run 1, graded 2026-11-02; see GRADING.md)

- Gate held. All 50 tags were read (4,390-5,933 version notes each).
- **P1 held:** 10 future notes beyond the known pair at the four branch heads.
- **P2 held:** 437 of 448 bugfix-release notes (97.5%) survive at the head.
- **P3 failed:** none of the candidates is a "wrong version on this branch" under the
  pre-registered label. Most future notes are intended forward references, such as
  soft deprecations and planned removals.
- **Two real problems outside that label** (`FIXLIST.md`). In each, a backport copied a
  `main` note about a 3.15-only change into an older branch:
  - the 3.14 docs say `datetime.utcfromtimestamp` "Changed in version 3.15: Accepts any real
    number";
  - the 3.13 docs say the legacy lock API "now always uses PyMutex" (3.15). 3.13's code uses OS
    locks.
- **Runtime checks (2026-11-02): all 18 pre-registered cells matched.** On 3.14.10,
  `utcfromtimestamp(Fraction(1, 2))` raises `TypeError` (it works on 3.15.2), and
  `sys.thread_info.lock` is `semaphore` on 3.13.18 and 3.14.10 (`pymutex` on 3.15.2). So both
  problems are confirmed by running the interpreters. P3 stays failed. Output:
  `results/runtime-checks.json`.

The verdicts were reached by AI agents reading the sources and running the interpreters. No
human has checked them. Follow-up: munimtechnologies/backport-version-notes runs the same
check on Django and NumPy.

## Files

- `PREREG.md`: question, prior art, rules, gate and predictions, fixed before the data run.
- `GRADING.md`, `FIXLIST.md`: the graded result and the hand-checked fix list.
- `results/`: the run 1 outputs (summary, future notes, lost and gone notes, tags) and the
  runtime-check output.
- `notes.py`: scanner, owner matching, branch report, gate and grading (pure functions).
- `job.py`: the data run (streams tarballs from codeload.github.com; nothing is stored).
- `test_notes.py`: tests with hand-traced expected values.
- `check.py`, `test_check.py`, `EXPECTED.md`: runtime checks behind the hand review (this
  repo and munimtechnologies/stdlib-deprecation-ledger).

Run it with `python -m unittest -v`, then `python job.py --out-dir OUT`, or
`python check.py --out-dir OUT` (needs `uv`). You need network access.

## Licence

Code Apache-2.0. Text and data CC BY 4.0. MV2, Munim, Inc., mv2@munimtech.com.
