import click
from typing import Dict
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
@click.argument("name", type = str)
def add(name: str):
    """Create a new assistant."""
    # TODO(justin): implement the logic to create an assistant
    print(f"summawise 'assistant add' not yet implemented. (name: {name})")

@assistant.command()
@click.argument("assistant_id", type = str)
def delete(assistant_id: str):
    """Delete an assistant."""
    # TODO(justin): implement the logic to delete an assistant
    print(f"summawise 'assistant delete' not yet implemented. (id: {assistant_id})")
