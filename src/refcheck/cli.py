from typing import Callable, Dict, Any

def compare(original_func: Callable, migrated_func: Callable, input_data: Dict[str, list[Any]]) -> Dict[str, Any]:
    """
    Initial implementation: compare to basic functions given an input
    """

    comparison_results = {}

    for case_name, inputs in input_data.items():
        original_result = original_func(*inputs)
        migrated_result = migrated_func(*inputs)

        comparison_results[case_name] = {
            "original": original_result,
            "migrated": migrated_result,
            "match": original_result == migrated_result
        }

    return comparison_results