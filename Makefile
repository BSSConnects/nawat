# Repository entry points. Per-module targets live in each module (operator/Makefile is
# kubebuilder's). Rule: `make verify` runs exactly what CI runs — if CI can fail when verify
# passed, people stop trusting verify. The CI stages in .github/workflows/ci.yml call only
# the targets below; add a stage here first, then reference it from the workflow.

.DEFAULT_GOAL := help
.PHONY: help check-context operator verify lint lint-charts test validate validate-schemas \
        check-generated check-secrets dev-up dev-down

GO_MODULES := operator sdk cli services

help: ## List targets
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

check-context: ## Refuse to touch any cluster but the local practice one
	@ctx=$$(kubectl config current-context); \
	if [ "$$ctx" != "kind-nawat" ]; then \
	  echo "refusing: current context is '$$ctx', expected kind-nawat"; exit 1; \
	fi

operator: ## Pass a target through to the kubebuilder project: make operator T=manifests
	$(MAKE) -C operator $(T)

## ---- CI stage: lint -------------------------------------------------------------------

lint: ## Lint every Go module (golangci-lint)
	@for m in $(GO_MODULES); do \
	  [ -f $$m/go.mod ] || continue; \
	  echo "==> golangci-lint $$m"; (cd $$m && golangci-lint run ./...) || exit 1; \
	done

lint-charts: ## helm lint + render every chart under deploy/charts
	./hack/lint-charts.sh

## ---- CI stage: test -------------------------------------------------------------------

test: ## Unit tests across modules, plus Rego policy tests
	@for m in $(GO_MODULES); do \
	  [ -f $$m/go.mod ] || continue; \
	  echo "==> go test $$m"; (cd $$m && go test -race ./...) || exit 1; \
	done
	@if ls deploy/policies/*.rego deploy/policies/*/*.rego >/dev/null 2>&1; then \
	  echo "==> opa test deploy/policies"; opa test deploy/policies -v; \
	else echo "no Rego policies yet - skipping opa test"; fi

## ---- CI stage: contracts --------------------------------------------------------------

validate-schemas: ## JSON Schema metaschema + testdata checks, OpenAPI lint
	./hack/validate-schemas.sh

validate: ## Validate every committed module contract with the CLI
	@if [ -f cli/go.mod ]; then \
	  (cd cli && go run ./cmd/bssconnectsctl module validate ../examples/hello-module/__metadata__.json); \
	else echo "cli not built yet (BP-19) - skipping module validate"; fi

check-generated: ## Regenerate artefacts and fail on drift (generated files are never hand-edited)
	./hack/check-generated.sh

## ---- CI stage: secrets ----------------------------------------------------------------

check-secrets: ## No key/licence files in git; gitleaks over history
	./hack/check-secrets.sh

## ---- Everything -----------------------------------------------------------------------

verify: lint lint-charts test validate-schemas validate check-generated check-secrets ## Everything CI runs. Run before opening a PR.

dev-up: check-context ## kind + Istio + Keycloak + Flux, then Tilt
	./hack/kind-up.sh && ./hack/install-deps.sh && tilt up

dev-down: ## Tear it all down
	tilt down; kind delete cluster --name nawat
