"""Convert comparison results into readable, strict JSON reports."""

import json
import math
from pathlib import Path
from typing import Any

from refcheck.models import ComparisonResults, ExecutionResult


def _type_name(value: Any) -> str:
    return f"{type(value).__module__}.{type(value).__qualname__}"


def _unsupported(value: Any, *, circular: bool = False) -> dict[str, Any]:
    if circular:
        representation = "<circular reference>"
    else:
        try:
            representation = repr(value)
        except Exception:  # noqa: BLE001 -- A target object's broken repr must not prevent reporting.
            representation = "<representation unavailable>"
    return {
        "$type": "unsupported",
        "python_type": _type_name(value),
        "repr": representation,
    }


def _json_value(value: Any, active: set[int] | None = None) -> Any:
    """Encode values without silently dropping types or dictionary keys."""
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        label = "nan" if math.isnan(value) else "infinity" if value > 0 else "-infinity"
        return {"$type": "float", "value": label}
    if not isinstance(value, (list, tuple, dict)):
        return _unsupported(value)

    if active is None:
        active = set()
    identity = id(value)
    if identity in active:
        return _unsupported(value, circular=True)
    active.add(identity)
    try:
        if isinstance(value, list):
            return [_json_value(item, active) for item in value]
        if isinstance(value, tuple):
            return {
                "$type": "tuple",
                "items": [_json_value(item, active) for item in value],
            }
        if all(isinstance(key, str) for key in value):
            return {key: _json_value(item, active) for key, item in value.items()}
        return {
            "$type": "dict",
            "items": [
                [_json_value(key, active), _json_value(item, active)]
                for key, item in value.items()
            ],
        }
    finally:
        active.remove(identity)


def _execution_report(result: ExecutionResult) -> dict[str, Any]:
    report = {
        "arguments_before": _json_value(list(result.arguments)),
        "arguments_after": (
            None
            if result.arguments_after is None
            else _json_value(list(result.arguments_after))
        ),
    }
    if result.exception_type is not None:
        report.update(
            outcome="exception",
            exception={
                "type": f"{result.exception_type.__module__}.{result.exception_type.__qualname__}",
                "message": result.exception_message,
            },
        )
    else:
        report.update(outcome="return", value=_json_value(result.value))
    return report


def build_report(
    results: dict[str, ComparisonResults],
    *,
    original_reference: str | None = None,
    migrated_reference: str | None = None,
) -> dict[str, Any]:
    """Build report data without writing files or changing execution results."""
    cases = []
    different_cases = 0
    incomplete_cases = 0
    for name, result in results.items():
        different = result.return_diff or bool(result.mutation_diff)
        incomplete = result.mutation_diff is None
        different_cases += different
        incomplete_cases += incomplete
        status = "different" if different else "incomplete" if incomplete else "match"
        cases.append(
            {
                "name": name,
                "status": status,
                "original": _execution_report(result.execution_Result_original),
                "migrated": _execution_report(result.execution_Result_migrated),
                "return_diff": result.return_diff,
                "mutation_diff": (
                    None
                    if result.mutation_diff is None
                    else {
                        str(index): _json_value(values)
                        for index, values in result.mutation_diff.items()
                    }
                ),
                "performance": {
                    "original_seconds": _json_value(result.performance_original),
                    "migrated_seconds": _json_value(result.performance_migrated),
                },
            }
        )
    return {
        "schema_version": 1,
        "functions": {"original": original_reference, "migrated": migrated_reference},
        "summary": {
            "total_cases": len(cases),
            "different_cases": different_cases,
            "incomplete_cases": incomplete_cases,
        },
        "cases": cases,
    }


def write_json_report(
    results: dict[str, ComparisonResults],
    path: str | Path,
    *,
    original_reference: str | None = None,
    migrated_reference: str | None = None,
) -> Path:
    """Write an indented report, replacing an existing file at path."""
    report = build_report(
        results,
        original_reference=original_reference,
        migrated_reference=migrated_reference,
    )
    # Serialize before opening the file, so serialization errors cannot truncate it.
    contents = json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False)
    destination = Path(path)
    destination.write_text(contents + "\n", encoding="utf-8")
    return destination
