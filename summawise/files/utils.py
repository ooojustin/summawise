import os
import re
import gzip
import tempfile
import chardet
from typing import List, Optional, NamedTuple
from pathlib import Path
from summawise.files.encodings import Encoding
from summawise.data import DataUnit


def write_str(file_path: Path, text: str, compress: bool = False) -> None:
    write_bytes(file_path, text.encode("utf-8"), compress)


def read_str(file_path: Path) -> str:
    data = read_bytes(file_path)
    text = data.decode("utf-8")
    return text


def write_bytes(file_path: Path, data: bytes, compress: bool = False) -> None:
    """
    Atomically writes owner-only (0600) data: a temp file in the destination directory is fsynced and renamed over
    the target, so readers see the old or the new content, never a truncated file. Replacing the inode also tightens
    a pre-existing looser file, and a symlink at the target is replaced rather than followed.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if compress:
        if ".gz" not in file_path.suffixes:
            file_path = file_path.with_suffix(file_path.suffix + ".gz")
        data = gzip.compress(data)
    fd, tmp_name = tempfile.mkstemp(
        dir=file_path.parent, prefix=f".{file_path.name}.", suffix=".tmp")  # mkstemp creates the file 0600
    try:
        with os.fdopen(fd, "wb") as file:
            file.write(data)
            file.flush()
            os.fsync(file.fileno())
        os.replace(tmp_name, file_path)
    except BaseException:
        os.unlink(tmp_name)
        raise


def read_bytes(file_path: Path) -> bytes:
    with open(file_path, 'rb') as file:
        data = file.read()
    if ".gz" in file_path.suffixes:
        try:
            data = gzip.decompress(data)
        except gzip.BadGzipFile:
            pass
    return data


def list_files(directory: Path, recursive: bool = True) -> List[Path]:
    assert directory.is_dir(
    ), f"The provided path to 'list_files' must be a directory. (Value: '{directory}')"
    files = []
    for item in directory.iterdir():
        if item.is_file():
            files.append(item)
        elif item.is_dir() and recursive:
            files.extend(list_files(item, recursive=True))
    return files


def get_encoding(file_path: Path) -> Optional[Encoding]:
    """
    Attempts to determine the encoding of a file based on the first 4 KB. If none is recognized, the function returns 'None'.
    Supported encodings: https://link.justin.ooo/chardet-encodings
    """
    with file_path.open('rb') as f:
        raw_data = f.read(4 * DataUnit.KB)  # read the first 4KB of the file
        result = chardet.detect(raw_data)
        encoding_str = result.get("encoding")
        if isinstance(encoding_str, str):
            encoding = Encoding.from_string(encoding_str)
            return encoding
    return None


def has_parent_directory(path: Path, dir_name: str) -> bool:
    # def normalize(s): return f"/{s.strip('/\\').replace('\\', '/')}/" # NOTE(justin): SyntaxError reference: https://pastebin.com/ATPVSDH5
    def normalize(s): return "/" + s.strip('/\\').replace('\\', '/') + "/"
    dir_name = normalize(dir_name)
    path_str = normalize(str(path))
    return dir_name in path_str


def matches_pattern(text: str, pattern: str) -> bool:
    return re.search(pattern, text) is not None


class FilteredFiles(NamedTuple):
    files: List[Path]
    files_conv: List[Path]
    total_count: int
    valid_count: int


def filter_files(all_files: List[Path]) -> FilteredFiles:
    encoding_whitelist = [Encoding.UTF_8, Encoding.ASCII]
    dir_blacklist = [".git", "node_modules", "site-packages", ".mypy_cache"]
    pattern_blacklist = [r".*\.egg-info"]

    # extensions we'll still create embeddings for by creating a temp .txt duplicate
    extensions_convert = {'.lua'}

    # extensions supported by OpenAI by default
    extension_whitelist = {
        '.py', '.js', '.txt', '.md', '.html', '.css', '.java', '.c', '.cpp',
        '.rb', '.php', '.ts', '.json', '.xml', '.csv', '.xlsx', '.pptx', '.docx',
        '.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.zip', '.tar', '.tex'
    }

    files = [
        file_path for file_path in all_files
        if file_path.suffix in extension_whitelist | extensions_convert
        and get_encoding(file_path) in encoding_whitelist
        and not any(has_parent_directory(file_path, dir) for dir in dir_blacklist)
    ]

    # NOTE(justin): run actual path pattern checks in a separate loop (for optimization purposes)
    # the goal is to filter out *most* invalid paths without regex prior to this using has_parent_directory
    files = [
        file for file in files if
        not any(matches_pattern(str(file), pattern)
                for pattern in pattern_blacklist)
    ]

    # move files which need to be converted to txt into separate list
    files_conv = [
        file_path for file_path in files
        if file_path.suffix in extensions_convert
    ]
    files = [
        file_path for file_path in files
        if not file_path in files_conv
    ]

    return FilteredFiles(
        files=files,
        files_conv=files_conv,
        total_count=len(all_files),
        valid_count=len(files)
    )
