# nawat

The unified platform that hosts Mediation, Roaming, CRM, Interconnect and every future OSS/BSS
product as installable **modules** on Kubernetes.

One login, one UI, one permission model, one licence mechanism, one install procedure. Install a
licence, and a product's screens, permissions, CLI commands and dashboards appear.

> **New here?** Read [docs/README.md](docs/README.md) first — team guide, GitHub workflow, design
> principles, and the required-knowledge map.

---

## The one rule

**Platform Core must never contain the word "Mediation".**

If adding a product requires changing core, we have not built a platform — we have built a bigger
monolith. Products describe themselves through the **module contract** in
[`schemas/module-metadata/`](schemas/module-metadata/); core reads that contract and adapts.

---

## Layout

Several Go modules plus an npm workspace, tied together by [`go.work`](go.work).

| Path | What | Toolchain |
|---|---|---|
| [`schemas/`](schemas/) | **the two contracts** everything else depends on | JSON Schema, OpenAPI |
| [`operator/`](operator/) | kubebuilder project: CRDs + controllers | Go module |
| [`sdk/`](sdk/) | what **module teams** import — contract types, authz, licence | Go module (public API) |
| [`cli/`](cli/) | `bssconnectsctl` and the shared API client | Go module |
| [`services/`](services/) | licence, platform-api, authz, shell services | Go module |
| [`web/`](web/) | UI Shell and design system | npm workspace |
| [`deploy/`](deploy/) | the `platform-core` chart, Rego policies | YAML, Rego |
| [`examples/`](examples/) | `hello-module` — reference module and conformance target | Go |
| [`test/`](test/) | conformance suite and end-to-end tests | Go |
| [`hack/`](hack/) | kind, Tilt, codegen, dev scripts | Bash |
| [`docs/`](docs/) | design, ADRs, team guides | Markdown |

**Why the operator is in a subdirectory and not at the root:** kubebuilder owns a project root —
`PROJECT`, `config/`, `Dockerfile`, its own `Makefile`. At the repository root those would make this
look like an operator project, when it is a platform repository that also holds a React app, a CLI,
four services and Helm charts. `operator/` keeps kubebuilder's world scoped to the operator.

**Dependency direction — one way only:**

```
operator/  ─┐
cli/       ─┼──► sdk/ ──► schemas/
services/  ─┘
web/       ────────────►  schemas/   (generated TypeScript types)
```

Nothing may import `operator/`. The SDK depends on nobody in this repo. A pull request that breaks
that arrow gets rejected — it is what lets a module team import the SDK without pulling in
controller-runtime.

## Go workspace

```bash
go work sync          # after adding or changing a module
go build ./...        # inside a module directory
```

`go.work` **is committed** — it is how the modules see each other during development. Release builds
set `GOWORK=off` so dependencies resolve from each module's own `go.mod`, exactly as an external
consumer would get them.

## Quickstart

```bash
make help              # every target
make dev-up            # kind + Istio + Keycloak + Flux, then Tilt
make -C operator help  # kubebuilder's own targets
```

## Current phase

**Phase 0 — contracts and inner loop.** See [docs/design/10-rollout-plan.md](docs/design/10-rollout-plan.md).

The two files in `schemas/` block five consumers each, so they are written first — and the first
binary is `bssconnectsctl module validate`, not the operator. You cannot write a validator for a
rule nobody has decided, which is exactly why writing it settles the contract.
