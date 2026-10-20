def multiply(a: int, b: int) -> int:
    return a * b


def divide(numerator: float, denominator: float) -> float:
    """Raise ZeroDivisionError when the denominator is zero."""
    return numerator / denominator


def absolute_original(value: int) -> int:
    return abs(value)


def absolute_changed(value: int) -> int:
    """Intentional behavior change: negative inputs remain negative."""
    return value
