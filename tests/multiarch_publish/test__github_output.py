import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from multiarch_publish._github_output import write_output


class GithubOutputTests(unittest.TestCase):
    def test_write_output_appends_key_value(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "github-output.txt"
            with patch.dict("os.environ", {"GITHUB_OUTPUT": str(output_file)}, clear=False):
                write_output("manifest_digest", "sha256:test")

            self.assertEqual(
                output_file.read_text(encoding="utf-8"),
                "manifest_digest=sha256:test\n",
            )


if __name__ == "__main__":
    unittest.main()
