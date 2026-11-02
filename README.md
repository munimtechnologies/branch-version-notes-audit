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

- `PREREG.md`: question, prior art, rules, gate and predictions, fixed before the data run.
- `notes.py`: scanner, owner matching, branch report, gate and grading (pure functions).
- `job.py`: the data run (streams tarballs from codeload.github.com; nothing is stored).
- `test_notes.py`: tests with hand-traced expected values.

Run it with `python -m unittest -v`, then `python job.py --out-dir OUT`. You need network
access. Results, including failed predictions, will be added under `results/` with a
hand-checked `FIXLIST.md`.

## Licence

Code Apache-2.0. Text and data CC BY 4.0. MV2, Munim, Inc., mv2@munimtech.com.
