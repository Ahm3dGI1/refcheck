import subprocess
import sys
import unittest
from pathlib import Path


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
