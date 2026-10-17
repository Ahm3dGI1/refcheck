from refcheck.loader.loader import get_function_signature, load_function_from_file

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python cli.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    func = load_function_from_file(file_path)
    signature = get_function_signature(func)

    print(f"Function: {func.__name__}")
    print("Signature:")
    for param, details in signature.items():
        print(f"  {param}: {details}")