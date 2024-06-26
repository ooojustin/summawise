import tempfile, pickle, gzip, inspect, hashlib
from pathlib import Path
from typing import List, TypeVar, Type

T = TypeVar('T')

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
        assert sz_bytes >= 0, "num_bytes must be non-negative"
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

class FileUtils:

    @staticmethod
    def write_str(file_path: Path, text: str, compress: bool = False) -> None:
        file_path.parent.mkdir(parents = True, exist_ok = True)
        data = text.encode("utf-8")
        FileUtils.write_bytes(file_path, data, compress)

    @staticmethod
    def read_str(file_path: Path) -> str:
        data = FileUtils.read_bytes(file_path)
        text = data.decode("utf-8")
        return text

    @staticmethod
    def write_bytes(file_path: Path, data: bytes, compress: bool = False) -> None:
        file_path.parent.mkdir(parents = True, exist_ok = True)
        if compress:
            if file_path.suffix != ".bin" and ".gz" not in file_path.suffixes:
                file_path = file_path.with_suffix(file_path.suffix + ".gz")
            data = gzip.compress(data)
        with open(file_path, 'wb') as file:
            file.write(data)

    @staticmethod
    def read_bytes(file_path: Path) -> bytes:
        with open(file_path, 'rb') as file:
            data = file.read()
        if ".gz" in file_path.suffixes or ".bin" in file_path.suffixes:
            try:
                data = gzip.decompress(data)
            except gzip.BadGzipFile:
                pass
        return data

    @staticmethod
    def save_object(file_path: Path, obj: object, compress: bool = True) -> None:
        data = pickle.dumps(obj)
        FileUtils.write_bytes(file_path, data, compress)

    @staticmethod
    def load_object(file_path: Path, cls: Type[T]) -> T:
        obj = FileUtils.load_object_any(file_path)
        if not isinstance(obj, cls):
            raise TypeError(f"Expected object of type {cls.__name__}, but got {type(obj).__name__}")
        return obj

    @staticmethod
    def load_object_any(file_path: Path) -> object:
        data = FileUtils.read_bytes(file_path)
        return pickle.loads(data)

    @staticmethod
    def calculate_hash(file_path: Path) -> str:
        hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            reader = lambda: f.read(8 * DataUnit.KB)
            for chunk in iter(reader, b""):
                hash.update(chunk)
        return hash.hexdigest()

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
