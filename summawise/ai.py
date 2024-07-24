import json, textwrap
from typing_extensions import override
from typing import List, Optional, NamedTuple, Dict, Set
from pathlib import Path
from dataclasses import dataclass, field
from openai import OpenAI, AssistantEventHandler
from openai.types.file_object import FileObject
from openai.types.beta import Thread, Assistant, VectorStore 
from openai.types.beta.threads import TextContentBlock, TextDelta, Message, Text
from openai.types.beta.threads.runs import ToolCall, ToolCallDelta
from openai.types.beta.thread_create_params import ToolResources, Message as TCPMessage
from prompt_toolkit import ANSI, HTML, print_formatted_text as print
from pygments.formatters import Terminal256Formatter
from .files.cache import FileCacheObj
from .files import utils as FileUtils
from .settings import Settings
from . import utils

Client: OpenAI
FileCache: FileCacheObj

@dataclass
class Resources:
    vector_store_ids: List[str] = field(default_factory = list)
    file_ids: List[str] = field(default_factory = list)
    file_contents: Dict[Path, str] = field(default_factory = dict)

    @property
    def vector_store_id(self):
        if not len(self.vector_store_ids):
            raise ValueError("Resources object has no vector store id.")
        elif len(self.vector_store_ids) > 1:
            raise ValueError("Resources object has more than 1 vector store id associated with it.")
        return self.vector_store_ids[0]

class EventHandler(AssistantEventHandler):

    auto_print: bool
    response_text: str

    _tool_calls: Dict[str, ToolCall]
    _completed_tool_calls: Set[str]

    def __init__(self, auto_print: bool = False):
        self.auto_print = auto_print
        self.response_text = ""

        self._tool_calls = dict()
        self._completed_tool_calls = set()

        super().__init__()

    @override
    def on_text_created(self, text: Text) -> None:
        _ = text
        if self.auto_print: 
            print("\nsummawise > ", end = "", flush = True)

    @override
    def on_text_delta(self, delta: TextDelta, snapshot: Text) -> None:
        _ = snapshot
        if self.auto_print: 
            print(delta.value, end = "", flush = True)

    @override
    def on_message_done(self, message: Message) -> None:
        print(flush = True) # new line
        for content in message.content:
            # other possibilities: ImageFileContentBlock, ImageURLContentBlock
            if isinstance(content, TextContentBlock):
                self.response_text += content.text.value

    @override
    def on_tool_call_created(self, tool_call: ToolCall):
        if self.tool_call_completed(tool_call):
            return

        if self.auto_print:
            print(flush = True)
            print(HTML(f"Tool call created: <b><ansiblue>{tool_call.type}</ansiblue> <i>[ID: {tool_call.id}]</i></b>"), flush = True)

    @override
    def on_tool_call_delta(self, delta: ToolCallDelta, snapshot: ToolCall) -> None:
        if self.tool_call_completed(snapshot):
            return

        if delta.type == "code_interpreter" and delta.code_interpreter:
            if self.auto_print: 
                print(delta.code_interpreter.input or "", end = "", flush = True)

    @override
    def on_tool_call_done(self, tool_call: ToolCall) -> None:
        if self.tool_call_completed(tool_call, True):
            return

        if not self.auto_print:
            return

        if tool_call.type == "code_interpreter":
            self.syntax_highlight_code_interpreter(tool_call)

        print(HTML(f"Tool call completed: <b><ansiblue>{tool_call.type}</ansiblue> <i>[ID: {tool_call.id}]</i></b>"), flush = True)

    def tool_call_completed(self, tool_call: ToolCall, completed: bool = False) -> bool:
        """
        Updates the state of a ToolCall stored in the EventHandler based on its id.

        Parameters:
            tool_call (ToolCall): The ToolCall object to update the state for.
            completed (bool): Indicates whether the tool call has been completed upon this call. Default is False.

        Returns:
            completed (bool): Indicates whether or not the tool call has already been completed previously.

        Invoke on the following funcs:
        - on_tool_call_created: set_tool_call(tool_call)
        - on_tool_call_delta: set_tool_call(snapshot)
        - on_tool_call_done: set_tool_call(tool_call, True)
        """
        if tool_call.id in self._completed_tool_calls:
            # already maked as completed, return early
            return True

        # update object based on id
        self._tool_calls[tool_call.id] = tool_call

        # conditionally mark as completed
        if completed:
            self._completed_tool_calls.add(tool_call.id)

        # NOTE(justin): this func only returns True if the tool_call was marked as completed *prior* to the current invokation
        return False
    
    def syntax_highlight_code_interpreter(self, tool_call: ToolCall) -> None:
        assert tool_call.type == "code_interpreter"
        settings = Settings() # type: ignore
        code_str = tool_call.code_interpreter.input
        if not code_str.endswith("\n"):
            print(flush = True)
        code_lines = len(code_str.splitlines())
        utils.delete_lines(code_lines)
        formatter = Terminal256Formatter(style = settings.code_style)
        highlighted_code = utils.highlight_code(code_str, formatter = formatter)
        print(ANSI(highlighted_code), end = "", flush = True)

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

    global Client
    if "Client" in globals():
        if Client.api_key == api_key:
            return
    
    Client = OpenAI(api_key = api_key)
    if verify:
        Client.models.list()

class FileInfo(NamedTuple):
    hash: str
    file_id: str
    cached: bool = False

def create_file(file_path: Path) -> FileObject:
    with open(file_path, 'rb') as file:
        file_response = Client.files.create(file = file, purpose = "assistants")
        return file_response

def get_file_infos(files: List[Path]) -> List[FileInfo]:
    file_infos: List[FileInfo] = []
    for file_path in files:

        hash = utils.calculate_hash(file_path)
        assert isinstance(hash, str), \
            "Calculated hash should be of type 'str'. Ensure the 'intdigest' parameter is set to false."

        file_id = FileCache.get_file_id_by_hash(hash)
        if file_id is None:
            # not cached, upload new file
            file = create_file(file_path)
            info = FileInfo(hash, file.id,)
            file_infos.append(info)
            FileCache.set_hash_file_id(hash, file.id)
        else:
            # use cached file id
            info = FileInfo(hash, file_id, True)
            file_infos.append(info)

    FileCache.save()
    return file_infos

def create_vector_store_from_file_ids(name: str, file_ids: List[str]) -> VectorStore:
    return Client.beta.vector_stores.create(name = name, file_ids = file_ids)

def create_vector_store(name: str, file_paths: List[Path]) -> Resources:
    print(f"Creating vector store with {len(file_paths)} file(s).", end = " ")
    file_infos = get_file_infos(file_paths)
    file_ids = [info.file_id for info in file_infos]
    file_contents = {fp: FileUtils.read_str(fp) for fp in file_paths}

    cached_count = sum(1 for info in file_infos if info.cached)
    print(f"[{cached_count} file(s) already cached]" if cached_count > 0 else "")

    vector_store = create_vector_store_from_file_ids(name, file_ids)
    return Resources([vector_store.id], file_ids, file_contents)

def create_assistant(
    model: str,
    name: str, 
    instructions: str, 
    file_search: bool = False,
    interpret_code: bool = False,
    respond_with_json: bool = False,
    description: Optional[str] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None
) -> Assistant:
    tools = []
    if file_search:
        tools.append({"type": "file_search"})
    if interpret_code:
        tools.append({"type": "code_interpreter"})
    response_format = { "type": "json_object" } if respond_with_json else "auto"
    assistant = Client.beta.assistants.create(
        model = model,
        name = name,
        instructions = instructions,
        tools = tools,
        description = description,
        metadata = { 
            "created_by": utils.package_name(),
            "version": str(utils.get_version()),
        },
        top_p = top_p,
        temperature = temperature,
        response_format = response_format, # type: ignore
    )
    return assistant

def get_assistant(id: str) -> Assistant:
    return Client.beta.assistants.retrieve(id)

def get_thread(id: str) -> Thread:
    return Client.beta.threads.retrieve(id)

def create_thread(resources: Resources, file_search: bool = False, code_interpreter: bool = False, send_messages: bool = False) -> Thread:
    # https://platform.openai.com/docs/api-reference/threads/createThread#threads-createthread-tool_resources

    messages: List[TCPMessage] = []
    if send_messages:
        msg = TCPMessage(
            role = "user",
            content = textwrap.dedent(f"""
            The following {len(resources.file_contents)} messages will contain a file path, and the contents of the file.
            This information will be provided in the following json schema:
            {{
                'path': "file path",
                'contents': "file contents"
            }}
            This information will be used throughout the duration of the conversation.
        """))
        messages.append(msg)

        for path, content in resources.file_contents.items():
            content_obj = {
                "path": str(path),
                "content": content
            }
            content = json.dumps(content_obj)
            if len(content) > 256000:
                # print(f"Skipping content of file {path.name}, as it exceeds the maximum length.")
                continue
            msg = TCPMessage(content = content, role = "user")
            messages.append(msg)

    tool_resources = ToolResources(
        file_search = {"vector_store_ids": resources.vector_store_ids}, 
        # code_interpreter = {"file_ids": file_ids}
    )

    if not file_search:
        del tool_resources["file_search"]
    if not code_interpreter:
        del tool_resources["code_interpreter"]

    return Client.beta.threads.create(messages = messages, tool_resources = tool_resources)

def get_thread_response(thread_id: str, assistant_id: str, prompt: str, auto_print: bool = False) -> str:
    Client.beta.threads.messages.create(thread_id = thread_id, content = prompt, role = "user")

    event_handler = EventHandler(auto_print = auto_print)
    with Client.beta.threads.runs.stream(
        thread_id = thread_id,
        assistant_id = assistant_id,
        event_handler = event_handler
    ) as stream:
        stream.until_done()

    return event_handler.response_text

def set_file_cache(file_cache: FileCacheObj):
    global FileCache
    FileCache = file_cache
