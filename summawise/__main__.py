import ai, youtube, validators, requests, tempfile, os
from settings import init_settings
from utils import DataUnit
from pathlib import Path

class NotSupportedError(Exception):
    def __init__(self, append: str = ""):
        msg = "Failed to vectorize data. Your input is not yet supported" + (": " if append else ".")
        msg += (": " if append else ".") + append
        super().__init__(msg)

def process_dir(dir_path: Path, delete: bool = True) -> str:
    # TODO
    _, _ = dir_path, delete
    raise NotSupportedError()

def process_file(file_path: Path, delete: bool = False) -> str:
    # TODO(justin): 
    # - cache vector store id based on file hash
    # - add archive support (.zip, .tar.gz) - extract, call process_dir
    # - maybe add automatic extraction of text from pdf or html (undecided)
    vector_store = ai.create_vector_store(file_path.stem, [file_path])
    _ = delete and file_path.exists() and file_path.unlink()
    return vector_store.id

def process_url(url: str) -> str:
    if youtube.is_url(url):
        return youtube.process(url)

    extensions = {
        "text/plain": ".txt",
        "application/pdf": ".pdf",
        "text/html": ".html"
    }

    response = requests.head(url, allow_redirects = True)
    response.raise_for_status()

    result_url = response.url
    content_type = response.headers.get("Content-Type", "")

    valid_types = list(extensions.keys())
    for ctype in valid_types:
        if content_type.startswith(ctype):
            content_type = ctype
            break

    if not content_type in valid_types:
        raise NotSupportedError(f"\nUnsupported content type detected from HEAD request: {content_type}")
    
    # send requst to download file from url (stream the data)
    response = requests.get(result_url, stream = True)
    response.raise_for_status()
    
    # create temp file and write chunks of streamed data to disk
    extension = extensions.get(content_type, ".txt")
    temp_file = tempfile.NamedTemporaryFile(suffix = extension, delete = False)
    try:
        temp_file_path = Path(temp_file.name)
        for chunk in response.iter_content(chunk_size = 8 * DataUnit.KB):
            temp_file.write(chunk)
    except Exception as ex:
        raise RuntimeError(f"Failed to write bytes to temporary file: {ex}")
    finally:
        temp_file.close()

    # process the temp file, automatically delete it after
    try:
        result = process_file(temp_file_path, delete = True)
    finally:
        if temp_file_path.exists():
            temp_file_path.unlink()
    return result

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

    try:
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
