import json
from typing import TypeVar, Type
from pathlib import Path
from dataclasses import is_dataclass, asdict
from .data import DataMode
from .files import utils as FileUtils

ST = TypeVar("ST", bound = "Serializable")

class Serializable:

    def save_to_file(self, file_path: Path, mode: DataMode = DataMode.JSON, compress: bool = False):
        if mode == DataMode.JSON:
            json_str = self.to_json()
            FileUtils.write_str(file_path, json_str, compress)
        elif mode == DataMode.BIN:
            FileUtils.save_object(file_path, self, compress)

    @classmethod
    def from_file(cls: Type[ST], file_path: Path, mode: DataMode = DataMode.JSON) -> ST:
        if mode == DataMode.JSON:
            json_str = FileUtils.read_str(file_path)
            return cls.from_json(json_str)
        elif mode == DataMode.BIN:
            return FileUtils.load_object(file_path, cls)

    @classmethod
    def from_json(cls: Type[ST], json_str: str) -> ST:
        if not is_dataclass(cls):
            raise NotImplementedError(f"Class '{cls.__name__}' is not a dataclass, so it must provide its own implementation of 'from_json'.")
        # NOTE(justin): My LSP gives me a 'Code is unreachable' warning here, but that is not accurate.
        # If a subclass extends 'Serializable' and has the '@dataclass' decorator, the above exception will not be raised.
        data = json.loads(json_str)
        return cls(**data)

    def to_json(self, pretty: bool = False) -> str:
        if not is_dataclass(self):
            raise NotImplementedError(f"Class '{type(self).__name__}' is not a dataclass, so it must provide its own implementation of 'to_json'.")
        return json.dumps(asdict(self), indent = 4 if pretty else None)
