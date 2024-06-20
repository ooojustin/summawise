import ai, youtube, utils, validators
from settings import init_settings

class NotSupportedError(Exception):
    def __init__(self):
        super().__init__("Failed to vectorize data. Your input type is not yet supported.")

def process_input(input_str: str) -> str:
    """Takes user input, attempts to return OpenAI VectorStore ID after processing data."""
    if validators.url(input_str):
        # it's a URL
        url = input_str

        # youtube url handling
        if youtube.is_url(url):
            return youtube.process(url)

    raise NotSupportedError()


def main():
    settings = init_settings()

    if not hasattr(ai, "client"):
        # TODO(justin): handle api key that becomes invalid *after* initial setup prompts
        ai.init(settings.api_key)

    input_str = input("Enter a URL or local file path: ")

    try:
        vector_store_id = process_input(input_str)
    except NotSupportedError as ex:
        print(ex)
        return
    except Exception as ex:
        print(f"An unhandled error occurred while processing input:\n{ex}")
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
