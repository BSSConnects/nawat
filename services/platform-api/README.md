# `cmd/platform-api` — the Platform API

A **thin facade over the CRDs**. It holds no data model of its own: `POST /modules/crm:install`
creates a `ModuleInstance` and returns its status.

Why a facade at all, if the CRDs are the API? Because a browser cannot hold a kubeconfig, and
because we want one place to apply per-user authorization, shape responses into the platform
envelope, and aggregate across objects. Customers who *do* have cluster access can skip it
entirely and use `kubectl` — both paths are supported, and both converge on the same objects.

**Contract:** [../../schemas/platform-api/openapi.yaml](../../schemas/platform-api/)
Generated from it: the Go client in `pkg/client/`, TypeScript types in `web/shell/`.

## Example — a handler

```go
// POST /roles
func (h *Handler) CreateRole(w http.ResponseWriter, r *http.Request) {
    var req client.CreateRoleRequest
    if err := httpx.DecodeJSON(r, &req); err != nil {
        httpx.WriteProblem(w, httpx.BadRequest("invalid JSON body", err))
        return
    }

    // Every permission must exist in the catalog built from installed modules'
    // __metadata__. This rejects typos and — more importantly — rejects a role that
    // references a module the customer has not licensed.
    if unknown := h.Catalog.Unknown(req.Permissions); len(unknown) > 0 {
        httpx.WriteProblem(w, httpx.Problem{
            Type:   "https://errors.bssconnects.io/platform/unknown-permission",
            Title:  "Unknown permission",
            Status: 422,
            // errors[].field is what lets the generated form highlight the bad input
            // instead of showing an unhelpful toast.
            Errors: httpx.FieldErrors("permissions", unknown),
        })
        return
    }

    role := &platformv1alpha1.Role{
        ObjectMeta: metav1.ObjectMeta{Name: req.Name, Namespace: h.SystemNamespace},
        Spec:       platformv1alpha1.RoleSpec{Permissions: req.Permissions},
    }

    // Act as the CALLING USER, not as our own service account. The API server's own RBAC
    // then backs up our authorization check — defence in depth, and the audit log shows
    // the real actor rather than "platform-api".
    if err := h.ClientFor(r.Context()).Create(r.Context(), role); err != nil {
        httpx.WriteProblemFromKubeErr(w, err)
        return
    }
    httpx.WriteJSON(w, 201, client.RoleFrom(role))
}
```

The "act as the calling user" line is worth defending in review: it is tempting to use the
service account because it always works, and that silently discards the entire per-user
permission model.
