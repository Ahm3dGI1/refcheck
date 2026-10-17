import tempfile
import unittest
from pathlib import Path

from refcheck.loader.loader import load_function_from_file


class LoaderTests(unittest.TestCase):
    def test_dotted_module(self):
        from refcheck.comparison.compare import compare

        self.assertIs(
            load_function_from_file("refcheck.comparison.compare:compare"), compare
        )

    def test_relative_windows_path_without_extension(self):
        import os

        if os.name != "nt":
            self.skipTest("Windows path syntax")
        function = load_function_from_file(
            r".\src\refcheck\comparison\compare:compare"
        )
        self.assertEqual(function.__name__, "compare")

    def test_absolute_file_with_spaces_and_dataclass(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example module.py"
            path.write_text(
                "from dataclasses import dataclass\n"
                "@dataclass\n"
                "class Example:\n"
                "    value: int = 1\n"
                "def sample():\n"
                "    return Example().value\n",
                encoding="utf-8",
            )
            self.assertEqual(load_function_from_file(f"{path}:sample")(), 1)

    def test_invalid_reference(self):
        for reference in ("", "refcheck", ":compare", "refcheck:"):
            with self.subTest(reference=reference), self.assertRaises(ValueError):
                load_function_from_file(reference)

    def test_non_callable(self):
        with self.assertRaises(TypeError):
            load_function_from_file("sys:version")
