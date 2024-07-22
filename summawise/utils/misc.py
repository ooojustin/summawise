import tempfile, traceback, sys
from datetime import datetime
from dataclasses import dataclass, asdict, is_dataclass, fields
from importlib import metadata
from typing import Any, Optional, Callable, Union, Tuple, Set, Dict
from pathlib import Path
from packaging.version import Version
from packaging.version import Version
from ..errors import ValueTypeError
from ..data import HashAlg
from .. import utils

package_name = lambda: __name__.split('.')[0]
utc_now = lambda: datetime.utcnow()

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
        sys.stdout.flush()
        sys.stdout.write(ERASE_LINE)
        sys.stdout.flush()

converter_iso: Callable[[datetime], str] = lambda v: v.isoformat()
converter_ts: Callable[[datetime], float] = lambda v: v.timestamp()
converter_ts_int: Callable[[datetime], float] = lambda v: int(v.timestamp())

def convert_datetimes(
    input_dict: Dict[str, Any], 
    converter: Callable[[datetime], Any] = converter_iso
) -> Dict[str, Any]:
    """
    Converts datetime objects in the input dictionary based on the converter func.
        - converter_iso: returns datetime.isoformat() [DEFAULT]
        - converter_ts: returns datetime.timestamp()
        - converter_ts_int: returns int(datetime.timestamp())
    Recursively applies the conversion to nested dictionaries.

    Args:
        input_dict (Dict[str, Any]): A dictionary where keys are strings and values can be of any type.

    Returns:
        Dict[str, Any]: A dict with the same keys as the input dictionary, but with datetime objects converted to ISO formatted strings.
    """
    output = {}
    for key, value in input_dict.items():
        if isinstance(value, datetime):
            output[key] = converter(value)
        elif isinstance(value, dict):
            output[key] = convert_datetimes(value, converter)
        else:
            output[key] = value
    return output

def ex_to_str(ex: Exception, append = "", include_traceback: bool = True) -> str:
    """
    Returns a formatted string representation of the given exception.

    Parameters:
        ex (Exception): The exception object to be formatted.

    Returns:
        str: A string containing the exception type and traceback information.
    """
    strval = f"[{type(ex).__name__}] {str(ex)}"
    if len(append):
        strval += f": {append}"

    if include_traceback:
        traceback_str = traceback.format_exc()
        strval += f"\nTraceback: {traceback_str}"

    return strval

def try_parse_int(value: str, default: Optional[int] = None) -> Optional[int]:
    """
    Tries to parse the input value as an integer.

    Parameters:
        value (str): The value to be parsed as an integer.
        default (Optional[int]): The default value to return if parsing fails. Default is None.

    Returns:
        Optional[int]: The parsed integer value if successful, or the default value if parsing fails.
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def calculate_hash(
    _input: Union[Path, str, bytes], 
    algorithm: HashAlg = HashAlg.SHA3_256,
    intdigest: bool = False
) -> Union[str, int]:
    """
    Calculate the hash of the input using the specified algorithm.

    Parameters:
        _input (Union[Path, str, bytes]): The input data to calculate the hash for.
        algorithm (HashAlg): The hashing algorithm to use to calculate the hash with.
        intdigest (bool): Whether to return the hash as an integer or a string.

    Returns:
        Union[str, int]: The calculated hash, either as a string or an integer.

    Raises:
        ValueError: If the hash algorithm/object is not valid.
        ValueTypeError: If the input data type is not one of Path, str, or bytes.
    """
    assert_type(_input, (bytes, str, Path))
    return algorithm.calculate(_input, intdigest)

def conditional_exit(user_input: str) -> None:
    """Conditionally exit the program based on the users input."""
    if user_input.lower() in ["exit", "quit", ":q"]:
        if user_input == ":q": 
            print("They should call you Vim Diesel.") # NOTE(justin): this is here to stay
        sys.exit()
