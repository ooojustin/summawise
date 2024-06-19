from typing import List
from pathlib import Path
from openai import OpenAI
from openai.types.beta import Thread, Assistant, VectorStore 

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
