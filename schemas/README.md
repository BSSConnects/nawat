# `schemas/` — the contracts

**The two most important files in the repository live here.** Five separate components read
them; a careless change breaks all five at once.

| File | Defines | Consumed by |
|---|---|---|
| `module-metadata/v1alpha1.json` | what a module must declare about itself | UI Shell, CLI, Authorization Service, Operator, docs generator |
| `platform-api/openapi.yaml` | the Platform API the UI and CLI call | client library, CLI, UI Shell, customer automation |

## Rules for this directory

1. **Two approvals and an ADR** for any change. Enforced by CODEOWNERS.
2. **Additive changes bump the minor version. Breaking changes need a new `apiVersion`.**
   See [../docs/design/example__metadata__.md](../docs/design/example__metadata__.md) §10 for the
   compatibility table.
3. **Generated code is never hand-edited.** `make generate` produces Go types from these
   schemas into `pkg/metadata/` and TypeScript types into `web/shell/src/generated/`.
4. **Every schema change ships with a test case** in `testdata/` — one valid document and
   one that must be rejected.

## Why schemas before code

Writing `bssconnectsctl module validate` against this schema is the cheapest way to discover
everything vague in the design. You cannot write a validator for a rule you have not decided.
That is why the validator is the first binary we build, not the operator.

## Example — the shape of `module-metadata/v1alpha1.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://bssconnects.io/schemas/module-metadata/v1alpha1.json",
  "title": "ModuleMetadata",
  "type": "object",
  "required": ["apiVersion", "kind", "module", "permissions", "resources"],
  "properties": {
    "apiVersion": { "const": "platform.bssconnects.io/v1alpha1" },
    "kind":       { "const": "ModuleMetadata" },

    "module": {
      "type": "object",
      "required": ["id", "version", "basePath", "metadataRevision"],
      "properties": {
        // the module id must match the id in the ModuleDescriptor shipped with the chart,
        // and is also the mandatory prefix of every permission this module declares
        "id":       { "type": "string", "pattern": "^[a-z][a-z0-9-]{1,30}$" },
        "basePath": { "type": "string", "pattern": "^/api/[a-z0-9-]+/v[0-9]+$" },
        // cache key for the whole chain: operator -> registry -> shell -> browser.
        // MUST be generated from a content hash in the build, never maintained by hand
        "metadataRevision": { "type": "string" }
      }
    },

    "permissions": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "displayName"],
        "properties": {
          // format is <module>:<resource>:<action> — the <module> segment is validated
          // against module.id at load time, so a module cannot declare permissions
          // inside another module's namespace
          "id": { "type": "string", "pattern": "^[a-z0-9-]+:[a-z0-9-]+:[a-z0-9-]+$" },
          // these two strings are what a customer's security officer reads in the role
          // builder. Write them for that person, not for a developer
          "displayName": { "type": "string", "minLength": 3 },
          "description": { "type": "string" },
          // granting `write` grants `read` transitively. The graph must be acyclic
          "implies": { "type": "array", "items": { "type": "string" } }
        }
      }
    }

    // ... resources[], navigation[], suggestedRoles[] — see the design doc
  }
}
```

> JSON Schema has no comment syntax. The `//` comments above are for this README only —
> strip them in the real file, and put explanations in `description` keywords instead.
