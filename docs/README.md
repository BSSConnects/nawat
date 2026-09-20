# Documentation

## Start here, in this order

| # | Document | Read it when |
|---|---|---|
| 1 | [collaboration.md](collaboration.md) | day one — team shape, required knowledge with links, SRE practice |
| 2 | [github-workflow.md](github-workflow.md) | before your first PR — branching, commits, reviews, issues, releases |
| 3 | [platform-design-principles.md](platform-design-principles.md) | before writing any service — twelve-factor and what we add |
| 4 | [opensource-stack.md](opensource-stack.md) | before adding any dependency — and it answers "do we fork Flux?" (no) |

## Design

The architecture, decided before implementation started.

| Document | Contents |
|---|---|
| [design/keynote.md](design/keynote.md) | the high-level concept, as presented to management. Best overview of *why* |
| [design/02-platform-core-components.md](design/02-platform-core-components.md) | every component choice, alternatives considered, and the reasoning |
| [design/example__metadata__.md](design/example__metadata__.md) | **the module contract specification** — the most important document here |
| [design/09-cli.md](design/09-cli.md) | BSSConnectsCLI: commands, config, caching, credentials |
| [design/10-rollout-plan.md](design/10-rollout-plan.md) | phases, what parallelises, exit tests |

## Decisions

[adr/](adr/) — one record per architectural decision. Proposed as a PR, so the decision itself gets
reviewed. Accepted ADRs are never edited; a changed decision supersedes rather than rewrites.

## Incidents

[postmortems/](postmortems/) — blameless, one per incident and per near miss, published within three
working days.

## Writing documentation here

- **A document explains *why*.** A README explains *what goes in this directory*. Don't mix them.
- Every directory in the repo has a `README.md`. Update it in the same PR as the code.
- Diagrams are mermaid, in the markdown, so they are reviewable in a diff. Not images.
- Code examples carry comments explaining the non-obvious choice — the reason something is done
  *this* way rather than the way a reader would first try.
