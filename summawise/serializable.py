import json
from typing import TypeVar, Type
from pathlib import Path
from dataclasses import is_dataclass, asdict
from summawise.files import utils as FileUtils

ST = TypeVar("ST", bound="Serializable")


class Serializable:

    def save_to_file(
        self,
        file_path: Path,
        compress: bool = False,
        pretty_json: bool = False
    ):
        json_str = self.to_json(pretty_json)
        FileUtils.write_str(file_path, json_str, compress)

    @classmethod
    def from_file(
        cls: Type[ST],
        file_path: Path
    ) -> ST:
        json_str = FileUtils.read_str(file_path)
        return cls.from_json(json_str)

    @classmethod
    def from_json(cls: Type[ST], json_str: str) -> ST:
        try:
            data = json.loads(json_str)
            return cls(**data)
        except Exception as ex:
            if not is_dataclass(cls):
                raise NotImplementedError(
                    f"Class '{cls.__name__}' is not a dataclass, and alternative method failed, "
                    f"so it must provide its own implementation of 'from_json'.\nException: {ex}"
                )
            else:
                raise Exception(
                    f"Unexpected exception occurred while invoking '{cls.__name__}.from_json' on @dataclass.\n"
                    f"Exception: {ex}"
                )

    def to_json(self, pretty: bool = False) -> str:
        try:
            obj = asdict(self) if is_dataclass(self) else self.__dict__
            return json.dumps(obj, indent=4 if pretty else None)
        except Exception as ex:
            if not is_dataclass(self):
                raise NotImplementedError(
                    f"Class '{type(self).__name__}' is not a dataclass, and alternative method failed, "
                    f"so it must provide its own implementation of 'to_json'.\nException: {ex}"
                )
            else:
                raise Exception(
                    f"Unexpected exception occurred while invoking '{type(self).__name__}.to_json' on @dataclass.\n"
                    f"Exception: {ex}"
                )
