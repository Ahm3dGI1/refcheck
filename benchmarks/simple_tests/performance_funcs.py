def sum_original(limit: int) -> int:
    """Bound work even when generated integers are very large."""
    count = min(abs(limit), 10_000)
    total = 0
    for value in range(count):
        total += value
    return total


def sum_optimized(limit: int) -> int:
    count = min(abs(limit), 10_000)
    return count * (count - 1) // 2
