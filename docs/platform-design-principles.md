# Design principles

The rules every service in `cmd/`, every library in `pkg/`, and **every module** must follow.

Baseline: [the Twelve-Factor App](https://12factor.net/). It was written in 2011 for PaaS-hosted
web apps, so parts of it map cleanly onto Kubernetes, one factor needs correcting for our case,
and several things it never covered are mandatory for us. All three categories are below.

---

## 1. The twelve factors, mapped to our platform

| # | Factor | How it applies here |
|---|---|---|
| 1 | **Codebase** — one codebase, many deploys | One monorepo, one `platform-core` chart. The same artifacts run in a lab, a customer staging cluster and production — differences live in values, never in branches. Never a customer-specific fork. |
| 2 | **Dependencies** — explicitly declared, isolated | `go.mod` with pinned versions, pinned subchart versions, pinned image digests. No `latest` tag anywhere, ever: an air-gapped customer cannot resolve it and a floating tag makes a deploy irreproducible. |
| 3 | **Config** — in the environment | Service config comes from env vars, injected by the chart. **Customer** configuration is different — see §2. |
| 4 | **Backing services** — attached resources | A module never embeds Postgres or Kafka. It declares a capability; the operator provisions a CloudNativePG `Database` or Strimzi `KafkaTopic` and injects the coordinates. A module must work against a database it did not create. |
| 5 | **Build, release, run** — strictly separated | Build produces a signed image. Release is an immutable chart version plus values. Run changes nothing. No `kubectl edit` on a running deployment — Flux reverts it, which is the point. |
| 6 | **Processes** — stateless, share nothing | No in-process session state, no local disk for anything that must survive a restart. Our one in-memory cache (the Shell's bootstrap payload) is derived data that rebuilds itself. |
| 7 | **Port binding** — self-contained service | Each binary serves HTTP on a port. Istio handles TLS, routing and mTLS; services speak plain HTTP inside the pod. |
| 8 | **Concurrency** — scale out with processes | Horizontal scaling only. Every service must tolerate N replicas: no singleton assumptions, leader election for the operator, idempotent handlers. |
| 9 | **Disposability** — fast startup, graceful shutdown | `SIGTERM` → stop accepting, drain in-flight, exit inside `terminationGracePeriodSeconds`. Startup must not depend on another service being up — degrade and retry instead, or a dependency cycle deadlocks the whole platform on cold start. |
| 10 | **Dev/prod parity** | `hack/kind-up.sh` runs the same Istio, Keycloak, Flux and OPA as production. Different topology, identical components. A bug that only reproduces in production is a parity failure. |
| 11 | **Logs** — event streams | Structured JSON to stdout. Never a log file, never rotation, never a logging sidecar of our own. Collection is Loki's job. Trace id in every line, so logs join to traces. |
| 12 | **Admin processes** — one-off processes | Migrations and backfills are Kubernetes `Job`s shipped in the same image, or `bssconnectsctl` subcommands. Never `kubectl exec` into a running pod to fix something — that is an undocumented change that vanishes on the next restart. |

---

## 2. Where we deliberately deviate

### Factor 3, config in the environment, does not scale to customer configuration

Twelve-factor assumes config is a handful of strings. A mediation module's configuration is a
nested document with collectors, routing rules and enrichment tables — and it must be
**validated, versioned, auditable and editable through a UI**.

So we split it:

| Kind of config | Mechanism | Why |
|---|---|---|
| Service wiring (issuer URL, DB coordinates, OPA address) | **env vars**, injected by the operator | twelve-factor, and the customer never sees it |
| Customer configuration | **`ModuleInstance.spec.config`** in a CRD, validated against the module's `values.schema.json` | versioned by etcd, auditable, editable from the UI, GitOps-able |
| Secrets | **External Secrets Operator** → `Secret` → env var or file | never in a CRD, never in values, never in the repo |

The decision rule: *if a customer would ever want to change it, or audit who changed it, it goes in
a CRD. If only we set it, it is an env var.*

---

## 3. What twelve-factor does not cover, and we require anyway

Twelve-factor predates Kubernetes, operators and service meshes. These are not optional.

### Health, readiness and startup probes are distinct

```go
// /healthz — is this process alive? Must NOT check dependencies.
//
// Checking the database here means a brief database blip kills every replica at once:
// Kubernetes restarts them all, they all fail again, and a recoverable incident becomes
// an outage. Liveness answers one question: should this process be killed?
func healthz(w http.ResponseWriter, _ *http.Request) { w.WriteHeader(200) }

// /readyz — should this pod receive traffic right now? DOES check dependencies.
// A pod that cannot serve is removed from endpoints and comes back on its own.
func (s *Server) readyz(w http.ResponseWriter, r *http.Request) {
    if err := s.db.PingContext(r.Context()); err != nil {
        http.Error(w, "database unavailable", 503)
        return
    }
    w.WriteHeader(200)
}
```

Conflating these two is the single most common cause of self-inflicted cascading failure.

### Reconciliation, for anything that manages state

Our operator follows the controller pattern, not a procedural installer:

- **Idempotent.** Running reconcile twice changes nothing the second time.
- **Level-triggered, not edge-triggered.** Act on observed state, never on "an event arrived" —
  events are missed, and a missed event in an edge-triggered design leaves state wrong forever.
- **No ordering assumptions.** A `ModuleInstance` may arrive before its `License`. Requeue; do not
  fail.
- **Status is the only output a human reads.** If the operator knows something, it belongs in
  `status.conditions`, not only in a log line.
- **Every error is either retried with backoff or reported as a condition.** Never both silently
  neither.

### Observability is a requirement, not an add-on

Every service: `/metrics` in Prometheus format, OTel traces with context propagated from the
gateway, structured logs carrying the trace id. RED metrics for every HTTP surface (rate, errors,
duration) and queue depth plus age for every worker.

A service that cannot be debugged in production is not finished, regardless of whether it passes
its tests.

### Security defaults

- Non-root, read-only root filesystem, all capabilities dropped, seccomp `RuntimeDefault`.
- Resource requests **and** limits on every container. No limits means one module can starve
  Mediation on a shared node.
- Secrets via ESO; never in env vars that get logged, never in a CRD spec.
- mTLS between all services, via Istio. Every service re-validates the JWT even though the gateway
  already did — zero trust means a workload does not become trustworthy by being inside the cluster.
- Images signed with cosign, verified at admission. Signing without verification proves nothing.

### API and contract versioning

- `apiVersion` on every CRD and on the module contract; alpha → beta → stable with real meaning.
- Additive changes only within a version. Removing or renaming a field needs a new version and a
  migration path.
- Two versions served concurrently during a migration window, because **customers cannot upgrade
  every module on the same day**. Designing as if they can is the most common way a platform
  becomes unshippable.

### Multi-tenancy is in the data model, not bolted on

Every tenant-scoped resource declares its `tenantField` in its metadata, and list filtering is
enforced by OPA. Adding tenancy later means touching every query in every module — so it is
present from the first resource we write, even while every customer is single-tenant.

---

## 4. Module-specific rules

Beyond everything above, a module must:

1. Serve `__metadata__`, and **fail its readiness probe if that document does not validate**. A
   module with a broken contract should never receive traffic and produce broken screens.
2. Use `pkg/sdk`, or pass `test/conformance` — the suite is the definition of conformance for a
   module written without the SDK.
3. Declare four to seven permissions per resource. Scopes and field rules are **not** permissions;
   modelling them as permissions produces a role builder no customer can use.
4. Never call another module's database. Cross-module integration is APIs and Kafka events only.
5. Never render its own login, its own navigation, or its own permission UI.
6. Tolerate the platform being partially down: if the Authorization Service is unreachable, **fail
   closed**; if the License Service is unreachable, **fail open with a warning**. These look alike
   and must behave oppositely — authorization protects data, licensing protects revenue, and only
   one of those justifies dropping a customer's traffic.
7. Emit declared events with stable schemas. An event others consume is an API.

---

## 5. The two questions to ask in review

**"What happens when this dependency is down?"** Asked of every external call. If the answer is
"it crashes" or "it hangs", the PR is not finished.

**"Does this put a product name into Platform Core?"** If yes, it belongs in a module or in the
contract. This is the rule the whole platform rests on, and it erodes one reasonable-looking
special case at a time.
