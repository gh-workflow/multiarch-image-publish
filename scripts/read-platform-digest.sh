#!/usr/bin/env bash

# Print the platform-specific digest for a manifest list or image index as
# `digest=<sha256...>` so the caller can append it to GITHUB_OUTPUT.

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./lib.sh
source "${script_dir}/lib.sh"

image="${1-}"
platform="${2-}"

require_arg "${image}" "image" "full image reference including tag or digest"
require_arg "${platform}" "platform" "target platform such as linux/amd64"

if [[ "${platform}" != */* ]]; then
  fail "platform must use os/arch format, for example linux/amd64"
fi

platform_os="${platform%%/*}"
platform_architecture="${platform#*/}"

digest="$(
  docker buildx imagetools inspect --raw "${image}" \
    | jq -r \
      --arg platform_os "${platform_os}" \
      --arg platform_architecture "${platform_architecture}" \
      '.manifests[]
      | select(.platform.os==$platform_os and .platform.architecture==$platform_architecture)
      | .digest' \
    | head -n1
)"

if [[ -z "${digest}" ]]; then
  fail "failed to resolve platform digest for ${image} (${platform})"
fi

printf 'digest=%s\n' "${digest}"
