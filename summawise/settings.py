import json, os, copy
from dataclasses import dataclass, fields, field
from typing import Set, Union, Dict, Any, ClassVar
from openai import AuthenticationError, BadRequestError
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from . import utils, ai
from .utils import Singleton
from .data import DataMode
from .files import utils as FileUtils
from .assistants import DEFAULT_ASSISTANTS, DEFAULT_MODEL, Assistant, AssistantList
    
@dataclass
class Settings(metaclass = Singleton):
    api_key: str
    assistant_id: str = field(repr = False) # NOTE(justin): deprecated in version 0.3.0
    assistants: AssistantList
    model: str
    compression: bool
    data_mode: DataMode

    DEFAULT_MODEL: ClassVar[str] = DEFAULT_MODEL
    DEFAULT_COMPRESSION: ClassVar[bool] = True
    DEFAULT_DATA_MODE: ClassVar[DataMode] = DataMode.BIN
    DEPRECATED_FIELDS: ClassVar[Set[str]] = {"assistant_id"}

    # NOTE(justin): This class functions as a singleton. Example usage anywhere:
    # settings = Settings() # type: ignore (dismiss warnings related to required arguments)
    # print(settings.to_dict()) # contains info established in main()

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Settings":
        assistants = data.pop("assistants", [])

        # turn assistant dicts into object oriented representations
        if len(assistants):
            assistants = [Assistant(**obj) for obj in assistants]

        # version 0.3.0 backwards compatability (adding multi-assistant support)
        assistant_id = data.pop("assistant_id", None)
        if assistant_id:
            default_assistant = copy.copy(DEFAULT_ASSISTANTS[0])
            default_assistant.id = assistant_id
            assistants.append(default_assistant)

        return Settings(
            assistant_id = assistant_id,
            assistants = AssistantList(assistants),
            model = data.pop("model", Settings.DEFAULT_MODEL),
            compression = data.pop("compression", Settings.DEFAULT_COMPRESSION),
            data_mode = DataMode(data.pop("data_mode", Settings.DEFAULT_DATA_MODE.value)),
            **data
        )

    def to_dict(self) -> Dict[str, Any]:
        data = utils.asdict_exclude(self, Settings.DEPRECATED_FIELDS)
        # data["assistants"] = {a.name: a.to_dict() for a in self.assistants.values()}
        data["assistants"] = self.assistants.to_dict_list()
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

    # automatically create default assistants added in future versions
    for da in DEFAULT_ASSISTANTS:
        if not settings.assistants.get_by_name(da.name):
            if not hasattr(ai, "Client"):
                ai.init(settings.api_key, verify = False)
            da = copy.copy(da)
            assistant = ai.create_assistant(**da.to_create_params())
            assert assistant.name # NOTE(justin): OpenAI Assistant type has this field as optional, but we require it for identification
            da.id = assistant.id
            settings.assistants.append(da)
            save = True
                
    if save:
        s_str = json.dumps(settings.to_dict(), indent = 4)
        FileUtils.write_str(settings_file, s_str)

    return settings

def prompt_for_settings() -> Settings:
    api_key = os.getenv("OPENAI_API_KEY", "")
    api_key = validate_api_key(api_key)
    
    while api_key is None:
        api_key = prompt("Enter your OpenAI API key: ")
        api_key = validate_api_key(api_key)
        if not api_key:
            print("The API key you entered is invalid. Try again.")

    model_completer = WordCompleter(["gpt-4o", "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"])
    while True:
        try:
            model = prompt(f"Enter the OpenAI model to use [Default: {Settings.DEFAULT_MODEL}]: ", completer = model_completer)
            break
        except BadRequestError as ex:
            if ex.code == "model_not_found":
                print("The model identifier you entered is invalid. Try again.")
                continue
            raise ex

    assistants: AssistantList = AssistantList()
    for da in DEFAULT_ASSISTANTS:
        da = copy.copy(da)
        assistant = ai.create_assistant(**da.to_create_params())
        da.id = assistant.id
        assistants.append(da)

    # TODO(justin): maybe add ability to select data mode. possibly a cli option to re-configure settings too.
    # it's not too important, for now it'll default to binary and can be changed manually.

    return Settings(
        api_key = api_key, 
        model = model, 
        assistant_id = "", # NOTE(justin): deprecated in version 0.3.0
        assistants = assistants,
        data_mode = Settings.DEFAULT_DATA_MODE,
        compression = Settings.DEFAULT_COMPRESSION
    )

def validate_api_key(api_key: str) -> Union[str, None]:
    try:
        ai.init(api_key)
        return api_key
    except AuthenticationError:
        return None
