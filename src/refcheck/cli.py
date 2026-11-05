from refcheck.checkers.compare import compare
from refcheck.loader.loader import load_function_from_file
from refcheck.models import ComparisonResults


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


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python cli.py <original_func_path> <modified_func_path>")
        sys.exit(1)

    original_path = sys.argv[1]
    modified_path = sys.argv[2]
    original_func = load_function_from_file(original_path)
    modified_func = load_function_from_file(modified_path)

    results = compare(original_func, modified_func, max_examples=10)
    print_results(results)
