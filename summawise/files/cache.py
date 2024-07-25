import json
from typing import Optional, Dict, Any
from ..settings import Settings
from ..serializable import Serializable
from .. import utils, ai

FileCache: "FileCacheObj"

def init():
    global FileCache
    try:
        FileCache = FileCacheObj.load()
        ai.set_file_cache(FileCache)
    except ModuleNotFoundError:
        FileCacheObj.delete()
        FileCache = FileCacheObj.load()

class FileCacheObj(Serializable):
    """Maps file hashes to OpenAI file_ids, and support our dynamic data serialization."""
    
    def __init__(self, cache: Dict[str, str] = {}):
        self._cache = cache
        self.settings = Settings() # type: ignore
        self.path = FileCacheObj.get_path()

    def set_hash_file_id(self, hash: str, file_id: str):
        self._cache[hash] = file_id

    def get_file_id_by_hash(self, hash: str) -> Optional[str]:
        return self._cache.get(hash)

    @classmethod
    def load(cls) -> "FileCacheObj":
        # create empty FileCache
        cache = cls()
        settings = cache.settings

        # if the file doesn't exist, save empty version by default
        if not cache.path.exists():
            cache.save()
            return cache

        # if the file does exist, use functionality fom Serializable base class to establish populated object
        return cache.from_file(cache.path, settings.data_mode)

    def save(self):
        data_mode = self.settings.data_mode
        compress = self.settings.compression
        self.save_to_file(self.path, data_mode, compress, pretty_json = True)

    @classmethod
    def from_json(cls, json_str: str) -> "FileCacheObj":
        cache_dict = json.loads(json_str)
        cache_dict = FileCacheObj.filter_dict(cache_dict)
        cache = FileCacheObj(cache_dict)
        return cache

    def to_json(self, pretty: bool = False) -> str:
        return json.dumps(self._cache, indent = 4 if pretty else None)

    @staticmethod
    def filter_dict(obj: Dict[str, Any]) -> Dict[str, str]:
        """Returns a dict in which any values that aren't strings are removed."""
        return {
            k: v for k, v in obj.items() \
            if isinstance(v, str)
        }

    @staticmethod
    def get_path():
        settings = Settings() # type: ignore
        return utils.get_summawise_dir() / f"file_cache.{settings.data_mode.ext()}"

    @staticmethod
    def delete():
        path = FileCacheObj.get_path()
        path.unlink(missing_ok = True)
