from hypothesis import given, settings

from refcheck.generators.input_generation import (
    generate_inputs_strategies,
)



def run_generated_inputs(original_func, migrated_func, max_examples=10):
    strategy = generate_inputs_strategies(original_func)

    @settings(
        max_examples=max_examples,
        deadline=None,
        database=None,
    )
    @given(args=strategy)
    def run_case(args):
        inputs_before = repr(args)

        original_results = {}
        migrated_results = {}

        try:
            original_result = original_func(*args)
        except Exception as error:  # noqa: BLE001 -- Report target failures and continue generating cases.
            original_results[inputs_before] = f"raised {type(error).__name__}: {error}"
        else:
            original_results[inputs_before] = original_result


        try:
            migrated_result = migrated_func(*args)
        except Exception as error:  # noqa: BLE001 -- Report target failures and continue generating cases.
            migrated_results[inputs_before] = f"raised {type(error).__name__}: {error}"
        else:
            migrated_results[inputs_before] = migrated_result

        return original_results, migrated_results

    return run_case()
