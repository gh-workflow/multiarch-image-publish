import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from multiarch_publish._action import _run_action, main
from multiarch_publish._models import Platform, PlatformDigest
from multiarch_publish._registry_ops import _PlatformVerificationDigests


class ActionTests(unittest.TestCase):
    def test_run_action_writes_manifest_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "github-output.txt"
            env = {
                "INPUT_IMAGE_REF": "ghcr.io/acme/test",
                "INPUT_TAGS": "latest",
                "INPUT_PLATFORM_DIGESTS": "linux/amd64=sha256:index",
                "INPUT_CERTIFICATE_OIDC_ISSUER": "https://token.actions.githubusercontent.com",
                "GITHUB_REPOSITORY": "acme/test",
                "GITHUB_OUTPUT": str(output_file),
            }
            with patch.dict("os.environ", env, clear=False), patch(
                "multiarch_publish._action.resolve_platform_verification_digests",
                return_value=_PlatformVerificationDigests(
                    platform_digest="sha256:platform",
                    attestation_digest="sha256:attestation",
                ),
            ), patch(
                "multiarch_publish._action.sign_and_verify_platform_image",
                return_value=None,
            ), patch(
                "multiarch_publish._action.publish_platform_tags",
                return_value=None,
            ), patch(
                "multiarch_publish._action.publish_manifest_by_digest",
                return_value="sha256:manifest",
            ), patch(
                "multiarch_publish._action.sign_and_verify_manifest",
                return_value=None,
            ), patch(
                "multiarch_publish._action.publish_final_tags",
                return_value=None,
            ):
                manifest_digest = _run_action()
                written_output = output_file.read_text(encoding="utf-8")

            self.assertEqual(manifest_digest, "sha256:manifest")
            self.assertEqual(
                written_output,
                "manifest_digest=sha256:manifest\n",
            )

    def test_main_returns_zero_on_success(self) -> None:
        with patch("multiarch_publish._action._run_action", return_value="sha256:manifest"):
            self.assertEqual(main(), 0)

    def test_run_action_publishes_platform_tags_after_manifest_verification(self) -> None:
        call_order: list[str] = []
        output_file = Path(tempfile.gettempdir()) / "github-output-order.txt"
        env = {
            "INPUT_IMAGE_REF": "ghcr.io/acme/test",
            "INPUT_TAGS": "latest",
            "INPUT_PLATFORM_DIGESTS": "linux/amd64=sha256:amd64,linux/arm64=sha256:arm64",
            "INPUT_CERTIFICATE_OIDC_ISSUER": "https://token.actions.githubusercontent.com",
            "GITHUB_REPOSITORY": "acme/test",
            "GITHUB_OUTPUT": str(output_file),
        }

        entries = [
            PlatformDigest(Platform(os="linux", architecture="amd64"), "sha256:amd64"),
            PlatformDigest(Platform(os="linux", architecture="arm64"), "sha256:arm64"),
        ]

        with patch.dict("os.environ", env, clear=False), patch(
            "multiarch_publish._action.parse_platform_digests",
            return_value=entries,
        ), patch(
            "multiarch_publish._action.resolve_platform_verification_digests",
            side_effect=[
                _PlatformVerificationDigests(
                    platform_digest="sha256:platform-amd64",
                    attestation_digest="sha256:attestation-amd64",
                ),
                _PlatformVerificationDigests(
                    platform_digest="sha256:platform-arm64",
                    attestation_digest="sha256:attestation-arm64",
                ),
            ],
        ), patch(
            "multiarch_publish._action.sign_and_verify_platform_image",
            side_effect=lambda **_: call_order.append("platform"),
        ), patch(
            "multiarch_publish._action.publish_manifest_by_digest",
            side_effect=lambda *_, **__: call_order.append("manifest") or "sha256:manifest",
        ), patch(
            "multiarch_publish._action.sign_and_verify_manifest",
            side_effect=lambda **_: call_order.append("verify-manifest"),
        ), patch(
            "multiarch_publish._action.publish_platform_tags",
            side_effect=lambda **_: call_order.append("platform-tag"),
        ), patch(
            "multiarch_publish._action.publish_final_tags",
            side_effect=lambda *_: call_order.append("final-tag"),
        ):
            _run_action()

        self.assertEqual(
            call_order,
            [
                "platform",
                "platform",
                "manifest",
                "verify-manifest",
                "platform-tag",
                "platform-tag",
                "final-tag",
            ],
        )

    def test_run_action_builds_final_manifest_from_resolved_platform_digests(self) -> None:
        output_file = Path(tempfile.gettempdir()) / "github-output-manifest-inputs.txt"
        env = {
            "INPUT_IMAGE_REF": "ghcr.io/acme/test",
            "INPUT_TAGS": "latest",
            "INPUT_PLATFORM_DIGESTS": "linux/amd64=sha256:index-amd64\nlinux/arm64=sha256:index-arm64",
            "INPUT_CERTIFICATE_OIDC_ISSUER": "https://token.actions.githubusercontent.com",
            "GITHUB_REPOSITORY": "acme/test",
            "GITHUB_OUTPUT": str(output_file),
        }
        entries = [
            PlatformDigest(Platform(os="linux", architecture="amd64"), "sha256:index-amd64"),
            PlatformDigest(Platform(os="linux", architecture="arm64"), "sha256:index-arm64"),
        ]

        with patch.dict("os.environ", env, clear=False), patch(
            "multiarch_publish._action.parse_platform_digests",
            return_value=entries,
        ), patch(
            "multiarch_publish._action.resolve_platform_verification_digests",
            side_effect=[
                _PlatformVerificationDigests(
                    platform_digest="sha256:manifest-amd64",
                    attestation_digest="sha256:attestation-amd64",
                ),
                _PlatformVerificationDigests(
                    platform_digest="sha256:manifest-arm64",
                    attestation_digest="sha256:attestation-arm64",
                ),
            ],
        ), patch(
            "multiarch_publish._action.sign_and_verify_platform_image",
            return_value=None,
        ), patch(
            "multiarch_publish._action.publish_manifest_by_digest",
            return_value="sha256:manifest",
        ) as publish_manifest_mock, patch(
            "multiarch_publish._action.sign_and_verify_manifest",
            return_value=None,
        ), patch(
            "multiarch_publish._action.publish_platform_tags",
            return_value=None,
        ), patch(
            "multiarch_publish._action.publish_final_tags",
            return_value=None,
        ):
            _run_action()

        publish_manifest_mock.assert_called_once()
        manifest_entries = publish_manifest_mock.call_args.args[1]
        self.assertEqual(
            manifest_entries,
            [
                PlatformDigest(Platform(os="linux", architecture="amd64"), "sha256:manifest-amd64"),
                PlatformDigest(Platform(os="linux", architecture="arm64"), "sha256:manifest-arm64"),
            ],
        )
        self.assertEqual(publish_manifest_mock.call_args.kwargs["annotations"], {})

    def test_run_action_passes_annotations_to_publish_manifest(self) -> None:
        output_file = Path(tempfile.gettempdir()) / "github-output-annotations.txt"
        env = {
            "INPUT_IMAGE_REF": "ghcr.io/acme/test",
            "INPUT_TAGS": "latest",
            "INPUT_PLATFORM_DIGESTS": "linux/amd64=sha256:index-amd64",
            "INPUT_ANNOTATIONS": (
                "org.opencontainers.image.source=https://github.com/acme/test\n"
                "org.opencontainers.image.version=v1.2.3"
            ),
            "INPUT_CERTIFICATE_OIDC_ISSUER": "https://token.actions.githubusercontent.com",
            "GITHUB_REPOSITORY": "acme/test",
            "GITHUB_OUTPUT": str(output_file),
        }
        entries = [
            PlatformDigest(Platform(os="linux", architecture="amd64"), "sha256:index-amd64"),
        ]

        with patch.dict("os.environ", env, clear=False), patch(
            "multiarch_publish._action.parse_platform_digests",
            return_value=entries,
        ), patch(
            "multiarch_publish._action.resolve_platform_verification_digests",
            return_value=_PlatformVerificationDigests(
                platform_digest="sha256:manifest-amd64",
                attestation_digest="sha256:attestation-amd64",
            ),
        ), patch(
            "multiarch_publish._action.sign_and_verify_platform_image",
            return_value=None,
        ), patch(
            "multiarch_publish._action.publish_manifest_by_digest",
            return_value="sha256:manifest",
        ) as publish_manifest_mock, patch(
            "multiarch_publish._action.sign_and_verify_manifest",
            return_value=None,
        ), patch(
            "multiarch_publish._action.publish_platform_tags",
            return_value=None,
        ), patch(
            "multiarch_publish._action.publish_final_tags",
            return_value=None,
        ):
            _run_action()

        self.assertEqual(
            publish_manifest_mock.call_args.kwargs["annotations"],
            {
                "org.opencontainers.image.source": "https://github.com/acme/test",
                "org.opencontainers.image.version": "v1.2.3",
            },
        )


if __name__ == "__main__":
    unittest.main()
