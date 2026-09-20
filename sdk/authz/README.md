# `sdk/authz` — authorization client

How a module asks "is this allowed?". Used by `sdk` and directly by modules that do not use
the SDK.

## The two questions

| Asked by | Where | Question |
|---|---|---|
| Envoy (`ext_authz`) | gateway and sidecar | may this subject call this method and path? |
| the module itself | in-process | may they see *this record*, *which fields*, *which rows*? |

The gateway cannot answer the second set — it does not know that a support agent may see a
subscriber's name but not their IMSI, or that a list must return one tenant's rows. That
decision has to happen next to the data.

## Example — the decision call

```go
// Check asks the local OPA sidecar. The endpoint is localhost, so this is roughly 1 ms;
// a shared authorization service would put a network hop on every request, which is
// unacceptable at mediation-adjacent throughput.
func (c *Client) Check(ctx context.Context, in Input) (*Decision, error) {
    body, _ := json.Marshal(map[string]any{"input": in})

    req, _ := http.NewRequestWithContext(ctx, http.MethodPost,
        c.opaURL+"/v1/data/platform/authz", bytes.NewReader(body))

    resp, err := c.http.Do(req)
    if err != nil {
        // FAIL CLOSED. An authorization system that allows requests when it cannot decide
        // is worse than one that is simply down. Note the contrast with pkg/license,
        // which fails OPEN — a licence outage must not stop CDR processing, but an authz
        // outage must not leak data.
        return nil, fmt.Errorf("authz unavailable: %w", err)
    }
    defer resp.Body.Close()

    var out struct{ Result Decision }
    if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
        return nil, err
    }
    return &out.Result, nil
}

// Input is the contract every module must satisfy. Keeping it identical everywhere is what
// lets ONE Rego policy serve every module — modules never write Rego.
type Input struct {
    Subject  Subject  `json:"subject"`  // id, groups, tenant — straight from the JWT
    Action   Action   `json:"action"`   // the permission id, e.g. "crm:subscriber:read"
    Resource Resource `json:"resource"` // type, id, tenant of the object being touched
}

// Decision carries more than a boolean, because "allowed" is not the whole answer.
type Decision struct {
    Allow bool `json:"allow"`

    // Redact lists fields to null out; Omit lists fields to remove entirely. Declared once
    // in __metadata__ and applied both server-side here and client-side by the Shell, so
    // the API and the UI can never disagree about what is hidden.
    Redact []string `json:"redact,omitempty"`
    Omit   []string `json:"omit,omitempty"`

    // Residual is the partial-evaluation result for LIST: a condition tree the module
    // translates into a WHERE clause. This is how "only rows you may see" is enforced
    // without fetching everything and filtering in memory.
    Residual *Condition `json:"residual,omitempty"`
}
```

The fail-closed/fail-open contrast with `sdk/license` is deliberate and worth stating in review:
the two packages look similar and must behave oppositely.
