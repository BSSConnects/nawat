#!/usr/bin/env bash
# Contract checks for schemas/:
#   1. every *.json schema is a valid JSON Schema (checked against its declared metaschema)
#   2. testdata/valid/*.json must validate, testdata/invalid/*.json must be rejected
#   3. schemas/platform-api/openapi.yaml passes the OpenAPI linter
# Tools: check-jsonschema (Python), redocly (Node). Both pinned in .github/workflows/ci.yml.
set -euo pipefail

rc=0

schemas=$(find schemas -name '*.json' -not -path '*/testdata/*' 2>/dev/null || true)
if [ -z "$schemas" ]; then
  echo "validate-schemas: no JSON schemas under schemas/ yet (BP-4)"
else
  for schema in $schemas; do
    echo "==> metaschema check: $schema"
    check-jsonschema --check-metaschema "$schema" || rc=1

    dir=$(dirname "$schema")
    if ls "$dir"/testdata/valid/*.json >/dev/null 2>&1; then
      echo "==> must pass: $dir/testdata/valid/"
      check-jsonschema --schemafile "$schema" "$dir"/testdata/valid/*.json || rc=1
    fi
    for bad in "$dir"/testdata/invalid/*.json; do
      [ -f "$bad" ] || continue
      echo "==> must fail: $bad"
      if check-jsonschema --schemafile "$schema" "$bad" >/dev/null 2>&1; then
        echo "ERROR: $bad was accepted but is expected to be rejected"
        rc=1
      fi
    done
  done
fi

openapi=schemas/platform-api/openapi.yaml
if [ -f "$openapi" ]; then
  echo "==> openapi lint: $openapi"
  redocly lint "$openapi" || rc=1
else
  echo "validate-schemas: $openapi not published yet (BP-9)"
fi

exit $rc
