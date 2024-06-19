import json, tempfile
import ai, youtube, utils
from typing import Tuple
from pathlib import Path
from openai import OpenAI

DEFAULT_MODEL = "gpt-3.5-turbo"

def establish_settings() -> Tuple[str, str]:
    temp_dir = Path(tempfile.gettempdir())
    settings_file = temp_dir / "summawise.json"
    
    if settings_file.exists():
        data_str = utils.read_file(settings_file)
        data = json.loads(data_str)
        api_key = data.get("key")
        model = data.get("model", DEFAULT_MODEL)
        return api_key, model
    else:
        api_key = input("Enter your OpenAI API key: ")
        model = input(f"Enter the OpenAI model to use [Default: {DEFAULT_MODEL}]: ") or DEFAULT_MODEL
        settings = { 
            "key": api_key, 
            "model": model 
        }
        utils.write_file(settings_file, json.dumps(settings))
        return api_key, model

def main():
    youtube_url = input("Enter a YouTube video URL: ")
    openai_api_key, model = establish_settings()
    client = OpenAI(api_key = openai_api_key)
    
    # get youtube video id
    try:
        video_id = youtube.parse_video_id(youtube_url)
        print(f"Extracted Video ID: {video_id}")
    except ValueError as e:
        print(e)
        return
    
    # get transcript from youtube video
    try:
        transcript = youtube.get_transcript(video_id)
        print("Transcript retrieved and converted to text.")
    except Exception as e:
        print(f"Error retrieving transcript: {e}")
        return
    
    # save transcript to file, create vector store from it
    try:
        temp_dir = Path(tempfile.gettempdir())
        transcript_path = temp_dir / f"transcript_{video_id}.txt"
        utils.write_file(transcript_path, str(transcript))
        vector_store = ai.create_vector_store(client, transcript_path)
        print(f"Vector store created with ID: {vector_store.id}")
    except Exception as e:
        print(f"Error creating vector store: {e}")
        return
    
    # initialize assistant
    try:
        # NOTE: this assistant is will be configured for transcript summarization/analysis by default
        assistant = ai.create_assistant(client, [vector_store.id], model)
        print(f"Assistant created with ID: {assistant.id}")
    except Exception as e:
        print(f"Error creating assistant: {e}")
        return
    
    try:
        thread = ai.create_thread(client, [vector_store.id], "Please summarize the transcript.")
        print(f"Thread created with ID: {thread.id}")
        print("Generating summary...")
        ai.get_thread_response(client, thread.id, assistant.id, "Please summarize the transcript.", auto_print = True)
    except Exception as e:
        print(f"Error generating summary: {e}")
        return
    
    print("\nYou can now ask questions about the transcript. Type 'exit' to quit.")
    while True:
        user_input = input("\nyou > ")
        if user_input.lower() == "exit":
            break
        try:
            ai.get_thread_response(client, thread.id, assistant.id, user_input, auto_print = True)
        except Exception as e:
            print(f"Error in chat: {e}")

if __name__ == "__main__":
    main()
