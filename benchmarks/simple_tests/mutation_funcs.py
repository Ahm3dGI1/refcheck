STATE = {"calls": 0}


def count_call(value: int) -> int:
    """Mutate module state while returning the input unchanged."""
    STATE["calls"] += 1
    return value


def keep_value(value: int) -> int:
    """Return the same result as count_call without changing state."""
    return value


def sort_in_place(values: list[int]) -> list[int]:
    """Requires explicit inputs: list annotations are not generated yet."""
    values.sort()
    return values


def sort_copy(values: list[int]) -> list[int]:
    """Return equal sorted values without mutating the supplied list."""
    return sorted(values)
