from collections.abc import Callable
from typing import Any

from refcheck.execution.runner import run_generated_inputs
from refcheck.checkers.performance import get_performance
from refcheck.models import ComparisonResults


def compare(original_func: Callable, migrated_func: Callable) -> dict[str, ComparisonResults]:
    """
    Initial implementation: compare to basic functions given an input
    """

    original_results, migrated_results = run_generated_inputs(original_func, migrated_func)

    comparison_results = {}

    for case_name in original_results.keys() | migrated_results.keys():
        original_result = original_results.get(case_name)
        migrated_result = migrated_results.get(case_name)

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

    original_results, migrated_results = run_generated_inputs(original_func, migrated_func)
    
    comparison_results = {}

    for case_name in original_results.keys() | migrated_results.keys():
        original_result = original_results.get(case_name)
        migrated_result = migrated_results.get(case_name)

        comparison_results[case_name] = ComparisonResults(
            return_diff=original_result != migrated_result,
            performance_original=get_performance(original_func, (case_name,))[case_name],
            performance_migrated=get_performance(migrated_func, (case_name,))[case_name],
            mutation_diff=False
        )

    return comparison_results

