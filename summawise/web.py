import requests, tempfile
from pathlib import Path
from . import youtube
from .files.processing import process_file
from .data import DataUnit
from .errors import NotSupportedError

def process_url(url: str) -> str:
    if youtube.is_url(url):
        return youtube.process_url(url)

    extensions = {
        "text/plain": ".txt",
        "application/pdf": ".pdf",
        "text/html": ".html"
    }

    response = requests.head(url, allow_redirects = True)
    response.raise_for_status()

    result_url = response.url
    content_type = response.headers.get("Content-Type", "")

    valid_types = list(extensions.keys())
    for ctype in valid_types:
        if content_type.startswith(ctype):
            content_type = ctype
            break

    if not content_type in valid_types:
        raise NotSupportedError(f"\nUnsupported content type detected from HEAD request: {content_type}")
    
    # send requst to download file from url (stream the data)
    response = requests.get(result_url, stream = True)
    response.raise_for_status()
    
    # create temp file and write chunks of streamed data to disk
    extension = extensions.get(content_type, ".txt")
    temp_file = tempfile.NamedTemporaryFile(suffix = extension, delete = False)
    try:
        temp_file_path = Path(temp_file.name)
        for chunk in response.iter_content(chunk_size = 8 * DataUnit.KB):
            temp_file.write(chunk)
    except Exception as ex:
        raise RuntimeError(f"Failed to write bytes to temporary file: {ex}")
    finally:
        temp_file.close()

    # process the temp file, automatically delete it after
    try:
        result = process_file(temp_file_path, delete = True)
    finally:
        if temp_file_path.exists():
            temp_file_path.unlink()
    return result
