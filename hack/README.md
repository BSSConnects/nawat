# `hack/` — developer scripts

The inner loop. **Phase 0.6 delivers this before any platform code depends on it** — Istio,
Keycloak, Flux and OPA are four unfamiliar-in-combination systems, and meeting all of them for
the first time while also debugging a controller is how projects stall.

## Contents

```
kind-up.sh          create a kind cluster with MetalLB, a local registry, storage
install-deps.sh     Istio, Keycloak, Flux, cert-manager, CNPG, kube-prometheus-stack
Tiltfile            live-reload our services into the cluster on save
licence-sign/       offline tool that signs development licences
gen-metadata.sh     regenerate example __metadata__.json files
verify.sh           everything CI runs — run this before opening a PR
```

## Example — `kind-up.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

CLUSTER="${CLUSTER:-bssconnects}"

# A local registry saves a push to Harbor on every code change. With four services and a
# tight loop, that difference is minutes per iteration, which decides whether people use
# the loop at all.
if ! docker inspect kind-registry >/dev/null 2>&1; then
  docker run -d --restart=always -p 5001:5000 --name kind-registry registry:2
fi

cat <<YAML | kind create cluster --name "$CLUSTER" --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
containerdConfigPatches:
  - |-
    [plugins."io.containerd.grpc.v1.cri".registry.mirrors."localhost:5001"]
      endpoint = ["http://kind-registry:5000"]
nodes:
  - role: control-plane
    kubeadmConfigPatches:
      - |
        kind: InitConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            node-labels: "ingress-ready=true"
    extraPortMappings:
      # Expose the Istio gateway on the host so the browser can reach the UI without
      # port-forwarding, which otherwise breaks the OIDC redirect.
      - { containerPort: 30080, hostPort: 8080, protocol: TCP }
      - { containerPort: 30443, hostPort: 8443, protocol: TCP }
  # Two workers: enough to catch anti-affinity and PDB mistakes that a single-node
  # cluster silently hides until a customer's rolling upgrade fails.
  - role: worker
  - role: worker
YAML

docker network connect kind kind-registry 2>/dev/null || true
echo "cluster ready — next: ./hack/install-deps.sh"
```

## Rule

`./hack/verify.sh` must run exactly what CI runs. If CI can fail when verify passed, people stop
trusting verify and start pushing to find out.
