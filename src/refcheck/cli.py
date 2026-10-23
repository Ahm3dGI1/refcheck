from refcheck.checkers.compare import compare
from refcheck.loader.loader import load_function_from_file

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
    for case_name, result in results.items():
        status = "DIFFERENT" if result.return_diff else "MATCH"
        print(f"{case_name}: {status}")
    differences = sum(result.return_diff for result in results.values())
    print(f"Compared {len(results)} cases; {differences} different.")
