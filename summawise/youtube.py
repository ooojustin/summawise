import json, re
from datetime import timedelta
from typing import List
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi
from . import utils, ai
from .data import DataMode
from .files import utils as FileUtils
from .serializable import Serializable
from .settings import Settings

class TranscriptEntry:

    def __init__(self, text: str, start: float, duration: float):
        self.text = text
        self.start = start
        self.duration = duration

    def __str__(self):
        start_time = str(timedelta(seconds=self.start))
        return f"{start_time} {self.text}"

    def to_dict(self):
        return {
            "text": self.text,
            "start": self.start,
            "duration": self.duration
        }

class Transcript(Serializable):

    def __init__(
        self, 
        video_id: str, 
        entries: List[TranscriptEntry], 
        vector_store_id: str = "",
        vectorize: bool = False
    ):
        self.video_id = video_id
        self.entries = entries
        self.vector_store_id = vector_store_id
        if vectorize and not vector_store_id:
            self.vectorize()

    def __str__(self):
        return "\n".join(str(entry) for entry in self.entries)

    def vectorize(self) -> ai.VectorStore:
        name = f"transcript_{self.video_id}"
        content_path = utils.get_summawise_dir() / "youtube" / f"{name}.txt"
        FileUtils.write_str(content_path, str(self))
        vector_store = ai.create_vector_store(name, [content_path])
        content_path.unlink()
        self.vector_store_id = vector_store.id
        return vector_store

    def to_json(self, pretty: bool = False) -> str:
        return json.dumps({ 
            "video_id": self.video_id,
            "entries": [entry.to_dict() for entry in self.entries],
            "vector_store_id": self.vector_store_id
        }, indent = 4 if pretty else None)

    @classmethod
    def from_json(cls, json_str: str) -> "Transcript":
        data = json.loads(json_str)
        data["entries"] = [TranscriptEntry(**entry) for entry in data.get("entries", [])]
        transcript = cls(**data)
        return transcript

def get_transcript(video_id: str, vectorize: bool = False) -> Transcript:
    transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
    entries = [TranscriptEntry(**entry) for entry in transcript_data]
    return Transcript(video_id, entries, vectorize = vectorize)

def load_transcript(file_path: Path, mode: DataMode = DataMode.JSON) -> Transcript:
    # shortcut to reduce verbosity
    return Transcript.from_file(file_path, mode)

def parse_video_id(url: str) -> str:
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid YouTube video URL")

def is_url(url: str) -> bool:
    pattern = r"(youtu\.be|(?:www\.)?youtube\.com)\/"
    return re.search(pattern, url) is not None

def process_url(url: str) -> str:
    """
    Process a youtube URL as input.
    This function will extract a transcript, handle caching/storage, and return an OpenAI vector store ID.
    """
    # use settings class (singleton)
    settings = Settings() # type: ignore

    # file extension to cache certain objects/data (json or bin)
    ext = settings.data_mode.ext()

    video_id = parse_video_id(url)
    name = f"transcript_{video_id}"
    transcript_path = utils.fp(utils.get_summawise_dir() / "youtube" / f"{name}.{ext}")

    if not transcript_path.exists():
        # fetch transcript data from youtube
        try:
            transcript = get_transcript(video_id)
            print("Transcript retrieved and converted to text.")
        except Exception as e:
            raise Exception(f"Error retrieving transcript ({type(e).__name__}): {e}")
        
        # create vector store on openai, cache data
        try:
            vector_store_id = transcript.vectorize().id
            transcript.save_to_file(
                file_path = transcript_path,
                mode = settings.data_mode,
                compress = settings.compression
            )
            print(f"Vector store created with ID: {vector_store_id}")
        except Exception as ex:
            raise Exception(f"Error creating vector store [{type(ex)}]: {ex}")
    else:
        # restore transcript object from file and use cached vector store id
        transcript = load_transcript(transcript_path, settings.data_mode)
        vector_store_id = transcript.vector_store_id
        print(f"Restored vector store ID from cache: {vector_store_id}")

    return vector_store_id
