import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from multiarch_publish._action import _run_action, main


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
                "multiarch_publish._action.resolve_platform_manifest_digest",
                return_value="sha256:platform",
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


if __name__ == "__main__":
    unittest.main()
