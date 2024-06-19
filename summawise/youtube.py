import re
from datetime import timedelta
from typing import List
from youtube_transcript_api import YouTubeTranscriptApi

class TranscriptEntry:

    def __init__(self, text: str, start: float, duration: float):
        self.text = text
        self.start = start
        self.duration = duration

    def __str__(self):
        start_time = str(timedelta(seconds=self.start))
        return f"{start_time} {self.text}"

class Transcript:

    def __init__(self, entries: List[TranscriptEntry]):
        self.entries = entries

    def __str__(self):
        return "\n".join(str(entry) for entry in self.entries)

def get_transcript(video_id: str) -> Transcript:
    transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
    entries = [TranscriptEntry(**entry) for entry in transcript_data]
    return Transcript(entries)

def parse_video_id(url: str) -> str:
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, url)
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid YouTube video URL")
