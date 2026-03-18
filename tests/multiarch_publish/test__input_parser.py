import unittest

from multiarch_publish._errors import InputError
from multiarch_publish._input_parser import (
    caller_certificate_identity_regexp,
    parse_platform_digests,
    parse_tags,
)
from multiarch_publish._models import Platform


class InputParserTests(unittest.TestCase):
    def test_parse_tags_rejects_blank_lines(self) -> None:
        with self.assertRaisesRegex(InputError, "tags must not contain empty lines"):
            parse_tags("v1\n\nlatest")

    def test_parse_platform_digests_returns_platform_objects(self) -> None:
        entries = parse_platform_digests(
            "linux/amd64=sha256:aaa\nlinux/arm/v7=sha256:bbb"
        )

        self.assertEqual(entries[0].platform, Platform(os="linux", architecture="amd64"))
        self.assertEqual(entries[0].digest, "sha256:aaa")
        self.assertEqual(
            entries[1].platform,
            Platform(os="linux", architecture="arm", variant="v7"),
        )
        self.assertEqual(entries[1].digest, "sha256:bbb")

    def test_caller_certificate_identity_regexp_escapes_repo(self) -> None:
        pattern = caller_certificate_identity_regexp("org/repo.name")
        self.assertIn("org/repo\\.name", pattern)


if __name__ == "__main__":
    unittest.main()
