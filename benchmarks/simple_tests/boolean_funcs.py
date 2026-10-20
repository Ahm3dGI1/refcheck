def exclusive_or(left: bool, right: bool) -> bool:
    return left != right


def choose_number(enabled: bool, value: int) -> int:
    return value if enabled else 0


def greet(name: str, excited: bool = False) -> str:
    """The generator supplies both parameters, including the defaulted one."""
    punctuation = "!" if excited else "."
    return f"Hello, {name}{punctuation}"
