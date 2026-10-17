from collections.abc import Callable
from typing import Any


def get_performance(func: Callable, input_data: tuple[str, list[Any]], num_executions: int = 1000) -> dict[str, float]:
    """
    Measure the performance of a function by executing it multiple times and calculating the average execution time."""

    import time

    time_by_case = {}

    for case_name, inputs in input_data.items():
        start_time = time.time()

        for _ in range(num_executions):
            func(*inputs)

        end_time = time.time()

        average_time = (end_time - start_time) / num_executions

        time_by_case[case_name] = average_time


    return time_by_case