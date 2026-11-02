# Fix list (run 1)

MV2, Munim, Inc. (mv2@munimtech.com). Found by AI agents working in MV2's name, read in the
CPython sources at the commits named in GRADING.md. Not checked by a human or a CPython
maintainer. CPython accepts contributions only from humans, so nothing here has been filed
upstream by these agents. Text CC BY 4.0.

| # | Branch | Where | Problem | Suggested change | Fixable? |
|---|---|---|---|---|---|
| 1 | 3.14 | `Doc/c-api/threads.rst`, `PyUnstable_ThreadState_SetStackProtection` / `..._ResetStackProtection` | say "Added in version 3.15"; both shipped in 3.14.1, and the 3.14.0-incompatibility warning shown in the 3.14.1-3.14.3 docs is gone (lost in the GH-145061 split backport) | `versionadded:: 3.14.1` and restore the warning, as at v3.14.3 `Doc/c-api/init.rst` | yes (bugfix branch) |
| 2 | 3.14 | `Doc/library/datetime.rst:1074`, `datetime.utcfromtimestamp` | "Changed in version 3.15: Accepts any real number as *timestamp*" was carried in by GH-144956 ("Datetime: Tidy up docs"); gh-67795 is a 3.15 change | delete the two-line `versionchanged:: 3.15` block on the 3.14 branch only | yes (bugfix branch); runtime check queued |
| 3 | 3.13 | `Doc/c-api/init.rst`, "Legacy Locking APIs" and `PyThread_allocate_lock` | two "Changed in version 3.15" notes say the API now uses `PyMutex`; 3.13 uses `sem_t` / pthread locks. Carried in by GH-141955 | delete both `versionchanged:: 3.15` blocks on 3.13 | unlikely: 3.13 is security-only |

Item 1 was found while grading munimtechnologies/capi-versionadded-audit and confirmed here by
the gate. Items 2 and 3 are new in this run.
