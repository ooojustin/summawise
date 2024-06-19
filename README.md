# summawise
Summarize information from vectorized file(s) via OpenAI, and use an interactive prompt to dig deeper.

(Currently only supports YouTube video transcripts - see [disclaimer](https://github.com/ooojustin/summawise?tab=readme-ov-file#disclaimer) for more info)

## Notes

This tool uses OpenAI API features which are currently in beta.

**Resources:**
- [Assistants API](https://platform.openai.com/docs/assistants/overview)
- [Threads](https://platform.openai.com/docs/api-reference/threads)
- [Vector Stores](https://platform.openai.com/docs/api-reference/vector-stores)
- [File Search (assistant "tool")](https://platform.openai.com/docs/assistants/tools/file-search)

## Disclaimer

As of the repository being made public, it currently only supports YouTube videos (provide a URL, and it'll allow you to ask questions about the transcript) but the intention is to support other use cases in the future. 

Examples include:
- Books (input could be a large `.pdf` or `.txt` file)
- Codebases (input could be a local directory, archives such as `.zip` files, or a repository URL)
