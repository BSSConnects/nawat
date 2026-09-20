# `test/conformance`

Point it at a running module; it reads the module's own `__metadata__` and verifies the
implementation matches what was declared.

```bash
go test ./test/conformance -target http://localhost:8080/api/hello/v1
```

## What it checks

| Area | Checks |
|---|---|
| metadata | valid against the schema; all ten cross-field rules pass |
| declared vs. real | every `capabilities: true` verb actually responds; every `actions[].path` exists |
| query syntax | `q`, every filter operator, `sort` ascending and descending, paging boundaries |
| envelope | `{ items, page, pageSize, total }`; `total` consistent across pages |
| errors | RFC 9457 shape; `errors[].field` present on validation failures |
| authorization | a token without the permission gets 403; redacted fields absent or null; list returns only in-scope rows |
| licence | a gated feature is rejected when the entitlement is absent |
| operations | `/healthz`, `/readyz`, `/metrics`, `/openapi.json` respond |

## Example

```go
// Declared capabilities must match reality. A module that advertises delete:true but returns
// 405 produces a delete button in the generated UI that always fails — and nothing else in
// the system would ever notice.
func TestCapabilitiesAreReal(t *testing.T) {
    meta := fetchMetadata(t, target)

    for _, res := range meta.Resources {
        t.Run(res.Type, func(t *testing.T) {
            if res.Capabilities.List {
                resp := get(t, target+res.Paths.Collection)
                require.Equal(t, 200, resp.StatusCode,
                    "capabilities.list is true but the collection endpoint does not respond")

                var page Envelope
                require.NoError(t, json.NewDecoder(resp.Body).Decode(&page))
                // The envelope is not negotiable: the generated UI and CLI both depend on
                // these exact field names to paginate.
                require.NotNil(t, page.Items, "response must use the platform envelope")
            }

            if !res.Capabilities.Delete {
                // Declaring delete:false must mean it is actually unavailable. An endpoint
                // that exists but is hidden from the UI is a security hole, not a feature.
                resp := del(t, target+strings.Replace(res.Paths.Item, "{id}", "probe", 1))
                require.Contains(t, []int{404, 405}, resp.StatusCode)
            }
        })
    }
}

// Field rules must be enforced SERVER SIDE. The Shell hides these fields too, but a caller
// using curl with a valid token must not receive them either.
func TestFieldRedaction(t *testing.T) {
    meta := fetchMetadata(t, target)
    for _, res := range meta.Resources {
        for _, rule := range res.Authorization.FieldRules {
            tok := tokenWithout(t, rule.Requires)
            body := getJSON(t, target+res.Paths.Collection, tok)
            for _, f := range rule.Fields {
                require.True(t, absentOrNull(body, f),
                    "field %q leaked to a caller lacking %q", f, rule.Requires)
            }
        }
    }
}
```
