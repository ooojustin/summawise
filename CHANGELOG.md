# Changelog

All notable changes to summawise will be documented in this file.

## [Unreleased]

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
