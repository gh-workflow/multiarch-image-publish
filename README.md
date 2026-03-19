# multiarch-image-publish

[![Release](https://img.shields.io/github/v/release/gh-workflow/multiarch-image-publish?style=flat-square)](https://github.com/gh-workflow/multiarch-image-publish/releases)
[![Tests](https://img.shields.io/github/actions/workflow/status/gh-workflow/multiarch-image-publish/test-suite.yml?branch=main&label=test&style=flat-square)](https://github.com/gh-workflow/multiarch-image-publish/actions/workflows/test-suite.yml)

Publish a signed multi-arch container image from pre-built per-architecture
images.

Build and test each architecture in your workflow, then use this action to:

- publish per-platform tags such as `v1.2.3-amd64`
- publish the final multi-arch tags such as `v1.2.3` and `latest`
- sign and verify the platform images and final manifest
- verify provenance on the signed architecture images

The built images are passed to the action as `platform=digest` entries.

## Usage

```yaml
- name: Publish multi-arch image
  id: publish
  uses: gh-workflow/multiarch-image-publish@8e1cd7ed6d945ab406211187e9582237d2700ac4  # 0.0.4
  with:
    image_ref: ghcr.io/acme/my-image
    tags: |
      ${{ github.ref_name }}
      latest
    platform_digests: |
      linux/amd64=sha256:...
      linux/arm64=sha256:...
```

For each requested tag, the action publishes:

- the multi-arch tag, for example `v1.2.3`
- a tag on each arch image, for example `v1.2.3-amd64` or `v1.2.3-arm64`

## Inputs

| Name | Required | Description |
| --- | --- | --- |
| `image_ref` | yes | Image reference, for example `ghcr.io/acme/my-image`. |
| `tags` | yes | Newline-separated tags to publish. |
| `platform_digests` | yes | Newline-separated `platform=digest` entries. |
| `certificate_oidc_issuer` | no | Expected issuer for cosign verification. |

## Outputs

| Name | Description |
| --- | --- |
| `manifest_digest` | Published multi-arch manifest digest. |

## Requirements

- registry login already performed in the publishing job
- `id-token: write` for keyless `cosign` signing
- `packages: write` for GHCR registries

## Examples

- [.github/workflows/example.yml](.github/workflows/example.yml)
- [.github/workflows/example-non-matrix.yml](.github/workflows/example-non-matrix.yml)
