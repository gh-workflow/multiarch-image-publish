#!/usr/bin/env bash

# Common helpers shared by the action's shell scripts.

set -euo pipefail

fail() {
  local message="$1"
  echo "Error: ${message}" >&2
  exit 1
}

require_arg() {
  local value="$1"
  local name="$2"
  local description="$3"

  if [[ -z "${value}" ]]; then
    fail "missing argument '${name}': ${description}"
  fi
}
