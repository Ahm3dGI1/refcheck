from collections.abc import Callable
from typing import Any

from refcheck.checkers.performance import get_performance
from refcheck.models import ComparisonResults


def compare(original_func: Callable, migrated_func: Callable, input_data: dict[str, list[Any]], **kwargs) -> dict[str, ComparisonResults]:
    """
    Initial implementation: compare to basic functions given an input
    """

    comparison_results = {}

    for case_name, inputs in input_data.items():
        original_result = original_func(*inputs)
        migrated_result = migrated_func(*inputs)

        comparison_results[case_name] = ComparisonResults(
            return_diff=original_result != migrated_result,
            performance_original=None,
            performance_migrated=None,
            mutation_diff=False
        )

    return comparison_results

def compare_with_performance(original_func: Callable, migrated_func: Callable, input_data: dict[str, list[Any]], **kwargs) -> dict[str, ComparisonResults]:
    """
    Compare two functions based on their return values and performance.
    """

    comparison_results = {}

    for case_name, inputs in input_data.items():
        original_result = original_func(*inputs)
        migrated_result = migrated_func(*inputs)

        comparison_results[case_name] = ComparisonResults(
            return_diff=original_result != migrated_result,
            performance_original=get_performance(original_func, (case_name, inputs))[case_name],
            performance_migrated=get_performance(migrated_func, (case_name, inputs))[case_name],
            mutation_diff=False
        )

    return comparison_results

