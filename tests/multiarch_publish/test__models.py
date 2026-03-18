import unittest

from multiarch_publish._models import Platform


class PlatformTests(unittest.TestCase):
    def test_parse_accepts_os_arch(self) -> None:
        self.assertEqual(
            Platform.parse("linux/amd64"),
            Platform(os="linux", architecture="amd64"),
        )

    def test_parse_accepts_os_arch_variant(self) -> None:
        self.assertEqual(
            Platform.parse("linux/arm/v7"),
            Platform(os="linux", architecture="arm", variant="v7"),
        )

    def test_tag_suffix_uses_arch_and_variant(self) -> None:
        self.assertEqual(Platform.parse("linux/amd64").tag_suffix, "amd64")
        self.assertEqual(Platform.parse("linux/arm/v7").tag_suffix, "arm-v7")


if __name__ == "__main__":
    unittest.main()
