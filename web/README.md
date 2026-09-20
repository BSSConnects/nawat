# `web/` — the frontend

Not a Go module — its own npm workspace, which is the main reason the repository is not a single
Go module rooted at the top.


| Directory | Contains |
|---|---|
| [`shell/`](shell/) | the UI Shell SPA: generic renderers, nav, auth, routing |
| [`design-system/`](design-system/) | shared components every module's custom UI must use |

## Build order: last

Build the Shell **after** the CLI proves the module contract. If the contract is wrong, the CLI
exposes that in days; discovering it through a half-built React renderer costs weeks, and you
cannot tell whether the contract or the renderer is at fault.

**This does not mean the frontend developer idles.** `examples/hello-module/__metadata__.json`
and the CRM example are static mocks — the entire Shell can be built against files on disk, with
no backend running, for most of phase 1.

## The split that makes this work

| Screen kind | Share | How |
|---|---|---|
| list / search / detail / edit / act | ~75% | **generated** from `__metadata__` — no module-specific code |
| genuinely domain-specific | ~25% | hand-written micro-frontend, loaded at runtime via Module Federation |

A module team's escalation ladder: metadata → widget override → slot injection → full custom
page. Reaching for a custom page first is the failure mode to watch for in review.

## Stack

```jsonc
{
  "react": "18",              // UMD-free, bundled; Module Federation needs a shared singleton
  "typescript": "5",
  "vite": "5",                // + @module-federation/enhanced for runtime module loading
  "@tanstack/react-query": "5", // server cache, retries, pagination
  "oidc-client-ts": "3",      // Authorization Code + PKCE; tokens in memory, never localStorage
  "ajv": "8"                  // validate forms against the module's JSON Schema client-side
}
```

Tokens stay in memory deliberately: a token in `localStorage` is readable by any XSS on the page,
and this is an admin UI for telco operators.
