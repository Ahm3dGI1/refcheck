import unittest

from benchmarks.comparison_cases import (
    CASES,
    reject_changed,
    reject_equivalent,
    reject_original,
    return_error_text,
)

from refcheck.checkers.compare import compare, compare_with_performance


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

    def test_generated_cases_are_collected(self):
        results = compare(simple_original, simple_equivalent, max_examples=5)

        self.assertGreater(len(results), 0)
        self.assertLessEqual(len(results), 5)
        self.assertTrue(all(not result.return_diff for result in results.values()))

    def test_generated_differences_are_reported(self):
        results = compare(simple_original, simple_changed, max_examples=5)

        self.assertTrue(results)
        self.assertTrue(all(result.return_diff for result in results.values()))

    def test_exceptions_are_compared_separately_from_returns(self):
        for function, expected_diff in (
            (reject_equivalent, False),
            (reject_changed, True),
            (return_error_text, True),
        ):
            with self.subTest(function=function.__name__):
                result = compare(reject_original, function, {"case": [1]})
                self.assertEqual(result["case"].return_diff, expected_diff)

    def test_independent_mutable_arguments(self):
        def mutate(values):
            values.append(1)
            return len(values)

        inputs = {"case": [[]]}
        result = compare(mutate, mutate, inputs)

        self.assertFalse(result["case"].return_diff)
        self.assertEqual(inputs, {"case": [[]]})

    def test_incompatible_signature_is_rejected(self):
        def needs_two(first, second):
            return first + second

        with self.assertRaises(TypeError):
            compare(simple_original, needs_two, {"case": [1]})

    def test_benchmark_scenarios(self):
        expected_differences = [0, 1, 1, 1, 0, 1, 1, 0, 1]
        for (label, original, migrated, inputs), expected in zip(
            CASES, expected_differences, strict=True
        ):
            with self.subTest(scenario=label):
                results = compare(original, migrated, inputs)
                self.assertEqual(set(results), set(inputs))
                self.assertEqual(
                    sum(result.return_diff for result in results.values()), expected
                )

    def test_exception_cases_are_not_timed(self):
        result = compare_with_performance(
            reject_original, reject_equivalent, {"case": [1]}, num_executions=2
        )["case"]

        self.assertFalse(result.return_diff)
        self.assertIsNone(result.performance_original)
        self.assertIsNone(result.performance_migrated)
