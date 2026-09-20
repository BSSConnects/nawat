# `cmd/authz-service` — the Authorization Service

The **write side and source of truth** for authorization. OPA is the read/decision side;
this service owns the data OPA decides with.

It is *not* a policy engine, and it is not in the request path of any authorization decision.

## Responsibilities

1. Import each module's declared permissions from its `__metadata__` (via the registry).
2. Store roles, role bindings and field rules — PostgreSQL, not Redis. This is a system of
   record; Redis is a cache.
3. Serve the **bundle** (our Rego + generated JSON data) over HTTP for OPA to pull.
4. Emit data-update events for the **OPAL server** to push to every OPA in the cluster.

## Distribution: push for data, pull for policy

| What | Changes | Mechanism |
|---|---|---|
| Rego policy (ours) | on a platform release | bundle from an OCI artifact, polled |
| roles / bindings / field rules | whenever an admin clicks save | OPAL push, sub-second |
| fallback for both | — | bundle polled at 60 s; OPA persists it to disk so a restart during an outage still boots with working policy |

Phase 1 ships **polling only**. OPAL arrives in phase 2 — it is an optimisation of propagation
latency, not a prerequisite for correctness, and it is one more moving part while nothing works
end to end yet.

## Example — compiling roles into OPA data

```go
// BuildDataDocument converts the relational model into the flat JSON that OPA evaluates
// against. OPA never queries PostgreSQL: a database round-trip per request would be fatal
// at mediation-adjacent throughput, so we push a snapshot instead.
func (s *Service) BuildDataDocument(ctx context.Context) (*authz.Data, error) {
    roles, err := s.store.ListRoles(ctx)
    if err != nil {
        return nil, err
    }

    data := &authz.Data{
        Roles:    map[string]authz.Role{},
        Bindings: []authz.Binding{},
    }

    for _, r := range roles {
        // Expand `implies` now, not in Rego. Graph traversal in Rego is slow and hard to
        // read; an expanded flat set keeps the policy trivial and the decision fast.
        data.Roles[r.Name] = authz.Role{Permissions: s.catalog.Expand(r.Permissions)}
    }

    bindings, err := s.store.ListBindings(ctx)
    if err != nil {
        return nil, err
    }
    for _, b := range bindings {
        data.Bindings = append(data.Bindings, authz.Binding{
            // Subjects are usually GROUPS federated from the customer's LDAP/AD, matched
            // against the `groups` claim in the token. We do not manage their users.
            Subject: authz.Subject{Kind: b.SubjectKind, Name: b.SubjectName},
            Role:    b.RoleName,
            // Scope is how "only their own tenant" is expressed. It belongs on the
            // BINDING — modelling it as a permission produces an unusable role builder.
            Scope: authz.Scope{Tenant: b.Tenant, Self: b.Self},
        })
    }
    return data, nil
}
```
