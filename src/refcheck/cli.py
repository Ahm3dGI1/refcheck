import importlib
import inspect
from collections.abc import Callable
from typing import Any


def load_function_from_file(file_path: str) -> Callable:

    module_name, function_name = file_path.replace('/', '.').split(':')

    module = importlib.import_module(module_name)
    function = getattr(module, function_name)

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
