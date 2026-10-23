"""Pairs with explicit edge cases: run with python -m benchmarks.comparison_cases."""

from refcheck.checkers.compare import compare


def double_original(value: int) -> int:
    return value * 2


def double_equivalent(value: int) -> int:
    return value + value


def double_changed(value: int) -> int:
    return value * 2 + 1


def boundary_original(value: int) -> bool:
    return value >= 0


def boundary_changed(value: int) -> bool:
    """Intentional regression at zero only."""
    return value > 0


def divide_original(value: float, divisor: float) -> float:
    return value / divisor


def divide_changed(value: float, divisor: float) -> float:
    """Intentional change: zero division returns zero instead of raising."""
    return 0.0 if divisor == 0 else value / divisor


def reject_original(value: int) -> int:
    raise ValueError("invalid value")


def reject_equivalent(value: int) -> int:
    raise ValueError("invalid value")


def reject_changed(value: int) -> int:
    raise TypeError("invalid value")


def return_error_text(value: int) -> str:
    """A normal return that must not compare equal to a raised exception."""
    return "raised ValueError: invalid value"


def nan_original(value: float) -> float:
    return float("nan")


def nan_equivalent(value: float) -> float:
    return float("nan")


def record_original(value: int) -> dict[str, int]:
    return {"value": value}


def record_changed(value: int) -> dict[str, int]:
    return {"value": value + 1}


CASES = [
    (
        "equivalent",
        double_original,
        double_equivalent,
        {"negative": [-3], "zero": [0], "positive": [3]},
    ),
    ("changed return", double_original, double_changed, {"zero": [0]}),
    (
        "boundary regression",
        boundary_original,
        boundary_changed,
        {"negative": [-1], "boundary": [0], "positive": [1]},
    ),
    (
        "return versus exception",
        divide_original,
        divide_changed,
        {"normal": [4.0, 2.0], "zero divisor": [4.0, 0.0]},
    ),
    ("same exception", reject_original, reject_equivalent, {"invalid": [1]}),
    ("different exception type", reject_original, reject_changed, {"invalid": [1]}),
    ("exception versus text", reject_original, return_error_text, {"invalid": [1]}),
    ("NaN equivalence", nan_original, nan_equivalent, {"nan": [0.0]}),
    ("structured return", record_original, record_changed, {"zero": [0]}),
]


if __name__ == "__main__":
    for label, original, migrated, inputs in CASES:
        print(f"\n{label}:")
        for case_name, result in compare(original, migrated, inputs).items():
            status = "DIFFERENT" if result.return_diff else "MATCH"
            print(f"  {case_name}: {status}")
