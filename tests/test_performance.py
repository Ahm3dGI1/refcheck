import unittest
from unittest.mock import patch

from refcheck.checkers.compare import compare_with_performance
from refcheck.checkers.performance import get_performance


class PerformanceTests(unittest.TestCase):
    def test_average_and_repetition_count(self):
        calls = []

        def target(value):
            calls.append(value)

        with patch(
            "refcheck.checkers.performance.perf_counter", side_effect=[10, 12, 20, 24]
        ):
            results = get_performance(target, {"case": [7]}, num_executions=2)

        self.assertEqual(results, {"case": 3.0})
        self.assertEqual(calls, [7, 7])

    def test_mutable_arguments_start_fresh_each_repetition(self):
        lengths = []

        def target(values):
            lengths.append(len(values))
            values.append(1)

        inputs = {"case": [[]]}
        get_performance(target, inputs, num_executions=2)

        self.assertEqual(lengths, [0, 0])
        self.assertEqual(inputs, {"case": [[]]})

    def test_non_positive_repetitions_are_rejected(self):
        for repetitions in (0, -1):
            with self.subTest(repetitions=repetitions), self.assertRaises(ValueError):
                get_performance(lambda: None, {"case": []}, repetitions)

    def test_comparison_passes_original_arguments_to_timing(self):
        with patch(
            "refcheck.checkers.performance.perf_counter", side_effect=[1, 3, 5, 8]
        ):
            result = compare_with_performance(
                lambda value: value + 1,
                lambda value: value + 1,
                {"case": [7]},
                num_executions=1,
            )["case"]

        self.assertFalse(result.return_diff)
        self.assertEqual(result.performance_original, 2.0)
        self.assertEqual(result.performance_migrated, 3.0)
