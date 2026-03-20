# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.6] - 2026-03-20

### Changed

- Refined the README quickstart and usage guidance to make the example workflow easier to copy, customize, and
  understand.
- Simplified the end-to-end workflow by reusing the example publish workflow.

### Internal

- Added a release-time check that requires action references to match the tag currently being released.

## [0.0.5] - 2026-03-20

### Fixed

- Delayed publication of final per-platform tags until after the multi-arch manifest has been published, signed,
  and verified to avoid partial releases when manifest validation fails.

### Internal

- Expanded unit test coverage for registry operations, including manifest inspection errors, platform digest
  resolution failures, attestation resolution, provenance validation, and empty manifest publish results.

## [0.0.3] - 2026-03-19

### Changed

- Reworked the README to be shorter, clearer, and focused on actual action usage.
- Added pinned example workflows for matrix and non-matrix usage under `.github/workflows`.
- Updated action references after the repository rename to `multiarch-image-publish`.

## [0.0.2] - 2026-03-19

### Changed

- Simplified the release workflow by removing custom release tarball packaging and checksum signing.

## [0.0.1] - 2026-03-18

### Added

- Initial public release of the `multiarch-image-publish` GitHub Action.
- Support for publishing a multi-arch manifest from already-built per-platform image digests.
- Cosign signing and verification for per-platform image digests and the final multi-arch manifest digest.
- Provenance presence verification on signed per-platform image digests before final publication.
- Publication of per-platform tags and final multi-arch tags from newline-separated `tags` and
  `platform_digests` inputs.

### Internal

- Rewrote the action implementation in Python and kept the internal module surface private-prefixed.
- Added repository standards, linting, and test workflows, including an end-to-end workflow that exercises the
  action against real multi-architecture images in GHCR.
