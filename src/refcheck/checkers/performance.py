from collections.abc import Callable
from copy import deepcopy
from time import perf_counter
from typing import Any


def get_performance(
    func: Callable,
    input_data: dict[str, list[Any]],
    num_executions: int = 1000,
) -> dict[str, float]:
    """Average elapsed seconds per call, excluding argument copying."""
    if num_executions < 1:
        raise ValueError("num_executions must be positive")
    time_by_case = {}
    for case_name, inputs in input_data.items():
        elapsed = 0.0
        for _ in range(num_executions):
            call_args = deepcopy(inputs)
            start = perf_counter()
            func(*call_args)
            elapsed += perf_counter() - start
        time_by_case[case_name] = elapsed / num_executions
    return time_by_case
