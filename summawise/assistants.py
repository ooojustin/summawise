from typing import List, Set, Optional
from dataclasses import dataclass, asdict
from . import utils

DEFAULT_MODEL = "gpt-3.5-turbo"

@dataclass
class Assistant:
    name: str
    instructions: str
    model: str = DEFAULT_MODEL
    file_search: bool = False
    interpret_code: bool = False
    respond_with_json: bool = False
    description: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    id: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
    
    def to_create_params(self) -> dict:
        return utils.asdict_exclude(self, {"id"})

TranscriptAnalyzer: Assistant = Assistant(
    name = "Transcript Analysis Assistant",
    instructions = "You are an assistant that summarizes video transcripts and answers questions about them.",
    file_search = True
)

DEFAULT_ASSISTANTS: List[Assistant] = [TranscriptAnalyzer]
