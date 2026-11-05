import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from refcheck.cli import print_results
from refcheck.models import ComparisonResults, ExecutionResult


class CliTests(unittest.TestCase):
    def run_cli(self, *arguments):
        return subprocess.run(
            [sys.executable, "-m", "refcheck.cli", *arguments],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_two_equivalent_functions_print_matches(self):
        process = self.run_cli(
            "benchmarks.comparison_cases:double_original",
            "benchmarks.comparison_cases:double_equivalent",
        )

        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("MATCH", process.stdout)
        self.assertIn("0 different.", process.stdout)

    def test_changed_function_prints_differences(self):
        process = self.run_cli(
            "benchmarks.comparison_cases:double_original",
            "benchmarks.comparison_cases:double_changed",
        )

        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("DIFFERENT", process.stdout)

    def test_missing_function_prints_usage(self):
        process = self.run_cli()

        self.assertEqual(process.returncode, 1)
        self.assertIn("Usage:", process.stdout)

    def test_mutation_only_difference_is_reported(self):
        result = ComparisonResults(
            ExecutionResult(arguments=([],), arguments_after=([1],)),
            ExecutionResult(arguments=([],), arguments_after=([],)),
            False,
            None,
            None,
        )
        output = StringIO()
        with redirect_stdout(output):
            print_results({"case": result})

        self.assertIn("case: DIFFERENT", output.getvalue())
        self.assertIn("1 different.", output.getvalue())

    def test_unknown_mutations_do_not_print_match(self):
        result = ComparisonResults(
            ExecutionResult(arguments=(1,)),
            ExecutionResult(arguments=(1,)),
            False,
            None,
            None,
        )
        output = StringIO()
        with redirect_stdout(output):
            print_results({"case": result})

        self.assertIn("case: INCOMPLETE", output.getvalue())
        self.assertIn("mutation comparison unavailable", output.getvalue())
        self.assertNotIn("MATCH", output.getvalue())

    def test_return_difference_is_reported_with_unknown_mutations(self):
        result = ComparisonResults(
            ExecutionResult(arguments=(1,), value=1),
            ExecutionResult(arguments=(1,), value=2),
            True,
            None,
            None,
        )
        output = StringIO()
        with redirect_stdout(output):
            print_results({"case": result})

        self.assertIn("case: DIFFERENT", output.getvalue())
        self.assertIn("mutation comparison unavailable", output.getvalue())
