from dataclasses import dataclass
from typing import Any

from refcheck.value_comparison import values_differ


@dataclass
class ExecutionResult:
    """One call's starting arguments and return value or exception."""

    arguments: tuple[Any, ...]
    arguments_after: tuple[Any, ...] | None = None
    value: Any = None
    exception_type: type[Exception] | None = None
    exception_message: str | None = None


class ComparisonResults:
    def __init__(
        self,
        execution_Result_original: ExecutionResult,
        execution_Result_migrated: ExecutionResult,
        return_diff: bool,
        performance_original: float | None,
        performance_migrated: float | None,
        mutation_diff: dict[int, dict[str, Any]] | None = None,
    ) -> None:
        self.return_diff = return_diff
        self.performance_original = performance_original
        self.performance_migrated = performance_migrated
        self.mutation_diff = (
            mutation_diff
            if mutation_diff is not None
            else self._get_mutation_diff(
                execution_Result_original, execution_Result_migrated
            )
        )
        self.execution_Result_original = execution_Result_original
        self.execution_Result_migrated = execution_Result_migrated

    def __str__(self) -> str:
        return f"ComparisonResults(return_diff={self.return_diff}, performance_original={self.performance_original}, performance_migrated={self.performance_migrated}, mutation_diff={self.mutation_diff})"

    def _get_mutation_diff(
        self,
        execution_Result_original: ExecutionResult,
        execution_Result_migrated: ExecutionResult,
    ) -> dict[int, dict[str, Any]] | None:
        if (
            execution_Result_original.arguments_after is None
            or execution_Result_migrated.arguments_after is None
        ):
            return None

        diff = {}

        for index, (original_value, migrated_value) in enumerate(
            zip(
                execution_Result_original.arguments_after,
                execution_Result_migrated.arguments_after,
                strict=True,
            )
        ):
            if values_differ(original_value, migrated_value):
                diff[index] = {
                    "original_value": original_value,
                    "migrated_value": migrated_value,
                }

        return diff
