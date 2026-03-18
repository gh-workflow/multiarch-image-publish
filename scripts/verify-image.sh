#!/usr/bin/env bash

# Sign and verify both the index digest and the platform manifest digest for one
# architecture, then confirm that provenance is attached to the signed index.

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./lib.sh
source "${script_dir}/lib.sh"

image_ref="${1-}"
index_digest="${2-}"
platform_digest="${3-}"
certificate_oidc_issuer="${4-}"
certificate_identity_regexp="${5-}"

require_arg "${image_ref}" "image_ref" "registry/repository image reference"
require_arg "${index_digest}" "index_digest" "single-architecture image index digest"
require_arg "${platform_digest}" "platform_digest" "resolved platform manifest digest"
require_arg "${certificate_oidc_issuer}" "certificate_oidc_issuer" "expected OIDC issuer for cosign verification"
require_arg "${certificate_identity_regexp}" "certificate_identity_regexp" "expected certificate identity regexp"

index_image="${image_ref}@${index_digest}"
platform_image="${image_ref}@${platform_digest}"

# Buildx often returns an OCI index digest even for a single-arch build.
# Sign and verify both digests so downstream consumers can trust either form.
cosign sign --yes "${index_image}"
cosign sign --yes "${platform_image}"

cosign verify \
  --certificate-oidc-issuer "${certificate_oidc_issuer}" \
  --certificate-identity-regexp "${certificate_identity_regexp}" \
  "${index_image}"

cosign verify \
  --certificate-oidc-issuer "${certificate_oidc_issuer}" \
  --certificate-identity-regexp "${certificate_identity_regexp}" \
  "${platform_image}"

attestation_output="$("${script_dir}/read-attestation-digest.sh" "${index_image}")"
attestation_digest="${attestation_output#digest=}"

if [[ -z "${attestation_digest}" ]]; then
  fail "failed to resolve attestation digest for ${index_image}"
fi

# Verify that the attestation manifest contains an in-toto provenance predicate.
docker buildx imagetools inspect --raw "${image_ref}@${attestation_digest}" \
  | jq -e '.layers[]?
    | .annotations."in-toto.io/predicate-type"
    | select(startswith("https://slsa.dev/provenance/"))' \
  >/dev/null
