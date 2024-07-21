import click
from ..settings import Settings

@click.group()
def thread():
    """Commands related to managing threads."""
    pass

@thread.command()
def list():
    """List your available threads."""
    settings = Settings() # type: ignore
    for idx, thread in enumerate(settings.threads, start = 1):
        print(f"{idx}) {thread.name}")


@thread.command()
@click.argument("thread_id", type = str)
def delete(thread_id: str):
    """
    Delete a thread.\n
    Provided ID can be the thread name, id, or number from 'list'.
    """
    settings = Settings() # type: ignore

    thread, idx = settings.threads.get(thread_id)
    if not thread:
        print("Failed to identify thread to delete.")
        return

    del settings.threads[idx]
    settings.save()
    print(f"Deleted thread successfully: {thread.name}")

