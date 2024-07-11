import tempfile, sys
from importlib import metadata
from dataclasses import is_dataclass, fields
from typing import Any, Union, Tuple, Set, Dict
from pathlib import Path
from packaging.version import Version
from .errors import ValueTypeError

package_name = lambda: __name__.split('.')[0]

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

def get_version(pkg_name: str = "") -> Version:
    """
    Retrieves the version of a specified package.
    By default, it will return the running packages (summawise) version. 
    Args:
        pkg_name (str): The name of the package to retrieve the version for. If not provided, the default package name will be used.
    Returns:
        Version: An object representing the version of the specified package.
    """
    if not pkg_name: 
        pkg_name = package_name()
    version_str = metadata.version(pkg_name)
    return Version(version_str)

def delete_lines(count: int = 1):
    """
    Deletes the specified number of lines from the terminal output.
    VT100 docs: https://vt100.net/docs/vt100-ug/chapter3.html
    Parameters:
        count (int): The number of lines to delete. Default is 1.
    """
    CURSOR_UP_ONE = '\x1b[1A'
    ERASE_LINE = '\x1b[2K'
    for _ in range(count):
        sys.stdout.write(CURSOR_UP_ONE)
        sys.stdout.write(ERASE_LINE)
    sys.stdout.flush()
