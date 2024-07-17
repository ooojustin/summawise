import tempfile, traceback, pygments, sys
from datetime import datetime
from dataclasses import is_dataclass, fields
from importlib import metadata
from typing import Any, Optional, Callable, Union, Tuple, Set, Dict, List
from pathlib import Path
from packaging.version import Version
from packaging.version import Version
from whats_that_code.election import guess_language_all_methods
from pygments.lexers import TextLexer, get_lexer_by_name
from pygments.lexers import guess_lexer as pygments_guess_lexer
from pygments.lexer import Lexer
from pygments.formatter import Formatter
from pygments.formatters import  TerminalFormatter
from pygments.util import ClassNotFound
from prompt_toolkit.document import Document
from prompt_toolkit.validation import Validator, ValidationError
from .errors import ValueTypeError
from .data import HashAlg

package_name = lambda: __name__.split('.')[0]
utc_now = lambda: datetime.utcnow()

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class NumericChoiceValidator(Validator):

    def __init__(self, valid_choices: List[int]):
        self.valid_choices = valid_choices

    def validate(self, document: Document):
        try:
            value = int(document.text)
            if value not in self.valid_choices:
                raise ValidationError(
                    message="That number isn't a valid choice.",
                    cursor_position=len(document.text)
                )
        except ValueError:
            raise ValidationError(
                message="Input the number corresponding with your choice.",
                cursor_position=len(document.text)
            )

class ChoiceValidator(Validator):

    def __init__(self, valid_choices: List[str], allow_empty: bool = False):
        self.valid_choices = valid_choices
        if allow_empty:
            self.valid_choices.append("")

    def validate(self, document: Document):
        choice = document.text # input as a string
        if choice not in self.valid_choices:
            raise ValidationError(
                message = "The choice you have input is invalid.",
                cursor_position = len(document.text)
            )

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

def try_parse_int(value: str, default: Optional[int] = None) -> Optional[int]:
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def calculate_hash(
    _input: Union[Path, str, bytes], 
    algorithm: HashAlg = HashAlg.SHA3_256,
    intdigest: bool = False
) -> Union[str, int]:
    assert_type(_input, (bytes, str, Path))
    return algorithm.calculate(_input, intdigest)

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

def expand_ex(ex: Exception, append = "", include_traceback: bool = True) -> Exception:
    strval = ex_to_str(ex, append, include_traceback)
    return ex.__class__(strval)

def guess_lexer(code: str) -> Optional[Lexer]:
    language_name = guess_language_all_methods(code)
    if language_name:
        try:
            return get_lexer_by_name(language_name)
        except ClassNotFound:
            pass
    try:
        return pygments_guess_lexer(code)
    except Exception:
        pass

def highlight_code(code: str, lexer: Optional[Lexer] = None, formatter: Optional[Formatter] = None):
    if lexer is None:
        lexer = guess_lexer(code) or TextLexer()
    if formatter is None:
        formatter = TerminalFormatter()
    highlighted_code = pygments.highlight(code, lexer, formatter)
    return highlighted_code
