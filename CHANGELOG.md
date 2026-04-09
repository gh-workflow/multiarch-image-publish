# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.7] - 2026-04-09

### Fixed

- Build the final multi-arch manifest from the original per-arch index digests so SBOM and
  provenance attestations are kept.

## [0.1.6] - 2026-04-08

### Added

- Added optional `annotations` input so callers can attach OCI annotations to the published
  multi-arch manifest.

## [0.1.5] - 2026-03-27

### Changed

- Bumped `sigstore/cosign-installer` from `v4.1.0` to `v4.1.1`.

### Fixed

- Switched release reference verification from `rg -P` to `grep -P`.

## [0.1.4] - 2026-03-27

### Changed

- Removed the README coverage badge and its generation.

## [0.1.3] - 2026-03-26

### Fixed

- Switched the release coverage badge asset from SVG to PNG.

## [0.1.2] - 2026-03-26

### Added

- Added a coverage badge to the README that points at `coverage.svg` from the latest GitHub release.

### Internal

- Generate the coverage badge during the release workflow and upload it as a release asset.
- Added `genbadge` as a development dependency for release-time badge generation.

## [0.1.1] - 2026-03-26

### Fixed

- Corrected the README multiarch badge label.

## [0.1.0] - 2026-03-26

### Changed

- Renamed the action metadata title to `Publish MultiArch Image` and added Marketplace branding.
- Refined the README badge set for release status, Marketplace availability, test status, multi-arch
  publishing, and cosign signing.

### Internal

- Added concurrency cancellation to `change-validation.yml` so superseded validation runs are stopped.

## [0.0.10] - 2026-03-24

### Fixed

- Published multi-arch manifests by digest instead of through a mutable repository tag, preventing concurrent
  action runs from interfering with each other during publication.

### Internal

- Moved repository rule tests into `tests/repo_rules` so repo-level structure and visibility checks are kept
  separate from package-specific tests.
- Emptied package `__init__.py` files in `tests` to keep them marker-only.

## [0.0.9] - 2026-03-21

### Changed

- Cosmetic changes in `README.md`.

## [0.0.8] - 2026-03-20

### Added

- Added `example-main.yml` as a manual-run copy of the main GHCR example workflow.
- Added Docker Hub example workflows for released and main-branch action usage:
  `example-dockerhub.yml` and `example-dockerhub-main.yml`.

### Changed

- Extended the test-suite workflow with drift checks that require each `@main` example workflow to stay aligned
  with its released counterpart aside from the workflow name and action reference.

### Fixed

- Reworked registry operations to avoid `docker buildx imagetools` for manifest inspection and publication,
  using `regctl` and `docker manifest` instead.
- Built final multi-arch manifests from resolved platform manifest digests instead of the original per-platform
  index digests, avoiding manifest-list inputs during final publication.
- Resolved pushed manifest digests with `regctl image digest` instead of parsing `docker manifest push` output.
- Reused each fetched per-platform index manifest for both platform-digest and attestation-digest resolution to
  avoid duplicate registry reads during verification.
- Retried transient `cosign verify` failures when registries briefly report `no signatures found` immediately
  after signing.

## [0.0.7] - 2026-03-20

### Changed

- Run the end-to-end workflow during tagged releases before publishing the GitHub release.

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
