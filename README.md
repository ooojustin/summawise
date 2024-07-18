# summawise

[![PyPI - Version](https://img.shields.io/pypi/v/summawise?color=00B4FF)](https://pypi.org/project/summawise/)
[![PyPI - License](https://img.shields.io/pypi/l/summawise)](https://github.com/ooojustin/summawise/blob/main/LICENSE)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/summawise)](https://pypi.org/project/summawise/)

Summarize information from files, links, and vectorized data using OpenAI's powerful models. Explore data further and generate code/information using an interactive prompt for deep dives into content.
The beta API features that are built in make it superior to a standard LLM in the context of code generation relative to existing context/codebases.

## Installation

For the sake of convenience (and to be added to your `$PATH`), the program is available via PyPI:

```bash
pip install --upgrade summawise
```

## Notes

This tool uses OpenAI API features which are currently in beta.

**Resources:**

- [Assistants API](https://platform.openai.com/docs/assistants/overview)
- [Threads](https://platform.openai.com/docs/api-reference/threads)
- [Vector Stores](https://platform.openai.com/docs/api-reference/vector-stores)
- [File Search (assistant tool)](https://platform.openai.com/docs/assistants/tools/file-search)
- [Code Interpreter (assistant tool)](https://platform.openai.com/docs/assistants/tools/code-interpreter)

## Information

The following inputs are supported:

- YouTube video URLs. (Transcript is extracted and used as text)
- Local files. (Any type of content, file will be uploaded byte for byte)
- Local directories. (Includes files in nested directories)
- Other URLs, depending on the response content. (Text content, PDF files, and HTML are all supported)

Support for a wider variety of input may be added in the future.

### Potential improvements:

- Archive support (Both URLs and local files - automatically extract/upload contents of `.zip`/`.tar.gz` files)
- Extract natural language from certain types of content. (Ex: html/pdf)
