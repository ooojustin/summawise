import tempfile
from dataclasses import is_dataclass, fields
from typing import Any, Union, Tuple, Set, Dict
from pathlib import Path
from .errors import ValueTypeError

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

def get_summawise_dir() -> Path:
    temp_dir = Path(tempfile.gettempdir())
    return temp_dir / "summawise"

def fp(file_path: Path) -> Path:
    """
    Patch a given 'Path' object in a specific scenario:
    The correct path is the same exact location, but with a .gz suffix, denoting gzip compression.
    """
    if not file_path.exists():
        gz_path = file_path.with_suffix(file_path.suffix + ".gz")
        if gz_path.exists():
            return gz_path
    return file_path

def assert_type(value: Any, type_or_types: Union[type, Tuple[type, ...]]) -> None:
    """
    Asserts that a variable is of a given type.
    
    Parameters:
        value (Any): The variable to be checked.
        type_or_types (Union[type, Tuple[type, ...]]): The type or types that the variable should be checked against.

    Raises:
        TypeError: If 'type_or_types' is not a type or tuple of types.
        ValueTypeError: If the variable is not of the specified type or types.
    """
    if not isinstance(type_or_types, (type, tuple)):
        raise TypeError("Function 'assert_type' parameter 'type_or_types' must be a type, or a tuple of types.")
    elif not isinstance(value, type_or_types):
        raise ValueTypeError(value, type_or_types)

def asdict_exclude(obj: Any, exclude: Set[str]) -> Dict[str, Any]:
    """
    Convert a dataclass object to a dictionary, excluding specified fields.

    Parameters:
        obj (Any): The dataclass object to convert to a dictionary.
        exclude (Set[str]): A set of field names to exclude from the resulting dictionary.

    Returns:
        Dict[str, Any]: A dictionary representation of the dataclass object, excluding the specified fields.

    Raises:
        TypeError: If the input object is not a dataclass.
    """
    if not is_dataclass(obj):
        raise TypeError("Object must be a dataclass.")

    result = {}
    for f in fields(obj):
        if f.name not in exclude:
            result[f.name] = getattr(obj, f.name)
    return result
