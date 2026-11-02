"""Data run: scan Doc/**/*.rst at the heads of CPython's 3.12-3.15 branches and at every
final release tag of each, then report future-version notes and lost bugfix-release notes.
Tarballs are streamed and not stored.

MV2, Munim, Inc. Apache-2.0. Made with AI agents.
"""
import argparse
import csv
import json
import os
import sys
import tarfile
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import notes as N  # noqa: E402

UA = {"User-Agent": "mv2-branch-version-notes-audit/0.1 (Munim, Inc.; mv2@munimtech.com)"}
HEAD = "https://codeload.github.com/python/cpython/tar.gz/refs/heads/%s"
TAG = "https://codeload.github.com/python/cpython/tar.gz/refs/tags/%s"
# Latest final tags on 2026-11-02 (github.com/python/cpython/tags).
LATEST = {12: 16, 13: 18, 14: 10, 15: 2}


def tag_names(minor):
    return ["v3.%d.%d" % (minor, z) for z in range(LATEST[minor] + 1)]


def read_docs(url, tries=3):
    err = None
    for k in range(tries):
        try:
            docs = {}
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=600) as r:
                with tarfile.open(fileobj=r, mode="r|gz") as tf:
                    for m in tf:
                        parts = m.name.split("/", 1)
                        if len(parts) != 2 or not m.isfile():
                            continue
                        rel = parts[1]
                        if rel.startswith("Doc/") and rel.endswith(".rst"):
                            docs[rel] = tf.extractfile(m).read().decode("utf-8", "replace")
                    commit = tf.pax_headers.get("comment", "")
            return docs, commit
        except Exception as e:
            err = e
            if "404" in str(e):
                break
            time.sleep(5 * (k + 1))
    raise err


def scan_docs(docs):
    return N.merge(N.scan(docs[p], p) for p in sorted(docs))


def write_csv(path, rows, cols):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow([json.dumps(r.get(c)) if isinstance(r.get(c), (list, dict))
                        else r.get(c, "") for c in cols])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="/out")
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    reports, tag_counts, tags_meta, heads_meta = {}, {}, [], {}
    fetched = expected = 0
    for minor in sorted(LATEST):
        br = "3.%d" % minor
        docs, commit = read_docs(HEAD % br)
        head = scan_docs(docs)
        heads_meta[br] = {"commit": commit, "rst_files": len(docs), "notes": len(head[0]),
                          "owners": len(head[1])}
        print("head %s: commit %s, %d files, %d notes" % (br, commit[:12], len(docs),
                                                          len(head[0])), flush=True)
        del docs
        tag_scans = []
        for t in tag_names(minor):
            expected += 1
            try:
                docs, tcommit = read_docs(TAG % t)
            except Exception as e:
                tags_meta.append({"tag": t, "error": str(e)[:200]})
                print("tag %s failed: %s" % (t, e), flush=True)
                continue
            fetched += 1
            notes, owners = scan_docs(docs)
            del docs
            tag_counts[t] = len(notes)
            tags_meta.append({"tag": t, "commit": tcommit, "notes": len(notes),
                              "future": sum(1 for n in notes if N.is_future(n, minor)),
                              "micro": sum(1 for n in notes if N.is_micro(n)),
                              "next": sum(1 for n in notes if n["version"] == "next")})
            tag_scans.append((t, notes, owners))
            print("tag %s: %d notes" % (t, len(notes)), flush=True)
        reports[br] = N.branch_report(minor, tag_scans, head)
        del tag_scans

    verdict, details = N.gate(reports, tag_counts, fetched, expected)
    res = N.grade(reports)
    res["P0_gate"] = {"verdict": verdict, "details": details}
    if verdict != "HELD":
        for k in ("P1", "P2", "P3"):
            res[k]["verdict"] = "NOT_TESTABLE (gate failed)"
    res["per_branch"] = {b: {"future": len(r["future"]), "lost": len(r["lost"]),
                             "gone": len(r["gone"]), "survived": r["survived"],
                             "next_at_tags": len(r["next_at_tags"])}
                         for b, r in reports.items()}
    res["source"] = {"started_at": started, "heads": heads_meta, "tags": tags_meta,
                     "tags_fetched": fetched, "tags_expected": expected}

    future, lost, gone, nexts = [], [], [], []
    for b, r in sorted(reports.items()):
        future += [dict(x, branch=b) for x in r["future"]]
        lost += [dict(x, branch=b) for x in r["lost"]]
        gone += [dict(x, branch=b) for x in r["gone"]]
        nexts += [dict(x, branch=b) for x in r["next_at_tags"]]
    with open(os.path.join(a.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, sort_keys=True)
    write_csv(os.path.join(a.out_dir, "future_notes.csv"), future,
              ["branch", "file", "line", "directive", "version", "removal", "owner",
               "first_tag"])
    write_csv(os.path.join(a.out_dir, "lost_micro.csv"), lost,
              ["branch", "owner", "directive", "version", "first_tag", "last_tag", "file",
               "line", "head_notes"])
    write_csv(os.path.join(a.out_dir, "gone_micro.csv"), gone,
              ["branch", "owner", "directive", "version", "first_tag", "last_tag", "file",
               "line"])
    write_csv(os.path.join(a.out_dir, "next_at_tags.csv"), nexts,
              ["branch", "tag", "file", "line", "directive", "owner"])
    write_csv(os.path.join(a.out_dir, "tags.csv"), tags_meta,
              ["tag", "commit", "notes", "future", "micro", "next", "error"])

    print("P0", verdict, json.dumps(details))
    for k in ("P1", "P2", "P3"):
        print(k, json.dumps(res[k], sort_keys=True))
    for x in future:
        print("FUTURE", x["branch"], x["file"], x["line"], x["directive"], x["version"],
              x["owner"], x["first_tag"])
    for x in lost:
        print("LOST", x["branch"], x["owner"], x["directive"], x["version"], x["first_tag"],
              x["last_tag"], json.dumps(x["head_notes"]))


if __name__ == "__main__":
    main()
