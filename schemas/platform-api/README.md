# `schemas/platform-api/`

The API that the UI Shell, `bssconnectsctl` and the customer's own automation all call.
Written **before** the implementation, because three consumers are generated from it.

## Design

The Platform API is a **thin facade over the CRDs**. It does not hold its own data model:
`POST /modules/{id}/install` creates a `ModuleInstance` object and returns its status. This is
why the UI, the CLI and a customer's GitOps pipeline can never diverge — they all end up
writing the same Kubernetes objects.

## Surface (phase 1 scope marked ✅)

```yaml
openapi: 3.1.0
info:
  title: BSSConnects Platform API
  version: 0.1.0

paths:
  # ---- module registry: what is installed, and each module's metadata --------------
  /registry:
    get:
      summary: List installed modules with their versions and revisions
      # The CLI calls this on EVERY invocation with If-None-Match and normally gets a 304.
      # That is what makes the local metadata cache correct without a TTL.
      parameters:
        - { name: view, in: query, schema: { enum: [full, revisions] } }
      responses:
        "200": { description: OK }          # ✅ phase 1
        "304": { description: Not Modified } # ✅ phase 1

  /registry/{module}/metadata:
    get:
      summary: The validated __metadata__ document for one module   # ✅ phase 1
      # Served from the Module Registry, NOT proxied to the module. One fetch, one
      # validation, one consistent snapshot for every consumer.

  # ---- licences -------------------------------------------------------------------
  /licenses:
    post:
      summary: Upload a signed licence                              # ✅ phase 1
      requestBody:
        content:
          application/jose: {}    # the opaque signed blob; the server verifies it

  # ---- modules --------------------------------------------------------------------
  /modules/{id}:install:
    post:
      summary: Install an entitled module
      # `config` is validated against the module's own values.schema.json by an
      # admission webhook, so the caller gets a precise error at submit time rather
      # than three minutes into a failed rollout.
      responses:
        "202": { description: Accepted — watch ModuleInstance status }  # ✅ phase 1

  # ---- RBAC: roles and bindings. NOT user management --------------------------------
  /roles:
    get:  { summary: List roles }                                   # ✅ phase 1
    post: { summary: Create a role from permissions in the catalog } # ✅ phase 1
  /rolebindings:
    post:
      summary: Bind a subject to a role within a scope              # ✅ phase 1
      # Subjects are normally GROUPS federated from the customer's LDAP/AD.
      # We never become a second place where a leaver has to be deleted.
```

## Rules

- **Errors are RFC 9457 Problem Details** (the 2023 successor to RFC 7807), with an
  `errors[].field` array so a generated form can highlight the offending input.
- **Every list endpoint uses the same envelope** — `{ items, page, pageSize, total }` — and the
  same filter syntax as module APIs. One convention across the platform, not two.
- **`make generate` produces** the Go client in `pkg/client/` and TypeScript types in
  `web/shell/src/generated/`. Hand-written API clients are rejected in review.
