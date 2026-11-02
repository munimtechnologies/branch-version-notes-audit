# Pre-registration: do CPython's maintenance-branch docs keep their own version notes?

MV2, Munim, Inc. (mv2@munimtech.com). Filed 2026-11-02, before the data run. Made with AI
agents working in MV2's name. Code Apache-2.0; text and results CC BY 4.0.

## Why this question

Each CPython branch builds its own docs (docs.python.org/3.14 comes from the `3.14` branch).
Maintainers expect each branch to state the version that applies to it. In python/cpython
#159013 (October 2026), a core developer pointed out that `tarfile.LinkFallbackError` reads
"Added in version 3.14" on the 3.14 docs and "Added in version 3.13.4" on the 3.13 docs.

Doc changes are written on `main` and backported. If a backport copies `main`'s text
wholesale, it can carry `main`'s version numbers into an older branch and overwrite notes
that only that branch had.

**The case that prompted this (found by hand on 2026-11-02, while grading
munimtechnologies/capi-versionadded-audit):**

- `PyUnstable_ThreadState_SetStackProtection()` and `..._ResetStackProtection()` were
  backported to 3.14 for 3.14.1 (gh-139653, PR #141661; listed in the 3.14.1 changelog).
- At tag v3.14.1 and still at v3.14.3, `Doc/c-api/init.rst` says
  `.. versionadded:: 3.14.1`, followed by a warning that extensions using them are
  incompatible with 3.14.0 and should declare `Requires-Python: != 3.14.0.*`.
- At v3.14.4 the page was split into several files ("[3.14] gh-141811: Split up `init.rst`
  into multiple pages", GH-145061, 2026-02-23). In the 3.14 branch's
  `Doc/c-api/threads.rst` both entries now say `.. versionadded:: 3.15`, and the
  warning is gone. docs.python.org/3.14 (3.14.10) shows "Added in version 3.15."
- The 3.14.10 interpreter exports both symbols, which is how the C API audit flagged them.

So the 3.14 docs tell extension authors that the functions arrived in a release after 3.14,
and they no longer warn about 3.14.0. Is this a one-off, or a pattern?

## Prior art (searched 2026-11-02)

- python/cpython #159013: one hand-found `versionadded:: 3.15` on `main` for a backported
  security fix. One object, `main` only.
- gh-121277: the `next` placeholder in version directives, replaced by the release manager
  at release time. It reduces wrong versions in new notes. It does not check old notes or
  other branches.
- bpo-43978 (typing.NoReturn) and PR #22618: one-off version-note fixes.
- Ours: munimtechnologies/versionadded-runtime-audit and capi-versionadded-audit check the
  notes on `main` against the interpreters. Neither compares branches or tags.
- No tool or study was found that compares a maintenance branch's version notes with its
  own release tags, or that lists notes naming a later version than the branch itself.

## Data (fixed now)

- `Doc/**/*.rst` from the GitHub tarballs of the heads of branches 3.12, 3.13, 3.14 and 3.15,
  and of every final tag v3.12.0-v3.12.16, v3.13.0-v3.13.18, v3.14.0-v3.14.10 and
  v3.15.0-v3.15.2 (50 tags). The tarballs are streamed and not stored. Commit ids are
  recorded.

## Rules (fixed in notes.py, tested in test_notes.py)

- **Version notes:** `versionadded`, `versionchanged`, `versionremoved`, `deprecated` and
  `deprecated-removed`. A note's version is its first argument. The removal version of
  `deprecated-removed` is never treated as the note's version.
- **Owner:** the chain of object directives the note sits inside (py and c domains, envvar,
  option, opcode and similar), with the current module as a prefix. C objects are keyed by
  their name, so a note keeps its owner when a page is split or moved.
- **Future note:** a note at the head of branch 3.Y whose version is 3.X with X > Y.
- **Micro note:** a note whose version names a bugfix release (3.m.z, z >= 1) and has an
  owner. It is **lost** if some release tag of the branch had it, the owner is still
  documented at the branch head, and the head has no note with the same directive and
  version on that owner. It is **gone** if the owner is no longer documented at the head
  (renamed or removed; not graded).
- **Gate (P0):** (a) the known `SetStackProtection` 3.14.1 note is found as lost on 3.14;
  (b) its 3.15 note is found as a future note at the 3.14 head; (c) control:
  `tarfile.LinkFallbackError` is documented at the 3.14 head with no future note (per
  #159013 it reads 3.14 there); (d) every fetched tag has at least 2,000 version notes;
  (e) at least 90% of the 50 tags are fetched. If the gate fails, P1-P3 are NOT TESTABLE.

## Predictions

- **P1.** Not counting the two known stack-protection entries, the four branch heads carry
  **at least 3** more future notes (mechanical count). About 55%. The init.rst split shows
  that whole-page backports can carry `main`'s numbers, and many C API and library pages
  were reorganised on `main` in 2025-2026. But most backports are small, and `next` was
  meant to stop exactly this.
- **P2.** Of micro notes ever seen at a tag whose owner is still documented at the head,
  **at least 95%** survive (pooled over the four branches). About 70%. Losing a note needs
  a rewrite of the surrounding text, which is rare on maintenance branches.
- **P3.** Hand review confirms **at least 2** real problems besides the known pair: a
  future note or a lost micro note, live at a branch head, that gives the wrong first
  version for that branch. About 45%. This is the least blind prediction, because the
  verdict is human judgement under the labels below.

Exploratory (no prediction): `next` placeholders left in the docs at release tags (they
should have been replaced when the release was cut).

## Hand review (fixed now)

Every future note and every lost micro note is read in the rst source at the branch head and
at the tag, and checked against the branch's What's New, changelog and headers or `Lib/`.

- **wrong version on this branch:** the object or behaviour exists in a 3.Y release, but the
  3.Y docs give a later version, or the bugfix-release note was replaced by a later
  version or dropped.
- **intended forward reference:** the 3.Y docs knowingly describe a later change (for
  example a planned removal).
- **renamed or moved:** the same note lives on under another owner.
- **parser artefact.**

Only "wrong version on this branch" counts for P3. Those go on FIXLIST.md with evidence. Each
is checked against python/cpython issues and PRs before anything is suggested upstream.

## How blind this is

The stack-protection pair and the #159013 control were known before this file was written,
and they define the gate. No other note on any branch or tag has been listed or counted.

## Limits

Final tags only (no alphas, betas or release candidates). Owners are matched by name, so two
objects with the same name in the same module chain are merged. A note outside any object
directive can be counted as a future note but never as lost.
