# Changelog

All notable changes to summawise will be documented in this file.

## [Unreleased]

## [0.5.0] - July 24th, 2024

### Added

- Added new "thread" subcommand to allow users to save/restore conversations:
  - Save a thread using the `-tn/--thread_name` option when invoking the `scan` command.
  - List threads using `summawise thread list`
  - Delete threads using `summawise thread delete <id>`
  - Restore a thread using `summawise thread restore <id>`
- New `-sm/--send_messages` option (boolean, defaults to false) will send content in messages when a thread is being created, alongside the attached vector store.

### Changed

- Refactored storage of API oriented objects.
  - Internal representation of Assistants/Threads share a base class (`ApiObjItem`).
  - Generic `ApiObjList` base class abstracts storage/retrieval of a list of `ApiObjItem` objects.

## [0.4.0] - July 18th, 2024

### Added

- Included generic coding assistant by default.
- Officially added support for the code interpreter tool.
- Added syntax highlighting for snippets processed by the code interpreter tool.
  - The code highlighting style is customizable via your config. It defaults to `monokai`, but all [pygments styles](https://pygments.org/styles/) are supported. This will apply to all syntax highlighting in the future.
- Propagate resources necessary for code interpretation to OpenAI API when using assistants which have the functionality enabled.
  - Note: There is a limit of 20 files (per execution, or "Thread") at the time of writing this. [[Code reference]](https://github.com/ooojustin/summawise/blob/95af17fe0ae058d242af27fef8029e08e133fb70/summawise/ai.py#L167-L178)
    I have a few ideas of how to address this, but it is a caveat when working with larger projects for now.
- Add `-v/--version` option to show the version of the package that is currently installed.
- Add `--debug` option for more informative exception messages. (It will include a traceback.)

### Changed

- Default assistants will automatically update based on changes made in newer versions.
- Improve how conversations are initialized based on the assistant being used/type of content.

## [0.3.1] - July 14th, 2024

### Changed

- Enable the `file_search` option by default when creating a new assistant.
- Change the `file_search`/`interpret_code` CLI options passed to the assistant creation command to from flags to [booleans](https://github.com/pallets/click/blob/14f735cf59618941cf2930e633eb77651b1dc7cb/src/click/types.py#L599-L621).

## [0.3.0] - July 13th, 2024

### Added

- Started building out CLI using. The 'scan' command mirrors the original functionality from past versions.
  - You can use the `summawise --help` command to get CLI help, and that functionality is nested. For example, the following commands would also work:
    - `summawise assistant --help`
    - `summawise assistant create --help`
- Added support for multiple assistants. This includes the following commands (as referenced above):
  - `summawise assistant list`
  - `summawise assistant create`
  - `summawise assistant delete`
- Assistants created/managed via this tool mirror the functionality offered by OpenAI's official beta API.

### Changed

- Implemented `prompt_toolkit` library for user prompts to include better completion/validation.
- Refactored certain aspects of codebase to better support CLI based functionality moving forward.

#### Disclaimer

As you may notice with some of the changes in this update, the functionality and intended use cases are growing beyond what the application was originally designed for.
This was ultimately the goal, and is intentional. As a result, this also means the project name _may_ change prior to or with the release of a version 1.0.

## [0.2.3] - July 6th, 2024

### Added

- Support for directories being used as input, storing many files in a vector store.
  - Since I plan on expanding the use cases of this project, it is already designed to support codebases.
- Cache all file IDs based on file hash to be re-used in new vector stores.

### Changed

- Expanded and optimized hash calculation capabilities.

## [0.2.2] - July 1st, 2024

### Added

- Attempt to restore OpenAI API key from environment variable (`OPENAI_API_KEY`) when initializing settings.
- New [CHANGELOG.md](https://github.com/ooojustin/summawise/blob/main/CHANGELOG.md) file to track history of changes.

### Changed

- Switch build system from setuptools to hatchling.

## [0.2.0] - June 26th, 2024

### Added

- Cache vector store for files based on SHA-256 hash.
  This applies to both files stored locally, and the contents of static data downloaded via a remote URL.
- Introduced generic [`Serializable`](https://github.com/ooojustin/summawise/blob/39f478cfe5917e58d08a4a5ac789a6a6bb9fa7ea/summawise/serializable.py#L10-L39) base class, which will be used for any object which would be saved to disk for caching purposes. It's built to support either json encoded data or pickled binary data, depending on the user `DataMode` setting.

### Changed

- A number of refactors to improve separation of concerns. [[PR]](https://github.com/ooojustin/summawise/pull/7)

## [0.1.2] - June 25th, 2024

### Added

- Initial release of project on PyPI.
