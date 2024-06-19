import tempfile
from pathlib import Path

def write_file(file_path: Path, content: str):
    file_path.parent.mkdir(parents = True, exist_ok = True)
    with open(file_path, 'w') as file:
        file.write(content)

def read_file(file_path: Path) -> str:
    with open(file_path, 'r') as file:
        content = file.read()
    return content

def get_summawise_dir() -> Path:
    temp_dir = Path(tempfile.gettempdir())
    return temp_dir / "summawise"

