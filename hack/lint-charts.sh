#!/usr/bin/env bash
# Lint every Helm chart under deploy/charts. Fails on any lint error.
# Passes with a notice while no chart exists yet (platform-core arrives with BP-10).
set -euo pipefail

charts=$(find deploy/charts -name Chart.yaml -not -path '*/charts/*/charts/*' 2>/dev/null | xargs -r -n1 dirname)
if [ -z "$charts" ]; then
  echo "lint-charts: no Chart.yaml under deploy/charts yet - nothing to lint"
  exit 0
fi

rc=0
for chart in $charts; do
  echo "==> helm lint $chart"
  helm lint --strict "$chart" || rc=1
  # Rendering catches template errors that lint alone does not.
  helm template ci-check "$chart" >/dev/null || rc=1
done
exit $rc
