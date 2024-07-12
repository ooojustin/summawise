from typing import List, Optional
from dataclasses import dataclass, asdict
from . import utils
from .errors import MultipleAssistantsFoundException

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

class AssistantList(List[Assistant]):

    def to_dict_list(self) -> List[dict]:
        return [a.to_dict() for a in self]

    def list_by_name(self, name: str) -> List[Assistant]:
        return [assistant for assistant in self if assistant.name == name]

    def get_by_name(self, name: str, default: Optional[Assistant] = None) -> Optional[Assistant]:
        assistants = self.list_by_name(name)
        if len(assistants) == 0:
            return default
        if len(assistants) > 1:
            raise MultipleAssistantsFoundException("name", name)
        return assistants[0]

TranscriptAnalyzer: Assistant = Assistant(
    name = "Transcript Analysis Assistant",
    instructions = "You are an assistant that summarizes video transcripts and answers questions about them.",
    file_search = True
)

DEFAULT_ASSISTANTS: List[Assistant] = [TranscriptAnalyzer]
