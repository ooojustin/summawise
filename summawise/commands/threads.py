import click
from prompt_toolkit import prompt
from .. import ai, utils
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

@thread.command()
@click.argument("thread_id", type = str)
@click.pass_context
def restore(ctx: click.Context, thread_id: str):
    """Restore a saved thread from its latest state."""
    settings = Settings() # type: ignore
    debug = ctx.obj.get("DEBUG", False)

    thread, _ = settings.threads.get(thread_id)
    if not thread:
        print("No thread found matching provided identifier.")
        return

    assistant_name, assistant_id = thread.assistant
    assistant, _ = settings.assistants.get(assistant_name)
    if assistant is not None:
        assistant_id = assistant.id

    # get a summary of where the conversation (aka "thread") left off
    try:
        ai.get_thread_response(thread.id, assistant_id, "Please summarize our conversation thus far.", auto_print = True)
    except Exception as ex:
        print(f"Error initializing conversation: {utils.ex_to_str(ex, include_traceback = debug)}")
        return
    
    # resume interactive prompt (from scan command) with restored thread
    print("\nYou can now continue to ask questions about the content. Type 'exit' to quit.")
    while True:
        input_str = prompt("\nyou > ")
        utils.conditional_exit(input_str)
        try:
            ai.get_thread_response(thread.id, assistant_id, input_str, auto_print = True)
        except Exception as ex:
            print(f"\nError occurred during conversation: {utils.ex_to_str(ex, include_traceback = debug)}")
