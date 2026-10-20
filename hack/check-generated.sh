#!/usr/bin/env bash
# Regenerate every generated artefact and fail if the result differs from what is committed.
# Generated files are never hand-edited (schemas/README.md rule 3); this is the gate that
# enforces it. The root `make generate` (Go + TypeScript from schemas/) is added by BP-11 and
# is picked up here automatically once it exists.
set -euo pipefail

if [ -f operator/Makefile ]; then
  echo "==> operator: controller-gen manifests + deepcopy"
  make -C operator manifests generate
fi

if grep -qE '^generate:' Makefile; then
  echo "==> root: make generate"
  make generate
fi

# Tool binaries land in */bin, which is gitignored; everything else must be unchanged.
if ! git diff --exit-code --stat; then
  echo
  echo "ERROR: generated artefacts are out of date. Run the generators and commit the result."
  exit 1
fi
untracked=$(git ls-files --others --exclude-standard)
if [ -n "$untracked" ]; then
  echo "ERROR: generation produced untracked files:"
  echo "$untracked"
  exit 1
fi
echo "generated artefacts are up to date"
