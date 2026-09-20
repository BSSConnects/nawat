# `sdk/metadata`

Go types and validation for the module contract. The first package we write, and the one
everything else depends on.

## Contents

```
types.go          structs mirroring schemas/module-metadata/v1alpha1.json
validate.go       the 10 cross-field rules JSON Schema cannot express
registry.go       an in-memory view of all installed modules
schema.go         embedded copy of the JSON Schema (go:embed) for structural validation
cache.go          on-disk cache used by the CLI, keyed by metadataRevision
```

## Example — structural then semantic validation

```go
package metadata

import _ "embed"

//go:embed schema/v1alpha1.json
var schemaBytes []byte // embedded so the validator works offline and cannot drift from the binary

// Validate runs structural validation (JSON Schema) and then the cross-field rules.
// Returns ALL problems, not just the first — a module author fixing one error at a time
// across ten round-trips will start to resent the contract.
func Validate(doc []byte) (*ModuleMetadata, []Problem) {
    var problems []Problem

    // 1. Structural. This is why every custom keyword is x- prefixed: the document stays
    //    valid JSON Schema and any standard library can check it.
    if errs := jsonschema.Validate(schemaBytes, doc); len(errs) > 0 {
        return nil, toProblems(errs)
    }

    var m ModuleMetadata
    if err := json.Unmarshal(doc, &m); err != nil {
        return nil, []Problem{{Path: "$", Message: err.Error()}}
    }

    // 2. Cross-field rules. Rule 2 below catches the most common real-world bug: a field
    //    renamed in the schema but still referenced by a column, which shows up in
    //    production as a silently blank table cell that nothing alerts on.
    for i, res := range m.Resources {
        fields := res.Schema.PropertyNames()

        for _, col := range res.List.Columns {
            if !fields.Has(col.Field) {
                problems = append(problems, Problem{
                    Path: fmt.Sprintf("$.resources[%d].list.columns", i),
                    Message: fmt.Sprintf("column %q is not a property of %s",
                        col.Field, res.Type),
                })
            }
        }

        // Permission ids must be namespaced to this module, so a module cannot grant
        // itself rights inside another module's namespace.
        for verb, perm := range res.Permissions {
            if !strings.HasPrefix(perm, m.Module.ID+":") {
                problems = append(problems, Problem{
                    Path: fmt.Sprintf("$.resources[%d].permissions.%s", i, verb),
                    Message: fmt.Sprintf("permission %q must start with %q", perm, m.Module.ID+":"),
                })
            }
        }
    }

    // Cycles in `implies` would make permission expansion loop forever in the authz service.
    if cycle := findImpliesCycle(m.Permissions); cycle != nil {
        problems = append(problems, Problem{
            Path:    "$.permissions",
            Message: "implies cycle: " + strings.Join(cycle, " -> "),
        })
    }

    if len(problems) > 0 {
        return nil, problems
    }
    return &m, nil
}
```
