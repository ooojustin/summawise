import inspect, hashlib, xxhash
from enum import Enum
from typing import List, Union
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

class HashAlg(Enum):
    SHA_256 = (hashlib, "sha256")
    SHA3_256 = (hashlib, "sha3_256")
    XXH_32 = (xxhash, "xxh32")
    XXH_64 = (xxhash, "xxh64")
    XXH_128 = (xxhash, "xxh128")
    XXH3_128 = (xxhash, "xxh3_128")
    XXH3_64 = (xxhash, "xxh3_64")

    def init(self):
        module, attr_name = self.value
        hash_init = getattr(module, attr_name)
        return hash_init() # initialze hash object

    def calculate(
        self,
        _input: Union[Path, str, bytes], 
        # algorithm: HashAlg = HashAlg.SHA3_256,
        intdigest: bool = False
    ) -> Union[str, int]:
        hash_obj = self.init()
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
