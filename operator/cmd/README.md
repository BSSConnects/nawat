# `operator/cmd/` — the manager binary

One binary: `main.go` builds the **manager** and registers every controller with it.

**All controllers run inside this one process.** Adding a controller does not add a pod — it adds
goroutines to the manager. `kubectl get pods -n nawat-system` shows one pod no matter how many
controllers exist, which is also why every `+kubebuilder:rbac` marker in the project merges into a
single ClusterRole for a single ServiceAccount.

```
Deployment nawat-controller-manager
└─ Pod └─ container "manager" └─ process
      ├─ manager: shared cache (informers) · client · leader election · metrics · webhooks
      ├─ goroutines: ModuleInstance controller ── queue ──► Reconcile()
      └─ goroutines: License controller        ── queue ──► Reconcile()
```

`main.go` does **only** wiring: config, telemetry, dependencies, start, graceful shutdown. Logic
lives in `internal/` so it can be tested without starting a process.

## What must be added by hand

`kubebuilder create api` registers our own schemes and controllers. Third-party types are on you —
forgetting this produces `no kind is registered for the type` at runtime, not at compile time:

```go
	// Flux types, so the operator can create HelmRelease and OCIRepository objects.
	utilruntime.Must(helmv2.AddToScheme(scheme))
	utilruntime.Must(sourcev1.AddToScheme(scheme))
```

Configuration that reconcilers need is read here and passed in — never read from the environment
deep inside a package, where it cannot be tested:

```go
	// Fail at STARTUP if the licence public key is missing. An operator that starts without it
	// and marks every licence invalid is far harder to diagnose than one that refuses to boot.
	pub, err := licence.PublicKeyFromEnv("LICENSE_PUBLIC_KEY")
	if err != nil {
		setupLog.Error(err, "LICENSE_PUBLIC_KEY is required")
		os.Exit(1)
	}
```

## Rules

- `/healthz` must **not** check dependencies. Liveness answers "should this process be killed?" —
  checking the database there turns a brief database blip into every replica restarting at once.
- `/readyz` **does** check dependencies.
- Handle `SIGTERM`: stop accepting, drain, exit inside `terminationGracePeriodSeconds`.
- With two replicas, **only the leader's controllers reconcile**; webhooks serve from both. That is
  why a webhook needs two replicas and a PodDisruptionBudget, and plain controllers do not.
