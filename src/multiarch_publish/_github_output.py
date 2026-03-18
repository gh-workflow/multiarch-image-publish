"""Helpers for communicating outputs back to GitHub Actions."""

import os
from pathlib import Path


def write_output(name: str, value: str) -> None:
    """Append a simple key=value output if GITHUB_OUTPUT is available."""
    output_path = os.environ.get("GITHUB_OUTPUT", "")
    if output_path == "":
        return

    with Path(output_path).open("a", encoding="utf-8") as handle:
        handle.write(f"{name}={value}\n")
