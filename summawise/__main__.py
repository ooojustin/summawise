import tempfile
import ai, youtube, utils
from settings import get_settings
from pathlib import Path

def main():
    settings = get_settings()
    youtube_url = input("Enter a YouTube video URL: ")

    if not hasattr(ai, "client"):
        ai.init(settings.api_key)
    
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
        vector_store = ai.create_vector_store(transcript_path)
        print(f"Vector store created with ID: {vector_store.id}")
    except Exception as e:
        print(f"Error creating vector store: {e}")
        return
    
    try:
        thread = ai.create_thread([vector_store.id], "Please summarize the transcript.")
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
