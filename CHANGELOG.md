# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
