import tempfile, pickle, gzip
from pathlib import Path
from typing import TypeVar, Type

T = TypeVar('T')

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

def get_summawise_dir() -> Path:
    temp_dir = Path(tempfile.gettempdir())
    return temp_dir / "summawise"
