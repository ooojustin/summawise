import json
import os
import zlib
from pathlib import Path
from typing import Optional, Dict, Any
from summawise.errors import MalformedCacheError
from summawise.files import utils as FileUtils
from summawise.settings import Settings
from summawise.serializable import Serializable
from summawise import utils, ai

FileCache: "FileCacheObj"


def init():
    global FileCache
    FileCache = FileCacheObj.load()
    ai.set_file_cache(FileCache)


class FileCacheObj(Serializable):
    """Maps file hashes to OpenAI file_ids, and support our dynamic data serialization."""

    def __init__(self, cache: Optional[Dict[str, str]] = None):
        self._cache = {} if cache is None else cache
        self.settings = Settings()  # type: ignore
        self.path = FileCacheObj.get_path()

    def set_hash_file_id(self, hash: str, file_id: str):
        self._cache[hash] = file_id

    def get_file_id_by_hash(self, hash: str) -> Optional[str]:
        return self._cache.get(hash)

    @classmethod
    def load(cls) -> "FileCacheObj":
        """Loads the cache from disk. An absent or malformed file yields an empty cache (and a malformed one is set aside)."""
        cache = cls()

        # NOTE: save() may have written a .gz variant; utils.fp resolves whichever exists
        path = utils.fp(cache.path)
        if path.exists():
            try:
                return cls.from_file(path)
            except MalformedCacheError as ex:
                # set it aside: fp() prefers an existing .json over .json.gz, so a leftover would shadow the next save()
                print(f"{ex}. Starting with an empty cache.")
                os.replace(path, path.with_name(path.name + ".corrupt"))

        cache.save()
        return cache

    def save(self):
        compress = self.settings.compression
        self.save_to_file(self.path, compress=compress, pretty_json=True)

    @classmethod
    def from_file(cls, file_path: Path) -> "FileCacheObj":
        """Raises MalformedCacheError if the file can't be read as a JSON object (truncated or corrupt gzip, invalid UTF-8 or JSON, non-object JSON)."""
        try:
            data = json.loads(FileUtils.read_str(file_path))
        except (EOFError, zlib.error, ValueError, RecursionError) as ex:  # ValueError: UnicodeDecodeError, JSONDecodeError
            raise MalformedCacheError(file_path, f"{type(ex).__name__}: {ex}") from ex
        if not isinstance(data, dict):
            raise MalformedCacheError(file_path, f"expected a JSON object, got {type(data).__name__}")
        return cls(cls.filter_dict(data))

    def to_json(self, pretty: bool = False) -> str:
        return json.dumps(self._cache, indent=4 if pretty else None)

    @staticmethod
    def filter_dict(obj: Dict[str, Any]) -> Dict[str, str]:
        """Returns a dict in which any values that aren't strings are removed."""
        return {
            k: v for k, v in obj.items()
            if isinstance(v, str)
        }

    @staticmethod
    def get_path():
        return utils.get_summawise_dir() / "file_cache.json"
