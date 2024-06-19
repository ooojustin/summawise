from typing_extensions import override
from typing import List
from pathlib import Path
from openai import OpenAI, AssistantEventHandler
from openai.types.beta import Thread, Assistant, VectorStore 
from openai.types.beta.threads import TextContentBlock, TextDelta, Message, Text
from openai.types.beta.threads.runs import ToolCall

class EventHandler(AssistantEventHandler):

    def __init__(self, auto_print: bool = False):
        super().__init__()
        self.auto_print = auto_print
        self.response_text = ""

    @override
    def on_text_created(self, text: Text) -> None:
        _ = text
        _ = self.auto_print and print("\nsummawise > ", end = "", flush = True)

    @override
    def on_text_delta(self, delta: TextDelta, snapshot: Text) -> None:
        _ = snapshot
        _ = self.auto_print and print(delta.value, end = "", flush = True)

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

def create_vector_store(client: OpenAI, file_path: Path) -> VectorStore:
    file_response = client.files.create(file=open(file_path, 'rb'), purpose='assistants')
    file_id = file_response.id
    vector_store = client.beta.vector_stores.create(
        name=f"transcript_{file_path.stem}",
        file_ids=[file_id]
    )
    return vector_store

def create_assistant(client: OpenAI, vector_store_ids: List[str], model: str) -> Assistant:
    assistant = client.beta.assistants.create(
        name="Transcript Analysis Assistant",
        instructions="You are an assistant that summarizes video transcripts and answers questions about them.",
        model=model,
        tools=[{"type": "file_search"}],
        tool_resources={"file_search": {"vector_store_ids": vector_store_ids}}
    )
    return assistant

def create_thread(client: OpenAI, vector_store_ids: List[str], question: str) -> Thread:
    thread = client.beta.threads.create(
        messages=[{"role": "user", "content": question}],
        tool_resources={"file_search": {"vector_store_ids": vector_store_ids}}
    )
    return thread

def get_thread_response(client: OpenAI, thread_id: str, assistant_id: str, prompt: str, auto_print: bool = False) -> str:
    client.beta.threads.messages.create(thread_id = thread_id, content = prompt, role = "user")

    event_handler = EventHandler(auto_print = auto_print)
    with client.beta.threads.runs.stream(
        thread_id = thread_id,
        assistant_id = assistant_id,
        event_handler = event_handler
    ) as stream:
        stream.until_done()

    return event_handler.response_text
