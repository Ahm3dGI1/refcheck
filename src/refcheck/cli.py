import argparse
import inspect
import sys
from collections.abc import Sequence
from pathlib import Path

from refcheck.checkers.compare import compare
from refcheck.loader.loader import load_function_from_file
from refcheck.models import ComparisonResults
from refcheck.replay import load_replay_cases
from refcheck.reporting import write_json_report


def print_results(results: dict[str, ComparisonResults]) -> None:
    differences = 0
    incomplete = 0
    for case_name, result in results.items():
        different = result.return_diff or bool(result.mutation_diff)
        if different:
            status = "DIFFERENT"
            differences += 1
        elif result.mutation_diff is None:
            status = "INCOMPLETE"
        else:
            status = "MATCH"
        if result.mutation_diff is None:
            incomplete += 1
            status += " (mutation comparison unavailable)"
        print(f"{case_name}: {status}")
    print(f"Compared {len(results)} cases; {differences} different.")
    if incomplete:
        print(f"Mutation comparison unavailable for {incomplete} cases.")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare two Python functions.")
    parser.add_argument(
        "original_func_path", help="Original module:function or file.py:function"
    )
    parser.add_argument(
        "modified_func_path", help="Migrated module:function or file.py:function"
    )
    parser.add_argument(
        "--output",
        type=Path,
        metavar="PATH",
        help="Write a JSON report (replaces an existing file)",
    )
    parser.add_argument(
        "--max-cases",
        type=int,
        metavar="INT",
        help="Generation budget (default: 100; cannot be used with --replay)",
    )
    parser.add_argument(
        "--replay",
        type=Path,
        metavar="REPORT",
        help="Replay starting inputs from a version 2 JSON report",
    )
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument(
        "--select",
        choices=("all", "different", "match", "incomplete"),
        help="Select by saved status (requires --replay; default: all)",
    )
    selection.add_argument(
        "--case",
        action="append",
        dest="case_names",
        metavar="NAME",
        help="Replay a named case; repeat for multiple cases (requires --replay)",
    )
    options = parser.parse_args(argv)

    if options.max_cases is not None and options.max_cases < 1:
        parser.error("--max-cases must be positive")
    if options.replay is None and (
        options.select is not None or options.case_names is not None
    ):
        parser.error("--select and --case require --replay")
    if options.replay is not None and options.max_cases is not None:
        parser.error(
            "--max-cases cannot be used with --replay; selected cases run exactly once"
        )
    input_data = None
    replay_source = None
    if options.replay is not None:
        try:
            if options.output is not None and (
                options.replay.resolve() == options.output.resolve()
                or (
                    options.replay.exists()
                    and options.output.exists()
                    and options.replay.samefile(options.output)
                )
            ):
                parser.error("--output must not overwrite the source replay report")
            input_data = load_replay_cases(
                options.replay, status=options.select, case_names=options.case_names
            )
        except (OSError, ValueError, RecursionError) as error:
            parser.error(f"Cannot replay report: {error}")
        replay_source = {
            "report": str(options.replay.resolve()),
            "cases": list(input_data),
        }

    original_func = load_function_from_file(options.original_func_path)
    modified_func = load_function_from_file(options.modified_func_path)

    if input_data is not None:
        for name, arguments in input_data.items():
            try:
                inspect.signature(original_func).bind(*arguments)
                inspect.signature(modified_func).bind(*arguments)
            except TypeError as error:
                parser.error(
                    f"Replay case {name!r} is incompatible with the supplied functions: {error}"
                )

    results = compare(
        original_func,
        modified_func,
        input_data=input_data,
        max_cases=options.max_cases if options.max_cases is not None else 100,
    )
    print_results(results)
    if options.output is not None:
        try:
            destination = write_json_report(
                results,
                options.output,
                original_reference=options.original_func_path,
                migrated_reference=options.modified_func_path,
                replay_source=replay_source,
            )
        except OSError as error:
            print(f"Could not write JSON report: {error}", file=sys.stderr)
            return 1
        print(f"JSON report written to {destination}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
