# `cli/pkg/client` — the shared client library

**One API client, used by both the CLI and the UI Shell Service.** This is what guarantees the
CLI and the UI cannot drift apart.

## The important non-goal

The Shell Service does **not** execute the CLI binary. Both import this package. Spawning a
process per request would mean: a new OS process and TLS handshake every call, parsing text
instead of typed errors, no streaming, trace context lost at the process boundary — and worst,
the user's token would have to travel through a command line, an environment variable or a temp
file. The easy shortcut there is to run as a service account, which silently discards the entire
per-user permission model.

## Contents

```
generated/        produced by `make generate` from schemas/platform-api/openapi.yaml — never edited
auth.go           device flow, client credentials, token refresh, keyring
transport.go      retries with jitter, trace propagation, RFC 9457 decoding
resources.go      metadata-driven CRUD against any module's API
paging.go         iterator over the { items, page, total } envelope
```

## Example — a resource call that works for any module

```go
// List calls any module's collection endpoint using only its metadata. There is no
// CRM-specific code here, and there never will be — that is the whole point.
func (c *Client) List(ctx context.Context, res *metadata.Resource, q Query) (*Page, error) {
    u := c.baseURL.JoinPath(res.Module.BasePath, res.Paths.Collection)

    // Filters are validated LOCALLY against x-filterable before the request goes out, so a
    // typo gets an instant, precise error instead of a 400 from a module that may or may
    // not explain itself well.
    qs, err := q.Encode(res)
    if err != nil {
        return nil, fmt.Errorf("invalid query: %w", err)
    }
    u.RawQuery = qs

    req, _ := http.NewRequestWithContext(ctx, http.MethodGet, u.String(), nil)

    // The caller's own token, passed straight through. Never a service account: OPA must
    // see the real subject or tenant scoping and field redaction cannot work.
    if err := c.auth.Authorize(ctx, req); err != nil {
        return nil, err
    }

    resp, err := c.http.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    if resp.StatusCode >= 400 {
        // Decode RFC 9457 so callers get structured field errors rather than a string.
        return nil, DecodeProblem(resp)
    }

    var page Page
    if err := json.NewDecoder(resp.Body).Decode(&page); err != nil {
        return nil, err
    }

    // _redacted tells the caller which fields authorization removed, so the UI can show
    // "hidden — requires crm:subscriber:pii" instead of a confusing empty cell.
    return &page, nil
}
```
