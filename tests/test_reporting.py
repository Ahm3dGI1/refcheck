import json
import math
import tempfile
import unittest
from pathlib import Path

from refcheck.checkers.compare import compare
from refcheck.models import ComparisonResults, ExecutionResult
from refcheck.reporting import build_report, write_json_report


def result_with_value(value):
    return ComparisonResults(
        ExecutionResult(arguments=(), arguments_after=(), value=value),
        ExecutionResult(arguments=(), arguments_after=(), value=value),
        False,
        None,
        None,
        mutation_diff={},
    )


class ReportingTests(unittest.TestCase):
    def test_report_contains_mutation_evidence_and_function_references(self):
        def in_place(values):
            values.sort()
            return values

        def copied(values):
            return sorted(values)

        results = compare(in_place, copied, {"sort": [[3, 1, 2]]})
        report = build_report(
            results,
            original_reference="example:in_place",
            migrated_reference="example:copied",
        )
        case = report["cases"][0]

        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["functions"]["original"], "example:in_place")
        self.assertEqual(
            report["summary"],
            {"total_cases": 1, "different_cases": 1, "incomplete_cases": 0},
        )
        self.assertEqual(case["status"], "different")
        self.assertEqual(case["original"]["arguments_before"], [[3, 1, 2]])
        self.assertEqual(case["original"]["arguments_after"], [[1, 2, 3]])
        self.assertEqual(case["migrated"]["arguments_after"], [[3, 1, 2]])
        self.assertEqual(case["original"]["value"], [1, 2, 3])
        self.assertFalse(case["return_diff"])
        self.assertEqual(
            case["mutation_diff"],
            {"0": {"original_value": [1, 2, 3], "migrated_value": [3, 1, 2]}},
        )
        self.assertEqual(
            results["sort"].execution_Result_original.arguments, ([3, 1, 2],)
        )

    def test_exception_is_distinct_from_successful_none_return(self):
        def raises(value):
            raise ValueError("invalid")

        report = build_report(compare(raises, lambda value: None, {"case": [1]}))
        case = report["cases"][0]

        self.assertEqual(case["original"]["outcome"], "exception")
        self.assertEqual(
            case["original"]["exception"],
            {"type": "builtins.ValueError", "message": "invalid"},
        )
        self.assertNotIn("value", case["original"])
        self.assertEqual(case["migrated"]["outcome"], "return")
        self.assertIsNone(case["migrated"]["value"])

    def test_unknown_mutations_remain_null_and_mark_incomplete(self):
        result = ComparisonResults(
            ExecutionResult((1,)), ExecutionResult((1,)), False, None, None
        )
        report = build_report({"case": result})

        self.assertEqual(report["cases"][0]["status"], "incomplete")
        self.assertIsNone(report["cases"][0]["mutation_diff"])
        self.assertIsNone(report["cases"][0]["original"]["arguments_after"])
        self.assertEqual(report["summary"]["incomplete_cases"], 1)

    def test_known_difference_can_also_have_incomplete_mutations(self):
        result = ComparisonResults(
            ExecutionResult((1,)), ExecutionResult((1,)), True, None, None
        )
        report = build_report({"case": result})

        self.assertEqual(report["cases"][0]["status"], "different")
        self.assertEqual(report["summary"]["different_cases"], 1)
        self.assertEqual(report["summary"]["incomplete_cases"], 1)

    def test_nonfinite_floats_are_explicit_and_strict_json(self):
        value = [float("nan"), float("inf"), float("-inf")]
        report = build_report({"case": result_with_value(value)})
        encoded = report["cases"][0]["original"]["value"]

        self.assertEqual(
            encoded,
            [
                {"$type": "float", "value": "nan"},
                {"$type": "float", "value": "infinity"},
                {"$type": "float", "value": "-infinity"},
            ],
        )
        json.dumps(report, allow_nan=False)
        self.assertTrue(math.isnan(value[0]))

    def test_non_string_dictionary_keys_are_not_collapsed(self):
        report = build_report(
            {"case": result_with_value({1: "integer", "1": "string"})}
        )

        self.assertEqual(
            report["cases"][0]["original"]["value"],
            {"$type": "dict", "items": [[1, "integer"], ["1", "string"]]},
        )

    def test_tuples_keep_a_type_marker(self):
        report = build_report({"case": result_with_value((1, "hello"))})

        self.assertEqual(
            report["cases"][0]["original"]["value"],
            {"$type": "tuple", "items": [1, "hello"]},
        )

    def test_unsupported_object_is_marked(self):
        report = build_report({"case": result_with_value({1, 2})})
        value = report["cases"][0]["original"]["value"]

        self.assertEqual(value["$type"], "unsupported")
        self.assertEqual(value["python_type"], "builtins.set")
        self.assertIn("repr", value)

    def test_broken_repr_does_not_stop_report_generation(self):
        class BrokenRepr:
            def __repr__(self):
                raise ValueError("broken")

        report = build_report({"case": result_with_value(BrokenRepr())})

        self.assertEqual(
            report["cases"][0]["original"]["value"]["repr"],
            "<representation unavailable>",
        )

    def test_circular_container_is_marked(self):
        value = []
        value.append(value)
        report = build_report({"case": result_with_value(value)})
        encoded = report["cases"][0]["original"]["value"]

        self.assertEqual(encoded[0]["repr"], "<circular reference>")
        json.dumps(report, allow_nan=False)

    def test_performance_is_reported_in_seconds(self):
        result = result_with_value(1)
        result.performance_original = 0.01
        result.performance_migrated = 0.02
        report = build_report({"case": result})

        self.assertEqual(
            report["cases"][0]["performance"],
            {"original_seconds": 0.01, "migrated_seconds": 0.02},
        )

    def test_empty_report(self):
        report = build_report({})

        self.assertEqual(report["cases"], [])
        self.assertEqual(
            report["summary"],
            {"total_cases": 0, "different_cases": 0, "incomplete_cases": 0},
        )

    def test_write_report_replaces_file_with_valid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            path.write_text("old contents", encoding="utf-8")
            returned_path = write_json_report(
                {"unicode": result_with_value("你好\ud800")}, path
            )
            report = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(returned_path, path)
        self.assertEqual(report["cases"][0]["original"]["value"], "你好\ud800")

    def test_missing_parent_raises_file_error(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            self.assertRaises(FileNotFoundError),
        ):
            write_json_report({}, Path(directory) / "missing" / "report.json")
