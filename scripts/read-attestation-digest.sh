#!/usr/bin/env bash

# Print the attestation manifest digest for an image as `digest=<sha256...>`.

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./lib.sh
source "${script_dir}/lib.sh"

image="${1-}"

require_arg "${image}" "image" "full image reference including digest"

digest="$(
  docker buildx imagetools inspect --raw "${image}" \
    | jq -r '.manifests[]
      | select(.annotations."vnd.docker.reference.type"=="attestation-manifest")
      | .digest' \
    | head -n1
)"

if [[ -z "${digest}" ]]; then
  fail "failed to resolve attestation digest for ${image}"
fi

printf 'digest=%s\n' "${digest}"
