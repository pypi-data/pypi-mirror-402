# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.4] - 2026-01-21

### Added
- Submodel $value retrieval helpers at the repository level
- Sync wrapper for async operation invocation on submodel elements
- types-PyYAML for dev mypy runs

### Fixed
- CLI aligned with endpoint method names and pagination result shape
- AASX CLI uses package download/upload entrypoints consistently
- Discovery CLI maps to discovery endpoint APIs

## [0.1.3] - 2026-01-21

### Added
- Submodel element helpers for $metadata, $reference, and $path
- Async operation status/result helpers
- Discovery unlink for specific asset identifiers

## [0.1.2] - 2026-01-21

### Added
- TestPyPI prerelease for trusted publisher verification
- GHCR Docker image publishing workflow

## [0.1.1] - 2026-01-21

### Added
- Root-level SubmodelElement creation helpers
- Canonical $value serialization for booleans, datetimes, bytes, and enums
- Configurable encoding toggles for Discovery assetIds and AASX package IDs
- Expanded unit coverage for edge cases and async helpers

### Fixed
- Update endpoints now refetch on 204 No Content responses
- Examples aligned with Docker compose base URLs

## [0.1.0] - 2025-01-22

### Added
- Initial project structure
- Core encoding utilities for base64url identifiers and idShortPath
- Exception hierarchy for typed error handling
- Authentication support (Bearer, Basic, OAuth2, certificates)
- Serialization bridge for BaSyx model objects
- AAS Repository endpoint
- Submodel Repository endpoint with element access
- Concept Description endpoint
- AAS Registry endpoint
- Submodel Registry endpoint
- AASX Server endpoint
- Discovery endpoint
- Pagination support with iterators
- Sync and async client support via httpx

[0.1.0]: https://github.com/hadijannat/basyx-client/releases/tag/v0.1.0
[0.1.1]: https://github.com/hadijannat/basyx-client/releases/tag/v0.1.1
[0.1.2]: https://github.com/hadijannat/basyx-client/releases/tag/v0.1.2
[0.1.3]: https://github.com/hadijannat/basyx-client/releases/tag/v0.1.3
[0.1.4]: https://github.com/hadijannat/basyx-client/releases/tag/v0.1.4
