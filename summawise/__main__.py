import validators, requests, time, sys
from openai.types.beta import VectorStore 
from typing import Optional
from pathlib import Path
from . import ai
from .settings import init_settings
from .web import process_url
from .files.processing import process_file, process_dir
from .data import DataUnit
from .errors import NotSupportedError

def main():
    settings = init_settings()

    if not hasattr(ai, "client"):
        # TODO(justin): handle api key that becomes invalid *after* initial setup prompts
        ai.init(settings.api_key)

    while True:
        # prompt user for data source
        user_input = input("Enter a URL or local file path: ").strip('\'"')

        # invoke process_input func to handle processing of data and retrieve VectorStore ID
        try:
            vector_store_id = process_input(user_input)
            break
        except NotSupportedError as ex:
            print(ex)
            continue
        except (requests.RequestException, requests.HTTPError) as ex:
            print(f"An error occurred while sending a web request to the provided URL:\n{ex}")
            continue
        except Exception as ex:
            print(f"An unhandled error occurred while processing input:\n{ex}")
            continue

    # make sure the VectorStore ID we got seems correct
    try:
        assert len(vector_store_id) > 0, "empty"
        assert vector_store_id.startswith("vs_"), "invalid format"
    except AssertionError as ex:
        print(f"An unknown occurred while processing input: invalid VectorStore ID. ({ex})")
        return

    # verify vector store validity w/ openai, output some generic info
    processing: bool = True
    vector_store: Optional[VectorStore] = None
    while processing:
        try:
            first_run = vector_store is None
            vector_store = ai.client.beta.vector_stores.retrieve(vector_store_id) # model dump example: https://pastebin.com/k4fwANdi
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
        thread = ai.create_thread([vector_store_id], "Please summarize the transcript.")
        print(f"Thread created with ID: {thread.id}")
        print("Generating summary...")
        ai.get_thread_response(thread.id, settings.assistant_id, "Please summarize the transcript.", auto_print = True)
    except Exception as e:
        print(f"Error generating summary: {e}")
        return
    
    print("\nYou can now ask questions about the transcript. Type 'exit' to quit.")
    while True:
        user_input = input("\nyou > ")
        conditional_exit(user_input)
        try:
            ai.get_thread_response(thread.id, settings.assistant_id, user_input, auto_print = True)
        except Exception as e:
            print(f"Error in chat: {e}")

def process_input(user_input: str) -> str:
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

if __name__ == "__main__":
    main()
