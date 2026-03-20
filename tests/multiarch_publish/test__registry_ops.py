import unittest
from unittest.mock import patch

from multiarch_publish._errors import CommandError
from multiarch_publish._models import Platform, PlatformDigest
from multiarch_publish._registry_ops import (
    _inspect_raw_manifest,
    _PlatformVerificationDigests,
    _resolve_attestation_digest,
    _resolve_platform_manifest_digest,
    _verify_attestation_contains_provenance,
    publish_final_tags,
    publish_manifest_by_digest,
    publish_platform_tags,
    resolve_platform_verification_digests,
    sign_and_verify_manifest,
    sign_and_verify_platform_image,
)


class RegistryOpsTests(unittest.TestCase):
    def test_inspect_raw_manifest_returns_decoded_json(self) -> None:
        with patch(
            "multiarch_publish._registry_ops.run_command",
            return_value='{"schemaVersion": 2}',
        ):
            manifest = _inspect_raw_manifest("ghcr.io/acme/test@sha256:index")

        self.assertEqual(manifest, {"schemaVersion": 2})

    def test_inspect_raw_manifest_raises_command_error_on_invalid_json(self) -> None:
        with patch("multiarch_publish._registry_ops.run_command", return_value="not-json"):
            with self.assertRaisesRegex(
                CommandError,
                "registry returned invalid JSON for image reference ghcr.io/acme/test@sha256:index",
            ):
                _inspect_raw_manifest("ghcr.io/acme/test@sha256:index")

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
            digest = _resolve_platform_manifest_digest("ghcr.io/acme/test", entry)

        self.assertEqual(digest, "sha256:match")

    def test_resolve_platform_manifest_digest_raises_when_no_candidate_matches(self) -> None:
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
                    "platform": {"os": "linux", "architecture": "arm", "variant": "v6"},
                    "digest": "sha256:wrong-variant",
                },
                {
                    "platform": {"os": "linux", "architecture": "arm", "variant": "v7"},
                    "digest": "",
                },
            ]
        }

        with patch(
            "multiarch_publish._registry_ops._inspect_raw_manifest",
            return_value=manifest,
        ):
            with self.assertRaisesRegex(
                CommandError,
                "failed to resolve platform digest for ghcr.io/acme/test@sha256:index",
            ):
                _resolve_platform_manifest_digest("ghcr.io/acme/test", entry)

    def test_resolve_platform_manifest_digest_skips_non_matching_os(self) -> None:
        entry = PlatformDigest(
            platform=Platform(os="linux", architecture="arm64"),
            digest="sha256:index",
        )
        manifest = {
            "manifests": [
                {
                    "platform": {"os": "windows", "architecture": "arm64"},
                    "digest": "sha256:windows",
                },
                {
                    "platform": {"os": "linux", "architecture": "arm64"},
                    "digest": "sha256:linux",
                },
            ]
        }

        with patch(
            "multiarch_publish._registry_ops._inspect_raw_manifest",
            return_value=manifest,
        ):
            digest = _resolve_platform_manifest_digest("ghcr.io/acme/test", entry)

        self.assertEqual(digest, "sha256:linux")

    def test_resolve_attestation_digest_returns_attestation_manifest_digest(self) -> None:
        manifest = {
            "manifests": [
                {
                    "annotations": {"vnd.docker.reference.type": "sbom"},
                    "digest": "sha256:sbom",
                },
                {
                    "annotations": {"vnd.docker.reference.type": "attestation-manifest"},
                    "digest": "sha256:attestation",
                },
            ]
        }

        with patch(
            "multiarch_publish._registry_ops._inspect_raw_manifest",
            return_value=manifest,
        ):
            digest = _resolve_attestation_digest("ghcr.io/acme/test@sha256:index")

        self.assertEqual(digest, "sha256:attestation")

    def test_resolve_attestation_digest_raises_when_missing(self) -> None:
        with patch(
            "multiarch_publish._registry_ops._inspect_raw_manifest",
            return_value={"manifests": []},
        ):
            with self.assertRaisesRegex(
                CommandError,
                "failed to resolve attestation digest for ghcr.io/acme/test@sha256:index",
            ):
                _resolve_attestation_digest("ghcr.io/acme/test@sha256:index")

    def test_resolve_platform_verification_digests_returns_both_digests(self) -> None:
        entry = PlatformDigest(
            platform=Platform(os="linux", architecture="arm64"),
            digest="sha256:index",
        )
        manifest = {
            "manifests": [
                {
                    "platform": {"os": "linux", "architecture": "arm64"},
                    "digest": "sha256:platform",
                },
                {
                    "annotations": {"vnd.docker.reference.type": "attestation-manifest"},
                    "digest": "sha256:attestation",
                },
            ]
        }

        with patch(
            "multiarch_publish._registry_ops._inspect_raw_manifest",
            return_value=manifest,
        ):
            digests = resolve_platform_verification_digests("ghcr.io/acme/test", entry)

        self.assertEqual(digests.platform_digest, "sha256:platform")
        self.assertEqual(digests.attestation_digest, "sha256:attestation")

    def test_resolve_platform_verification_digests_raises_when_attestation_missing(self) -> None:
        entry = PlatformDigest(
            platform=Platform(os="linux", architecture="arm64"),
            digest="sha256:index",
        )
        manifest = {
            "manifests": [
                {
                    "platform": {"os": "linux", "architecture": "arm64"},
                    "digest": "sha256:platform",
                }
            ]
        }

        with patch(
            "multiarch_publish._registry_ops._inspect_raw_manifest",
            return_value=manifest,
        ):
            with self.assertRaisesRegex(
                CommandError,
                "failed to resolve attestation digest for ghcr.io/acme/test@sha256:index",
            ):
                resolve_platform_verification_digests("ghcr.io/acme/test", entry)

    def test_verify_attestation_contains_provenance_accepts_slsa_predicate(self) -> None:
        manifest = {
            "layers": [
                {
                    "annotations": {
                        "in-toto.io/predicate-type": "https://slsa.dev/provenance/v1",
                    }
                }
            ]
        }

        with patch(
            "multiarch_publish._registry_ops._inspect_raw_manifest",
            return_value=manifest,
        ):
            _verify_attestation_contains_provenance("ghcr.io/acme/test", "sha256:attestation")

    def test_verify_attestation_contains_provenance_raises_without_provenance(self) -> None:
        manifest = {
            "layers": [
                {"annotations": {"in-toto.io/predicate-type": "https://example.com/other"}},
                {"annotations": {}},
            ]
        }

        with patch(
            "multiarch_publish._registry_ops._inspect_raw_manifest",
            return_value=manifest,
        ):
            with self.assertRaisesRegex(
                CommandError,
                "does not contain an in-toto provenance predicate",
            ):
                _verify_attestation_contains_provenance("ghcr.io/acme/test", "sha256:attestation")

    def test_publish_manifest_by_digest_returns_digest(self) -> None:
        entries = [
            PlatformDigest(Platform(os="linux", architecture="amd64"), "sha256:amd64"),
            PlatformDigest(Platform(os="linux", architecture="arm64"), "sha256:arm64"),
        ]

        with patch(
            "multiarch_publish._registry_ops.run_command",
            side_effect=[
                "",
                "",
                "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            ],
        ):
            digest = publish_manifest_by_digest("ghcr.io/acme/test", entries)

        self.assertEqual(
            digest,
            "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        )

    def test_publish_manifest_by_digest_raises_when_digest_lookup_is_empty(self) -> None:
        entries = [
            PlatformDigest(Platform(os="linux", architecture="amd64"), "sha256:amd64"),
        ]

        with patch(
            "multiarch_publish._registry_ops.run_command",
            side_effect=["", "", "  "],
        ):
            with self.assertRaisesRegex(
                CommandError,
                "failed to resolve pushed manifest digest for ghcr.io/acme/test",
            ):
                publish_manifest_by_digest("ghcr.io/acme/test", entries)

    def test_sign_and_verify_platform_image_checks_attestation(self) -> None:
        with patch(
            "multiarch_publish._registry_ops.run_command",
            return_value="",
        ) as run_command_mock, patch(
            "multiarch_publish._registry_ops._verify_attestation_contains_provenance",
            return_value=None,
        ) as verify_attestation_mock:
            sign_and_verify_platform_image(
                image_ref="ghcr.io/acme/test",
                index_digest="sha256:index",
                digests=_PlatformVerificationDigests(
                    platform_digest="sha256:platform",
                    attestation_digest="sha256:attestation",
                ),
                certificate_oidc_issuer="https://token.actions.githubusercontent.com",
                certificate_identity_regexp="^https://github\\.com/acme/test/",
            )

        command_strings = [" ".join(call.args[0]) for call in run_command_mock.call_args_list]
        self.assertIn("cosign sign --yes ghcr.io/acme/test@sha256:index", command_strings)
        self.assertIn("cosign sign --yes ghcr.io/acme/test@sha256:platform", command_strings)
        self.assertIn(
            "cosign verify --certificate-oidc-issuer https://token.actions.githubusercontent.com "
            "--certificate-identity-regexp ^https://github\\.com/acme/test/ "
            "ghcr.io/acme/test@sha256:index",
            command_strings,
        )
        self.assertIn(
            "cosign verify --certificate-oidc-issuer https://token.actions.githubusercontent.com "
            "--certificate-identity-regexp ^https://github\\.com/acme/test/ "
            "ghcr.io/acme/test@sha256:platform",
            command_strings,
        )
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
            "regctl image copy ghcr.io/acme/test@sha256:index ghcr.io/acme/test:v1-amd64",
            command_strings,
        )
        self.assertIn(
            "regctl image copy ghcr.io/acme/test@sha256:index ghcr.io/acme/test:latest-amd64",
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
            "regctl image copy ghcr.io/acme/test@sha256:manifest ghcr.io/acme/test:v1",
            command_strings,
        )
        self.assertIn(
            "regctl image copy ghcr.io/acme/test@sha256:manifest ghcr.io/acme/test:latest",
            command_strings,
        )


if __name__ == "__main__":
    unittest.main()
