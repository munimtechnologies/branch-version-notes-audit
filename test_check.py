"""Tests for check.py (hand-traced expected values). Apache-2.0. MV2, Munim, Inc."""
import unittest

import check


class VerdictTests(unittest.TestCase):
    def test_eq(self):
        self.assertEqual(check.verdict("pymutex", "eq:pymutex"), "match")
        self.assertEqual(check.verdict("semaphore", "eq:pymutex"), "mismatch")

    def test_eq_value_with_space(self):
        self.assertEqual(check.verdict("error ValueError", "eq:error ValueError"), "match")

    def test_ne(self):
        self.assertEqual(check.verdict("semaphore", "ne:pymutex"), "match")
        self.assertEqual(check.verdict("pymutex", "ne:pymutex"), "mismatch")

    def test_prefix(self):
        self.assertEqual(check.verdict("error TypeError", "prefix:error"), "match")
        self.assertEqual(check.verdict("ok 1970-01-01T00:00:00.500000", "prefix:error"),
                         "mismatch")

    def test_missing_and_exploratory(self):
        self.assertEqual(check.verdict(None, "eq:x"), "no_result")
        self.assertEqual(check.verdict("x", None), "exploratory")
        self.assertEqual(check.verdict(None, None), "exploratory")

    def test_unknown_rule(self):
        with self.assertRaises(ValueError):
            check.verdict("x", "regex:x")


class HelperTests(unittest.TestCase):
    def test_last_line(self):
        self.assertEqual(check.last_line("a\n\nb\n"), "b")
        self.assertIsNone(check.last_line(""))
        self.assertIsNone(check.last_line(None))

    def test_rules_cover_listed_minors_only(self):
        for c in check.CHECKS:
            for m in c["expect"]:
                self.assertIn(m, c["minors"], c["id"])

    def test_ids_unique_and_snippets_compile(self):
        ids = [c["id"] for c in check.CHECKS]
        self.assertEqual(len(ids), len(set(ids)))
        for c in check.CHECKS:
            compile(c["code"], c["id"], "exec")

    def test_rule_kinds_known(self):
        for c in check.CHECKS:
            for rule in c["expect"].values():
                self.assertIn(rule.partition(":")[0], ("eq", "ne", "prefix"))


if __name__ == "__main__":
    unittest.main()
