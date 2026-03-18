"""Action entrypoint that reads env vars and orchestrates the publishing flow."""

import os
import sys
from typing import NoReturn

from multiarch_publish._errors import CommandError, InputError
from multiarch_publish._github_output import write_output
from multiarch_publish._input_parser import (
    caller_certificate_identity_regexp,
    parse_platform_digests,
    parse_tags,
)
from multiarch_publish._registry_ops import (
    publish_final_tags,
    publish_manifest_by_digest,
    publish_platform_tags,
    resolve_platform_manifest_digest,
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
    certificate_oidc_issuer = _require_env("INPUT_CERTIFICATE_OIDC_ISSUER")
    repository = _require_env("GITHUB_REPOSITORY")

    certificate_identity_regexp = caller_certificate_identity_regexp(repository)

    for entry in entries:
        platform_digest = resolve_platform_manifest_digest(image_ref, entry)
        sign_and_verify_platform_image(
            image_ref=image_ref,
            index_digest=entry.digest,
            platform_digest=platform_digest,
            certificate_oidc_issuer=certificate_oidc_issuer,
            certificate_identity_regexp=certificate_identity_regexp,
        )
        publish_platform_tags(
            image_ref=image_ref,
            index_digest=entry.digest,
            tag_suffix=entry.platform.tag_suffix,
            tags=tags,
        )

    manifest_digest = publish_manifest_by_digest(image_ref, entries)
    sign_and_verify_manifest(
        image_ref=image_ref,
        manifest_digest=manifest_digest,
        certificate_oidc_issuer=certificate_oidc_issuer,
        certificate_identity_regexp=certificate_identity_regexp,
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
