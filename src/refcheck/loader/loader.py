import importlib
import importlib.util
import inspect
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any
from uuid import uuid4


def load_function_from_file(file_path: str) -> Callable:
    """
    Load a callable from 'module.submodule:name' or 'path/to/file.py:name'.
    File paths may omit the .py extension.
    """

    module_name, separator, function_name = file_path.rpartition(':')
    if not separator or not module_name or not function_name:
        raise ValueError("Expected 'module:function' or 'path/to/file.py:function'.")

    is_file_path = '/' in module_name or '\\' in module_name or module_name.endswith('.py')
    if is_file_path:
        path = Path(module_name)
        if path.suffix != '.py':
            path = Path(f"{path}.py")
        path = path.resolve(strict=True)
        loaded_name = f"_refcheck_loaded_{uuid4().hex}"
        spec = importlib.util.spec_from_file_location(loaded_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load Python module from {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[loaded_name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            sys.modules.pop(loaded_name, None)
            raise
    else:
        module = importlib.import_module(module_name)
    function = getattr(module, function_name)
    if not callable(function):
        raise TypeError(f"{function_name!r} is not callable.")

    return function

def get_function_signature(func: Callable) -> dict[str, dict[str, Any]]:
    """
    Get the signature of a function as a string.
    """
    function_signature = inspect.signature(func)

    parameters = {}

    for name, param in function_signature.parameters.items():
        parameters[name] = {
            "default": param.default if param.default is not inspect.Parameter.empty else None,
            "annotation": str(param.annotation) if param.annotation is not inspect.Parameter.empty else None,
            "kind": str(param.kind)
        }

    return parameters
