import click
from typing import Optional
from .. import ai
from ..assistants import Assistant
from ..settings import Settings

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
@click.option("-fs", "--file_search", is_flag = True, help = "Enable file search capability.")
@click.option("-ic", "--interpret_code", is_flag = True, help = "Enable code interpretation capability.")
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
    """Delete an assistant."""
    # TODO(justin): implement the logic to delete an assistant
    print(f"summawise 'assistant delete' not yet implemented. (id: {assistant_id})")
