# `web/shell` — the UI Shell SPA

Renders any module's screens from its `__metadata__`. Contains **no** module-specific code.

## Layout

```
src/
  boot/           fetch /bootstrap, build the route table and nav from metadata
  auth/           PKCE flow, token refresh, permission helpers
  renderers/
    ResourceList.tsx     table, filter bar, search, saved views, row actions
    ResourceDetail.tsx   tabs, title/subtitle templates, status badge
    ResourceForm.tsx     generated from JSON Schema + x-ui hints
    RelationTab.tsx      reuses the TARGET resource's own list config
    ActionDialog.tsx     confirm + inputSchema form
    AuditTab.tsx
  widgets/        one component per x-ui.widget: msisdn, reference, tags, country...
  federation/     loads module remotes at runtime
  generated/      types from schemas/ — never hand-edited
```

`RelationTab` reusing the target's list config is what makes the Contracts tab inside a
subscriber look exactly like the Contracts screen, with no duplicated configuration.

## Example — resolving a route from metadata

```tsx
// The route table is DATA, built at boot from the bootstrap payload. Adding a module does
// not add a route file, and does not require rebuilding or redeploying this app — which is
// the entire "install a licence and screens appear" promise.
export function buildRoutes(bootstrap: Bootstrap): RouteObject[] {
  return bootstrap.navigation.flatMap((group) =>
    group.children
      // Hide what the user cannot open. This is privacy and clarity, NOT security —
      // the server enforces independently on every request.
      .filter((item) => hasPermission(bootstrap.permissions, item.requires))
      .map((item) =>
        item.renderer === "microfrontend"
          ? {
              path: item.route,
              // Lazy: a module's bundle is fetched only when first opened, so twenty
              // installed modules do not slow the first paint.
              element: <RemoteComponent remote={item.component.remote}
                                        module={item.component.module} />,
            }
          : {
              path: `/${item.resource!.replace("/", "/")}`,
              element: <ResourceList resourceType={item.resource!} />,
              children: [
                // The detail route is implied by the resource, not declared per module.
                { path: ":id", element: <ResourceDetail resourceType={item.resource!} /> },
              ],
            },
      ),
  );
}
```

## Rules

- **Never import from a module.** The Shell knows metadata and HTTP, nothing else.
- **Never hardcode a field name.** `if (field === "msisdn")` anywhere in this package is a bug;
  behaviour comes from `x-ui` hints in the schema.
- **Degrade, do not break.** An unknown `x-ui.widget` falls back to a text input. A missing
  micro-frontend remote shows an inline error in that tab and leaves the rest of the page usable.
- **Never put tokens in `localStorage`.** Metadata cache yes; tokens in memory only.
