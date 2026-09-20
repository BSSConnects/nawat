# GitHub workflow

The mechanics. Team structure and SRE practice are in [collaboration.md](collaboration.md).

---

## 1. Branching: trunk-based, short-lived branches

```
main                     always releasable, protected, never committed to directly
  feat/123-module-crd    one issue, one branch, merged within days
release/v0.1             cut at a release; only backported fixes land here
```

**Why not GitFlow.** GitFlow's long-lived `develop` branch plus release branches produces
painful merges and delays integration. We integrate into `main` continuously and cut a
`release/vX.Y` branch only when a customer needs maintenance fixes on a version while `main`
has moved on. That is a real need for a shipped telco product — but it is the *exception*, not
the daily flow.

### Branch naming

```
feat/123-short-slug      new capability          (issue 123)
fix/456-short-slug       bug fix
docs/789-short-slug      documentation only
chore/012-short-slug     tooling, deps, CI
spike/345-short-slug     throwaway investigation — never merged
```

The issue number is mandatory. A branch with no issue means work nobody could have found.

### Rules

- **Branch lifetime: days, not weeks.** A branch open for two weeks is a merge conflict being
  saved up. Split the work instead.
- Rebase onto `main` rather than merging `main` into your branch — it keeps history readable.
- Never force-push a branch someone else is reviewing. Push fixup commits; squash on merge.

---

## 2. Commits: Conventional Commits

```
<type>(<scope>): <imperative summary under 72 chars>

Why this change, not what — the diff already shows what. Anything a reviewer
or someone reading `git log` in a year would need to know.

Refs: #123
BREAKING CHANGE: ModuleMetadata now requires module.metadataRevision
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `build`, `ci`.
Scopes: `operator`, `cli`, `sdk`, `shell`, `authz`, `license`, `api`, `schemas`, `chart`, `ci`.

```
feat(operator): reconcile ModuleInstance into a Flux HelmRelease
fix(cli): do not cache permissions between invocations
docs(schemas): explain why metadataRevision must be a content hash
feat(schemas)!: require module.metadataRevision     # `!` marks a breaking change
```

The changelog and version bumps are generated from these, so the format is enforced by CI.
Squash-merge means the PR title becomes the commit — so the **PR title** must be conventional.

---

## 3. Pull requests

### Size

**Target under 400 changed lines.** Review quality falls off a cliff beyond that: large PRs get
approved without real reading, which is worse than no review. If a change cannot be split, say
why in the PR description.

Splitting strategies that work here: types first, then the logic that uses them; the interface
and a stub, then the implementation; the refactor in one PR, the behaviour change in the next.

### Draft early

Open a **draft PR on your first commit**. It tells the team what you are doing and invites
course correction before you have invested three days in the wrong direction.

### Approvals

| Paths touched | Approvals | Extra |
|---|---|---|
| `schemas/`, `api/` | **2** | ADR required; Architects must be among the approvers |
| `deploy/policies/` (Rego) | **2** | Security team among them — an error here is a data breach |
| everything else | 1 | CODEOWNERS for the touched paths |
| `docs/` only | 1 | — |

### Merging

- **Squash merge** onto `main`. Linear history, one commit per PR, easy revert.
- Required: green CI, required approvals, branch up to date with `main`.
- The author merges, not the reviewer — the author knows whether anything is still outstanding.

### Reviewing

- **Respond within one working day.** Blocking a colleague for three days costs more than the
  review saves. If you cannot review in time, say so and reassign.
- Review for: correctness, contract impact, failure modes, test coverage, readability. In that
  order.
- Distinguish blocking from non-blocking. Prefix optional remarks with **nit:** so the author
  knows what actually holds the merge.
- Ask questions rather than issuing instructions. "What happens if the registry is empty here?"
  finds more bugs than "add a nil check".
- Approve with minor comments rather than blocking on style. Taste disagreements go to the linter
  config, as a separate PR, once.

Worth reading once as a team: [Google's code review guide](https://google.github.io/eng-practices/review/).

---

## 4. Issues

### Labels

```
kind/bug  kind/feature  kind/spike  kind/adr  kind/toil
area/operator  area/cli  area/sdk  area/shell  area/authz  area/license  area/ci  area/docs
priority/critical  priority/high  priority/normal  priority/low
size/xs  size/s  size/m  size/l          # estimate, not a commitment
good-first-issue  help-wanted  blocked
```

`kind/toil` is there on purpose — see the toil budget in
[collaboration.md](collaboration.md#toil). Making toil visible on the board is what causes it to
get automated.

### Rules

- **One deliverable per issue.** "Build the operator" is an epic, not an issue.
- A `kind/spike` always carries a timebox and a named deliverable. Without both it becomes three
  weeks of reading.
- `blocked` issues name what they are blocked on, in a comment. An unexplained `blocked` label is
  invisible to everyone else.
- Milestones are the phases from [`design/10-rollout-plan.md`](design/10-rollout-plan.md):
  `phase-0-contracts`, `phase-1-skeleton`, `phase-2-real`, `phase-3-first-module`.

### The board

Five columns: **Backlog → Ready → In progress → In review → Done**.

*Ready* means the issue is understood well enough to start without asking anything. Grooming the
Backlog into Ready is the weekly design sync's job. Starting work from Backlog is how people end
up building the wrong thing politely.

**WIP limit: two items in progress per person.** More than that means nothing finishes.

---

## 5. ADRs — Architecture Decision Records

Any decision that is expensive to reverse gets a record in `docs/adr/`, proposed as a PR so the
decision itself is reviewed.

```
docs/adr/0001-identity-provider-keycloak.md
docs/adr/0002-authorization-opa-not-cedar.md
docs/adr/0003-deployment-engine-flux.md
```

Status: `proposed` → `accepted` | `rejected` | `superseded by ADR-00XX`.
**Accepted ADRs are never edited** — they are a record of what we knew at the time. A changed
decision gets a new ADR that supersedes the old one.

Write one when: adopting or rejecting a third-party component, changing a contract, choosing
between approaches with real trade-offs, or **forking an upstream project** (mandatory, see
[opensource-stack.md](opensource-stack.md)).

Format: [adr.github.io](https://adr.github.io/). Ours is in `docs/adr/README.md`.

---

## 6. Branch protection on `main`

Configure once, at repo creation:

- Require a pull request; no direct pushes, no force-pushes, no deletion.
- Require status checks: `lint`, `test`, `contracts`, `e2e`.
- Require branches to be up to date before merging.
- Require approvals per the table in §3; dismiss stale approvals on new commits.
- Require CODEOWNERS review.
- Require **signed commits** — telco customers ask about commit provenance during security
  review, and retrofitting signing across a year of history is not possible.
- Require linear history (squash-merge only).

---

## 7. Releases

Semantic versioning. `v0.x` while the contracts are still `v1alpha1` — we are explicitly allowed
to break things during phase 0 and 1, and should say so loudly rather than pretending stability we
do not have.

```bash
git tag -s v0.2.0 -m "phase 1: walking skeleton"   # signed tag
git push origin v0.2.0
```

`release.yaml` then builds every binary, builds and **signs images with cosign**, pushes to Harbor,
packages the chart as an OCI artifact, and generates the changelog from commit messages.

### What a release must contain

- All CI green on the tagged commit, including the nightly full-cluster run.
- An upgrade test from the previous release. A platform that cannot be upgraded is not a platform.
- Signed images, and a Kyverno/Gatekeeper policy in the chart that verifies those signatures at
  admission. Signing without verification is theatre.
- Release notes grouped by module contract impact — that is what module teams actually need to read.

---

## 8. Daily loop, end to end

```bash
# 1. Pick a Ready issue, assign yourself, move it to In progress.

git switch main && git pull --rebase
git switch -c feat/123-moduleinstance-crd

# 2. Commit in small steps; push and open a DRAFT PR on the first commit.
git push -u origin feat/123-moduleinstance-crd
gh pr create --draft --title "feat(api): add ModuleInstance CRD" --body-file .github/pull_request_template.md

# 3. Before asking for review, run exactly what CI runs.
./hack/verify.sh

# 4. Mark ready, request reviewers per CODEOWNERS.
gh pr ready
gh pr edit --add-reviewer @bssconnects/platform-core

# 5. Address feedback with fixup commits — never force-push during review.
# 6. Rebase onto main, squash-merge, delete the branch.
gh pr merge --squash --delete-branch
```
