import click
from click import types as ctypes
from typing import Optional
from .. import ai
from ..api_objects import Assistant
from ..settings import Settings
from ..data import HashAlg

@click.group()
def assistant():
    """Commands related to managing assistants."""
    pass

@assistant.command()
def list():
    """List your available assistants."""
    settings = Settings() # type: ignore
    for idx, assistant in enumerate(settings.assistants, start = 1):
        print(f"{idx}) {assistant.name}")

@assistant.command()
@click.option("-n", "--name", prompt = True, help = "The name of the assistant.")
@click.option("-i", "--instructions", prompt = True, help = "Instructions for the assistant.")
@click.option("-m", "--model", default = None, help = "The model to use.")
@click.option("-d", "--description", default = None, help = "Description of the assistant.")
@click.option("-fs", "--file_search", type = ctypes.BOOL, default = "true", help = "Enable or disable file search capability. [Enabled by default.]")
@click.option("-ic", "--interpret_code", type = ctypes.BOOL, default = "false", help = "Enable or disable code interpretation capability. [Disabled by default.]")
@click.option("-rwj", "--respond_with_json", is_flag = True, help = "Responses should be in valid JSON format.")
@click.option("--temperature", default = None, type = float, help = "Temperature setting for the model.")
@click.option("--top_p", default = None, type = float, help = "Top-p setting for the model.")
def create(
    name: str,
    instructions: str,
    file_search: bool,
    interpret_code: bool,
    respond_with_json: bool,
    model: Optional[str],
    description: Optional[str],
    temperature: Optional[float],
    top_p: Optional[float]
) -> None:
    """Create a new assistant."""
    settings = Settings() # type: ignore

    assistant = settings.assistants.get_by_name(name)
    if assistant:
        print("An assistant with that name already exists.")
        return

    model = model or settings.model
    assistant = Assistant(
        model = model,
        name = name,
        instructions = instructions,
        file_search = file_search,
        interpret_code = interpret_code,
        respond_with_json = respond_with_json,
        description = description,
        temperature = temperature,
        top_p = top_p
    )

    api_assistant = ai.create_assistant(**assistant.to_create_params())
    assistant.apply_api_obj(api_assistant)
    settings.assistants.append(assistant)
    settings.save()

    print(f"Your new assistant has been created successfully.\nName: {name}\nID: {assistant.id}")
    return

@assistant.command()
@click.argument("assistant_id", type = str)
def delete(assistant_id: str):
    """
    Delete an assistant.\n
    Provided ID can be the assistant name, id, or number from 'list'.
    """
    settings = Settings() # type: ignore

    assistant, idx = settings.assistants.get(assistant_id)
    if not assistant:
        print("Failed to identify assistant to delete.")
        return

    del settings.assistants[idx]
    settings.save()
    print(f"Deleted assistant successfully: {assistant.name}")
    
@assistant.command(hidden = True)
@click.argument("assistant_id", type = str)
def hash(assistant_id: str):
    settings = Settings() # type: ignore

    assistant, _ = settings.assistants.get(assistant_id)
    if not assistant:
        print("Failed to identify assistant to delete.")
        return

    instructions_hash = HashAlg.XXH_64.calculate(assistant.instructions)
    print(f"Instructions hash: {instructions_hash}")
