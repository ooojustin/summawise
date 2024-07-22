import warnings
from typing import Dict, List, Optional, TypeVar, NamedTuple, Iterable
from datetime import datetime, timezone
from dataclasses import dataclass, field
from .. import utils
from .generic import ApiObjList, BaseApiObj
from ..data import HashAlg
from openai.types.beta import Assistant as APIAssistant

T = TypeVar('T')

DEFAULT_MODEL = "gpt-3.5-turbo"

@dataclass
class Assistant(BaseApiObj):
    id: str = ""
    name: str = ""
    instructions: str = ""
    model: str = DEFAULT_MODEL
    file_search: bool = False
    interpret_code: bool = False
    respond_with_json: bool = False
    description: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    created_at: datetime = field(default_factory = utils.utc_now)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Assistant):
            return NotImplemented
        return (
            self.name == other.name and 
            self.instructions == other.instructions
        )

    def __hash__(self) -> int:
        strval = f"{self.name}\n{self.instructions}"
        hashval = HashAlg.XXH_64.calculate(strval, intdigest = True)
        return int(hashval)

    def __post_init__(self):
        missing_field_warning = lambda x: warnings.warn(f"'Assistant' object is missing expected field {x}.\nThis field should always be provided.", UserWarning)
        if not self.name: missing_field_warning("name")
        if not self.instructions: missing_field_warning("instructions")

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

class AssistantList(ApiObjList[Assistant]):

    def __init__(self, assistants: Iterable[Assistant] = [], **kwargs):
        super().__init__(assistants, cls = Assistant, **kwargs)

    @staticmethod
    def from_dict_list(assistants: Iterable[Assistant], **kwargs) -> "AssistantList": # type: ignore
        return ApiObjList.from_dict_list(assistants, cls = Assistant, **kwargs) # type: ignore

class ConversationInit(NamedTuple):
    user_msg: str
    gpt_msg: str

TranscriptAnalyzer: Assistant = Assistant(
    name = "Transcript Analysis Assistant",
    instructions = "You are an assistant that summarizes video transcripts and answers questions about them.",
    file_search = True
)

CodingAssistant: Assistant = Assistant(
    name = "Coding Assistant",
    instructions = (
        "You are an assistant which helps users by generating, debugging, and optimizing code snippets.\n"
        "It provides clear, well-commented code along with explanations to aid user understanding.\n"
        "\nGeneral Guidelines\n"
        "1.) Understand the Request: Ensure you fully understand the users requirements. Ask clarifying questions if needed.\n"
        "2.) Simplicity and Clarity: Provide simple, clean, and well-documented code. Avoid overly complex solutions unless explicitly requested.\n"\
        "3.) Explain the Code: Always include a brief explanation of the code to help the user understand how it works.\n"
        "4.) Best Practices: Follow coding best practices and conventions for the relevant programming language.\n"
        "5.) Error Handling: Include error handling where appropriate to make the code robust.\n"
        "6.) Modularity: Write modular code with functions or classes to enhance readability and reusability.\n"
        "\nCode Generation Steps\n"
        "1.) Identify the Language: Confirm the programming language to be used (e.g., Python, JavaScript, etc.).\n"
        "2.) Gather Requirements: Understand the specific functionality or problem the user needs the code to address.\n"
        "3.) Write the Code: Generate the code snippet or full program.\n"
        "4.) Comment the Code: Add comments to explain key parts of the code.\n"
        "5.) Provide Explanation: Write a brief explanation of what the code does and how it works.\n"
        "6.) Optimize: If applicable, suggest optimizations or improvements."
    ),
    file_search = True,
    interpret_code = True
)

CONVERSATION_INITS: Dict[Assistant, ConversationInit] = {
    TranscriptAnalyzer: ConversationInit(
        "Generating summary of transcript...", 
        "Please summarize the transcript."
    ),
    CodingAssistant: ConversationInit(
        "Generating summary of codebase...", 
        "Please summarize the codebase."
    )
}

DEFAULT_ASSISTANTS: List[Assistant] = list(CONVERSATION_INITS.keys())
