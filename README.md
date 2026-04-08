# multiarch-image-publish

[![Release](https://img.shields.io/github/v/release/gh-workflow/multiarch-image-publish?style=flat-square)](https://github.com/gh-workflow/multiarch-image-publish/releases)
[![Immutable Releases](https://img.shields.io/badge/releases-immutable-blue?labelColor=333)](https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/immutable-releases)
[![GitHub Marketplace](https://img.shields.io/badge/marketplace-publish--multiarch--image-blue?logo=github&labelColor=333&style=flat-square)](https://github.com/marketplace/actions/publish-multi-arch-image)
[![Tests](https://img.shields.io/github/actions/workflow/status/gh-workflow/multiarch-image-publish/change-validation.yml?branch=main&label=test&style=flat-square)](https://github.com/gh-workflow/multiarch-image-publish/actions/workflows/change-validation.yml)
[![Multi-Arch](https://img.shields.io/badge/image-multiarch-2496ED?logo=docker&logoColor=white&style=flat-square)](#usage)
[![Cosign](https://img.shields.io/badge/signing-cosign-3EAAAF?logo=sigstore&logoColor=white&style=flat-square)](#usage)

Publish a signed multi-arch container image from pre-built per-architecture images.

Build and test each architecture in your workflow, then use this action to publish the final image.

- multi-arch tags such as `v1.2.3` and `latest`
- per-platform tags such as `v1.2.3-amd64`
- sign and verify the per-platform images and final multi-arch manifest
- verify provenance on the per-platform images before publishing final tags

## Quickstart

To quickly get up and running:

1. Copy the workflow that matches your registry to your default branch:
   - [Example Publish](.github/workflows/example.yml) for GHCR or
   - [Example Publish Docker Hub](.github/workflows/example-dockerhub.yml) for Docker Hub.
2. On GitHub, in your repo's Actions tab, run the copied workflow.

This will publish a demo image package at `ghcr.io/<owner>/<repo-name>-demo`.

> Notes:
>
> - The published package also includes signatures and provenance for the per-platform images.
> - GHCR is recommended for larger or frequently re-run publish jobs because Docker Hub free accounts have pull-rate
>   limits.

### Customize

To now build your projects images, change this in the copied workflow:

1. Step `Build image`: Set `file` to `Dockerfile` (in your repo root)
2. Optional: Update step `Test image` with real tests for your image
3. Update the env variable `IMAGE_REF` to your real image name, for example `ghcr.io/<owner>/<repo-name>`

## Usage

```yaml
- name: Publish MultiArch Image
  id: publish
  uses: gh-workflow/multiarch-image-publish@0.1.6
  with:
    image_ref: ghcr.io/acme/my-image
    tags: |
      ${{ github.ref_name }}
      latest
    platform_digests: |
      linux/amd64=sha256:...
      linux/arm64=sha256:...
    annotations: |
      org.opencontainers.image.source=https://github.com/acme/my-image
      org.opencontainers.image.version=${{ github.ref_name }}
```

`platform_digests` are the pushed per-architecture image digests produced earlier in your workflow.

For each requested tag, the action publishes:

- the multi-arch tag, for example `v1.2.3`
- a tag on each arch image, for example `v1.2.3-amd64` or `v1.2.3-arm64`

The action does not build images for you. It takes already-built per-platform digests, signs and verifies
those images, then publishes the final multi-arch manifest and tags.

## Inputs

| Name                      | Required | Description                                           |
|---------------------------|----------|-------------------------------------------------------|
| `image_ref`               | yes      | Image reference, for example `ghcr.io/acme/my-image`. |
| `tags`                    | yes      | Newline-separated tags to publish.                    |
| `platform_digests`        | yes      | Newline-separated `platform=digest` entries.          |
| `annotations`             | no       | Newline-separated `key=value` manifest annotations.   |
| `certificate_oidc_issuer` | no       | Expected issuer for cosign verification.              |

## Outputs

| Name              | Description                           |
|-------------------|---------------------------------------|
| `manifest_digest` | Published multi-arch manifest digest. |

## Requirements

- registry login already performed in the publishing job
- `id-token: write` for keyless `cosign` signing
- `packages: write` for GHCR registries
- `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets for Docker Hub examples
