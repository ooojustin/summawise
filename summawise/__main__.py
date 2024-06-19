import ai, youtube, utils
from settings import get_settings

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
    
    name = f"transcript_{video_id}"
    transcript_path = utils.get_summawise_dir() / "youtube" / f"{name}.json"
    if not transcript_path.exists():
        # fetch transcript data from youtube
        try:
            transcript = youtube.get_transcript(video_id)
            print("Transcript retrieved and converted to text.")
        except Exception as e:
            print(f"Error retrieving transcript ({type(e).__name__}): {e}")
            return
        
        # create vector store on openai, cache data
        try:
            vector_store_id = transcript.vectorize().id
            transcript.save_to_file(transcript_path)
            print(f"Vector store created with ID: {vector_store_id}")
        except Exception as e:
            print(f"Error creating vector store: {e}")
            return
    else:
        # restore transcript object from file and use cached vector store id
        json_str = utils.read_file(transcript_path)
        transcript = youtube.Transcript.from_json(json_str)
        vector_store_id = transcript.vector_store_id
        print(f"Restored vector store ID from cache: {transcript.vector_store_id}")

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
