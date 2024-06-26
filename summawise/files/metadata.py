from dataclasses import dataclass
from pathlib import Path
from . import utils as FileUtils
from ..serializable import Serializable

@dataclass
class FileMetadata(Serializable):
    hash: str
    name: str
    full_path: str
    sz_bytes: int
    created_at: float
    last_modified_at: float
    last_accessed_at: float
    vector_store_id: str = ""

    @classmethod
    def create_from_path(cls, file_path: Path) -> "FileMetadata":
        hash = FileUtils.calculate_hash(file_path)
        stats = file_path.stat()
        sz_bytes = stats.st_size
        created_at = stats.st_ctime
        last_modified_at = stats.st_mtime
        last_accessed_at = stats.st_atime

        return cls(hash, file_path.name, str(file_path), sz_bytes,
                   created_at, last_modified_at, last_accessed_at)    

