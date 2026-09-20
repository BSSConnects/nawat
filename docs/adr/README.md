# Architecture Decision Records

One file per significant decision: `NNNN-short-title.md`.

Template:

```markdown
# ADR-NNNN — <title>

**Status:** proposed | accepted | superseded by ADR-XXXX
**Date:** YYYY-MM-DD
**Deciders:** <names>

## Context
What forces are at play. Constraints (air-gapped, telco, team size, existing stack).

## Options considered
| Option | Pros | Cons |

## Decision
What we chose and the deciding reason.

## Consequences
What becomes easy, what becomes hard, what we must now also build or staff.
```

## Index

| ADR | Title | Status |
|---|---|---|
| 0001 | Identity provider: Keycloak | to write |
| 0002 | Authorization: central service + OPA, permissions not in the JWT | to write |
| 0003 | Deployment engine: custom operator emitting Flux objects | to write |
| 0004 | Ingress: Istio vs Envoy Gateway | **open** |
| 0005 | License format: JWS/Ed25519 over PASETO | to write |
| 0006 | UI: metadata-driven renderer + Module Federation, Backstage rejected | to write |
| 0007 | Chart & descriptor distribution as OCI artifacts in Harbor | to write |
| 0008 | Policy distribution: OPAL push for data, bundle pull for policy | **needs spike** |
| 0009 | Module `__metadata__` contract as the single source for UI, CLI and authz | to write |
