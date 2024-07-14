import validators, click, requests, time, sys
from openai.types.beta import VectorStore
from typing import Tuple, Dict, Optional
from prompt_toolkit import prompt
from pathlib import Path
from .. import ai
from ..settings import Settings
from ..assistants import Assistant
from ..web import process_url
from ..files.processing import process_file, process_dir
from ..files import cache as FileCache
from ..errors import NotSupportedError
from ..utils import NumericChoiceValidator, delete_lines
from ..data import DataUnit

@click.command()
@click.argument("user_input", nargs = -1)
def scan(user_input: Tuple[str, ...]):
    """Scan and process the given input (URL or file path), and offer an interactive prompt to inquire about the vectorized data."""
    settings = Settings() # type: ignore
    FileCache.init()

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
            print(f"An error occurred while sending a web request to the provided URL:\n{ex}")
            user_input = ()
            continue
        except Exception as ex:
            print(f"An unhandled error occurred while processing input:\n{ex}")
            user_input = ()
            continue

    # make sure the VectorStore ID we got seems correct
    vector_store_id = resources.vector_store_id
    try:
        assert len(vector_store_id) > 0, "empty"
        assert vector_store_id.startswith("vs_"), "invalid format"
    except AssertionError as ex:
        print(f"An unknown occurred while processing input: invalid VectorStore ID. ({ex})")
        return

    assistant: Assistant = settings.assistants[0]
    if len(settings.assistants) > 1:
        # list assistant choices, map numeric index to name
        assistant_choices: Dict[int, Assistant] = {}
        for idx, assistant in enumerate(settings.assistants, start = 1):
            assistant_choices[idx] = assistant
            print(f"{idx}) {assistant.name}")

        # prompt user to select assistant 
        choice = int(prompt("Select an assistant: ", validator = NumericChoiceValidator(assistant_choices.keys())))
        assistant = assistant_choices[choice]

        # remove assistant selection menu, output valid choice
        delete_lines(len(assistant_choices) + 2)
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
            print(f"Failed to validate VectorStore from provided ID (error: {type(ex)}, id: {vector_store_id}):\n{ex}")
            return

    # create thread for this conversation
    try:
        # TODO(justin): change message used to initialize thread based on type of input data/source
        thread = ai.create_thread(
            resources,
            file_search = assistant.file_search,
            code_interpreter = assistant.interpret_code
        )
        print(f"Thread created with ID: {thread.id}")
        print("Generating summary...")
        ai.get_thread_response(thread.id, assistant.id, "Please summarize the transcript.", auto_print = True)
    except Exception as e:
        print(f"Error generating summary: {e}")
        return
    
    print("\nYou can now ask questions about the transcript. Type 'exit' to quit.")
    while True:
        input_str = prompt("\nyou > ")
        conditional_exit(input_str)
        try:
            ai.get_thread_response(thread.id, assistant.id, input_str, auto_print = True)
        except Exception as e:
            print(f"Error in chat [{type(e)}]: {e}")

def process_input(user_input: str) -> ai.Resources:
    """Takes user input, attempts to return OpenAI VectorStore ID after processing data."""
    conditional_exit(user_input)

    path = Path(user_input)
    if path.exists():
        if path.is_file():
            return process_file(path)
        elif path.is_dir():
            return process_dir(path)

    if validators.url(user_input):
        return process_url(user_input)

    raise NotSupportedError()

def conditional_exit(user_input: str) -> None:
    """Conditionally exit the program based on the users input."""
    if user_input.lower() in ["exit", "quit", ":q"]:
        if user_input == ":q": print("They should call you Vim Diesel.") # NOTE(justin): this is here to stay
        sys.exit()
