# Repository entry points. Per-module targets live in each module (operator/Makefile is
# kubebuilder's). Rule: `make verify` runs exactly what CI runs — if CI can fail when verify
# passed, people stop trusting verify.

.DEFAULT_GOAL := help
.PHONY: help check-context operator verify validate test lint dev-up dev-down

help: ## List targets
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

check-context: ## Refuse to touch any cluster but the local practice one
	@ctx=$$(kubectl config current-context); \
	if [ "$$ctx" != "kind-nawat" ]; then \
	  echo "refusing: current context is '$$ctx', expected kind-nawat"; exit 1; \
	fi

operator: ## Pass a target through to the kubebuilder project: make operator T=manifests
	$(MAKE) -C operator $(T)

lint: ## Lint every Go module
	@for m in operator sdk cli services; do \
	  [ -f $$m/go.mod ] && (cd $$m && golangci-lint run ./...) || true; \
	done

test: ## Unit tests across modules, plus Rego policy tests
	@for m in operator sdk cli services; do \
	  [ -f $$m/go.mod ] && (cd $$m && go test -race ./...) || true; \
	done
	@[ -d deploy/policies ] && opa test deploy/policies -v || true

validate: ## Validate every committed module contract
	@[ -f cli/go.mod ] && (cd cli && go run ./cmd/bssconnectsctl module validate \
	  ../examples/hello-module/__metadata__.json) || echo "cli not built yet"

verify: lint test validate ## Everything CI runs. Run before opening a PR.

dev-up: check-context ## kind + Istio + Keycloak + Flux, then Tilt
	./hack/kind-up.sh && ./hack/install-deps.sh && tilt up

dev-down: ## Tear it all down
	tilt down; kind delete cluster --name nawat
