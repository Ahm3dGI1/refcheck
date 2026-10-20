from refcheck.execution.runner import run_generated_inputs
from refcheck.loader.loader import load_function_from_file

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python cli.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    func = load_function_from_file(file_path)

    run_generated_inputs(func, max_examples=10)
