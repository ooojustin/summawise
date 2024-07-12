from typing import List, Optional, Iterable, Callable, TypeVar
from datetime import datetime, timezone
from dataclasses import dataclass, asdict, field
from . import utils
from .errors import MultipleAssistantsFoundError, MissingSortKeyError
from openai.types.beta import Assistant as APIAssistant

T = TypeVar('T')

DEFAULT_MODEL = "gpt-3.5-turbo"

@dataclass
class Assistant:
    name: str
    instructions: str
    model: str = DEFAULT_MODEL
    id: str = ""
    file_search: bool = False
    interpret_code: bool = False
    respond_with_json: bool = False
    description: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    created_at: datetime = field(default_factory = utils.utc_now)

    def to_dict(self) -> dict:
        obj = asdict(self)
        return utils.convert_datetimes(obj, converter = utils.converter_ts_int)
    
    def to_create_params(self) -> dict:
        return utils.asdict_exclude(self, {"id", "created_at"})

    def apply_api_obj(self, obj: APIAssistant):
        """Use official library API object to apply/overwrite specific fields to this dataclass."""
        self.id = obj.id
        self.name = obj.name or ""
        self.instructions = obj.instructions or ""
        self.model = obj.model
        self.description = obj.description
        self.top_p = obj.top_p
        self.temperature = obj.temperature
        self.created_at = datetime.fromtimestamp(obj.created_at, timezone.utc)

class AssistantList(List[Assistant]):

    def __init__(
        self, 
        assistants: Iterable[Assistant] = [], 
        sort: bool = False,
        key: Optional[Callable[[Assistant], T]] = None, 
        reverse: bool = False
    ):
        if not sort:
            super().__init__(assistants)
            return

        if not key or not callable(key):
            raise MissingSortKeyError("Can't initialize 'AssistantList' in sorted order without callable key.")

        sorted_assistants = sorted(assistants, key = key, reverse = reverse) # type: ignore
        super().__init__(sorted_assistants)

    def to_dict_list(self) -> List[dict]:
        return [a.to_dict() for a in self]

    def list_by_name(self, name: str) -> List[Assistant]:
        return [assistant for assistant in self if assistant.name == name]

    def get_by_name(self, name: str, default: Optional[Assistant] = None) -> Optional[Assistant]:
        assistants = self.list_by_name(name)
        if len(assistants) == 0:
            return default
        if len(assistants) > 1:
            raise MultipleAssistantsFoundError("name", name)
        return assistants[0]

TranscriptAnalyzer: Assistant = Assistant(
    name = "Transcript Analysis Assistant",
    instructions = "You are an assistant that summarizes video transcripts and answers questions about them.",
    file_search = True
)

DEFAULT_ASSISTANTS: List[Assistant] = [TranscriptAnalyzer]
