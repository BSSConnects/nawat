#!/usr/bin/env bash
# Two checks behind the BP-6 / BP-17 constraint "no private signing keys in the repository":
#   1. no committed key or licence files outside testdata/ (the .gitignore allows test keys there)
#   2. gitleaks over the full history (config: .gitleaks.toml)
set -euo pipefail

rc=0
echo "==> committed key material outside testdata/"
offenders=$(git ls-files | grep -E '\.(pem|key|p12|pfx|jks|lic)$' | grep -v -E '(^|/)testdata/' || true)
if [ -n "$offenders" ]; then
  echo "ERROR: key or licence files committed:"
  echo "$offenders"
  rc=1
fi

echo "==> gitleaks"
if command -v gitleaks >/dev/null 2>&1; then
  gitleaks detect --source . --config .gitleaks.toml --redact --verbose --exit-code 1 || rc=1
else
  echo "WARNING: gitleaks not installed; skipping secret scan (CI always runs it)"
fi
exit $rc
