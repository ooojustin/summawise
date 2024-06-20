import tempfile, pickle
from pathlib import Path
from typing import TypeVar, Type

T = TypeVar('T')

class FileUtils:

    @staticmethod
    def write_str(file_path: Path, content: str) -> None:
        file_path.parent.mkdir(parents = True, exist_ok = True)
        with open(file_path, 'w') as file:
            file.write(content)

    @staticmethod
    def read_str(file_path: Path) -> str:
        with open(file_path, 'r') as file:
            return file.read()

    @staticmethod
    def write_bytes(file_path: Path, content: bytes) -> None:
        file_path.parent.mkdir(parents = True, exist_ok = True)
        with open(file_path, 'wb') as file:
            file.write(content)

    @staticmethod
    def read_bytes(file_path: Path) -> bytes:
        with open(file_path, 'rb') as file:
            return file.read()

    @staticmethod
    def save_object(file_path: Path, obj: object) -> None:
        data = pickle.dumps(obj)
        FileUtils.write_bytes(file_path, data)

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
