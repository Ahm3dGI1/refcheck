import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from refcheck.cli import main, print_results
from refcheck.models import ComparisonResults, ExecutionResult
from refcheck.reporting import write_json_report


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

        self.assertEqual(process.returncode, 2)
        self.assertIn("usage:", process.stderr)

    def test_output_option_writes_report_and_keeps_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "comparison report.json"
            process = self.run_cli(
                "benchmarks.comparison_cases:double_original",
                "benchmarks.comparison_cases:double_equivalent",
                "--output",
                str(path),
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            report = json.loads(path.read_text(encoding="utf-8"))

        self.assertIn("MATCH", process.stdout)
        self.assertIn("JSON report written to", process.stdout)
        self.assertEqual(report["schema_version"], 2)
        self.assertGreater(report["summary"]["total_cases"], 0)
        self.assertEqual(report["summary"]["different_cases"], 0)
        self.assertEqual(
            report["functions"]["original"],
            "benchmarks.comparison_cases:double_original",
        )

    def test_report_write_error_is_clear(self):
        with tempfile.TemporaryDirectory() as directory:
            process = self.run_cli(
                "benchmarks.comparison_cases:double_original",
                "benchmarks.comparison_cases:double_equivalent",
                "--output",
                str(Path(directory) / "missing" / "report.json"),
            )

        self.assertEqual(process.returncode, 1)
        self.assertIn("Could not write JSON report:", process.stderr)
        self.assertNotIn("Traceback", process.stderr)

    def test_help_describes_output_option(self):
        process = self.run_cli("--help")

        self.assertEqual(process.returncode, 0)
        self.assertIn("--output", process.stdout)

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

    def make_replay_report(self, path):
        results = {}
        for name, value, different, incomplete in (
            ("same", 1, False, False),
            ("changed", 2, True, False),
            ("unknown", 3, False, True),
        ):
            after = None if incomplete else (value,)
            results[name] = ComparisonResults(
                ExecutionResult((value,), arguments_after=after),
                ExecutionResult((value,), arguments_after=after),
                different,
                None,
                None,
            )
        write_json_report(results, path)

    def test_replay_selects_saved_status_and_records_fresh_results(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.json"
            output = Path(directory) / "replayed.json"
            self.make_replay_report(source)
            contents = source.read_bytes()
            for status, names in (
                ("all", ["same", "changed", "unknown"]),
                ("different", ["changed"]),
                ("match", ["same"]),
                ("incomplete", ["unknown"]),
            ):
                with self.subTest(status=status):
                    process = self.run_cli(
                        "benchmarks.comparison_cases:double_original",
                        "benchmarks.comparison_cases:double_equivalent",
                        "--replay",
                        str(source),
                        "--select",
                        status,
                        "--output",
                        str(output),
                    )
                    self.assertEqual(process.returncode, 0, process.stderr)
                    report = json.loads(output.read_text(encoding="utf-8"))
                    self.assertEqual([case["name"] for case in report["cases"]], names)
                    self.assertTrue(
                        all(case["status"] == "match" for case in report["cases"])
                    )
                    self.assertEqual(
                        report["replay_source"],
                        {"report": str(source.resolve()), "cases": names},
                    )
                    self.assertEqual(source.read_bytes(), contents)

    def test_replay_defaults_to_all_cases(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.json"
            self.make_replay_report(source)
            process = self.run_cli(
                "benchmarks.comparison_cases:double_original",
                "benchmarks.comparison_cases:double_equivalent",
                "--replay",
                str(source),
            )
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("Compared 3 cases", process.stdout)

    def test_replay_repeated_case_option_preserves_selection_order(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.json"
            self.make_replay_report(source)
            process = self.run_cli(
                "benchmarks.comparison_cases:double_original",
                "benchmarks.comparison_cases:double_equivalent",
                "--replay",
                str(source),
                "--case",
                "changed",
                "--case",
                "same",
            )
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(
            process.stdout.splitlines()[:2], ["changed: MATCH", "same: MATCH"]
        )
        self.assertNotIn("unknown:", process.stdout)

    def test_replay_cannot_overwrite_source(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.json"
            self.make_replay_report(source)
            contents = source.read_bytes()
            process = self.run_cli(
                "benchmarks.comparison_cases:double_original",
                "benchmarks.comparison_cases:double_equivalent",
                "--replay",
                str(source),
                "--output",
                str(source),
            )
            self.assertEqual(source.read_bytes(), contents)
        self.assertEqual(process.returncode, 2)
        self.assertIn("must not overwrite", process.stderr)

    def test_replay_validation_precedes_function_imports(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.json"
            self.make_replay_report(source)
            process = self.run_cli(
                "missing_module:original",
                "missing_module:migrated",
                "--replay",
                str(source),
                "--case",
                "missing",
            )
        self.assertEqual(process.returncode, 2)
        self.assertIn("Unknown case names", process.stderr)
        self.assertNotIn("Traceback", process.stderr)

    def test_replay_option_conflicts(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.json"
            self.make_replay_report(source)
            for options in (
                ["--select", "match"],
                ["--case", "same"],
                ["--replay", str(source), "--max-cases", "3"],
                ["--replay", str(source), "--select", "match", "--case", "same"],
            ):
                with self.subTest(options=options):
                    process = self.run_cli(
                        "missing:original", "missing:migrated", *options
                    )
                    self.assertEqual(process.returncode, 2)
                    self.assertNotIn("Traceback", process.stderr)

    def test_invalid_or_missing_replay_file_has_clear_error(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.json"
            for contents in (None, "not json", '{"schema_version": 1, "cases": []}'):
                if contents is not None:
                    source.write_text(contents, encoding="utf-8")
                with self.subTest(contents=contents):
                    process = self.run_cli(
                        "missing:original", "missing:migrated", "--replay", str(source)
                    )
                    self.assertEqual(process.returncode, 2)
                    self.assertIn("Cannot replay report", process.stderr)
                    self.assertNotIn("Traceback", process.stderr)

    def test_all_replay_calls_are_validated_before_any_target_executes(self):
        calls = []

        def target(value):
            calls.append(value)
            return value

        results = {
            "valid": ComparisonResults(
                ExecutionResult((1,), arguments_after=(1,)),
                ExecutionResult((1,), arguments_after=(1,)),
                False,
                None,
                None,
            ),
            "invalid": ComparisonResults(
                ExecutionResult((1, 2), arguments_after=(1, 2)),
                ExecutionResult((1, 2), arguments_after=(1, 2)),
                False,
                None,
                None,
            ),
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            write_json_report(results, path)
            with (
                patch("refcheck.cli.load_function_from_file", return_value=target),
                redirect_stderr(StringIO()) as error,
                self.assertRaises(SystemExit) as raised,
            ):
                main(["example:original", "example:migrated", "--replay", str(path)])
        self.assertEqual(raised.exception.code, 2)
        self.assertEqual(calls, [])
        self.assertIn("Replay case 'invalid' is incompatible", error.getvalue())
