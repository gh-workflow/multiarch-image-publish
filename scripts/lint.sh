#!/usr/bin/env bash
set -euo pipefail

repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"

yamllint .
pymarkdown \
  --config .pymarkdown.json scan \
  --recurse \
  --exclude '**/.venv*/**' \
  .
ruff check .
pyright .
