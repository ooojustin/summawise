from typing_extensions import override
from typing import Optional, List, NamedTuple
from pathlib import Path
from openai import OpenAI, AssistantEventHandler
from openai.types.file_object import FileObject
from openai.types.beta import Thread, Assistant, VectorStore 
from openai.types.beta.threads import TextContentBlock, TextDelta, Message, Text
from openai.types.beta.threads.runs import ToolCall
from . import utils
from .files import utils as FileUtils
from .files.cache import FileCacheObj

client: OpenAI
FileCache: FileCacheObj

class EventHandler(AssistantEventHandler):

    def __init__(self, auto_print: bool = False):
        super().__init__()
        self.auto_print = auto_print
        self.response_text = ""

    @override
    def on_text_created(self, text: Text) -> None:
        _ = text
        if self.auto_print: print("\nsummawise > ", end = "", flush = True)

    @override
    def on_text_delta(self, delta: TextDelta, snapshot: Text) -> None:
        _ = snapshot
        if self.auto_print: print(delta.value, end = "", flush = True)

    @override
    def on_tool_call_created(self, tool_call: ToolCall):
        _ = tool_call

    @override
    def on_message_done(self, message: Message) -> None:
        print() # new line
        for content in message.content:
            # other possibilities: ImageFileContentBlock, ImageURLContentBlock
            if isinstance(content, TextContentBlock):
                self.response_text += content.text.value

def init(api_key: str, verify: bool = True):
    """
    Initializes the OpenAI client with the provided API key.

    Parameters:
        api_key (str): The API key to initialize the OpenAI API client with.
        verify (bool): Verify the API key by making a test request to the API. Default is True.

    Raises:
        ValueError: If the API key is not provided or is not a string.
        openai.AuthenticationError: If the API key is invalid or the verification request fails.
    """
    if not api_key or not isinstance(api_key, str):
        raise ValueError("API key must be a non-empty string.")
    
    global client
    client = OpenAI(api_key = api_key)
    
    if verify:
        client.models.list()

class FileInfo(NamedTuple):
    hash: str
    file_id: str
    file: Optional[FileObject] = None

    @property
    def cached(self):
        return self.file is not None

def create_file(file_path: Path) -> FileObject:
    with open(file_path, 'rb') as file:
        file_response = client.files.create(file = file, purpose = "assistants")
        return file_response

def get_file_infos(files: List[Path]) -> List[FileInfo]:
    file_infos: List[FileInfo] = []
    for file_path in files:
        hash = FileUtils.calculate_hash(file_path)
        file_id = FileCache.get_file_id_by_hash(hash)
        if file_id is None:
            # not cached, upload new file
            file = create_file(file_path)
            info = FileInfo(hash, file.id, file)
            file_infos.append(info)
            FileCache.set_hash_file_id(hash, file.id)
        else:
            # use cached file id
            info = FileInfo(hash, file_id)
            file_infos.append(info)
    FileCache.save()
    return file_infos

def create_vector_store(name: str, file_paths: List[Path]) -> VectorStore:
    file_infos = get_file_infos(file_paths)
    file_ids = [info.file_id for info in file_infos]

    cached_count = sum(1 for info in file_infos if info.cached)
    msg = f"Creating vector store with {len(file_infos)} file(s)."
    if cached_count > 0:
        msg += f" ({cached_count} are already cached)"

    vector_store = client.beta.vector_stores.create(name = name, file_ids = file_ids)
    return vector_store

def create_assistant(model: str) -> Assistant:
    # TODO(justin): more generic instructions, since this program is for more than just video transcripts
    assistant = client.beta.assistants.create(
        name = "Transcript Analysis Assistant",
        instructions = "You are an assistant that summarizes video transcripts and answers questions about them.",
        model = model,
        tools = [{"type": "file_search"}],
    )
    return assistant

def create_thread(vector_store_ids: List[str], question: str) -> Thread:
    thread = client.beta.threads.create(
        messages = [{"role": "user", "content": question}],
        tool_resources = {"file_search": {"vector_store_ids": vector_store_ids}}
    )
    return thread

def get_thread_response(thread_id: str, assistant_id: str, prompt: str, auto_print: bool = False) -> str:
    client.beta.threads.messages.create(thread_id = thread_id, content = prompt, role = "user")

    event_handler = EventHandler(auto_print = auto_print)
    with client.beta.threads.runs.stream(
        thread_id = thread_id,
        assistant_id = assistant_id,
        event_handler = event_handler
    ) as stream:
        stream.until_done()

    return event_handler.response_text

def set_file_cache(file_cache: FileCacheObj):
    global FileCache
    FileCache = file_cache
