import unittest

from refcheck.checkers.compare import compare


def simple_original(value: int) -> int:
    return value + 1


def simple_equivalent(value: int) -> int:
    return 1 + value


def simple_changed(value: int) -> int:
    return value + 2


class CompareTests(unittest.TestCase):
    def test_equal_returns_are_not_reported_as_different(self):
        cases = {
            "negative": [-3],
            "zero": [0],
            "positive": [3],
        }

        results = compare(simple_original, simple_equivalent, cases)

        self.assertEqual(set(results), set(cases))

        for case_name, result in results.items():
            with self.subTest(case=case_name):
                self.assertFalse(result.return_diff)

    def test_different_returns_are_reported(self):
        cases = {"positive": [3]}

        results = compare(simple_original, simple_changed, cases)

        self.assertTrue(results["positive"].return_diff)

    def test_empty_inputs_produce_empty_results(self):
        results = compare(simple_original, simple_equivalent, {})

        self.assertEqual(results, {})