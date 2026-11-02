"""Find every version note (versionadded, versionchanged, versionremoved, deprecated,
deprecated-removed) in CPython's Doc/ tree, attach it to the object it documents, and
compare a maintenance branch's docs with its own release tags.

Two checks:
- future notes: a note on branch 3.Y whose own version is a later 3.x (for example
  "Added in version 3.15" in the 3.14 docs). Removal versions are not counted.
- lost micro notes: a note naming a bugfix release (3.m.z, z >= 1) that a release tag
  of the branch carried and the branch head no longer carries, while the object is still
  documented there.

MV2, Munim, Inc. Apache-2.0. Made with AI agents.
"""
import re

DIRECTIVE = re.compile(r"^( *)\.\. ([a-z][a-z0-9-]*(?::[a-z][a-z0-9-]*)?)::(.*)$")
VERSION_DIRECTIVES = ("versionadded", "versionchanged", "versionremoved",
                      "deprecated", "deprecated-removed")
PY_OBJECTS = {"function", "class", "method", "attribute", "data", "exception",
              "classmethod", "staticmethod", "property", "decorator", "decoratormethod",
              "coroutinefunction", "coroutinemethod", "abstractmethod",
              "awaitablefunction", "awaitablemethod", "type"}
OTHER_OBJECTS = {"envvar", "option", "cmdoption", "opcode", "describe", "object",
                 "pdbcommand", "monitoring-event"}
C_NOT_OBJECTS = {"c:namespace", "c:namespace-push", "c:namespace-pop", "c:alias"}
C_TYPE_WORDS = {"void", "int", "char", "const", "unsigned", "signed", "long", "short",
                "double", "float", "struct", "union", "enum", "static", "inline"}
VER = re.compile(r"^(\d+)\.(\d+)(?:\.(\d+))?$")
CALL = re.compile(r"([A-Za-z_]\w*)\s*\(")
IDENT = re.compile(r"[A-Za-z_]\w*")
PYNAME = re.compile(r"[A-Za-z_][\w.]*")

# Known case found by hand on 2026-11-02 (gate positive) and a control (gate negative).
KNOWN_OWNERS = ("|c:function:PyUnstable_ThreadState_SetStackProtection",
                "|c:function:PyUnstable_ThreadState_ResetStackProtection")
CONTROL_OWNER = "tarfile|exception:LinkFallbackError"
MIN_NOTES_PER_TAG = 2000
P1_BAR = 3
P2_BAR = 0.95


def vtuple(tok):
    """'3.14' -> (3, 14, None); '3.14.1' -> (3, 14, 1); anything else -> None."""
    m = VER.match(tok or "")
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)),
            int(m.group(3)) if m.group(3) is not None else None)


def is_object(kind):
    if kind.startswith("c:"):
        return kind not in C_NOT_OBJECTS
    return kind in PY_OBJECTS or kind in OTHER_OBJECTS


def obj_name(kind, arg):
    if kind.startswith("c:"):
        if kind in ("c:function", "c:macro"):
            for m in CALL.finditer(arg):
                if m.group(1) not in C_TYPE_WORDS:
                    return m.group(1)
        ids = [x for x in IDENT.findall(arg) if x not in C_TYPE_WORDS]
        return ids[-1] if ids else arg
    if kind in PY_OBJECTS:
        m = PYNAME.match(arg)
        return m.group(0).rstrip(".") if m else arg
    return arg


def key(module, stack):
    return module + "|" + "/".join(lbl for _, lbl in stack)


def scan(text, path=""):
    """Return (notes, owners) for one .rst file.

    A note's owner is the chain of object directives it sits inside (module or
    currentmodule prefix), or None when it is not inside any object directive.
    owners is the set of keys of every object directive in the file.
    """
    notes, owners = [], set()
    stack = []
    module = ""
    for i, line in enumerate(text.splitlines()):
        if not line.strip():
            continue
        ind = len(line) - len(line.lstrip(" "))
        while stack and stack[-1][0] >= ind:
            stack.pop()
        m = DIRECTIVE.match(line)
        if not m:
            continue
        kind = m.group(2)
        if kind.startswith("py:"):
            kind = kind[3:]
        arg = " ".join(m.group(3).split())
        if kind in ("module", "currentmodule"):
            module = "" if arg == "None" else arg
            continue
        if kind in VERSION_DIRECTIVES:
            tok = arg.split()
            notes.append({"file": path, "line": i + 1, "directive": kind,
                          "version": tok[0] if tok else "",
                          "removal": tok[1] if kind == "deprecated-removed" and len(tok) > 1
                          else "",
                          "owner": key(module, stack) if stack else None})
            continue
        if is_object(kind):
            stack.append((ind, "%s:%s" % (kind, obj_name(kind, arg))))
            owners.add(key(module, stack))
    return notes, owners


def merge(scans):
    """Combine (notes, owners) pairs from several files into one."""
    notes, owners = [], set()
    for n, o in scans:
        notes.extend(n)
        owners |= o
    return notes, owners


def is_future(note, minor):
    """The note's own version is a later 3.x than branch 3.minor (removal not counted)."""
    v = vtuple(note["version"])
    return v is not None and v[0] == 3 and v[1] > minor


def is_micro(note):
    v = vtuple(note["version"])
    return v is not None and v[2] is not None and v[2] >= 1


def fkey(note):
    return (note["owner"] or "file:" + note["file"], note["directive"], note["version"])


def branch_report(minor, tag_scans, head):
    """tag_scans: [(tag, notes, owners)] in release order; head: (notes, owners)."""
    head_notes, head_owners = head
    head_idx = {}
    for n in head_notes:
        if n["owner"]:
            head_idx.setdefault(n["owner"], set()).add((n["directive"], n["version"]))
    seen, future_first, nexts = {}, {}, []
    for tag, notes, _owners in tag_scans:
        for n in notes:
            if n["version"] == "next":
                nexts.append({"tag": tag, "file": n["file"], "line": n["line"],
                              "directive": n["directive"], "owner": n["owner"] or ""})
            if is_future(n, minor):
                future_first.setdefault(fkey(n), tag)
            if n["owner"] and is_micro(n):
                k = (n["owner"], n["directive"], n["version"])
                if k not in seen:
                    seen[k] = {"first_tag": tag, "last_tag": tag,
                               "file": n["file"], "line": n["line"]}
                else:
                    seen[k]["last_tag"] = tag
    survived, lost, gone = [], [], []
    for (owner, d, v) in sorted(seen):
        row = dict(seen[(owner, d, v)], owner=owner, directive=d, version=v)
        if owner not in head_owners:
            gone.append(row)
        elif (d, v) in head_idx.get(owner, set()):
            survived.append(row)
        else:
            row["head_notes"] = sorted(head_idx.get(owner, set()))
            lost.append(row)
    future = []
    for n in head_notes:
        if is_future(n, minor):
            future.append(dict(n, first_tag=future_first.get(fkey(n), "head_only")))
    return {"minor": minor, "future": future, "lost": lost, "gone": gone,
            "survived": len(survived), "next_at_tags": nexts,
            "control_owner_present": CONTROL_OWNER in head_owners}


def gate(reports, tag_counts, fetched, expected):
    det = {}
    r = reports.get("3.14")
    if r is None:
        return "FAILED", {"3.14 branch scanned": False}
    det["known lost: versionadded 3.14.1 on SetStackProtection gone from the 3.14 head"] = any(
        x["owner"] == KNOWN_OWNERS[0] and x["directive"] == "versionadded"
        and x["version"] == "3.14.1" for x in r["lost"])
    det["known future: versionadded 3.15 on SetStackProtection at the 3.14 head"] = any(
        x["owner"] == KNOWN_OWNERS[0] and x["version"] == "3.15" for x in r["future"])
    det["control: LinkFallbackError documented at the 3.14 head with no future note"] = (
        r["control_owner_present"]
        and not any(x["owner"] == CONTROL_OWNER for x in r["future"]))
    det["every fetched tag has >= %d version notes" % MIN_NOTES_PER_TAG] = bool(
        tag_counts) and min(tag_counts.values()) >= MIN_NOTES_PER_TAG
    det[">= 90%% of tags fetched (%d of %d)" % (fetched, expected)] = fetched >= 0.9 * expected
    return ("HELD" if all(det.values()) else "FAILED"), det


def grade(reports):
    """P1: future notes at the heads beyond the known pair. P2: micro-note survival."""
    extra = [x for r in reports.values() for x in r["future"]
             if x["owner"] not in KNOWN_OWNERS]
    survived = sum(r["survived"] for r in reports.values())
    lost = sum(len(r["lost"]) for r in reports.values())
    share = survived / (survived + lost) if survived + lost else None
    return {
        "P1": {"future_beyond_known": len(extra), "bar": P1_BAR,
               "verdict": "held" if len(extra) >= P1_BAR else "failed"},
        "P2": {"survived": survived, "lost": lost, "share": share, "bar": P2_BAR,
               "verdict": ("not_testable" if share is None else
                           "held" if share >= P2_BAR else "failed")},
        "P3": {"candidates": len(extra) + lost, "verdict": "pending hand review"},
    }
