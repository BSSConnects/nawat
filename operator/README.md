# nawat operator

Turns licences and configuration into running modules. Built with **kubebuilder**; the
platform's real API lives in its CRDs.

## What it does

1. Watches `License`; asks the License Service to verify it; maintains the module catalogue.
2. Fetches and validates each module's `__metadata__` **once**, and publishes it to the registry.
3. Validates `ModuleInstance.spec.config` against the module's `values.schema.json` in an
   admission webhook, so the customer gets a precise error at submit time.
4. Provisions the capabilities a module declares: a CloudNativePG `Database`, a Strimzi
   `KafkaTopic`, a Keycloak client.
5. Emits **Flux** `OCIRepository` + `HelmRelease`, plus `HTTPRoute`, `AuthorizationPolicy`
   and `ServiceMonitor`.
6. Aggregates status back onto `ModuleInstance`, which is what the UI and CLI read.

## What it does NOT do

**It does not implement Helm.** No `helm install` from Go, no release history, no rollback
logic. Flux already solves install, upgrade, rollback, drift and retry; reimplementing that
on the Helm SDK is months of work plus permanent maintenance.

We also do **not fork Flux**. We import its API types and create its objects — see
[../docs/opensource-stack.md](../docs/opensource-stack.md).

**The division of labour:** this operator decides *what should exist* (licence → entitlement
→ version → values). Flux decides *how it gets applied*.

## Layout

| Path | |
|---|---|
| [`api/`](api/) | CRD types, multigroup: `platform`, `licensing`, `iam` |
| `internal/controller/<group>/` | the reconcilers |
| [`cmd/`](cmd/) | `main.go` — the manager; every controller runs in this one process |
| `config/` | kustomize: CRDs, RBAC, manager, webhooks. `config/rbac/role.yaml` is **generated** |
| `test/` | envtest suites and the e2e scaffold |

## Daily loop

```sh
kubectl config current-context     # ALWAYS check — make install applies to the current cluster
make manifests generate            # after editing any +kubebuilder marker, then READ the YAML diff
make install                       # apply CRDs
make run                           # run the manager locally against your kubeconfig
```

`make run` uses **your** credentials, usually cluster-admin — so a missing `+kubebuilder:rbac`
marker goes unnoticed until the first `make deploy`, when the operator runs as its own
ServiceAccount. From the webhook stage onward, test deployed.

---

## Getting Started

### Prerequisites
- go version v1.24.6+
- docker version 17.03+.
- kubectl version v1.11.3+.
- Access to a Kubernetes v1.11.3+ cluster.

### To Deploy on the cluster
**Build and push your image to the location specified by `IMG`:**

```sh
make docker-build docker-push IMG=<some-registry>/nawat:tag
```

**NOTE:** This image ought to be published in the personal registry you specified.
And it is required to have access to pull the image from the working environment.
Make sure you have the proper permission to the registry if the above commands don’t work.

**Install the CRDs into the cluster:**

```sh
make install
```

**Deploy the Manager to the cluster with the image specified by `IMG`:**

```sh
make deploy IMG=<some-registry>/nawat:tag
```

> **NOTE**: If you encounter RBAC errors, you may need to grant yourself cluster-admin
privileges or be logged in as admin.

**Create instances of your solution**
You can apply the samples (examples) from the config/sample:

```sh
kubectl apply -k config/samples/
```

>**NOTE**: Ensure that the samples has default values to test it out.

### To Uninstall
**Delete the instances (CRs) from the cluster:**

```sh
kubectl delete -k config/samples/
```

**Delete the APIs(CRDs) from the cluster:**

```sh
make uninstall
```

**UnDeploy the controller from the cluster:**

```sh
make undeploy
```

## Project Distribution

Following the options to release and provide this solution to the users.

### By providing a bundle with all YAML files

1. Build the installer for the image built and published in the registry:

```sh
make build-installer IMG=<some-registry>/nawat:tag
```

**NOTE:** The makefile target mentioned above generates an 'install.yaml'
file in the dist directory. This file contains all the resources built
with Kustomize, which are necessary to install this project without its
dependencies.

2. Using the installer

Users can just run 'kubectl apply -f <URL for YAML BUNDLE>' to install
the project, i.e.:

```sh
kubectl apply -f https://raw.githubusercontent.com/<org>/nawat/<tag or branch>/dist/install.yaml
```

### By providing a Helm Chart

1. Build the chart using the optional helm plugin

```sh
kubebuilder edit --plugins=helm/v2-alpha
```

2. See that a chart was generated under 'dist/chart', and users
can obtain this solution from there.

**NOTE:** If you change the project, you need to update the Helm Chart
using the same command above to sync the latest changes. Furthermore,
if you create webhooks, you need to use the above command with
the '--force' flag and manually ensure that any custom configuration
previously added to 'dist/chart/values.yaml' or 'dist/chart/manager/manager.yaml'
is manually re-applied afterwards.

## Contributing
// TODO(user): Add detailed information on how you would like others to contribute to this project

**NOTE:** Run `make help` for more information on all potential `make` targets

More information can be found via the [Kubebuilder Documentation](https://book.kubebuilder.io/introduction.html)

## License

Copyright 2026 BSSConnects. All rights reserved.

This file is part of Nawat and is proprietary and confidential.
Unauthorized copying, modification, distribution or use of this file, via any
medium, is strictly prohibited. Use is permitted only under the terms of a
written licence agreement with BSSConnects.

SPDX-License-Identifier: LicenseRef-BSSConnects-Proprietary

