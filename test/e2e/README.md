# `test/e2e`

The phase-1 exit test, automated. If this passes, the platform works.

## The scenario

```go
// The demo script, as a test. Step 5 is the one that proves the whole design: a module's
// screens and commands appear with no redeploy of the Shell or the CLI.
func TestLicenceToWorkingModule(t *testing.T) {
    c := kind.NewCluster(t)              // Istio, Keycloak, Flux preinstalled by hack/
    platform := c.InstallChart(t, "deploy/charts/platform-core")

    // 1. Empty platform: login works, no modules.
    require.Empty(t, platform.Modules(t))

    // 2. A signed licence makes the module available — no engineer, no installer.
    platform.ApplyLicence(t, "testdata/hello.lic")
    require.Eventually(t, func() bool {
        return platform.Module(t, "hello").Status == "Available"
    }, 60*time.Second, time.Second)

    // 3. Install with config validated against the chart's values.schema.json.
    platform.InstallModule(t, "hello", map[string]any{"greeting": "hi"})
    platform.WaitReady(t, "hello", 5*time.Minute)

    // 4. The registry now holds validated metadata, fetched once by the operator.
    require.NotEmpty(t, platform.Registry(t).Module("hello").MetadataRevision)

    // 5. THE KEY ASSERTION: nav and screens exist for a module the Shell has never
    //    heard of, built from metadata at runtime.
    boot := platform.Bootstrap(t, asUser("admin"))
    require.Contains(t, navLabels(boot), "Widgets")

    // 6. The CLI generated the same commands from the same document.
    out := platform.CLI(t, "hello", "widgets", "list", "--output", "json")
    require.NoError(t, json.Unmarshal(out, &[]any{}))

    // 7. Revoke the permission: the button disappears AND the API refuses. Both, because
    //    either one alone is a bug — a hidden button with a working endpoint is a hole.
    platform.RemovePermission(t, "WidgetOperator", "hello:widget:retire")
    require.Eventually(t, func() bool {
        return !hasAction(platform.Bootstrap(t, asUser("operator")), "retire")
    }, 30*time.Second, time.Second)
    require.Equal(t, 403, platform.CallAction(t, asUser("operator"), "hello", "retire", "w-1"))
}
```

## Rules

- Runs on kind in CI. No dependency on a shared cluster — a test that needs one is not a test,
  it is a ritual.
- No `time.Sleep`. Poll with `require.Eventually` and a real condition, or the suite becomes
  flaky and people start ignoring it.
