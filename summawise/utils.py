import tempfile, inspect
from pathlib import Path
from enum import Enum
from typing import List

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
        assert sz_bytes >= 0, "sz_bytes must be non-negative"
        size, uidx = sz_bytes, 0
        units = DataUnit.units or DataUnit._get_units()
        while size >= DataUnit.KB and uidx < len(units) - 1:
            size /= float(DataUnit.KB)
            uidx += 1
        return f"{size:.2f} {units[uidx]}"

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
