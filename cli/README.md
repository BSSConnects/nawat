# `cli/` — BSSConnectsCLI

Its own Go module. Builds `bssconnectsctl`, the primary client of the platform and **the first
binary we build**.

```
cli/
  cmd/bssconnectsctl/     main.go, command tree
  pkg/client/             the shared API client — imported by services/shell-service too
  internal/               config, contexts, credentials, metadata cache
```


**The first binary we build, and the primary client of the platform.**

Principle: *anything the UI can do, the CLI can do.* Not a subset. If a capability exists only
in the UI, that is a bug.

**Full design:** [../../docs/design/09-cli.md](../../docs/design/09-cli.md)

## Build order

| Step | Command | Why this order |
|---|---|---|
| 1 | `module validate <file>` | needs no cluster, no auth, no API — forces the schema to be real |
| 2 | `login`, `context` | device flow, config file, keyring |
| 3 | `module list` / `install` | first real Platform API calls |
| 4 | `<module> <resource> list/get` | first metadata-driven command generation |
| 5 | actions, `apply -f`, output formats | |

Step 1 being first is the whole point of phase 0: a validator cannot be written for a rule
nobody has decided, so writing it surfaces every vague corner of the contract in days rather
than months.

## Commands are generated, not compiled in

`bssconnectsctl crm subscribers list` works because CRM declared that resource in its
`__metadata__` — **not** because a release of the CLI added CRM support. A module we have not
written yet must be manageable by a CLI we have already shipped.

```go
// cmd/bssconnectsctl/dynamic.go
//
// Build the command tree from the cached module registry. Called before Cobra executes,
// so `--help` and shell completion include modules installed after this binary was built.
func addModuleCommands(root *cobra.Command, reg *metadata.Registry) {
    for _, mod := range reg.Modules() {
        modCmd := &cobra.Command{
            Use:   mod.ID,                    // "crm"
            Short: mod.Description,
        }

        for _, res := range mod.Resources {
            resCmd := &cobra.Command{
                Use:     res.Names.Collection, // "subscribers"
                Aliases: res.Names.CLIAliases, // "sub", "subs"
                Short:   res.Docs.Summary,
            }

            // Only add verbs the module says it supports. Offering `delete` on a resource
            // whose capabilities say delete:false produces a confusing 405 instead of an
            // honest "unknown command".
            if res.Capabilities.List {
                resCmd.AddCommand(newListCmd(mod, res))
            }
            if res.Capabilities.Delete {
                resCmd.AddCommand(newDeleteCmd(mod, res))
            }

            // Non-CRUD operations become verbs too: `subscribers suspend 4711 --reason ...`
            for _, act := range res.Actions {
                resCmd.AddCommand(newActionCmd(mod, res, act))
            }

            modCmd.AddCommand(resCmd)
        }
        root.AddCommand(modCmd)
    }
}
```

## Two decisions worth not relitigating

**Cache on revision, never on a TTL.** Each invocation sends one conditional request
(`If-None-Match`) to `/registry?view=revisions` and normally gets `304` with no body. A TTL is
either too short (wasted requests) or too long (the CLI offers commands a module no longer has).

**Never cache the user's permissions.** Show every command the module offers and let the server
return `403`. A cached permission set risks acting on a grant that was revoked, and the
authoritative check is server-side regardless.

## Output

`--output table` for humans and explicitly **not** a stable interface. `--output json` is the
contract customers script against. Say so in the docs, or someone will parse the table.
