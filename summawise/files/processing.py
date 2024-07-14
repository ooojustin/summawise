from pathlib import Path
from .metadata import FileMetadata
from . import utils as FileUtils
from .. import ai, utils
from ..settings import Settings

def process_dir(dir_path: Path, delete: bool = True) -> ai.Resources:
    _ = delete

    resources: ai.Resources
    files = FileUtils.list_files(dir_path)
    filtered = FileUtils.filter_files(files) # TODO(justin): look into improving/validating approach
    try:
        print(f"Directory scan located and validated {filtered.valid_count}/{filtered.total_count} files.")
        resources = ai.create_vector_store(dir_path.name, filtered.files)
        print(f"Vector store created with ID: {resources.vector_store_id}")
    except Exception as ex:
        raise Exception(f"Error creating vector store [{type(ex)}]: {ex}")

    return resources

def process_file(file_path: Path, delete: bool = False) -> ai.Resources:
    # TODO(justin): 
    # - add archive support (.zip, .tar.gz) - extract, call process_dir
    # - maybe add automatic extraction of text from pdf or html (undecided)

    # use settings class (singleton)
    settings = Settings() # type: ignore

    # file extension to cache file metadata (json or bin)
    ext = settings.data_mode.ext()

    metadata = FileMetadata.create_from_path(file_path)
    hash = metadata.hash
    hash_path = utils.fp(utils.get_summawise_dir() / "files" / f"{hash}.{ext}")

    if not hash_path.exists():
        try:
            resources = ai.create_vector_store(file_path.stem, [file_path])
            metadata.vector_store_id = resources.vector_store_id
            metadata.file_id = next(iter(resources.file_ids))
            metadata.save_to_file(
                file_path = hash_path,
                mode = settings.data_mode,
                compress = settings.compression,
                pretty_json = True
            )
            print(f"Vector store created with ID: {metadata.vector_store_id}")
        except Exception as ex:
            raise Exception(f"Error creating vector store [{type(ex)}]: {ex}")
    else:
        metadata = FileMetadata.from_file(hash_path, settings.data_mode)
        print(f"Restored vector store ID from cache: {metadata.vector_store_id}")

    if delete and file_path.exists():
        file_path.unlink()

    return ai.Resources(
        vector_store_ids = [metadata.vector_store_id], 
        file_ids = [metadata.file_id]
    )
