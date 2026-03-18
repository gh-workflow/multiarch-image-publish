"""Structured data types used by the action."""

from dataclasses import dataclass

from multiarch_publish._errors import InputError

_PLATFORM_MIN_PARTS = 2


@dataclass(frozen=True)
class Platform:
    """A target container platform such as linux/amd64 or linux/arm/v7."""

    os: str
    architecture: str
    variant: str | None = None

    @classmethod
    def parse(cls, text: str) -> "Platform":
        parts = text.split("/")
        if len(parts) < _PLATFORM_MIN_PARTS:
            raise InputError(
                f"invalid platform '{text}': expected os/arch or os/arch/variant"
            )

        os_name = parts[0]
        architecture = parts[1]
        variant = "/".join(parts[2:]) or None

        if not os_name or not architecture:
            raise InputError(
                f"invalid platform '{text}': os and architecture must both be set"
            )

        return cls(os=os_name, architecture=architecture, variant=variant)

    def __str__(self) -> str:
        if self.variant:
            return f"{self.os}/{self.architecture}/{self.variant}"
        return f"{self.os}/{self.architecture}"

    @property
    def tag_suffix(self) -> str:
        parts = [self.architecture]
        if self.variant:
            parts.extend(self.variant.split("/"))
        return "-".join(parts)


@dataclass(frozen=True)
class PlatformDigest:
    """A platform and the pushed image digest that corresponds to it."""

    platform: Platform
    digest: str
