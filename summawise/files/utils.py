import pickle, gzip, hashlib, chardet, xxhash
from typing import TypeVar, Type, List, Optional, NamedTuple, Union
from pathlib import Path
from enum import Enum
from .encodings import Encoding
from ..data import DataUnit

T = TypeVar("T")

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

def calculate_hash(
    _input: Union[Path, str, bytes], 
    algorithm: HashAlg = HashAlg.SHA3_256,
    intdigest: bool = False
) -> Union[str, int]:
    hash_obj = algorithm.init()

    if isinstance(_input, (bytes, str)):
        _input = _input.encode() if isinstance(_input, str) else _input
        hash_obj.update(_input)
    elif isinstance(_input, Path):
        with open(_input, "rb") as f:
            for chunk in iter(lambda: f.read(8 * DataUnit.KB), b""):
                hash_obj.update(chunk)
    else:
        raise TypeError("Input to 'calculate_hash' must be of type 'str', 'bytes', or 'Path'.")

    return (
        hash_obj.hexdigest() if not intdigest else
        int.from_bytes(hash_obj.digest(), byteorder = "big")
    )

def list_files(directory: Path, recursive: bool = True) -> List[Path]:
    assert directory.is_dir(), f"The provided path to 'list_files' must be a directory. (Value: '{directory}')"
    files = []
    for item in directory.iterdir():
        if item.is_file():
            files.append(item)
        elif item.is_dir() and recursive:
            files.extend(list_files(item, recursive = True))
    return files

def get_encoding(file_path: Path) -> Optional[Encoding]:
    """
    Attempts to determine the encoding of a file based on the first 4 KB. If none is recognized, the function returns 'None'.
    Supported encodings: https://link.justin.ooo/chardet-encodings
    """
    with file_path.open('rb') as f:
        raw_data = f.read(4 * DataUnit.KB) # read the first 4KB of the file
        result = chardet.detect(raw_data)
        encoding_str = result.get("encoding")
        if isinstance(encoding_str, str):
            encoding = Encoding.from_string(encoding_str)
            return encoding
    return None

def has_parent_directory(path: Path, dir_name: str) -> bool:
    normalize = lambda s: f"/{s.strip('/\\').replace('\\', '/')}/"
    dir_name = normalize(dir_name)
    path_str = normalize(str(path))
    return dir_name in path_str

class FilteredFiles(NamedTuple):
    files: List[Path]
    total_count: int
    valid_count: int

def filter_files(all_files: List[Path]) -> FilteredFiles:
    encoding_whitelist = [Encoding.UTF_8, Encoding.ASCII]
    dir_blacklist = [".git", "node_modules", "site-packages"]
    extension_whitelist = {
        '.py', '.js', '.txt', '.md', '.html', '.css', '.java', '.c', '.cpp',
        '.rb', '.php', '.ts', '.json', '.xml', '.csv', '.xlsx', '.pptx', '.docx',
        '.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.zip', '.tar', '.tex'
    }

    files = [
        file_path for file_path in all_files
        if file_path.suffix in extension_whitelist \
        and get_encoding(file_path) in encoding_whitelist \
        and not any(has_parent_directory(file_path, dir) for dir in dir_blacklist)
    ]

    return FilteredFiles(
        files = files,
        total_count = len(all_files),
        valid_count = len(files)
    )
