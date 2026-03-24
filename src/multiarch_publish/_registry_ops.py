"""Operations that inspect, sign, verify, and publish container images."""

import json
import time
from dataclasses import dataclass

from multiarch_publish._command_runner import run_command
from multiarch_publish._errors import CommandError
from multiarch_publish._models import PlatformDigest

_VERIFY_RETRY_ATTEMPTS = 5
_VERIFY_RETRY_DELAY_SECONDS = 5


@dataclass(frozen=True)
class _PlatformVerificationDigests:
    platform_digest: str
    attestation_digest: str


def _run_verify_command(command: list[str]) -> None:
    """Retry transient cosign verification failures caused by registry propagation."""
    last_error: CommandError | None = None
    for attempt in range(_VERIFY_RETRY_ATTEMPTS):
        try:
            run_command(command)
            return
        except CommandError as exc:
            if "no signatures found" not in str(exc):
                raise
            last_error = exc
            if attempt == _VERIFY_RETRY_ATTEMPTS - 1:
                raise
            time.sleep(_VERIFY_RETRY_DELAY_SECONDS)

    if last_error is not None:
        raise last_error


def _inspect_raw_manifest(image_reference: str) -> dict:
    """Return the raw manifest JSON for an image reference."""
    raw_json = run_command(
        ["regctl", "manifest", "get", image_reference, "--format", "raw-body"]
    )
    try:
        return json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise CommandError(
            f"registry returned invalid JSON for image reference {image_reference}"
        ) from exc


def _copy_image(source_ref: str, target_ref: str) -> None:
    """Retag an existing image or index within a repository."""
    run_command(["regctl", "image", "copy", source_ref, target_ref])


def _resolve_platform_manifest_digest(image_ref: str, entry: PlatformDigest) -> str:
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


def resolve_platform_verification_digests(
    image_ref: str, entry: PlatformDigest
) -> _PlatformVerificationDigests:
    """Resolve the platform manifest and attestation digests from one index fetch."""
    manifest = _inspect_raw_manifest(f"{image_ref}@{entry.digest}")
    platform_digest = ""
    attestation_digest = ""

    for candidate in manifest.get("manifests", []):
        annotations = candidate.get("annotations", {})
        if annotations.get("vnd.docker.reference.type") == "attestation-manifest":
            digest = candidate.get("digest", "")
            if digest:
                attestation_digest = digest
            continue

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
            platform_digest = digest

    if platform_digest == "":
        raise CommandError(
            f"failed to resolve platform digest for {image_ref}@{entry.digest} ({entry.platform})"
        )
    if attestation_digest == "":
        raise CommandError(f"failed to resolve attestation digest for {image_ref}@{entry.digest}")

    return _PlatformVerificationDigests(
        platform_digest=platform_digest,
        attestation_digest=attestation_digest,
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
    digests: _PlatformVerificationDigests,
    *,
    certificate_oidc_issuer: str,
    certificate_identity_regexp: str,
) -> None:
    """Sign and verify the pushed index digest and resolved platform manifest digest."""
    index_image = f"{image_ref}@{index_digest}"
    platform_image = f"{image_ref}@{digests.platform_digest}"

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
    _run_verify_command([*verify_command, index_image])
    _run_verify_command([*verify_command, platform_image])

    _verify_attestation_contains_provenance(image_ref, digests.attestation_digest)


def publish_platform_tags(
    image_ref: str, index_digest: str, tag_suffix: str, tags: list[str]
) -> None:
    """Publish one per-platform tag for each requested tag."""
    source_ref = f"{image_ref}@{index_digest}"
    for tag in tags:
        _copy_image(source_ref, f"{image_ref}:{tag}-{tag_suffix}")


def publish_manifest_by_digest(image_ref: str, entries: list[PlatformDigest]) -> str:
    """Publish a multi-platform manifest by digest and return its digest."""
    manifest_json = run_command(
        [
            "docker",
            "buildx",
            "imagetools",
            "create",
            "--dry-run",
            *[f"{image_ref}@{entry.digest}" for entry in entries],
        ]
    )
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
        input_text=manifest_json,
    ).strip()
    if digest:
        return digest
    raise CommandError(f"failed to resolve pushed manifest digest for {image_ref}")


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
    _run_verify_command(
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
    source_ref = f"{image_ref}@{manifest_digest}"
    for tag in tags:
        _copy_image(source_ref, f"{image_ref}:{tag}")
