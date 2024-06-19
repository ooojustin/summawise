import json, utils, ai
from dataclasses import dataclass, field, asdict
from pathlib import Path
from openai import AuthenticationError, BadRequestError

DEFAULT_MODEL = "gpt-3.5-turbo"

@dataclass
class Settings:
    api_key: str
    assistant_id: str
    model: str = field(default=DEFAULT_MODEL)

def get_settings() -> Settings:
    settings_file = utils.get_summawise_dir() / "settings.json"
    
    if settings_file.exists():
        data_str = utils.read_file(settings_file)
        data = json.loads(data_str)
        settings = Settings(**data)
    else:
        settings = prompt_for_settings()
        utils.write_file(settings_file, json.dumps(asdict(settings)))

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
                model = input(f"Enter the OpenAI model to use [Default: {DEFAULT_MODEL}]: ") or DEFAULT_MODEL
                assistant = ai.create_assistant(model)
                break
            except BadRequestError as ex:
                if ex.code == "model_not_found":
                    print("The model identifier you entered is invalid. Try again.")
                    continue
                raise ex

        return Settings(
            api_key = api_key, 
            model = model, 
            assistant_id = assistant.id
        )

