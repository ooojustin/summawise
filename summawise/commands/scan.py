import validators, click, requests, time
from openai.types.beta import VectorStore
from typing import Tuple, Dict, Optional
from prompt_toolkit import prompt
from pathlib import Path
from datetime import datetime, timezone
from click import types as ctypes
from .. import ai, utils
from ..api_objects import Assistant, Thread, CONVERSATION_INITS, ConversationInit
from ..settings import Settings
from ..web import process_url
from ..files.processing import process_file, process_dir
from ..files import cache as FileCache
from ..errors import NotSupportedError
from ..data import DataUnit

@click.command()
@click.argument("user_input", nargs = -1)
@click.option("-tn", "--thread_name", help = "The name of the thread. [Optional: can't be restored if not specified.]", default = "")
@click.option("-sm", "--send_messages", type = ctypes.BOOL, default = "false", help = "Send content directly in messages alongside the VectorStore & FileSearch tool.\nThis increases the API cost, and is recommended to be used alongside saving/restoring threads with the '--thread_name' option for larger amounts of content such as codebases.")
@click.pass_context
def scan(ctx: click.Context, user_input: Tuple[str, ...], thread_name: str, send_messages: bool):
    """Scan and process the given input (URL or file path), and offer an interactive prompt to inquire about the vectorized data."""
    settings = Settings() # type: ignore
    FileCache.init()
    debug = ctx.obj.get("DEBUG", False)

    while True:
        # prompt user for data source if not provided as an argument
        if user_input:
            input_str = "".join(user_input)
        else:
            input_str = prompt("Enter a URL or local file path: ").strip('\'"')

        # invoke process_input func to handle processing of data and retrieve vector store/file id(s)
        try:
            resources = process_input(input_str)
            break
        except NotSupportedError as ex:
            print(ex)
            user_input = ()
            continue
        except (requests.RequestException, requests.HTTPError) as ex:
            print(f"An error occurred while sending a web request to the provided URL: {utils.ex_to_str(ex, include_traceback = debug)}")
            user_input = ()
            continue
        except Exception as ex:
            print(f"An unhandled error occurred while processing input: {utils.ex_to_str(ex, include_traceback = debug)}")
            user_input = ()
            continue

    # make sure the VectorStore ID we got seems correct
    vector_store_id = resources.vector_store_id
    try:
        assert len(vector_store_id) > 0, "empty"
        assert vector_store_id.startswith("vs_"), "invalid format"
    except AssertionError as ex:
        print(f"An unknown occurred while processing input: invalid VectorStore ID: {utils.ex_to_str(ex, include_traceback = debug)}")
        return

    # make sure thread name isn't already taken
    if thread_name:
        # allow user to fix thread name if it's already taken
        thread = settings.threads.get_by_name(thread_name)
        if thread:
            print("The thread name you provided has already been used. Please select a different name.")
            taken_names = [t.name for t in settings.threads]
            thread_name = prompt("Thread name: ", validator = utils.ChoiceValidator(taken_names, is_blacklist = True, invalid_message = "Thread name is already taken.", case_sensitive = False))
            utils.delete_lines(2)

        if not thread_name:
            print("No new thread name provided. Thread will not be saved.")

    if thread_name:
        print(f"Thread will be saved: {thread_name}")

    assistant: Assistant = settings.assistants[0]
    if len(settings.assistants) > 1:
        # list assistant choices, map numeric index to name
        assistant_choices: Dict[int, Assistant] = {}
        for idx, assistant in enumerate(settings.assistants, start = 1):
            assistant_choices[idx] = assistant
            print(f"{idx}) {assistant.name}")

        # prompt user to select assistant 
        choices = list(assistant_choices.keys())
        choice = int(prompt("Select an assistant: ", validator = utils.NumericChoiceValidator(choices)))
        assistant = assistant_choices[choice]

        # remove assistant selection menu, output valid choice
        utils.delete_lines(len(assistant_choices) + 1)
        print(f"Using selected assistant: {assistant.name}")

    # verify vector store validity w/ openai, output some generic info
    processing: bool = True
    vector_store: Optional[VectorStore] = None
    while processing:
        try:
            first_run = vector_store is None
            vector_store = ai.Client.beta.vector_stores.retrieve(vector_store_id) # model dump example: https://pastebin.com/k4fwANdi
            assert vector_store.status != "expired", "VectorStore is expired."

            id, name = vector_store_id, vector_store.name
            total_files = vector_store.file_counts.total
            completed_files = vector_store.file_counts.completed
            pending_files = vector_store.file_counts.in_progress
            processing = vector_store.status != "completed"

            size_str = DataUnit.bytes_to_str(vector_store.usage_bytes)
            info = f"{id} ({name}), {completed_files}/{total_files} file(s), {size_str}"
            if first_run: 
                print(f"Successfully established VectorStore!", end = " ")
                if processing:
                    print(f"Processing data from {pending_files} file(s)...")
                else:
                    print(f"{completed_files}/{total_files} file(s) have already been processed.")

            if processing: 
                time.sleep(2)
                continue

            print(f"VectorStore ready for use. [{info}]")
        except Exception as ex:
            print(f"Failed to validate VectorStore from provided ID ({vector_store_id}): {utils.ex_to_str(ex, include_traceback = debug)}")
            return

    # create thread for this conversation
    try:
        api_thread = ai.create_thread(
            resources,
            file_search = assistant.file_search,
            code_interpreter = assistant.interpret_code,
            send_messages = send_messages
        )
        print(f"Thread created with ID: {api_thread.id}")
    except Exception as ex:
        print(f"Error creating thread: {utils.ex_to_str(ex, include_traceback = debug)}")
        return

    # create internal representation of the thread (simplified)
    thread = Thread(
        id = api_thread.id, 
        name = thread_name,
        assistant = (assistant.name, assistant.id),
        created_at = datetime.fromtimestamp(api_thread.created_at, timezone.utc) 
    )

    # saved thread if a name was provided to identify it (so it can be restored later)
    if len(thread.name):
        settings.threads.append(thread)
        settings.save()

    # initialize the conversation with a summary
    try:
        default_ci = ConversationInit(
            user_msg = "Generating summary of content...",
            gpt_msg = "Please identify what the provided content is and provide a summary."
        )
        ci = CONVERSATION_INITS.get(assistant, default_ci)
        print(ci.user_msg)
        ai.get_thread_response(thread.id, assistant.id, ci.gpt_msg, auto_print = True)
    except Exception as ex:
        print(f"Error initializing conversation: {utils.ex_to_str(ex, include_traceback = debug)}")
        return
    
    print("\nYou can now ask questions about the content. Type 'exit' to quit.")
    while True:
        input_str = prompt("\nyou > ")
        utils.conditional_exit(input_str)
        try:
            ai.get_thread_response(thread.id, assistant.id, input_str, auto_print = True)
        except Exception as ex:
            print(f"\nError occurred during conversation: {utils.ex_to_str(ex, include_traceback = debug)}")

def process_input(user_input: str) -> ai.Resources:
    """Takes user input, attempts to return OpenAI VectorStore ID after processing data."""
    utils.conditional_exit(user_input)

    path = Path(user_input)
    if path.exists():
        if path.is_file():
            return process_file(path)
        elif path.is_dir():
            return process_dir(path)

    if validators.url(user_input):
        return process_url(user_input)

    raise NotSupportedError()
