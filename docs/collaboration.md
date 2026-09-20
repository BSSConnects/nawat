# How we work together

**Audience:** everyone joining the bssconnects platform project.
**Read with:** [github-workflow.md](github-workflow.md) (the mechanics),
[platform-design-principles.md](platform-design-principles.md) (how we build),
[opensource-stack.md](opensource-stack.md) (what we use and how).

---

## 1. What we are building, in one minute

Today we sell Mediation, Roaming, CRM and Interconnect as separate products. Each has its own
login, its own permission model, its own UI, its own installer and its own licence handling. Four
products means four of everything, and a fifth product means a fifth of everything.

We are building **one platform**. Products become **modules** that describe themselves through a
contract; the platform reads that contract and generates the UI, the CLI, the permissions and the
API documentation. Installing a licence makes a product appear.

**The rule that governs every decision:** Platform Core must never contain the word "Mediation".
If adding a product requires changing core, we have built a bigger monolith instead of a platform.

---

## 2. Team shape

### Steady state: 6–8 people

| Sub-team | Size | Owns | Phase it starts |
|---|---|---|---|
| **Architects** | 1–2 (a role, not a job) | `schemas/`, `api/`, ADRs, contract reviews | 0 |
| **Platform Core** | 2 | operator, CRDs, Flux wiring, `platform-core` chart | 0 |
| **Security & Identity** | 1–2 | Keycloak, OPA/Rego, OPAL, licence service, Istio security | 1 |
| **Developer Experience** | 1–2 | CLI, client library, module SDK, `hello-module`, docs | 0 |
| **Frontend** | 1–2 | UI Shell, design system | 1 (late) |
| **SRE / Delivery** | 1 | CI/CD, kind + Tilt, observability, releases, runbooks | 0 |

"Architect" is a **role held by working engineers**, not a separate person who only draws
diagrams. Whoever holds it reviews every `schemas/` PR and writes the ADRs.

### Minimum viable: 3 people

If we start with three, map it like this and accept the timeline doubles:

| Person | Wears |
|---|---|
| A (lead) | Architect + Platform Core |
| B | Developer Experience + Security |
| C | SRE + Platform Core, then Frontend in phase 2 |

**Do not start with a frontend-only hire.** There is nothing for them to integrate with until
phase 1 is close to done, and they would spend two months building against mocks that then change.

### Who decides what

| Decision | Who |
|---|---|
| anything under `schemas/` or `api/` | Architects, two approvals, ADR required |
| a component's internal design | that sub-team |
| adding a third-party dependency | sub-team proposes, Architects approve, ADR if it is load-bearing |
| forking an upstream project | Architects only, ADR mandatory — see [opensource-stack.md](opensource-stack.md) |
| commercial questions (licence strictness, tiers) | product owner, not engineering |

Disagreement escalates to a written ADR with options, not to a longer meeting.

---

## 3. Knowledge: what everyone needs

**Everyone on the project, regardless of sub-team.** Not expert level — working literacy, enough
to read a PR outside your area and review it usefully.

| Area | Why everyone needs it | Start here |
|---|---|---|
| Git & GitHub PR flow | daily | [Pro Git ch. 2–3](https://git-scm.com/book/en/v2), [Conventional Commits](https://www.conventionalcommits.org/) |
| Kubernetes fundamentals | pods, services, deployments, CRDs, RBAC | [kubernetes.io/docs](https://kubernetes.io/docs/concepts/), [CKA curriculum](https://github.com/cncf/curriculum) |
| `kubectl` and Helm | debugging anything | [Helm docs](https://helm.sh/docs/) |
| Containers | image building, layers, entrypoints | [Docker docs](https://docs.docker.com/build/) |
| **Reading** Go | every backend PR is Go | [A Tour of Go](https://go.dev/tour/), [Effective Go](https://go.dev/doc/effective_go) |
| JSON Schema | it is our contract language | [Understanding JSON Schema](https://json-schema.org/understanding-json-schema) |
| OpenAPI 3.1 | the Platform API contract | [learn.openapis.org](https://learn.openapis.org/) |
| OAuth2 / OIDC concepts | every request carries a token | [oauth.com](https://www.oauth.com/), [How OIDC works](https://openid.net/developers/how-connect-works/) |
| Observability basics | metrics, logs, traces; reading PromQL | [Prometheus docs](https://prometheus.io/docs/introduction/overview/), [OpenTelemetry](https://opentelemetry.io/docs/what-is-opentelemetry/) |
| SRE basics | SLOs, error budgets, postmortems, toil | [sre.google/books](https://sre.google/books/) — free online, read ch. 1–6 of the SRE Book |
| **Our own design** | non-negotiable | [`docs/design/02-platform-core-components.md`](design/02-platform-core-components.md) and [`example__metadata__.md`](design/example__metadata__.md) |

Last row included deliberately: the most expensive mistakes on a project like this come from
someone implementing a component without having read the contract it serves.

---

## 4. Knowledge: specialist tracks

### Platform Core

| Topic | Resources |
|---|---|
| Operators, controllers, reconciliation | [The Kubebuilder Book](https://book.kubebuilder.io/) — work through it end to end; *Programming Kubernetes* (O'Reilly) |
| controller-runtime API | [pkg.go.dev/sigs.k8s.io/controller-runtime](https://pkg.go.dev/sigs.k8s.io/controller-runtime) |
| CRD design, API conventions | [K8s API conventions](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-architecture/api-conventions.md) |
| Flux | [fluxcd.io/flux](https://fluxcd.io/flux/), specifically `HelmRelease` and `OCIRepository` |
| Helm authoring | [Chart best practices](https://helm.sh/docs/chart_best_practices/) |
| Harbor, OCI artifacts | [goharbor.io/docs](https://goharbor.io/docs/), [oras.land](https://oras.land/) |
| testing controllers | envtest chapter of the Kubebuilder book |

### Security & Identity

| Topic | Resources |
|---|---|
| Keycloak: realms, clients, mappers, federation, themes | [keycloak.org/documentation](https://www.keycloak.org/documentation) |
| OAuth2 flows in depth, PKCE, device grant | [oauth.net/2](https://oauth.net/2/), [RFC 8628](https://www.rfc-editor.org/rfc/rfc8628) |
| OPA and Rego | [openpolicyagent.org/docs](https://www.openpolicyagent.org/docs/), [Rego Playground](https://play.openpolicyagent.org/) |
| OPA + Envoy `ext_authz` | [OPA Envoy plugin](https://www.openpolicyagent.org/docs/envoy-introduction) |
| Partial evaluation (our list filtering) | [OPA partial evaluation docs](https://www.openpolicyagent.org/docs/policy-performance#partial-evaluation) |
| OPAL | [docs.opal.ac](https://docs.opal.ac/) |
| Istio security | [Istio security docs](https://istio.io/latest/docs/concepts/security/) — `RequestAuthentication` vs `AuthorizationPolicy` |
| Envoy | [envoyproxy.io/docs](https://www.envoyproxy.io/docs) |
| SPIFFE / SPIRE | [spiffe.io/docs](https://spiffe.io/docs/latest/spiffe-about/overview/) |
| Signing, supply chain | [docs.sigstore.dev](https://docs.sigstore.dev/) |
| JOSE / token signing | [RFC 7515](https://www.rfc-editor.org/rfc/rfc7515), [PASETO](https://paseto.io/) |

### Developer Experience

| Topic | Resources |
|---|---|
| Writing Go libraries others depend on | [Go module reference](https://go.dev/ref/mod), [Go API compatibility](https://go.dev/blog/module-compatibility) |
| CLI design | [Cobra](https://cobra.dev/), [Command Line Interface Guidelines](https://clig.dev/) |
| JSON Schema authoring | [json-schema.org/learn](https://json-schema.org/learn) |
| OpenAPI + codegen | [oapi-codegen](https://github.com/oapi-codegen/oapi-codegen) |
| API design | [RFC 9457 Problem Details](https://www.rfc-editor.org/rfc/rfc9457), [Google API Design Guide](https://cloud.google.com/apis/design) |

### Frontend

| Topic | Resources |
|---|---|
| React + TypeScript | [react.dev/learn](https://react.dev/learn), [TypeScript handbook](https://www.typescriptlang.org/docs/handbook/intro.html) |
| Runtime module loading | [module-federation.io](https://module-federation.io/) |
| Server cache and pagination | [TanStack Query](https://tanstack.com/query/latest/docs/framework/react/overview) |
| Schema-driven forms | [react-jsonschema-form](https://rjsf-team.github.io/react-jsonschema-form/), [JSONForms](https://jsonforms.io/) |
| OIDC in the browser | [oidc-client-ts](https://authts.github.io/oidc-client-ts/) |
| Accessibility | [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/) — telco customers have procurement checklists for this |

### SRE / Delivery

| Topic | Resources |
|---|---|
| SRE practice | [Google SRE Book + Workbook](https://sre.google/books/) (free) |
| SLOs in practice | *Implementing Service Level Objectives*, Alex Hidalgo |
| Prometheus, PromQL, alerting | [Prometheus docs](https://prometheus.io/docs/prometheus/latest/querying/basics/), [Awesome Prometheus alert rules](https://samber.github.io/awesome-prometheus-alerts/) |
| kind, Tilt | [kind.sigs.k8s.io](https://kind.sigs.k8s.io/), [docs.tilt.dev](https://docs.tilt.dev/) |
| Runtime security | [Falco docs](https://falco.org/docs/), [gVisor](https://gvisor.dev/docs/) |
| Progressive delivery | [Flagger](https://fluxcd.io/flagger/) |

---

## 5. Onboarding: the first week

Same path for everyone, regardless of sub-team. It ends with a merged PR.

| Day | Do |
|---|---|
| 1 | Read `README.md`, this document, `docs/design/02-platform-core-components.md`. Ask questions in the channel, not privately — the answers belong where others can find them. |
| 2 | Read `docs/design/example__metadata__.md` and `examples/hello-module/__metadata__.json` side by side until the mapping is obvious. This is the contract; everything else serves it. |
| 3 | `./hack/kind-up.sh && ./hack/install-deps.sh`. Break it, fix it, and **send a PR improving the script or its docs** — that is your first contribution and it makes onboarding better for the next person. |
| 4 | Read the code your sub-team owns. Write down three things that confused you and post them. |
| 5 | Pick a `good-first-issue`. Open a draft PR by end of day, even if unfinished. |

**Success measure:** a merged PR in week one. If that did not happen, onboarding is broken and we
fix the onboarding, not the person.

---

## 6. Rituals

Deliberately few. A distributed team drowns in meetings faster than a co-located one.

| When | What | Length |
|---|---|---|
| Daily | **Written** async standup in the channel: yesterday / today / blocked | 2 min to write |
| Weekly | **Design sync** — review open ADRs, resolve contract questions. Agenda is the ADR list; no agenda means no meeting | 60 min |
| Fortnightly | **Demo** — show working software on a kind cluster. No slides | 30 min |
| Monthly | **Retro** — what to change about how we work | 45 min |
| Per incident | **Postmortem** — see §7 | 45 min |

**Blocked is the only word that matters in standup.** A blocked item that is still blocked the
next day gets escalated by the lead, not by the person who is stuck.

---

## 7. SRE practices we adopt from day one

Not "later, when we have customers". Retrofitting these is far more expensive than starting with
them, and we are building a product other teams will depend on.

### SLOs and error budgets

Every service in `cmd/` defines SLIs and SLOs **before** it ships — in its own README.

```yaml
# an illustrative SLO for the Platform API
slo:
  availability:
    sli: "successful non-5xx responses / total responses"
    target: 99.9%           # ~43 min of budget per month
    window: 30d
  latency:
    sli: "p99 of GET /registry"
    target: "< 300ms"
    window: 30d
```

**Error budget policy:** if a service burns its monthly budget, the next sprint for that sub-team
is reliability work, not features. Written down in advance so it is not a negotiation at the time.

Note what is deliberately *not* an SLO target: 100%. A target of 100% means no room to deploy.

### Blameless postmortems

Written for **every** incident and every near miss. Template in `docs/postmortems/TEMPLATE.md`.

- **Blameless means the output is a changed system, not a changed person.** "Amal ran the wrong
  command" is never a root cause; "the command was destructive with no confirmation and no dry-run"
  is.
- Published to the whole team within 3 working days.
- Every action item has an owner and an issue number, or it is not an action item.
- Near misses get postmortems too. They are free lessons.

### Toil

Toil is manual, repetitive work that scales with usage and produces no lasting value.

- Track it. If a task is done manually more than **three times**, an issue is opened to automate it.
- **Cap: no more than 30% of anyone's time on toil.** Crossing that is a planning failure, reported
  in retro.
- The clearest early examples here: issuing development licences, regenerating metadata, setting up
  a test cluster. All three are `hack/` scripts for exactly this reason.

### Runbooks and actionable alerts

- Every alert links to a runbook. An alert with no runbook gets deleted — an alert nobody knows how
  to action teaches people to ignore alerts.
- Alert on **symptoms**, not causes. "Module install success rate dropped" is actionable; "CPU is
  at 80%" is not.
- Runbooks live next to the service they describe, in its `cmd/*/RUNBOOK.md`, so they are updated
  in the same PR as the behaviour they document.

### Production Readiness Review

A gate before any service or module is declared ready for a customer. One checklist:

- [ ] SLIs and SLOs defined and instrumented
- [ ] Dashboard and alerts exist; every alert links a runbook
- [ ] Graceful shutdown verified; resource requests and limits set
- [ ] Failure modes documented — including what happens when each dependency is down
- [ ] Backup and restore tested, not assumed
- [ ] Upgrade path tested from the previous version
- [ ] Conformance suite passes (modules); load tested at the expected order of magnitude
- [ ] Air-gapped install rehearsed

### Change management

- Progressive rollout for modules via Istio traffic shifting; the platform itself upgrades with
  Flux and rolls back automatically on failed remediation.
- **No deploys on Friday afternoon**, unless fixing something already broken.
- Every change is revertable by reverting a commit. If it is not, say so in the PR and explain why.

---

## 8. How we communicate

| Channel | For |
|---|---|
| GitHub issues | anything with a deliverable |
| GitHub PR comments | anything about specific code |
| ADRs in `docs/adr/` | decisions, with options and consequences |
| Team chat | quick questions, standup, incidents |
| Weekly design sync | only what could not be resolved in writing |

**Default to written and public.** A decision made in a direct message does not exist: the next
person to touch that code will not find it, and in six months neither will you.

**Ask early.** A question costing someone ten minutes is cheaper than a day spent in the wrong
direction. Nobody on this project is expected to already know Istio, OPA, Flux, Keycloak and
kubebuilder — that combination is the reason the stack needs a team rather than a hero.
