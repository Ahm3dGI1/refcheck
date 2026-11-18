"""Replay plain JSON inputs without decoding Python-object descriptions."""

import json
import math
from collections.abc import Sequence
from pathlib import Path
from typing import Any

REPORT_SCHEMA_VERSION = 2
CASE_STATUSES = ("match", "different", "incomplete")


class ReplayError(ValueError):
    """Invalid report contents or case selection."""


def replay_issue(
    value: Any, seen: set[int] | None = None, path: str = "arguments"
) -> str | None:
    """Explain why an input cannot round-trip through plain JSON exactly."""
    if type(value) in (type(None), bool, int, str):
        return None
    if type(value) is float:
        return (
            None
            if math.isfinite(value)
            else f"{path}: non-finite floats are not replayable"
        )
    if type(value) not in (list, dict):
        return f"{path}: unsupported input type {type(value).__module__}.{type(value).__qualname__}"
    if seen is None:
        seen = set()
    if id(value) in seen:
        return f"{path}: circular or shared container references are not replayable"
    seen.add(id(value))
    if type(value) is dict:
        if any(type(key) is not str for key in value):
            return f"{path}: dictionary keys must be strings"
        items = value.items()
    else:
        items = enumerate(value)
    for key, item in items:
        issue = replay_issue(item, seen, f"{path}[{key!r}]")
        if issue is not None:
            return issue
    return None


def _reject_constant(value: str) -> None:
    raise ReplayError(f"Non-standard JSON constant: {value}")


def _unique_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ReplayError(f"Duplicate JSON key: {key!r}")
        result[key] = value
    return result


def load_replay_cases(
    path: str | Path,
    *,
    status: str | None = None,
    case_names: Sequence[str] | None = None,
) -> dict[str, list[Any]]:
    """Validate all selected cases before returning their starting arguments."""
    if status not in (None, "all", *CASE_STATUSES):
        raise ReplayError(f"Unknown case status: {status!r}")
    if status is not None and case_names is not None:
        raise ReplayError("Select either a saved status or case names, not both")
    report = json.loads(
        Path(path).read_text(encoding="utf-8"),
        parse_constant=_reject_constant,
        object_pairs_hook=_unique_keys,
    )
    if (
        not isinstance(report, dict)
        or type(report.get("schema_version")) is not int
        or report["schema_version"] != REPORT_SCHEMA_VERSION
    ):
        raise ReplayError(
            f"Replay requires a schema version {REPORT_SCHEMA_VERSION} report; older reports lack replay metadata"
        )
    if not isinstance(report.get("cases"), list):
        raise ReplayError("Report must contain a cases array")
    indexed = {}
    for case in report["cases"]:
        if not isinstance(case, dict) or not isinstance(case.get("name"), str):
            raise ReplayError("Each case must have a string name")
        name = case["name"]
        if name in indexed:
            raise ReplayError(f"Duplicate case name: {name!r}")
        if case.get("status") not in CASE_STATUSES:
            raise ReplayError(f"Case {name!r} has an invalid saved status")
        indexed[name] = case

    if case_names is not None:
        if not case_names or len(set(case_names)) != len(case_names):
            raise ReplayError("Case selection must contain distinct case names")
        missing = [name for name in case_names if name not in indexed]
        if missing:
            raise ReplayError(f"Unknown case names: {', '.join(missing)}")
        selected = [indexed[name] for name in case_names]
    else:
        selected = [
            case
            for case in indexed.values()
            if status in (None, "all") or case["status"] == status
        ]
        if not selected and status in CASE_STATUSES:
            raise ReplayError(f"No cases have saved status {status!r}")

    inputs = {}
    for case in selected:
        name = case["name"]
        metadata = case.get("replay")
        if not isinstance(metadata, dict) or metadata.get("supported") is not True:
            reason = (
                metadata.get("reason", "missing replay metadata")
                if isinstance(metadata, dict)
                else "missing replay metadata"
            )
            raise ReplayError(f"Case {name!r} is not replayable: {reason}")
        original = case.get("original")
        arguments = (
            original.get("arguments_before") if isinstance(original, dict) else None
        )
        if not isinstance(arguments, list):
            raise ReplayError(f"Case {name!r} must contain an arguments_before array")
        issue = replay_issue(arguments)
        if issue is not None:
            raise ReplayError(f"Case {name!r} is not replayable: {issue}")
        inputs[name] = arguments
    return inputs
