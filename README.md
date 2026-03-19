# multiarch-image-publish

Reusable GitHub Action for publishing multi-arch container images with signature and provenance verification.

This action is intended for workflows that already built and tested architecture-specific images and now want to:

- resolve platform digests for the provided image indexes
- sign and verify the per-arch images with cosign
- confirm provenance is present on the signed image digests
- publish architecture-specific tags
- publish a multi-arch manifest by digest
- sign and verify the final multi-arch manifest
- publish final tags for the multi-arch image

For each provided tag, the action publishes:

- `${tag}-<platform suffix>`
- `${tag}`

For example:

- `linux/amd64` becomes `${tag}-amd64`
- `linux/arm/v7` becomes `${tag}-arm-v7`

The action runs in the caller workflow context. That keeps OIDC-based signing
identity anchored to the calling repository and workflow instead of a shared
reusable workflow repository.

## Inputs

| Name | Required | Description |
| --- | --- | --- |
| `image_ref` | yes | Full image reference, for example `ghcr.io/acme/my-image`. |
| `tags` | yes | Newline-separated list of tags to publish. |
| `platform_digests` | yes | Newline-separated list of `platform=digest` entries, for example
`linux/amd64=sha256:...`. |
| `certificate_oidc_issuer` | no | Expected OIDC issuer for cosign verification. Default:
`https://token.actions.githubusercontent.com`. |

## Outputs

| Name | Description |
| --- | --- |
| `manifest_digest` | Published multi-arch manifest digest. |

## Requirements

- `packages: write`
- `id-token: write`
- `contents: read`
- Docker Buildx available on the runner
- Registry login already performed in the job
- Python 3 available on the runner

If your runner does not already have Docker Buildx configured, set it up earlier in the workflow.

## Example

```yaml
name: Build Image

on:
  push:
    tags:
      - "*"

permissions:
  contents: read
  packages: write
  id-token: write

jobs:
  build-amd64:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - uses: docker/setup-buildx-action@v4
        with:
          driver: docker-container

      - name: Build image
        id: build
        uses: docker/build-push-action@v7
        with:
          context: .
          push: true
          provenance: true
          platforms: linux/amd64
          tags: ghcr.io/acme/my-image:${{ github.sha }}-amd64-test

    outputs:
      digest: ${{ steps.build.outputs.digest }}

  build-arm64:
    runs-on: ubuntu-24.04-arm
    steps:
      - uses: actions/checkout@v6

      - uses: docker/setup-buildx-action@v4
        with:
          driver: docker-container

      - name: Build image
        id: build
        uses: docker/build-push-action@v7
        with:
          context: .
          push: true
          provenance: true
          platforms: linux/arm64
          tags: ghcr.io/acme/my-image:${{ github.sha }}-arm64-test

    outputs:
      digest: ${{ steps.build.outputs.digest }}

  multiarch:
    name: Publish multi-arch image
    needs:
      - build-amd64
      - build-arm64
    runs-on: ubuntu-latest
    steps:
      - name: Log in to registry
        uses: docker/login-action@v4
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - uses: docker/setup-buildx-action@v4
        with:
          driver: docker-container

      - name: Publish signed multi-arch image
        id: publish
        uses: gh-workflow/multiarch-image-publish@v1
        with:
          image_ref: ghcr.io/acme/my-image
          tags: |
            ${{ github.ref_name }}
            latest
          platform_digests: |
            linux/amd64=${{ needs.build-amd64.outputs.digest }}
            linux/arm64=${{ needs.build-arm64.outputs.digest }}
```

## Notes

- This action assumes your per-architecture builds already pushed images and emitted their digests.
- This action assumes the job is already logged in to the target registry.
- Signature verification is bound to workflows in the calling repository.
- The action accepts one or more `platform=digest` entries.
