# summawise

[![PyPI - Version](https://img.shields.io/pypi/v/summawise?style=for-the-badge&color=%23C7FF00)](https://pypi.org/project/summawise/)

Summarize information from vectorized files using OpenAI's powerful models, and explore data further with an interactive prompt for deep dives into content.

## Notes

This tool uses OpenAI API features which are currently in beta.

**Resources:**

- [Assistants API](https://platform.openai.com/docs/assistants/overview)
- [Threads](https://platform.openai.com/docs/api-reference/threads)
- [Vector Stores](https://platform.openai.com/docs/api-reference/vector-stores)
- [File Search (assistant "tool")](https://platform.openai.com/docs/assistants/tools/file-search)

## Information

The following inputs are supported:

- YouTube video URLs. (Transcript is extracted and used as text)
- Local files. (Any type of content, file will be uploaded byte for byte)
- Other URLs, depending on the response content. (Text content, PDF files, and HTML are all supported)

Support for a wider variety of input may be added in the future.

### Potential improvements:

- Directory support (Enter a local directory path, contents are uploaded recursively)
- Archive support (Both URLs and local files - automatically extract/upload contents of `.zip`/`.tar.gz` files)
- VectorStore caching (already supported for youtube videos, the goal is to implement this for all inputs)
- Multiple "assistants" with more intricate instructions, which would be selected based on the type of information being analyzed.
  - A custom assistant can already be used by manually changing the "assistant_id" property in settings file.
- User friendly command line interface.
