import json
from . import ai
from .utils import FileUtils
from .errors import NotSupportedError
from .settings import DataMode
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class FileMetadata:
    file_name: str
    full_file_path: str
    file_hash: str
    size_in_bytes: int
    creation_time: float
    last_modification_time: float
    last_access_time: float
    vector_store_id: str = ""

    @classmethod
    def create_from_path(cls, file_path: Path) -> "FileMetadata":
        file_name = file_path.name
        full_file_path = str(file_path)
        file_hash = FileUtils.calculate_hash(file_path)
        size_in_bytes = file_path.stat().st_size
        creation_time = file_path.stat().st_ctime
        last_modification_time = file_path.stat().st_mtime
        last_access_time = file_path.stat().st_atime

        return cls(file_name, full_file_path, file_hash, size_in_bytes,
                   creation_time, last_modification_time, last_access_time)    

    def to_json(self, pretty: bool = True) -> str:
        return json.dumps(asdict(self), indent = 4 if pretty else None)

    def save_to_file(self, file_path: Path, mode: DataMode = DataMode.JSON, compress: bool = False):
        if mode == DataMode.JSON:
            json_str = self.to_json()
            FileUtils.write_str(file_path, json_str, compress)
        elif mode == DataMode.BIN:
            FileUtils.save_object(file_path, self, compress)

    @staticmethod
    def from_file(file_path: Path, mode: DataMode = DataMode.JSON) -> "FileMetadata":
        if mode == DataMode.JSON:
            json_str = FileUtils.read_str(file_path)
            return FileMetadata.from_json(json_str)
        elif mode == DataMode.BIN:
            return FileUtils.load_object(file_path, FileMetadata)

    @staticmethod
    def from_json(json_str: str) -> "FileMetadata":
        data = json.loads(json_str)
        metadata = FileMetadata(**data)
        return metadata

def process_dir(dir_path: Path, delete: bool = True) -> str:
    # TODO
    _, _ = dir_path, delete
    raise NotSupportedError()

def process_file(file_path: Path, delete: bool = False) -> str:
    # TODO(justin): 
    # - cache vector store id based on file hash
    # - add archive support (.zip, .tar.gz) - extract, call process_dir
    # - maybe add automatic extraction of text from pdf or html (undecided)
    vector_store = ai.create_vector_store(file_path.stem, [file_path])
    if delete and file_path.exists(): file_path.unlink()
    return vector_store.id
