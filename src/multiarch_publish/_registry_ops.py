"""Operations that inspect, sign, verify, and publish container images."""

import json

from multiarch_publish._command_runner import run_command
from multiarch_publish._errors import CommandError
from multiarch_publish._models import PlatformDigest


def _inspect_raw_manifest(image_reference: str) -> dict:
    """Return the raw manifest JSON for an image reference."""
    raw_json = run_command(
        ["docker", "buildx", "imagetools", "inspect", "--raw", image_reference]
    )
    try:
        return json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise CommandError(
            f"docker returned invalid JSON for image reference {image_reference}"
        ) from exc


def resolve_platform_manifest_digest(image_ref: str, entry: PlatformDigest) -> str:
    """Resolve the platform-specific manifest digest inside a pushed image index."""
    manifest = _inspect_raw_manifest(f"{image_ref}@{entry.digest}")
    for candidate in manifest.get("manifests", []):
        platform_info = candidate.get("platform", {})
        if platform_info.get("os") != entry.platform.os:
            continue
        if platform_info.get("architecture") != entry.platform.architecture:
            continue

        candidate_variant = platform_info.get("variant")
        if entry.platform.variant is not None and candidate_variant != entry.platform.variant:
            continue

        digest = candidate.get("digest", "")
        if digest:
            return digest

    raise CommandError(
        f"failed to resolve platform digest for {image_ref}@{entry.digest} ({entry.platform})"
    )


def _resolve_attestation_digest(image_reference: str) -> str:
    """Resolve the attestation manifest digest for an image digest."""
    manifest = _inspect_raw_manifest(image_reference)
    for candidate in manifest.get("manifests", []):
        annotations = candidate.get("annotations", {})
        if annotations.get("vnd.docker.reference.type") == "attestation-manifest":
            digest = candidate.get("digest", "")
            if digest:
                return digest

    raise CommandError(f"failed to resolve attestation digest for {image_reference}")


def _verify_attestation_contains_provenance(image_ref: str, attestation_digest: str) -> None:
    """Require the attestation manifest to contain an in-toto provenance predicate."""
    manifest = _inspect_raw_manifest(f"{image_ref}@{attestation_digest}")
    for layer in manifest.get("layers", []):
        annotations = layer.get("annotations", {})
        predicate_type = annotations.get("in-toto.io/predicate-type", "")
        if predicate_type.startswith("https://slsa.dev/provenance/"):
            return

    raise CommandError(
        f"attestation manifest {image_ref}@{attestation_digest} does not contain an in-toto provenance predicate"
    )


def sign_and_verify_platform_image(
    image_ref: str,
    index_digest: str,
    platform_digest: str,
    *,
    certificate_oidc_issuer: str,
    certificate_identity_regexp: str,
) -> None:
    """Sign and verify the pushed index digest and resolved platform manifest digest."""
    index_image = f"{image_ref}@{index_digest}"
    platform_image = f"{image_ref}@{platform_digest}"

    run_command(["cosign", "sign", "--yes", index_image])
    run_command(["cosign", "sign", "--yes", platform_image])

    verify_command = [
        "cosign",
        "verify",
        "--certificate-oidc-issuer",
        certificate_oidc_issuer,
        "--certificate-identity-regexp",
        certificate_identity_regexp,
    ]
    run_command([*verify_command, index_image])
    run_command([*verify_command, platform_image])

    attestation_digest = _resolve_attestation_digest(index_image)
    _verify_attestation_contains_provenance(image_ref, attestation_digest)


def publish_platform_tags(
    image_ref: str, index_digest: str, tag_suffix: str, tags: list[str]
) -> None:
    """Publish one per-platform tag for each requested tag."""
    target = f"{image_ref}@{index_digest}"
    for tag in tags:
        run_command(
            [
                "docker",
                "buildx",
                "imagetools",
                "create",
                "--tag",
                f"{image_ref}:{tag}-{tag_suffix}",
                target,
            ]
        )


def publish_manifest_by_digest(image_ref: str, entries: list[PlatformDigest]) -> str:
    """Publish a multi-platform manifest by digest and return its digest."""
    create_command = [
        "docker",
        "buildx",
        "imagetools",
        "create",
        "--dry-run",
        *[f"{image_ref}@{entry.digest}" for entry in entries],
    ]
    create_output = run_command(create_command)
    digest = run_command(
        [
            "regctl",
            "manifest",
            "put",
            "--by-digest",
            image_ref,
            "--format",
            "{{ ( .Manifest.GetDescriptor ).Digest }}",
        ],
        input_text=create_output,
    ).strip()

    if digest == "":
        raise CommandError(f"failed to publish multi-arch manifest for {image_ref}")
    return digest


def sign_and_verify_manifest(
    image_ref: str,
    manifest_digest: str,
    *,
    certificate_oidc_issuer: str,
    certificate_identity_regexp: str,
) -> None:
    """Sign and verify the final multi-platform manifest."""
    target = f"{image_ref}@{manifest_digest}"
    run_command(["cosign", "sign", "--yes", target])
    run_command(
        [
            "cosign",
            "verify",
            "--certificate-oidc-issuer",
            certificate_oidc_issuer,
            "--certificate-identity-regexp",
            certificate_identity_regexp,
            target,
        ]
    )


def publish_final_tags(image_ref: str, manifest_digest: str, tags: list[str]) -> None:
    """Attach the requested final tags to the multi-platform manifest digest."""
    target = f"{image_ref}@{manifest_digest}"
    for tag in tags:
        run_command(
            [
                "docker",
                "buildx",
                "imagetools",
                "create",
                "--tag",
                f"{image_ref}:{tag}",
                target,
            ]
        )
