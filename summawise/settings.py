import json
from dataclasses import dataclass, asdict, fields
from typing import Dict, Any, ClassVar
from openai import AuthenticationError, BadRequestError
from . import utils, ai
from .utils import Singleton
from .data import DataMode
from .files import utils as FileUtils

@dataclass
class Settings(metaclass = Singleton):
    api_key: str
    assistant_id: str
    model: str
    compression: bool
    data_mode: DataMode

    DEFAULT_MODEL: ClassVar[str] = "gpt-3.5-turbo"
    DEFAULT_COMPRESSION: ClassVar[bool] = True
    DEFAULT_DATA_MODE: ClassVar[DataMode] = DataMode.BIN

    # NOTE(justin): This class functions as a singleton. Example usage anywhere:
    # settings = Settings() # type: ignore (dismiss warnings related to required arguments)
    # print(settings.to_dict()) # contains info established in main()

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Settings":
        return Settings(
            model = data.pop("model", Settings.DEFAULT_MODEL),
            compression = data.pop("compression", Settings.DEFAULT_COMPRESSION),
            data_mode = DataMode(data.pop("data_mode", Settings.DEFAULT_DATA_MODE.value)),
            **data
        )

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["data_mode"] = self.data_mode.value
        return data

def init_settings() -> Settings:
    settings_file = utils.get_summawise_dir() / "settings.json"
    if settings_file.exists():
        s_str = FileUtils.read_str(settings_file)
        s_dict = json.loads(s_str)
        settings = Settings.from_dict(s_dict)
        save = len(s_dict) != len(fields(Settings))
    else:
        settings = prompt_for_settings()
        save = True

    if save:
        s_str = json.dumps(settings.to_dict(), indent = 4)
        FileUtils.write_str(settings_file, s_str)

    return settings

def prompt_for_settings() -> Settings:
    while True:
        api_key = input("Enter your OpenAI API key: ")
        try:
            ai.init(api_key)
            break
        except AuthenticationError:
            print("The API key you entered is invalid. Try again.")
            continue

    while True:
        try:
            model = input(f"Enter the OpenAI model to use [Default: {Settings.DEFAULT_MODEL}]: ")
            assistant = ai.create_assistant(model or Settings.DEFAULT_MODEL)
            break
        except BadRequestError as ex:
            if ex.code == "model_not_found":
                print("The model identifier you entered is invalid. Try again.")
                continue
            raise ex

    # TODO(justin): maybe add ability to select data mode. possibly a cli option to re-configure settings too.
    # it's not too important, for now it'll default to binary and can be changed manually.

    return Settings(
        api_key = api_key, 
        model = model, 
        assistant_id = assistant.id,
        data_mode = Settings.DEFAULT_DATA_MODE,
        compression = Settings.DEFAULT_COMPRESSION
    )
