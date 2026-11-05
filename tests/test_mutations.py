import unittest

from refcheck.checkers.compare import compare
from refcheck.models import ComparisonResults, ExecutionResult


class MutationTests(unittest.TestCase):
    def test_equal_returns_with_different_final_arguments(self):
        def in_place(values):
            values.sort()
            return values

        def copied(values):
            return sorted(values)

        inputs = {"case": [[3, 1, 2]]}
        result = compare(in_place, copied, inputs)["case"]

        self.assertFalse(result.return_diff)
        self.assertEqual(
            result.mutation_diff,
            {0: {"original_value": [1, 2, 3], "migrated_value": [3, 1, 2]}},
        )
        self.assertEqual(inputs, {"case": [[3, 1, 2]]})
        self.assertEqual(result.execution_Result_original.arguments, ([3, 1, 2],))

    def test_mutations_are_compared_when_both_functions_raise(self):
        def mutate_and_raise(values):
            values.append(1)
            raise ValueError("invalid")

        def just_raise(values):
            raise ValueError("invalid")

        result = compare(mutate_and_raise, just_raise, {"case": [[]]})["case"]

        self.assertFalse(result.return_diff)
        self.assertEqual(
            result.mutation_diff,
            {0: {"original_value": [1], "migrated_value": []}},
        )

    def test_mutations_are_compared_when_only_one_function_raises(self):
        def mutate_and_raise(values):
            values.append(1)
            raise ValueError("invalid")

        def unchanged(values):
            return None

        result = compare(mutate_and_raise, unchanged, {"case": [[]]})["case"]

        self.assertTrue(result.return_diff)
        self.assertEqual(
            result.mutation_diff,
            {0: {"original_value": [1], "migrated_value": []}},
        )

    def test_identical_mutations_match_even_when_raising(self):
        def mutate_and_raise(values):
            values.append(1)
            raise ValueError("invalid")

        result = compare(mutate_and_raise, mutate_and_raise, {"case": [[]]})["case"]

        self.assertFalse(result.return_diff)
        self.assertEqual(result.mutation_diff, {})

    def test_missing_snapshots_are_unknown(self):
        for original_after, migrated_after in (
            (None, None),
            ((1,), None),
            (None, (1,)),
        ):
            with self.subTest(original=original_after, migrated=migrated_after):
                result = ComparisonResults(
                    ExecutionResult(arguments=(1,), arguments_after=original_after),
                    ExecutionResult(arguments=(1,), arguments_after=migrated_after),
                    False,
                    None,
                    None,
                )
                self.assertIsNone(result.mutation_diff)

    def test_explicit_empty_override_is_preserved(self):
        override = {}
        result = ComparisonResults(
            ExecutionResult(arguments=([1],), arguments_after=([1],)),
            ExecutionResult(arguments=([1],), arguments_after=([1, 2],)),
            False,
            None,
            None,
            mutation_diff=override,
        )

        self.assertIs(result.mutation_diff, override)

    def test_nan_arguments_and_returns_match(self):
        def identity(value):
            return value

        result = compare(identity, identity, {"nan": [float("nan")]})["nan"]

        self.assertFalse(result.return_diff)
        self.assertEqual(result.mutation_diff, {})

    def test_nan_and_number_still_differ(self):
        def assign_nan(values):
            values[0] = float("nan")

        def assign_zero(values):
            values[0] = 0.0

        # A NaN versus a number must remain different, including inside a list.
        result = compare(assign_nan, assign_zero, {"case": [[1.0]]})["case"]

        self.assertEqual(set(result.mutation_diff), {0})

    def test_empty_argument_snapshots_are_checked(self):
        result = compare(lambda: None, lambda: None, {"case": []})["case"]

        self.assertEqual(result.mutation_diff, {})
