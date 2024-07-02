# Changelog

All notable changes to summawise will be documented in this file.

## [Unreleased]

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
