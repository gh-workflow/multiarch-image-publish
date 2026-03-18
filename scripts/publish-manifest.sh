#!/usr/bin/env bash

# Create and push a multi-arch manifest by digest and print the resulting digest
# as `digest=<sha256...>`.

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./lib.sh
source "${script_dir}/lib.sh"

image_ref="${1-}"
platform_digests_file="${2-}"

require_arg "${image_ref}" "image_ref" "registry/repository image reference"
require_arg "${platform_digests_file}" "platform_digests_file" "path to file with platform=digest entries"

if [[ ! -f "${platform_digests_file}" ]]; then
  fail "platform_digests_file does not exist: ${platform_digests_file}"
fi

manifest_args=()
while IFS= read -r entry; do
  if [[ -z "${entry}" ]]; then
    continue
  fi

  if [[ "${entry}" != *=* ]]; then
    fail "invalid platform=digest entry in ${platform_digests_file}: ${entry}"
  fi

  digest="${entry#*=}"
  if [[ -z "${digest}" ]]; then
    fail "missing digest in ${platform_digests_file}: ${entry}"
  fi

  manifest_args+=("${image_ref}@${digest}")
done < "${platform_digests_file}"

if [[ "${#manifest_args[@]}" -eq 0 ]]; then
  fail "no digests found in ${platform_digests_file}"
fi

digest="$(
  docker buildx imagetools create \
    --dry-run \
    "${manifest_args[@]}" \
  | regctl manifest put \
      --by-digest \
      "${image_ref}" \
      --format '{{ ( .Manifest.GetDescriptor ).Digest }}'
)"

if [[ -z "${digest}" ]]; then
  fail "failed to publish multi-arch manifest for ${image_ref}"
fi

printf 'digest=%s\n' "${digest}"
