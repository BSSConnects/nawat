# `deploy/policies/` — the Rego bundle

**One policy, written by us, identical for every module. Module teams never write Rego.**

That is the single most important property here. If modules wrote their own policies, we would
have per-module authorization bugs and no way to audit the system as a whole.

## Contents

```
authz/
  main.rego           the entry point: allow, redact, omit, residual
  permissions.rego    expand wildcards, resolve role -> permission
  scope.rego          tenant, owner and self scoping
  fields.rego         field-level rules
  main_test.rego      table-driven tests — these are our authorization test suite
bundle.yaml           manifest: roots, revision
```

## Example

```rego
package platform.authz

import rego.v1

# Deny by default. Every rule below must ADD permission; nothing subtracts.
default allow := false

# Effective permissions for this subject, from data pushed by the Authorization Service.
# `implies` is already expanded by that service, so no graph traversal here — Rego is slow
# at that and hard to read when doing it.
effective contains perm if {
    some binding in data.bindings
    subject_matches(binding.subject, input.subject)
    scope_matches(binding.scope, input.resource)
    some perm in data.roles[binding.role].permissions
}

allow if {
    some perm in effective
    grants(perm, input.action.permission)   # handles "crm:subscriber:*"
}

# Fields to null out. Declared once in the module's __metadata__ and applied both here
# (server side) and by the Shell (client side), so the API and UI cannot disagree.
redact contains field if {
    some rule in data.field_rules[input.resource.type]
    rule.onDeny == "redact"
    some field in rule.fields
    not holds(rule.requires)
}

# For LIST requests the answer is not yes/no — it is "these rows". Return the scopes the
# caller is entitled to and let the module translate them into a WHERE clause.
residual := {"scopes": scopes} if {
    input.action.verb == "list"
    scopes := {s | some b in data.bindings
                   subject_matches(b.subject, input.subject)
                   s := b.scope}
}

subject_matches(s, subj) if s.kind == "Group"; s.name in subj.groups
subject_matches(s, subj) if s.kind == "User";  s.name == subj.id
```

## Testing

`opa test deploy/policies -v` runs in CI. Treat these tests as seriously as production code: a
missing case here is a data breach, not a cosmetic bug. Every new scope or field rule lands with
both a positive and a negative test.
