# `sdk/license` — the licence SDK

Embedded in every module so licence enforcement happens at **runtime**, not only at install.
Install-time gating alone is trivially bypassed by anyone who can edit a `ModuleInstance`.

## Example — feature and quota checks

```go
// Enabled reports whether a licensed feature is active.
//
// Cached for 60 s. FAILS OPEN with a warning: if the License Service is restarting, a
// mediation node must keep processing CDRs. A licensing system that can halt a live telco
// workload is a worse outage than an unlicensed feature running for a minute.
//
// Contrast pkg/authz, which fails CLOSED. These two look alike and must behave oppositely:
// authorization protects data, licensing protects revenue, and only one of those justifies
// dropping traffic.
func (c *Client) Enabled(ctx context.Context, feature string) bool {
    ent, err := c.entitlements(ctx)
    if err != nil {
        c.log.Warn("licence check degraded, allowing", "feature", feature, "err", err)
        c.metrics.DegradedChecks.Inc() // alertable: someone must notice this
        return true
    }
    return slices.Contains(ent.Features, feature)
}

// ReportUsage sends a counter the License Service aggregates across replicas for quota
// accounting. Fire-and-forget: never block a request to report a number.
func (c *Client) ReportUsage(quota string, n int64) {
    select {
    case c.usage <- usagePoint{Quota: quota, N: n}:
    default:
        // Channel full — drop the sample rather than apply backpressure to the caller.
        c.metrics.DroppedUsage.Inc()
    }
}
```

## Quota behaviour

Exceeding a quota raises an alert and a prominent UI warning. It does **not** reject traffic.
Customers will accept a warning; they will not accept a platform that drops CDRs because a
counter rolled over at month end. If a hard limit is ever required, that is a commercial
decision recorded in an ADR, not a default.
