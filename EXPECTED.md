# Runtime checks: expected outcomes (fixed 2026-11-02, before the run)

MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents working in MV2's name. Code
Apache-2.0; text CC BY 4.0.

The hand review of `branch-version-notes-audit` and `stdlib-deprecation-ledger` (run 1) rests
on reading the rst sources at branch heads and tags. Several verdicts also make a claim about
behaviour. `check.py` tests those claims on python-build-standalone interpreters (Linux
x86-64, via `uv`). The expected outcomes below are also written into `check.py` (`CHECKS`), and
both were fixed before the job ran. Any mismatch will be reported in GRADING.md as a mismatch.

| Check | Claim being tested | Expected |
|---|---|---|
| thread_lock | 3.13's legacy lock API does not use PyMutex, and 3.15's does (the 3.13 docs say "Changed in version 3.15: ... now always uses PyMutex") | `sys.thread_info.lock`: 3.13 and 3.14 are not `pymutex`; 3.15 is `pymutex` |
| utcfromtimestamp_fraction | gh-67795 ("accept any real number") is 3.15-only, but the 3.14 docs carry its note | `utcfromtimestamp(Fraction(1, 2))`: error on 3.13 and 3.14, ok on 3.15 |
| fromtimestamp_fraction | same change family | error on 3.14, ok on 3.15 |
| gettext_l_functions | the `l*gettext` family and `output_charset` were removed in 3.11, not in 3.10 as the 3.10 docs say | all four present on 3.10, all absent on 3.11 |
| open_U_mode | `open()`'s `'U'` mode was removed in 3.11, not 3.10 | `open(p, 'rU')` works on 3.10, raises ValueError on 3.11 |
| typing_io_re_namespaces | `typing.io` / `typing.re` were removed in 3.13 (the 3.9 docs said 3.12) | import works on 3.12, fails on 3.13 |
| argparse_nested_group | the live note "removed in version 3.14" on nested groups is right | nesting works on 3.13, raises on 3.14 |
| nodevisitor_visit_num | the live note on `NodeVisitor.visit_Num` is right | called on 3.13, not called on 3.14 |
| sourceless_load_module | exploratory, no expectation | whether `load_module` is still present on 3.14, 3.15 and 3.16 |

3.16 is a pre-release. It is used only if uv has it, and no expectation depends on it.
