import inspect
from typing import get_type_hints

from hypothesis import strategies as st


def generate_inputs_strategies(func):
    """Build positional input tuples for an annotated function."""
    signature = inspect.signature(func)
    hints = get_type_hints(func)

    supported_types = {
        int: st.integers(),
        float: st.floats(),
        str: st.text(),
        bool: st.booleans(),
    }

    strategies = []

    for name, parameter in signature.parameters.items():
        if parameter.kind not in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            raise ValueError(
                f"{name}: only fixed positional parameters are supported"
            )

        if name not in hints:
            raise ValueError(f"{name}: missing type annotation")

        annotation = hints[name]

        if annotation not in supported_types:
            raise ValueError(
                f"{name}: unsupported type {annotation!r}"
            )

        strategies.append(supported_types[annotation])

    return st.tuples(*strategies)