#!/usr/bin/env bash
set -euo pipefail

repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"

# YAML
yamllint --config-file .github/linters/.yamllint .

# Markdown
pymarkdown \
  --config .github/linters/.pymarkdown.json scan \
  --recurse \
  --exclude '**/.venv*/**' \
  .

# ruff (Python)
ruff check .

# pyright (Python)
pyright .
