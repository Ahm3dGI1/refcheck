import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from refcheck.checkers.compare import compare
from refcheck.models import ComparisonResults, ExecutionResult
from refcheck.replay import load_replay_cases
from refcheck.reporting import build_report, write_json_report


def case_result(arguments, *, different=False, incomplete=False):
    return ComparisonResults(
        ExecutionResult(
            arguments=tuple(arguments),
            arguments_after=None if incomplete else tuple(arguments),
        ),
        ExecutionResult(
            arguments=tuple(arguments),
            arguments_after=None if incomplete else tuple(arguments),
        ),
        different,
        None,
        None,
        mutation_diff=None if incomplete else {},
    )


class ReplayTests(unittest.TestCase):
    def load(self, report, **selection):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            path.write_text(json.dumps(report, allow_nan=False), encoding="utf-8")
            return load_replay_cases(path, **selection)

    def report(self):
        return build_report(
            {
                "same": case_result([1]),
                "changed": case_result([2], different=True),
                "unknown": case_result([3], incomplete=True),
            }
        )

    def test_plain_inputs_round_trip(self):
        arguments = [
            None,
            True,
            42,
            -1.5,
            "你好",
            [1, {"nested": []}],
            {"$type": "tuple", "items": [2]},
        ]
        report = build_report({"plain": case_result(arguments)})

        self.assertEqual(report["cases"][0]["replay"], {"supported": True})
        self.assertEqual(self.load(report), {"plain": arguments})

    def test_select_each_saved_status(self):
        for status, name in (
            ("match", "same"),
            ("different", "changed"),
            ("incomplete", "unknown"),
        ):
            with self.subTest(status=status):
                self.assertEqual(list(self.load(self.report(), status=status)), [name])
        self.assertEqual(
            list(self.load(self.report(), status="all")), ["same", "changed", "unknown"]
        )

    def test_select_named_cases_in_requested_order(self):
        self.assertEqual(
            list(self.load(self.report(), case_names=["changed", "same"])),
            ["changed", "same"],
        )

    def test_unknown_and_duplicate_case_names_are_errors(self):
        for names in (["missing"], ["same", "same"], []):
            with self.subTest(names=names), self.assertRaises(ValueError):
                self.load(self.report(), case_names=names)

    def test_duplicate_report_case_names_are_rejected(self):
        report = self.report()
        report["cases"].append(report["cases"][0])
        with self.assertRaisesRegex(ValueError, "Duplicate case name"):
            self.load(report)

    def test_status_and_name_selection_cannot_be_combined(self):
        with self.assertRaises(ValueError):
            self.load(self.report(), status="different", case_names=["changed"])

    def test_empty_report_does_not_trigger_generation(self):
        inputs = self.load(build_report({}))
        with patch(
            "refcheck.execution.runner.generate_inputs_strategies",
            side_effect=AssertionError("Generation must not run"),
        ):
            self.assertEqual(compare(lambda: None, lambda: None, input_data=inputs), {})

    def test_no_status_matches_is_an_error(self):
        report = build_report({"same": case_result([1])})
        with self.assertRaisesRegex(ValueError, "No cases"):
            self.load(report, status="different")

    def test_unsupported_inputs_are_marked_and_rejected(self):
        shared = []
        circular = []
        circular.append(circular)

        class IntSubclass(int):
            pass

        for value in (
            (1, 2),
            {1, 2},
            {1: "integer key"},
            float("nan"),
            float("inf"),
            lambda: None,
            circular,
            [shared, shared],
            IntSubclass(1),
        ):
            with self.subTest(type=type(value).__name__):
                report = build_report({"unsupported": case_result([value])})
                self.assertFalse(report["cases"][0]["replay"]["supported"])
                self.assertIn("reason", report["cases"][0]["replay"])
                with self.assertRaisesRegex(ValueError, "not replayable"):
                    self.load(report)

    def test_unsupported_unselected_case_does_not_block_selected_case(self):
        report = build_report(
            {"plain": case_result([1]), "other": case_result([(1, 2)])}
        )
        self.assertEqual(self.load(report, case_names=["plain"]), {"plain": [1]})
        with self.assertRaisesRegex(ValueError, "not replayable"):
            self.load(report)

    def test_unsupported_return_does_not_block_input_replay(self):
        result = case_result([1])
        result.execution_Result_original.value = {1, 2}
        self.assertEqual(self.load(build_report({"case": result})), {"case": [1]})

    def test_replay_uses_starting_arguments_and_reproduces_mutation_difference(self):
        def in_place(values):
            values.sort()
            return values

        def copied(values):
            return sorted(values)

        original = compare(in_place, copied, {"sort": [[3, 1, 2]]})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            write_json_report(original, path)
            source = path.read_bytes()
            inputs = load_replay_cases(path)
            with patch(
                "refcheck.execution.runner.generate_inputs_strategies",
                side_effect=AssertionError("Generation must not run"),
            ):
                replayed = compare(in_place, copied, input_data=inputs)
            self.assertEqual(path.read_bytes(), source)

        self.assertEqual(inputs, {"sort": [[3, 1, 2]]})
        self.assertEqual(replayed["sort"].mutation_diff, original["sort"].mutation_diff)

    def test_malformed_reports_are_rejected(self):
        for report in (
            [],
            {},
            {"schema_version": 1, "cases": []},
            {"schema_version": True, "cases": []},
            {"schema_version": 2, "cases": {}},
            {"schema_version": 2, "cases": [{}]},
        ):
            with self.subTest(report=report), self.assertRaises(ValueError):
                self.load(report)

    def test_bad_case_payloads_are_rejected(self):
        for modification in (
            {"status": "bad"},
            {"replay": None},
            {"replay": {"supported": 1}},
            {"original": {}},
            {"original": {"arguments_before": None}},
        ):
            report = self.report()
            report["cases"][0].update(modification)
            with self.subTest(modification=modification), self.assertRaises(ValueError):
                self.load(report)

    def test_duplicate_json_keys_and_nonstandard_numbers_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            for contents in (
                '{"schema_version": 2, "schema_version": 1}',
                '{"schema_version": 2, "value": NaN}',
                "invalid json",
            ):
                path.write_text(contents, encoding="utf-8")
                with self.subTest(contents=contents), self.assertRaises(ValueError):
                    load_replay_cases(path)

    def test_nonfinite_numbers_are_rejected_even_with_supported_flag(self):
        report = self.report()
        report["cases"][0]["original"]["arguments_before"] = [float("inf")]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            # JSON's 1e999 is parsed as infinity by Python but is not replayable.
            path.write_text(
                json.dumps(report).replace("Infinity", "1e999"), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "non-finite"):
                load_replay_cases(path)
