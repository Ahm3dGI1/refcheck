def reverse_text(text: str) -> str:
    return text[::-1]


def count_occurrences(text: str, fragment: str) -> int:
    """Include Python's defined behavior for an empty fragment."""
    return text.count(fragment)


def normalize_original(text: str) -> str:
    return text.strip().lower()


def normalize_changed(text: str) -> str:
    """Intentional behavior change: surrounding whitespace is retained."""
    return text.lower()
