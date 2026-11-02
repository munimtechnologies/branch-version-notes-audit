"""Runtime checks behind the hand review of two CPython doc audits (run 1):
munimtechnologies/branch-version-notes-audit and munimtechnologies/stdlib-deprecation-ledger.

Each check runs a short snippet in a fresh `python -I` process for several CPython minors
(python-build-standalone via uv) and compares the last stdout line with an expected outcome
that was fixed in CHECKS (and EXPECTED.md) BEFORE the run. A rule of None is exploratory.

MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents working in MV2's name.
Licence: Apache-2.0.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time

UV_ENV = dict(os.environ, UV_PYTHON_PREFERENCE="only-managed",
              UV_PYTHON_INSTALL_DIR="/tmp/uv-python")
OPTIONAL = {"3.16"}   # pre-release; used only if uv has it

CHECKS = [
    {
        "id": "thread_lock",
        "about": "3.13 docs (Legacy Locking APIs) say 'Changed in version 3.15: ... now always "
                 "uses PyMutex'. Which lock does each interpreter report?",
        "minors": ["3.13", "3.14", "3.15", "3.16"],
        "expect": {"3.13": "ne:pymutex", "3.14": "ne:pymutex", "3.15": "eq:pymutex"},
        "code": "\n".join([
            "import sys",
            "print(sys.thread_info.lock)",
        ]),
    },
    {
        "id": "utcfromtimestamp_fraction",
        "about": "3.14 docs say datetime.utcfromtimestamp 'Changed in version 3.15: Accepts any "
                 "real number as timestamp' (gh-67795). Does 3.14 accept a Fraction?",
        "minors": ["3.13", "3.14", "3.15", "3.16"],
        "expect": {"3.13": "prefix:error", "3.14": "prefix:error", "3.15": "prefix:ok"},
        "code": "\n".join([
            "import datetime, fractions, warnings",
            "warnings.simplefilter('ignore')",
            "try:",
            "    r = datetime.datetime.utcfromtimestamp(fractions.Fraction(1, 2))",
            "    print('ok ' + r.isoformat())",
            "except Exception as e:",
            "    print('error ' + type(e).__name__)",
        ]),
    },
    {
        "id": "fromtimestamp_fraction",
        "about": "Same change family: datetime.fromtimestamp(Fraction, tz=UTC).",
        "minors": ["3.13", "3.14", "3.15", "3.16"],
        "expect": {"3.14": "prefix:error", "3.15": "prefix:ok"},
        "code": "\n".join([
            "import datetime, fractions, warnings",
            "warnings.simplefilter('ignore')",
            "try:",
            "    r = datetime.datetime.fromtimestamp(fractions.Fraction(1, 2),",
            "                                        tz=datetime.timezone.utc)",
            "    print('ok ' + r.isoformat())",
            "except Exception as e:",
            "    print('error ' + type(e).__name__)",
        ]),
    },
    {
        "id": "gettext_l_functions",
        "about": "3.10 docs say lngettext, ldngettext, bind_textdomain_codeset and "
                 "NullTranslations.output_charset were 'removed in version 3.10'.",
        "minors": ["3.10", "3.11"],
        "expect": {"3.10": "eq:True True True True", "3.11": "eq:False False False False"},
        "code": "\n".join([
            "import gettext",
            "names = ['lngettext', 'ldngettext', 'bind_textdomain_codeset']",
            "got = [hasattr(gettext, n) for n in names]",
            "got.append(hasattr(gettext.NullTranslations, 'output_charset'))",
            "print(' '.join(str(g) for g in got))",
        ]),
    },
    {
        "id": "open_U_mode",
        "about": "3.10 docs say open()'s 'U' mode was 'removed in version 3.10'.",
        "minors": ["3.10", "3.11"],
        "expect": {"3.10": "eq:ok", "3.11": "eq:error ValueError"},
        "code": "\n".join([
            "import os, tempfile, warnings",
            "warnings.simplefilter('ignore')",
            "p = os.path.join(tempfile.mkdtemp(), 'f.txt')",
            "with open(p, 'w') as f:",
            "    f.write('x')",
            "try:",
            "    with open(p, 'rU') as f:",
            "        f.read()",
            "    print('ok')",
            "except ValueError:",
            "    print('error ValueError')",
        ]),
    },
    {
        "id": "typing_io_re_namespaces",
        "about": "3.9 docs said the typing.io / typing.re namespaces would be removed in 3.12; "
                 "3.10+ docs say 3.13.",
        "minors": ["3.12", "3.13"],
        "expect": {"3.12": "eq:ok", "3.13": "prefix:error"},
        "code": "\n".join([
            "import warnings",
            "warnings.simplefilter('ignore')",
            "try:",
            "    import typing.io",
            "    import typing.re",
            "    print('ok')",
            "except ImportError as e:",
            "    print('error ' + type(e).__name__)",
        ]),
    },
    {
        "id": "argparse_nested_group",
        "about": "Live note (3.14+): nesting groups inside a mutually exclusive group is "
                 "'removed in version 3.14'.",
        "minors": ["3.13", "3.14"],
        "expect": {"3.13": "eq:ok", "3.14": "prefix:error"},
        "code": "\n".join([
            "import argparse, warnings",
            "warnings.simplefilter('ignore')",
            "p = argparse.ArgumentParser()",
            "g = p.add_mutually_exclusive_group()",
            "try:",
            "    g.add_mutually_exclusive_group()",
            "    print('ok')",
            "except Exception as e:",
            "    print('error ' + type(e).__name__)",
        ]),
    },
    {
        "id": "nodevisitor_visit_num",
        "about": "Live note (3.14+): NodeVisitor.visit_Num and friends 'will not be called in "
                 "Python 3.14+' (removed in version 3.14).",
        "minors": ["3.13", "3.14"],
        "expect": {"3.13": "eq:True", "3.14": "eq:False"},
        "code": "\n".join([
            "import ast, warnings",
            "warnings.simplefilter('ignore')",
            "class V(ast.NodeVisitor):",
            "    hit = False",
            "    def visit_Num(self, node):",
            "        V.hit = True",
            "V().visit(ast.parse('1'))",
            "print(V.hit)",
        ]),
    },
    {
        "id": "sourceless_load_module",
        "about": "Exploratory: do SourcelessFileLoader / SourceFileLoader still have "
                 "load_module ('will be removed in version 3.15' in the 3.12-3.14 docs)?",
        "minors": ["3.14", "3.15", "3.16"],
        "expect": {},
        "code": "\n".join([
            "import importlib.machinery as m",
            "print(hasattr(m.SourcelessFileLoader, 'load_module'),",
            "      hasattr(m.SourceFileLoader, 'load_module'))",
        ]),
    },
]


def verdict(got, rule):
    """Compare one observed line with one expected rule."""
    if rule is None:
        return "exploratory"
    if got is None:
        return "no_result"
    kind, _, value = rule.partition(":")
    if kind == "eq":
        ok = got == value
    elif kind == "ne":
        ok = got != value
    elif kind == "prefix":
        ok = got.startswith(value)
    else:
        raise ValueError("unknown rule kind: %r" % kind)
    return "match" if ok else "mismatch"


def last_line(text):
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    return lines[-1] if lines else None


def interpreter(minor):
    r = subprocess.run(["uv", "python", "install", minor], env=UV_ENV,
                       capture_output=True, text=True, timeout=1200)
    if r.returncode != 0:
        return None, (r.stderr or r.stdout)[-400:]
    r = subprocess.run(["uv", "python", "find", minor], env=UV_ENV,
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0 or not r.stdout.strip():
        return None, (r.stderr or r.stdout)[-400:]
    return r.stdout.strip().splitlines()[-1], ""


def run_snippet(py, code):
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "snippet.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(code + "\n")
    try:
        r = subprocess.run([py, "-I", path], cwd=tmp, stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return None, "timeout", -1
    return last_line(r.stdout), (r.stderr or "")[-300:], r.returncode


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)

    minors = sorted({m for c in CHECKS for m in c["minors"]}, key=lambda v: int(v.split(".")[1]))
    interps = {}
    for m in minors:
        py, err = interpreter(m)
        info = {"installed": py is not None, "error": err}
        if py:
            got, _, _ = run_snippet(py, "import sys, platform\n"
                                        "print(platform.python_version(), sys.platform)")
            info["version"] = got
        interps[m] = (py, info)

    results, counts = [], {"match": 0, "mismatch": 0, "no_result": 0, "exploratory": 0}
    for c in CHECKS:
        for m in c["minors"]:
            py, info = interps[m]
            rule = c["expect"].get(m)
            if py is None:
                got, err, rc = None, info["error"], None
            else:
                got, err, rc = run_snippet(py, c["code"])
            v = verdict(got, rule)
            if py is None and m in OPTIONAL and rule is None:
                v = "exploratory"
            counts[v] += 1
            results.append({"check": c["id"], "minor": m, "version": info.get("version"),
                            "got": got, "rule": rule, "verdict": v, "returncode": rc,
                            "stderr_tail": err if v in ("mismatch", "no_result") else ""})
            print("CHECK %s %s got=%r rule=%r %s" % (c["id"], m, got, rule, v))

    summary = {
        "checks": [{k: c[k] for k in ("id", "about", "minors", "expect")} for c in CHECKS],
        "results": results,
        "counts": counts,
        "all_expected_held": counts["mismatch"] == 0 and counts["no_result"] == 0,
        "interpreters": {m: info for m, (py, info) in interps.items()},
        "platform": sys.platform,
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1, sort_keys=True)
    print("COUNTS", json.dumps(counts, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
