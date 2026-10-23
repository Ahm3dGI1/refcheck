import math
from collections.abc import Callable
from typing import Any

from refcheck.checkers.performance import get_performance
from refcheck.execution.runner import run_generated_inputs
from refcheck.models import ComparisonResults, ExecutionResult


def _outcomes_differ(original: ExecutionResult, migrated: ExecutionResult) -> bool:
    if original.exception_type is not None or migrated.exception_type is not None:
        return (
            original.exception_type is not migrated.exception_type
            or original.exception_message != migrated.exception_message
        )
    # Two scalar NaNs count as equivalent despite Python's NaN != NaN.
    if (
        isinstance(original.value, float)
        and isinstance(migrated.value, float)
        and math.isnan(original.value)
        and math.isnan(migrated.value)
    ):
        return False
    return original.value != migrated.value


def compare(
    original_func: Callable,
    migrated_func: Callable,
    input_data: dict[str, list[Any]] | None = None,
    *,
    max_examples: int = 10,
) -> dict[str, ComparisonResults]:
    """Compare returns and exceptions using explicit or generated inputs."""
    original_results, migrated_results = run_generated_inputs(
        original_func, migrated_func, max_examples, input_data=input_data
    )
    return {
        case_name: ComparisonResults(
            return_diff=_outcomes_differ(original, migrated_results[case_name]),
            performance_original=None,
            performance_migrated=None,
            mutation_diff=False,
        )
        for case_name, original in original_results.items()
    }


def compare_with_performance(
    original_func: Callable,
    migrated_func: Callable,
    input_data: dict[str, list[Any]] | None = None,
    *,
    max_examples: int = 10,
    num_executions: int = 1000,
) -> dict[str, ComparisonResults]:
    """Compare outcomes and average timings; exception cases are not timed."""
    if num_executions < 1:
        raise ValueError("num_executions must be positive")
    original_results, migrated_results = run_generated_inputs(
        original_func, migrated_func, max_examples, input_data=input_data
    )
    comparison_results = {}
    for case_name, original in original_results.items():
        migrated = migrated_results[case_name]
        original_time = None
        migrated_time = None
        if original.exception_type is None and migrated.exception_type is None:
            cases = {case_name: list(original.arguments)}
            original_time = get_performance(original_func, cases, num_executions)[
                case_name
            ]
            migrated_time = get_performance(migrated_func, cases, num_executions)[
                case_name
            ]
        comparison_results[case_name] = ComparisonResults(
            return_diff=_outcomes_differ(original, migrated),
            performance_original=original_time,
            performance_migrated=migrated_time,
            mutation_diff=False,
        )
    return comparison_results
