"""Parsing and validation for action inputs."""

import re

from multiarch_publish._errors import InputError
from multiarch_publish._models import Platform, PlatformDigest


def _parse_required_multiline(raw_value: str, field_name: str) -> list[str]:
    """Parse a required multiline input and reject empty lines."""
    if raw_value == "":
        raise InputError(f"{field_name} input must not be empty")

    lines = raw_value.splitlines()
    if not lines:
        raise InputError(f"{field_name} input must not be empty")

    for line in lines:
        if line == "":
            raise InputError(f"{field_name} must not contain empty lines")

    return lines


def parse_tags(raw_value: str) -> list[str]:
    """Parse the newline-separated tag list."""
    return _parse_required_multiline(raw_value, "tags")


def parse_platform_digests(raw_value: str) -> list[PlatformDigest]:
    """Parse newline-separated platform=digest entries."""
    entries = _parse_required_multiline(raw_value, "platform_digests")
    parsed: list[PlatformDigest] = []

    for entry in entries:
        if "=" not in entry:
            raise InputError(
                f"invalid platform_digests entry '{entry}': expected 'platform=digest'"
            )

        platform_text, digest = entry.split("=", 1)
        if platform_text == "" or digest == "":
            raise InputError(
                f"invalid platform_digests entry '{entry}': platform and digest must both be non-empty"
            )

        parsed.append(PlatformDigest(platform=Platform.parse(platform_text), digest=digest))

    return parsed


def parse_annotations(raw_value: str) -> dict[str, str]:
    """Parse optional newline-separated key=value annotation entries."""
    if raw_value == "":
        return {}

    entries = _parse_required_multiline(raw_value, "annotations")
    annotations: dict[str, str] = {}

    for entry in entries:
        if "=" not in entry:
            raise InputError(
                f"invalid annotations entry '{entry}': expected 'key=value'"
            )

        key, value = entry.split("=", 1)
        if key == "":
            raise InputError(
                f"invalid annotations entry '{entry}': key must be non-empty"
            )
        if key in annotations:
            raise InputError(
                f"invalid annotations entry '{entry}': duplicate key '{key}'"
            )
        annotations[key] = value

    return annotations


def caller_certificate_identity_regexp(repository: str) -> str:
    """Build the default cosign identity regexp for caller workflows."""
    escaped_repo = re.escape(repository)
    return (
        "^https://github\\.com/"
        f"{escaped_repo}"
        "/\\.github/workflows/.*@(?:refs/.*/.*|[0-9a-f]{{40}})$"
    )
