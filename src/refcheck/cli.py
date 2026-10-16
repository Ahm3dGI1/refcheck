from types.comparison_results import ComparisonResults
from typing import Any, Callable

def compare(original_func: Callable, migrated_func: Callable, input_data: dict[str, list[Any]]) -> ComparisonResults:
    """
    Initial implementation: compare to basic functions given an input
    """

    comparison_results = {}

    for case_name, inputs in input_data.items():
        original_result = original_func(*inputs)
        migrated_result = migrated_func(*inputs)
        
        comparison_results[case_name] = ComparisonResults(
            return_diff=original_result != migrated_result,
            performance_diff=False,
            mutation_diff=False
        )
        

    return comparison_results