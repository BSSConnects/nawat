# `cmd/shell-service` — the UI Shell Service

**A static file server plus one JSON endpoint.** No server-side rendering. Nothing rebuilt per
request. Not in the data path.

## What it serves

| Route | Returns |
|---|---|
| `/` , `/assets/*` | the compiled SPA from `web/shell/dist` — identical for every user |
| `/bootstrap` | one JSON payload: nav tree, metadata for modules this user may see, resolved permissions |
| `/ui/<module>/*` | micro-frontend remote entries for modules with custom screens |

After the first load, the browser talks **directly to module APIs through the gateway**. A user
working all day touches this service two or three times.

## What it must never become

- A proxy for data requests. That adds a hop, creates a bottleneck in front of
  Mediation-scale traffic, and forces it to re-attach user identity on every call.
- A place where authorization decisions are made. It hides buttons the user cannot use; the
  server still enforces.
- Stateful. It can be killed at any moment and the platform loses only its face, not a
  capability.

## Example — the bootstrap handler

```go
// GET /bootstrap
func (h *Handler) Bootstrap(w http.ResponseWriter, r *http.Request) {
    sub := httpx.SubjectFrom(r.Context()) // from the JWT the gateway already verified

    // Cache key = registry revision + hash of this subject's permission set. Two users
    // with the same role share one cached payload, so this is cheap even with many users.
    key := h.cacheKey(sub)
    if payload, etag, ok := h.cache.Get(key); ok {
        if match := r.Header.Get("If-None-Match"); match == etag {
            w.WriteHeader(http.StatusNotModified) // the common case on reload
            return
        }
        httpx.WriteJSONWithETag(w, 200, payload, etag)
        return
    }

    // Read the Module Registry — NOT each module's __metadata__ endpoint. The operator
    // already fetched and validated it once, so every consumer sees one consistent
    // snapshot even during a rolling module upgrade.
    mods, rev, err := h.Registry.List(r.Context())
    if err != nil {
        httpx.WriteProblem(w, httpx.Upstream("module registry unavailable", err))
        return
    }

    // Filter by permission here so the browser never receives metadata for screens the
    // user cannot open. This is a privacy measure, not a security one — the server still
    // enforces on every request.
    payload := shell.BuildBootstrap(mods, sub, rev)
    etag := shell.ETag(payload)
    h.cache.Put(key, payload, etag)
    httpx.WriteJSONWithETag(w, 200, payload, etag)
}
```

## Build order: last

Build this after the CLI proves the contract. Then most of the work is rendering, not
discovering that the contract was wrong.
