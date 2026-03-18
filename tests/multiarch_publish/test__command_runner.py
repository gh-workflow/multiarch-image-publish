import subprocess
import unittest
from unittest.mock import patch

from multiarch_publish._command_runner import run_command
from multiarch_publish._errors import CommandError


class CommandRunnerTests(unittest.TestCase):
    def test_run_command_returns_stdout(self) -> None:
        completed = subprocess.CompletedProcess(
            args=["tool", "arg"],
            returncode=0,
            stdout="ok",
            stderr="",
        )

        with patch("multiarch_publish._command_runner.subprocess.run", return_value=completed):
            self.assertEqual(run_command(["tool", "arg"]), "ok")

    def test_run_command_raises_for_missing_binary(self) -> None:
        with patch(
            "multiarch_publish._command_runner.subprocess.run",
            side_effect=FileNotFoundError(),
        ):
            with self.assertRaisesRegex(CommandError, "required command not found"):
                run_command(["tool"])


if __name__ == "__main__":
    unittest.main()
