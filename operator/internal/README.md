# `internal/`

Go code shared between **our** binaries but deliberately not importable by anyone else.
The `internal/` path is enforced by the Go toolchain.

## What belongs here

```
internal/
  config/       env + flag parsing shared by all services
  telemetry/    OTel tracer, Prometheus registry, structured logger setup
  httpx/        middleware: request id, trace propagation, RFC 9457 error writer
  kube/         controller-runtime client helpers, owner references
  testutil/     envtest harness, fake Harbor, fake Keycloak
```

## What does NOT belong here

Anything a **module team** needs. If a module must import it, it goes in `pkg/` and we own its
compatibility. The deciding question: *would a CRM developer need this?* If yes → `pkg/`.

That distinction matters more than it looks. `pkg/` is a public API with versioning
obligations; `internal/` we can refactor freely on a Tuesday afternoon.

## Example — consistent telemetry across every service

```go
package telemetry

// Setup wires logging, metrics and tracing identically in every binary, so a request can
// be followed from the gateway through the Platform API into a module without anyone
// remembering to configure anything.
func Setup(ctx context.Context, serviceName string) (*Providers, error) {
    // Trace context arrives from Istio in W3C traceparent headers. Using the same
    // propagator everywhere is what makes cross-module traces actually join up —
    // mismatched propagators are the usual reason they silently do not.
    otel.SetTextMapPropagator(propagation.TraceContext{})

    // Exporters point at the in-cluster collector by default. No service should ever
    // hardcode an endpoint: the operator injects it via global.platform.*
    exporter, err := otlptracegrpc.New(ctx)
    if err != nil {
        return nil, fmt.Errorf("otlp exporter: %w", err)
    }
    // ...
}
```
