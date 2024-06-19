import json, ai, youtube, utils
from settings import get_settings

def create_transcript_vector_store(transcript: youtube.Transcript) -> str:
    name = f"transcript_{transcript.video_id}"
    transcript_path = utils.get_summawise_dir() / "youtube" / f"{name}.json"
    content_path = transcript_path.with_suffix(".txt")
    utils.write_file(content_path, str(transcript))
    vector_store = ai.create_vector_store(name, [content_path])
    utils.write_file(transcript_path, json.dumps({ 
        "vector_store_id": vector_store.id, 
        "content": str(transcript) 
    }))
    content_path.unlink()
    print(f"Vector store created with ID: {vector_store.id}")
    return vector_store.id

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
        name = f"transcript_{video_id}"
        transcript_path = utils.get_summawise_dir() / "youtube" / f"{name}.json"
        if not transcript_path.exists():
            vector_store_id = create_transcript_vector_store(transcript)
        else:
            json_str = utils.read_file(transcript_path)
            transcript_data = json.loads(json_str)
            vector_store_id = transcript_data.get("vector_store_id") 
            if vector_store_id is None:
                vector_store_id = create_transcript_vector_store(transcript)
            else:
                print(f"Restored vector store ID from cache: {vector_store_id}")

    except Exception as e:
        print(f"Error creating vector store: {e}")
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
