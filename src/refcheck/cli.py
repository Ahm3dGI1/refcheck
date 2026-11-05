import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from refcheck.checkers.compare import compare
from refcheck.loader.loader import load_function_from_file
from refcheck.models import ComparisonResults
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
    options = parser.parse_args(argv)
    original_func = load_function_from_file(options.original_func_path)
    modified_func = load_function_from_file(options.modified_func_path)

    results = compare(original_func, modified_func, max_examples=10)
    print_results(results)
    if options.output is not None:
        try:
            destination = write_json_report(
                results,
                options.output,
                original_reference=options.original_func_path,
                migrated_reference=options.modified_func_path,
            )
        except OSError as error:
            print(f"Could not write JSON report: {error}", file=sys.stderr)
            return 1
        print(f"JSON report written to {destination}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
