import unittest
from unittest.mock import patch

from multiarch_publish._models import Platform, PlatformDigest
from multiarch_publish._registry_ops import (
    publish_final_tags,
    publish_manifest_by_digest,
    publish_platform_tags,
    resolve_platform_manifest_digest,
    sign_and_verify_manifest,
    sign_and_verify_platform_image,
)


class RegistryOpsTests(unittest.TestCase):
    def test_resolve_platform_manifest_digest_returns_matching_digest(self) -> None:
        entry = PlatformDigest(
            platform=Platform(os="linux", architecture="arm", variant="v7"),
            digest="sha256:index",
        )
        manifest = {
            "manifests": [
                {
                    "platform": {"os": "linux", "architecture": "amd64"},
                    "digest": "sha256:other",
                },
                {
                    "platform": {"os": "linux", "architecture": "arm", "variant": "v7"},
                    "digest": "sha256:match",
                },
            ]
        }

        with patch(
            "multiarch_publish._registry_ops._inspect_raw_manifest",
            return_value=manifest,
        ):
            digest = resolve_platform_manifest_digest("ghcr.io/acme/test", entry)

        self.assertEqual(digest, "sha256:match")

    def test_publish_manifest_by_digest_returns_digest(self) -> None:
        entries = [
            PlatformDigest(Platform(os="linux", architecture="amd64"), "sha256:amd64"),
            PlatformDigest(Platform(os="linux", architecture="arm64"), "sha256:arm64"),
        ]

        with patch(
            "multiarch_publish._registry_ops.run_command",
            side_effect=['{"schemaVersion":2}', "sha256:manifest"],
        ):
            digest = publish_manifest_by_digest("ghcr.io/acme/test", entries)

        self.assertEqual(digest, "sha256:manifest")

    def test_sign_and_verify_platform_image_checks_attestation(self) -> None:
        with patch(
            "multiarch_publish._registry_ops.run_command",
            return_value="",
        ) as run_command_mock, patch(
            "multiarch_publish._registry_ops._resolve_attestation_digest",
            return_value="sha256:attestation",
        ), patch(
            "multiarch_publish._registry_ops._verify_attestation_contains_provenance",
            return_value=None,
        ) as verify_attestation_mock:
            sign_and_verify_platform_image(
                image_ref="ghcr.io/acme/test",
                index_digest="sha256:index",
                platform_digest="sha256:platform",
                certificate_oidc_issuer="https://token.actions.githubusercontent.com",
                certificate_identity_regexp="^https://github\\.com/acme/test/",
            )

        self.assertGreaterEqual(run_command_mock.call_count, 4)
        verify_attestation_mock.assert_called_once()

    def test_sign_and_verify_manifest_verifies_target_digest(self) -> None:
        with patch("multiarch_publish._registry_ops.run_command", return_value="") as run_command_mock:
            sign_and_verify_manifest(
                image_ref="ghcr.io/acme/test",
                manifest_digest="sha256:manifest",
                certificate_oidc_issuer="https://token.actions.githubusercontent.com",
                certificate_identity_regexp="^https://github\\.com/acme/test/",
            )

        command_strings = [" ".join(call.args[0]) for call in run_command_mock.call_args_list]
        self.assertTrue(any("cosign sign --yes ghcr.io/acme/test@sha256:manifest" == text for text in command_strings))
        self.assertTrue(any("cosign verify" in text for text in command_strings))

    def test_publish_platform_tags_creates_tag_per_suffix(self) -> None:
        with patch("multiarch_publish._registry_ops.run_command", return_value="") as run_command_mock:
            publish_platform_tags(
                image_ref="ghcr.io/acme/test",
                index_digest="sha256:index",
                tag_suffix="amd64",
                tags=["v1", "latest"],
            )

        command_strings = [" ".join(call.args[0]) for call in run_command_mock.call_args_list]
        self.assertIn(
            "docker buildx imagetools create --tag ghcr.io/acme/test:v1-amd64 ghcr.io/acme/test@sha256:index",
            command_strings,
        )
        self.assertIn(
            "docker buildx imagetools create --tag ghcr.io/acme/test:latest-amd64 ghcr.io/acme/test@sha256:index",
            command_strings,
        )

    def test_publish_final_tags_creates_final_manifest_tags(self) -> None:
        with patch("multiarch_publish._registry_ops.run_command", return_value="") as run_command_mock:
            publish_final_tags(
                image_ref="ghcr.io/acme/test",
                manifest_digest="sha256:manifest",
                tags=["v1", "latest"],
            )

        command_strings = [" ".join(call.args[0]) for call in run_command_mock.call_args_list]
        self.assertIn(
            "docker buildx imagetools create --tag ghcr.io/acme/test:v1 ghcr.io/acme/test@sha256:manifest",
            command_strings,
        )
        self.assertIn(
            "docker buildx imagetools create --tag ghcr.io/acme/test:latest ghcr.io/acme/test@sha256:manifest",
            command_strings,
        )


if __name__ == "__main__":
    unittest.main()
