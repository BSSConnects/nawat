# `cmd/license-service` — the License Service

The **only** component that holds licence verification logic.

The `License` CRD is storage and API surface — `kubectl`-able, GitOps-able, backed up with the
cluster. This service is the only writer of `License.status`, enforced by RBAC on the status
subresource.

## Why a service and not just the operator

- Verification logic must exist in exactly one place, never duplicated into modules.
- Runtime questions need a live endpoint: *is feature `contracts` enabled? how much quota is
  left?* Modules must not read etcd.
- Quota accounting needs aggregated state across replicas.
- Expiry, grace periods and warnings need a timer, not a reconcile loop.

## Enforcement happens twice

**At install time** (the operator asks) and **at runtime inside the module** (via the licence
SDK in `sdk/license`). Install-time gating alone is trivially bypassed by anyone who can edit a
`ModuleInstance`.

## Example — verification

```go
// Verify parses and checks a licence token. Offline only: no network call, because telco
// installations are frequently air-gapped and a licence must work with no route to us.
func (v *Verifier) Verify(token string) (*License, error) {
    // Pin the algorithm. Accepting whatever the token's header claims is the classic JWT
    // algorithm-confusion vulnerability; refusing anything but EdDSA removes it in one line.
    parsed, err := jose.ParseSignedCompact(token, []jose.SignatureAlgorithm{jose.EdDSA})
    if err != nil {
        return nil, fmt.Errorf("malformed licence: %w", err)
    }

    // kid selects from a small embedded keyring so we can rotate signing keys without
    // invalidating every licence already in the field.
    kid := parsed.Signatures[0].Header.KeyID
    pub, ok := v.keyring[kid]
    if !ok {
        return nil, fmt.Errorf("unknown signing key %q", kid)
    }

    payload, err := parsed.Verify(pub)
    if err != nil {
        return nil, fmt.Errorf("signature invalid: %w", err)
    }

    var lic License
    if err := json.Unmarshal(payload, &lic); err != nil {
        return nil, err
    }

    // Expiry is reported, NOT enforced by refusing to return the licence. The caller
    // decides what an expired licence means: the operator blocks a NEW install, while a
    // running mediation node keeps processing CDRs inside the grace period. A licence
    // must never stop a live telco workload at midnight.
    lic.Expired = time.Now().After(lic.NotAfter)
    return &lic, nil
}
```

## Signing

The private key never enters this repository or the cluster. It lives in an HSM or on an
offline signing machine; `hack/licence-sign/` is the operator-facing tool. The public keyring is
compiled into this service's image and into `sdk/license`.
