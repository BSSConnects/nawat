# `sdk/` — the public Go module

Everything here is imported by **module teams**, so it carries compatibility obligations:
breaking an API here breaks other people's builds.

| Package | Purpose | Imported by |
|---|---|---|
| `sdk` (this package) | build a conformant module | every module |
| [`sdk/metadata`](metadata/) | module-contract types + validation | operator, CLI, authz service, validator |
| [`sdk/authz`](authz/) | ask OPA for a decision | every module |
| [`sdk/license`](license/) | feature and quota checks at runtime | every module, operator |

**Its own Go module, deliberately.** A module team importing this must not be forced to pull
in controller-runtime and the whole Kubernetes client. It is also versioned and tagged
separately (`sdk/v0.3.0`), because module teams upgrade on their own schedule.

**Nothing here may import `operator/`.** The dependency arrow points one way: everything
depends on the SDK; the SDK depends on nobody in this repo.


**The most important package for adoption.** A module team should get platform conformance by
using this, not by reading a specification and hoping.

If conformance requires care, teams will get it wrong. If it requires importing this package,
they will get it right.

## What it provides

| Concern | What the SDK does |
|---|---|
| `__metadata__` | serves it, derives it from registered resources, validates at startup |
| query parsing | `?q=`, `filter[x][gte]=`, `sort=-createdAt`, `page`/`pageSize` |
| response envelope | `{ items, page, pageSize, total }` |
| errors | RFC 9457 Problem Details with `errors[].field` |
| authorization | calls the local OPA sidecar; applies field redaction; converts partial-eval residuals into SQL predicates |
| licence | feature checks and quota reporting with a 60 s cache |
| observability | `/metrics`, `/healthz`, `/readyz`, OTel tracing |
| OpenAPI | generates `/openapi.json` from the same definitions |

## Example — registering a resource

```go
func main() {
    mod := sdk.NewModule(sdk.Config{
        ID:       "hello",
        Version:  "0.1.0",
        BasePath: "/api/hello/v1",
    })

    sdk.Register(mod, sdk.Resource[Widget]{
        Type:       "hello/Widget",
        Names:      sdk.Names{Singular: "Widget", Plural: "Widgets", Collection: "widgets"},
        // Schema is generated from the struct tags below, so the API, the generated UI and
        // the Go type can never disagree about what a Widget is.
        Identity:   sdk.Identity{IDField: "id", DisplayField: "name"},
        Permissions: sdk.Permissions{
            Read:  "hello:widget:read",
            Write: "hello:widget:write",
        },
        Authorization: sdk.Authorization{
            TenantField:   "tenantId",
            ListFiltering: sdk.PartialEval, // OPA returns a predicate; the SDK applies it
        },
        Store: store, // implements sdk.Store[Widget]
    })

    // ListenAndServe validates the generated metadata against the embedded JSON Schema
    // BEFORE binding the port. A module with a broken contract fails its readiness probe
    // instead of starting and producing broken screens.
    log.Fatal(mod.ListenAndServe(":8080"))
}

// Widget's struct tags ARE the contract. x-* tags become the UI hints the Shell renders,
// so there is no second place to update when a field changes.
type Widget struct {
    ID       string    `json:"id"        meta:"readOnly,hidden"`
    TenantID string    `json:"tenantId"  meta:"readOnly,hidden"`
    Name     string    `json:"name"      meta:"title=Name,searchable,sortable" validate:"required,min=2"`
    Status   string    `json:"status"    meta:"title=Status,badge,filterable" enum:"active,retired"`
    // Sensitive fields are never logged, masked in the UI, and excluded from exports
    // unless the caller holds the named permission.
    Serial   string    `json:"serial"    meta:"title=Serial,sensitive,permission=hello:widget:pii"`
    Created  time.Time `json:"createdAt" meta:"readOnly,sortable,filterable"`
}
```

## Languages

Go first, because our modules are Go. A TypeScript and a Java SDK follow only when a real module
needs them — not speculatively. Until then, the conformance suite in `test/conformance` is the
contract for any module not using this SDK.
