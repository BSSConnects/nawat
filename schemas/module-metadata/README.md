# `schemas/module-metadata/`

The module contract. A module that satisfies this schema gets a generated admin UI, generated
CLI commands, generated API documentation and automatic permission registration — without
writing frontend code.

**Full specification:** [../../docs/design/example__metadata__.md](../../docs/design/example__metadata__.md)
**Worked example:** [../../examples/hello-module/__metadata__.json](../../examples/hello-module/)

## Files

```
v1alpha1.json           the schema itself
testdata/
  valid/
    minimal.json        the smallest document that must pass
    crm-full.json       the full CRM example — every feature exercised
  invalid/
    missing-id.json     each file documents ONE rule being broken,
    bad-permission.json   with the expected error in a sibling .error.txt
    column-not-in-schema.json
```

## Validation rules the schema cannot express

JSON Schema checks structure. These ten cross-field rules are implemented in
`pkg/metadata` and run by `bssconnectsctl module validate`:

1. Every `schema` block is itself valid JSON Schema 2020-12.
2. Every field named in `list.columns`, `list.filters`, `list.search`, `detail.sections`,
   `identity.*` and `authorization.*` exists in that resource's `schema.properties`.
3. Every permission referenced anywhere exists in the `permissions` catalog.
4. Every permission id starts with `module.id`.
5. The `implies` graph is acyclic.
6. Relation targets resolve — inside the module, or marked `optional` if cross-module.
7. Action ids in `list.rowActions` / `bulkActions` exist in `actions`.
8. `metadataRevision` changed if anything else changed (compared to the previous tag).
9. Declared `capabilities` match the routes the SDK actually registered.
10. No two resources share a `type`.

Rule 2 is the one that catches real bugs: a renamed field leaves a blank column in
production, and nothing else notices.

## Versioning

`v1alpha1.json` today. Additive changes edit this file in place and bump the minor version of
the repo. A breaking change creates `v1beta1.json` **alongside** it — the platform serves both
during a migration window, because customers cannot upgrade every module on the same day.
