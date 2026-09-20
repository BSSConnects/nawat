# `services/` — the platform control-plane services

One Go module, four binaries. They are grouped because they share the same wiring, telemetry and
HTTP middleware, and are released together as part of `platform-core`.

| Service | Role | Build order |
|---|---|---|
| [`license-service`](license-service/) | verifies licences, owns entitlements | phase 1 |
| [`platform-api`](platform-api/) | facade over the CRDs for the UI and CLI | phase 1 |
| [`authz-service`](authz-service/) | permission catalog, roles, OPA data source | phase 1 |
| [`shell-service`](shell-service/) | static assets + `/bootstrap` | phase 1, last |

```
services/
  cmd/<service>/          main.go per binary
  internal/               shared: config, telemetry, httpx (RFC 9457), kube helpers
  <service>/README.md     what each one does and does not do
```

## Rules

- Every service exposes `/healthz`, `/readyz` and `/metrics`, and shuts down gracefully on SIGTERM.
- Configuration from environment variables; **customer** configuration lives in CRDs.
  See [../docs/platform-design-principles.md](../docs/platform-design-principles.md) §2.
- These import `sdk/`. They must never import `operator/`.
