"""Unit tests with hand-traced expectations. MV2, Munim, Inc. Apache-2.0. Made with AI agents."""
import unittest

import job
import notes as N

SETSP = "|c:function:PyUnstable_ThreadState_SetStackProtection"
CLEAR = "|c:function:PyThreadState_Clear"
MACRO = "|c:macro:Py_BEGIN_ALLOW_THREADS"
LFE = "tarfile|exception:LinkFallbackError"
OLD = "tarfile|exception:OldError"

# Like Doc/c-api/init.rst at v3.14.3.
FIX_TAG = """\
Thread states
=============

.. c:function:: int PyUnstable_ThreadState_SetStackProtection(PyThreadState *tstate, void *stack_start_addr, size_t stack_size)

   Set the stack protection.

   .. versionadded:: 3.14.1

      .. warning::

         This function was added in a bugfix release.

.. c:function:: void PyThreadState_Clear(PyThreadState *tstate)

   .. versionchanged:: 3.9
      Now clears more.

.. note::

   .. versionadded:: next
"""

# Like Doc/c-api/threads.rst at the 3.14 head.
FIX_HEAD = """\
.. c:function:: int PyUnstable_ThreadState_SetStackProtection(PyThreadState *tstate, void *stack_start_addr, size_t stack_size)

   Set the stack protection.

   .. versionadded:: 3.15

.. c:function:: void PyThreadState_Clear(PyThreadState *tstate)

   .. versionchanged:: 3.9
      Now clears more.

   .. deprecated-removed:: 3.14 3.16

.. c:macro:: Py_BEGIN_ALLOW_THREADS

   .. versionchanged:: 3.16
"""

FIX_EXTRA_TAG = """\
.. module:: tarfile

.. exception:: LinkFallbackError

   .. versionchanged:: 3.14.5

.. exception:: OldError

   .. versionadded:: 3.14.2
"""

FIX_EXTRA_HEAD = """\
.. module:: tarfile

.. exception:: LinkFallbackError

   .. versionadded:: 3.14

   .. versionchanged:: 3.14.5
"""


def brief(notes):
    return [(n["line"], n["directive"], n["version"], n["removal"], n["owner"]) for n in notes]


class TestHelpers(unittest.TestCase):
    def test_vtuple(self):
        self.assertEqual(N.vtuple("3.14"), (3, 14, None))
        self.assertEqual(N.vtuple("3.14.1"), (3, 14, 1))
        self.assertIsNone(N.vtuple("next"))
        self.assertIsNone(N.vtuple(""))

    def test_obj_name(self):
        self.assertEqual(N.obj_name("c:function", "void (*PyOS_InputHook)(void)"),
                         "PyOS_InputHook")
        self.assertEqual(N.obj_name("c:macro", "Py_IS_TYPE(o, type)"), "Py_IS_TYPE")
        self.assertEqual(N.obj_name("c:var", "PyObject *Py_None"), "Py_None")
        self.assertEqual(N.obj_name("method", "Box.open(mode='r')"), "Box.open")
        self.assertEqual(N.obj_name("envvar", "PYTHONSAFEPATH"), "PYTHONSAFEPATH")

    def test_tag_names(self):
        self.assertEqual(job.tag_names(15), ["v3.15.0", "v3.15.1", "v3.15.2"])
        self.assertEqual(len(job.tag_names(13)), 19)


class TestScan(unittest.TestCase):
    def test_tag_fixture(self):
        notes, owners = N.scan(FIX_TAG, "Doc/c-api/init.rst")
        self.assertEqual(brief(notes), [
            (8, "versionadded", "3.14.1", "", SETSP),
            (16, "versionchanged", "3.9", "", CLEAR),
            (21, "versionadded", "next", "", None),
        ])
        self.assertEqual(owners, {SETSP, CLEAR})

    def test_head_fixture(self):
        notes, owners = N.scan(FIX_HEAD, "Doc/c-api/threads.rst")
        self.assertEqual(brief(notes), [
            (5, "versionadded", "3.15", "", SETSP),
            (9, "versionchanged", "3.9", "", CLEAR),
            (12, "deprecated-removed", "3.14", "3.16", CLEAR),
            (16, "versionchanged", "3.16", "", MACRO),
        ])
        self.assertEqual(owners, {SETSP, CLEAR, MACRO})

    def test_module_prefix(self):
        notes, owners = N.scan(FIX_EXTRA_TAG, "Doc/library/tarfile.rst")
        self.assertEqual(brief(notes), [
            (5, "versionchanged", "3.14.5", "", LFE),
            (9, "versionadded", "3.14.2", "", OLD),
        ])
        self.assertEqual(owners, {LFE, OLD})


def world():
    tag = N.merge([N.scan(FIX_TAG, "Doc/c-api/init.rst"),
                   N.scan(FIX_EXTRA_TAG, "Doc/library/tarfile.rst")])
    head = N.merge([N.scan(FIX_HEAD, "Doc/c-api/threads.rst"),
                    N.scan(FIX_EXTRA_HEAD, "Doc/library/tarfile.rst")])
    tags = [("v3.14.1", tag[0], tag[1]), ("v3.14.3", tag[0], tag[1])]
    return N.branch_report(14, tags, head)


class TestReport(unittest.TestCase):
    def test_branch_report(self):
        r = world()
        self.assertEqual([(x["owner"], x["directive"], x["version"], x["first_tag"],
                           x["last_tag"], x["head_notes"]) for x in r["lost"]],
                         [(SETSP, "versionadded", "3.14.1", "v3.14.1", "v3.14.3",
                           [("versionadded", "3.15")])])
        self.assertEqual([(x["owner"], x["version"]) for x in r["gone"]], [(OLD, "3.14.2")])
        self.assertEqual(r["survived"], 1)
        self.assertEqual([(x["owner"], x["version"], x["line"], x["first_tag"])
                          for x in r["future"]],
                         [(SETSP, "3.15", 5, "head_only"), (MACRO, "3.16", 16, "head_only")])
        self.assertEqual([(x["tag"], x["line"]) for x in r["next_at_tags"]],
                         [("v3.14.1", 21), ("v3.14.3", 21)])
        self.assertTrue(r["control_owner_present"])

    def test_gate_and_grade(self):
        reports = {"3.14": world()}
        verdict, det = N.gate(reports, {"v3.14.1": 2500, "v3.14.3": 2600}, 2, 2)
        self.assertEqual(verdict, "HELD", det)
        self.assertEqual(N.gate(reports, {"v3.14.1": 1999}, 2, 2)[0], "FAILED")
        self.assertEqual(N.gate(reports, {"v3.14.1": 2500}, 1, 2)[0], "FAILED")
        self.assertEqual(N.gate({}, {}, 0, 0)[0], "FAILED")
        g = N.grade(reports)
        self.assertEqual(g["P1"]["future_beyond_known"], 1)
        self.assertEqual(g["P1"]["verdict"], "failed")
        self.assertEqual((g["P2"]["survived"], g["P2"]["lost"]), (1, 1))
        self.assertAlmostEqual(g["P2"]["share"], 0.5)
        self.assertEqual(g["P2"]["verdict"], "failed")
        self.assertEqual(g["P3"]["candidates"], 2)


if __name__ == "__main__":
    unittest.main()
