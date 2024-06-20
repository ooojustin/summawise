import json, re, utils, ai
from utils import FileUtils
from settings import DataMode
from datetime import timedelta
from typing import List
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi

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

class Transcript:

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

    def to_json(self, pretty: bool = False) -> str:
        return json.dumps({ 
            "video_id": self.video_id,
            "entries": [entry.to_dict() for entry in self.entries],
            "vector_store_id": self.vector_store_id
        }, indent = 4 if pretty else None)

    def save_to_file(self, file_path: Path, mode: DataMode = DataMode.JSON, compress: bool = False):
        if mode == DataMode.JSON:
            json_str = self.to_json()
            FileUtils.write_str(file_path, json_str, compress)
        elif mode == DataMode.BIN:
            FileUtils.save_object(file_path, self, compress)

    @staticmethod
    def from_file(file_path: Path, mode: DataMode = DataMode.JSON) -> "Transcript":
        if mode == DataMode.JSON:
            json_str = FileUtils.read_str(file_path)
            return Transcript.from_json(json_str)
        elif mode == DataMode.BIN:
            return FileUtils.load_object(file_path, Transcript)

    @staticmethod
    def from_json(json_str: str) -> "Transcript":
        data = json.loads(json_str)
        data["entries"] = [TranscriptEntry(**entry) for entry in data.get("entries", [])]
        transcript = Transcript(**data)
        return transcript

    def vectorize(self) -> ai.VectorStore:
        name = f"transcript_{self.video_id}"
        content_path = utils.get_summawise_dir() / "youtube" / f"{name}.txt"
        FileUtils.write_str(content_path, str(self))
        vector_store = ai.create_vector_store(name, [content_path])
        content_path.unlink()
        self.vector_store_id = vector_store.id
        return vector_store

def get_transcript(video_id: str, vectorize: bool = False) -> Transcript:
    transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
    entries = [TranscriptEntry(**entry) for entry in transcript_data]
    return Transcript(video_id, entries, vectorize = vectorize)

def load_transcript(file_path: Path, mode: DataMode = DataMode.JSON) -> Transcript:
    # shortcut to reduce verbosity
    return Transcript.from_file(file_path, mode)

def parse_video_id(url: str) -> str:
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, url)
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid YouTube video URL")
