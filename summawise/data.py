import inspect, hashlib, xxhash
from enum import Enum
from typing import Any, List, Union, NamedTuple, cast
from types import ModuleType
from pathlib import Path
from .errors import ValueTypeError

class DataMode(Enum):
    JSON = "json"
    BIN = "binary"

    def ext(self) -> str:
        extensions = {
            DataMode.JSON: "json",
            DataMode.BIN: "bin"
        }
        try:
            return extensions[self]
        except KeyError:
            raise ValueError(f"Unsupported DataMode: {self}")

class DataUnit:
    """
    Utility class for converting sizes in bytes to human-readable string representations with appropriate units.
    
    Attributes:
        B (int): Size multiplier for bytes.
        KB (int): Size multiplier for kilobytes.
        MB (int): Size multiplier for megabytes.
        GB (int): Size multiplier for gigabytes.
        TB (int): Size multiplier for terabytes.

    Methods:
        _get_units(): Retrieve a list of available unit names based on class attributes.
        bytes_to_str(sz_bytes: int) -> str: Convert a size in bytes to a human-readable string representation.
    """
    __excludes__ = ["units"]

    B: int = 1
    KB: int = 2 ** 10
    MB: int = 2 ** 20
    GB: int = 2 ** 30
    TB: int = 2 ** 40

    units: List[str] = []

    @staticmethod
    def _get_units() -> List[str]:
        # "B", "KB", "MB", "GB", "TB"
        if len(DataUnit.units):
            return DataUnit.units
        units = [
            (name, value) for name, value in inspect.getmembers(DataUnit) 
            if not name.startswith("__") 
            and name not in DataUnit.__excludes__ 
            and not callable(value)
        ]
        units = sorted(units, key=lambda x: x[1])
        DataUnit.units = [name for name, _ in units]
        return DataUnit.units

    @staticmethod
    def bytes_to_str(sz_bytes: int) -> str:
        """
        Convert a size in bytes to a human-readable string representation.

        Parameters:
            sz_bytes (int): The size in bytes to convert to a human-readable string.

        Returns:
            str: A human-readable string representation of the size, including units (e.g. "1.23 MB").
        """
        assert sz_bytes >= 0, "sz_bytes must be non-negative"
        size, uidx = sz_bytes, 0
        units = DataUnit.units or DataUnit._get_units()
        while size >= DataUnit.KB and uidx < len(units) - 1:
            size /= float(DataUnit.KB)
            uidx += 1
        return f"{size:.2f} {units[uidx]}"

class _HashAlg(NamedTuple):
    module: ModuleType
    function_name: str

    def init(self) -> Any:
        alg_init = getattr(self.module, self.function_name)
        return alg_init()

class HashAlg(Enum):
    """An enumeration class representing various hashing algorithms and offering their implementation."""
    SHA_256 = _HashAlg(hashlib, "sha256")
    SHA3_256 = _HashAlg(hashlib, "sha3_256")
    XXH_32 = _HashAlg(xxhash, "xxh32")
    XXH_64 = _HashAlg(xxhash, "xxh64")
    XXH_128 = _HashAlg(xxhash, "xxh128")
    XXH3_128 = _HashAlg(xxhash, "xxh3_128")
    XXH3_64 = _HashAlg(xxhash, "xxh3_64")

    def calculate(
        self,
        _input: Union[Path, str, bytes], 
        intdigest: bool = False
    ) -> Union[str, int]:
        """
        Calculate the hash of the input using the specified algorithm.

        Parameters:
            _input (Union[Path, str, bytes]): The input data to calculate the hash for.
            intdigest (bool): Whether to return the hash as an integer or a string.

        Returns:
            Union[str, int]: The calculated hash, either as a string or an integer.

        Raises:
            ValueError: If the hash algorithm/object is not valid.
            ValueTypeError: If the input data type is not one of Path, str, or bytes.
        """
        try:
            alg = cast(_HashAlg, self.value)
            hash_obj = alg.init()
            assert HashAlg.hash_obj_valid(hash_obj)
        except (AssertionError, AttributeError) as ex:
            raise ValueError("Invalid hash object.") from ex

        if isinstance(_input, (bytes, str)):
            _input = _input.encode() if isinstance(_input, str) else _input
            hash_obj.update(_input)
        elif isinstance(_input, Path):
            with open(_input, "rb") as f:
                for chunk in iter(lambda: f.read(8 * DataUnit.KB), b""):
                    hash_obj.update(chunk)
        else:
            raise ValueTypeError(_input, (Path, str, bytes))

        return (
            hash_obj.hexdigest() if not intdigest else
            int.from_bytes(hash_obj.digest(), byteorder = "big")
        )

    @staticmethod
    def hash_obj_valid(alg: Any) -> bool:
        """Check if the given algorithm object is a valid hash algorithm."""
        updater = getattr(alg, "update", None)
        digester = getattr(alg, "digest", None)
        hexdigester = getattr(alg, "hexdigest", None)
        return (
            updater is not None and callable(updater) and
            digester is not None and callable(digester) and
            hexdigester is not None and callable(hexdigester)
        )
