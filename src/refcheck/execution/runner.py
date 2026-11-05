import inspect
from collections.abc import Callable
from copy import deepcopy
from typing import Any

from hypothesis import given, settings

from refcheck.generators.input_generation import generate_inputs_strategies
from refcheck.models import ExecutionResult


def _execute(func: Callable, args: tuple[Any, ...]) -> ExecutionResult:
    # Setup failures must not be mistaken for target-function failures.
    call_args = deepcopy(args)
    starting_args = deepcopy(call_args)
    try:
        value = func(*call_args)
    except Exception as error:  # noqa: BLE001 -- Capture arbitrary target-function failures as observations.
        return ExecutionResult(
            starting_args,
            arguments_after=deepcopy(call_args),
            exception_type=type(error),
            exception_message=str(error),
        )
    return ExecutionResult(
        starting_args, arguments_after=deepcopy(call_args), value=deepcopy(value)
    )


def run_generated_inputs(
    original_func: Callable,
    migrated_func: Callable,
    max_examples: int = 10,
    *,
    input_data: dict[str, list[Any]] | None = None,
) -> dict[str, tuple[ExecutionResult, ExecutionResult]]:
    """Run both targets with independent copies of each input case."""
    results = {}
    original_signature = inspect.signature(original_func)
    migrated_signature = inspect.signature(migrated_func)

    def run_pair(case_name, args):
        # TODO: Define whether incompatible inputs are rejected or reported as a diff.
        # Support explicit migration adapters for changed input shapes/units, mapping
        # one logical case to each interface instead of generating unrelated inputs.
        # Reject incompatible calls before treating errors as target behavior.
        original_signature.bind(*args)
        migrated_signature.bind(*args)
        results[case_name] = (
            _execute(original_func, args),
            _execute(migrated_func, args),
        )

    if input_data is not None:
        for case_name, inputs in input_data.items():
            run_pair(case_name, tuple(inputs))
    else:
        strategy = generate_inputs_strategies(original_func)

        @settings(max_examples=max_examples, deadline=None, database=None)
        @given(args=strategy)
        def run_case(args):
            run_pair(f"case_{len(results) + 1}", args)

        run_case()

    return results
