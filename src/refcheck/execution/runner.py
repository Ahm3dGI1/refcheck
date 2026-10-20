from hypothesis import given, settings

from refcheck.generators.input_generation import (
    generate_inputs_strategies,
)


def run_generated_inputs(func, max_examples=10):
    strategy = generate_inputs_strategies(func)

    @settings(
        max_examples=max_examples,
        deadline=None,
        database=None,
    )
    @given(args=strategy)
    def run_case(args):
        inputs_before = repr(args)

        try:
            result = func(*args)
        except Exception as error:  # noqa: BLE001 -- Report target failures and continue generating cases.
            print(
                f"inputs={inputs_before} -> "
                f"raised {type(error).__name__}: {error}"
            )
        else:
            print(f"inputs={inputs_before} -> return={result!r}")

    run_case()
