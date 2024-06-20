import ai, validators, requests
from settings import init_settings
from web import process_url
from filesystem import process_file, process_dir
from utils import DataUnit
from pathlib import Path
from errors import NotSupportedError

def process_input(input_str: str) -> str:
    """Takes user input, attempts to return OpenAI VectorStore ID after processing data."""
    path = Path(input_str)
    if path.exists():
        if path.is_file():
            return process_file(path)
        elif path.is_dir():
            return process_dir(path)

    if validators.url(input_str):
        return process_url(input_str)

    raise NotSupportedError()

def main():
    settings = init_settings()

    if not hasattr(ai, "client"):
        # TODO(justin): handle api key that becomes invalid *after* initial setup prompts
        ai.init(settings.api_key)

    while True:
        # prompt user for data source
        input_str = input("Enter a URL or local file path: ")
        input_str = input_str.strip('\'"')

        # handle early exit prompts
        if input_str.lower() in ["exit", "quit", ":q"]:
            _ = input_str == ":q" and print("They should call you Vim Diesel.") # NOTE(justin): this is here to stay
            return

        # invoke process_input func to get VectorStore ID after data is processed
        try:
            vector_store_id = process_input(input_str)
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
    try:
        vector_store = ai.client.beta.vector_stores.retrieve(vector_store_id) # model dump example: https://pastebin.com/k4fwANdi
        name = vector_store.name
        files = vector_store.file_counts.total
        sz = DataUnit.bytes_to_str(vector_store.usage_bytes)
        print(f"Successfully established vector store! [{name}, {files} file(s), {sz}]")
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
        if user_input.lower() == "exit":
            break
        try:
            ai.get_thread_response(thread.id, settings.assistant_id, user_input, auto_print = True)
        except Exception as e:
            print(f"Error in chat: {e}")

if __name__ == "__main__":
    main()
