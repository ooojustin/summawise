import ai
from pathlib import Path
from errors import NotSupportedError

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
