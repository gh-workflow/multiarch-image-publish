"""Action entrypoint that reads env vars and orchestrates the publishing flow."""

import os
import sys
from typing import NoReturn

from multiarch_publish._errors import CommandError, InputError
from multiarch_publish._github_output import write_output
from multiarch_publish._input_parser import (
    caller_certificate_identity_regexp,
    parse_annotations,
    parse_platform_digests,
    parse_tags,
)
from multiarch_publish._models import PlatformDigest
from multiarch_publish._registry_ops import (
    publish_final_tags,
    publish_manifest_by_digest,
    publish_platform_tags,
    resolve_platform_verification_digests,
    sign_and_verify_manifest,
    sign_and_verify_platform_image,
)


def _fail(message: str) -> NoReturn:
    """Exit with a concise user-facing error."""
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(1)


def _require_env(name: str) -> str:
    """Read a required environment variable."""
    value = os.environ.get(name, "")
    if value == "":
        raise InputError(f"missing required environment variable {name}")
    return value


def _run_action() -> str:
    """Execute the publishing flow and return the final manifest digest."""
    image_ref = _require_env("INPUT_IMAGE_REF")
    tags = parse_tags(_require_env("INPUT_TAGS"))
    entries = parse_platform_digests(_require_env("INPUT_PLATFORM_DIGESTS"))
    annotations = parse_annotations(os.environ.get("INPUT_ANNOTATIONS", ""))
    certificate_oidc_issuer = _require_env("INPUT_CERTIFICATE_OIDC_ISSUER")
    repository = _require_env("GITHUB_REPOSITORY")

    certificate_identity_regexp = caller_certificate_identity_regexp(repository)
    manifest_entries: list[PlatformDigest] = []

    for entry in entries:
        verification_digests = resolve_platform_verification_digests(image_ref, entry)
        manifest_entries.append(
            PlatformDigest(entry.platform, verification_digests.platform_digest)
        )
        sign_and_verify_platform_image(
            image_ref=image_ref,
            index_digest=entry.digest,
            digests=verification_digests,
            certificate_oidc_issuer=certificate_oidc_issuer,
            certificate_identity_regexp=certificate_identity_regexp,
        )

    manifest_digest = publish_manifest_by_digest(
        image_ref,
        manifest_entries,
        annotations=annotations,
    )
    sign_and_verify_manifest(
        image_ref=image_ref,
        manifest_digest=manifest_digest,
        certificate_oidc_issuer=certificate_oidc_issuer,
        certificate_identity_regexp=certificate_identity_regexp,
    )
    for entry in entries:
        publish_platform_tags(
            image_ref=image_ref,
            index_digest=entry.digest,
            tag_suffix=entry.platform.tag_suffix,
            tags=tags,
        )
    publish_final_tags(image_ref, manifest_digest, tags)

    write_output("manifest_digest", manifest_digest)
    return manifest_digest


def main() -> int:
    """CLI entrypoint used by the GitHub Action."""
    try:
        _run_action()
    except (InputError, CommandError) as exc:
        _fail(str(exc))
    return 0
