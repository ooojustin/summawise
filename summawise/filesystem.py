import json
from . import ai, utils
from .utils import FileUtils, Serializable, fp
from .errors import NotSupportedError
from .settings import Settings
from dataclasses import dataclass
from pathlib import Path

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

def process_dir(dir_path: Path, delete: bool = True) -> str:
    # TODO
    _, _ = dir_path, delete
    raise NotSupportedError()

def process_file(file_path: Path, delete: bool = False) -> str:
    # TODO(justin): 
    # - add archive support (.zip, .tar.gz) - extract, call process_dir
    # - maybe add automatic extraction of text from pdf or html (undecided)

    # use settings class (singleton)
    settings = Settings() # type: ignore

    # file extension to cache file metadata (json or bin)
    ext = settings.data_mode.ext()

    metadata = FileMetadata.create_from_path(file_path)
    hash = metadata.hash
    hash_path = fp(utils.get_summawise_dir() / "files" / f"{hash}.{ext}")

    vector_store_id: str = ""
    if not hash_path.exists():
        try:
            vector_store = ai.create_vector_store(file_path.stem, [file_path])
            metadata.vector_store_id = vector_store.id
            metadata.save_to_file(
                file_path = hash_path,
                mode = settings.data_mode,
                compress = settings.compression
            )
            vector_store_id = metadata.vector_store_id
            print(f"Vector store created with ID: {vector_store_id}")
        except Exception as ex:
            raise Exception(f"Error creating vector store [{type(ex)}]: {ex}")
    else:
        metadata = FileMetadata.from_file(hash_path, settings.data_mode)
        vector_store_id = metadata.vector_store_id
        print(f"Restored vector store ID from cache: {vector_store_id}")

    if delete and file_path.exists():
        file_path.unlink()

    return vector_store_id
