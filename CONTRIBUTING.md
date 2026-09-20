# Contributing

Three documents, in this order:

1. **[docs/collaboration.md](docs/collaboration.md)** — how the team is organised, who owns
   what, the knowledge each role needs, and the SRE practices we follow.
2. **[docs/github-workflow.md](docs/github-workflow.md)** — branching, commits, pull
   requests, issues, reviews, releases. The mechanics.
3. **[docs/platform-design-principles.md](docs/platform-design-principles.md)** — the
   twelve-factor baseline and the cloud-native rules we add on top. Applies to every
   service and every module.

## The short version

- Branch from `main`: `feat/123-short-slug`. Never commit to `main`.
- Conventional commits: `feat(operator): reconcile ModuleInstance into HelmRelease`.
- Open a **draft PR early** so others can see direction before you finish.
- A PR needs one approval, green CI, and a CODEOWNERS sign-off for the paths it touches.
- **Changes under `schemas/` need two approvals and an ADR.** They are the contract; a
  careless change breaks every consumer.
- Keep PRs under ~400 changed lines. Split anything larger.
