import pickle, gzip, hashlib
from pathlib import Path
from typing import TypeVar, Type
from ..data import DataUnit

T = TypeVar("T")

def write_str(file_path: Path, text: str, compress: bool = False) -> None:
    file_path.parent.mkdir(parents = True, exist_ok = True)
    data = text.encode("utf-8")
    write_bytes(file_path, data, compress)

def read_str(file_path: Path) -> str:
    data = read_bytes(file_path)
    text = data.decode("utf-8")
    return text

def write_bytes(file_path: Path, data: bytes, compress: bool = False) -> None:
    file_path.parent.mkdir(parents = True, exist_ok = True)
    if compress:
        if file_path.suffix != ".bin" and ".gz" not in file_path.suffixes:
            file_path = file_path.with_suffix(file_path.suffix + ".gz")
        data = gzip.compress(data)
    with open(file_path, 'wb') as file:
        file.write(data)

def read_bytes(file_path: Path) -> bytes:
    with open(file_path, 'rb') as file:
        data = file.read()
    if ".gz" in file_path.suffixes or ".bin" in file_path.suffixes:
        try:
            data = gzip.decompress(data)
        except gzip.BadGzipFile:
            pass
    return data

def save_object(file_path: Path, obj: object, compress: bool = True) -> None:
    data = pickle.dumps(obj)
    write_bytes(file_path, data, compress)

def load_object(file_path: Path, cls: Type[T]) -> T:
    obj = load_object_any(file_path)
    if not isinstance(obj, cls):
        raise TypeError(f"Expected object of type {cls.__name__}, but got {type(obj).__name__}")
    return obj

def load_object_any(file_path: Path) -> object:
    data = read_bytes(file_path)
    return pickle.loads(data)

def calculate_hash(file_path: Path) -> str:
    hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        reader = lambda: f.read(8 * DataUnit.KB)
        for chunk in iter(reader, b""):
            hash.update(chunk)
    return hash.hexdigest()
