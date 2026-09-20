# `operator/api/` — CRD types

The Kubernetes API of the platform. **These types are the platform's real API**; the Platform API
service, the CLI and the UI are all clients of them.

That is deliberate: a customer can drive the platform with `kubectl` or their own GitOps pipeline
without us building anything extra, and the UI and CLI cannot drift apart — they end up writing the
same objects.

## Multigroup layout

This project was scaffolded with `--multigroup`, so APIs live under `api/<group>/<version>/`:

```
api/
  platform/v1alpha1/     Platform (cluster) · Module (cluster) · ModuleInstance (namespaced)
  licensing/v1alpha1/    License (namespaced)
  iam/v1alpha1/          AccessRole · AccessRoleBinding (namespaced)
```

Three groups, not one, because Kubernetes RBAC is granted **per API group**: the License Service can
be given write access to `licensing.bssconnects.io` and nothing else. It also maps ownership onto
directories for CODEOWNERS.

> `AccessRole`, not `Role`. A CRD named `Role` collides with the built-in
> `rbac.authorization.k8s.io` kind, and `kubectl get role` would resolve to the built-in one —
> forcing customers to type `kubectl get roles.iam.bssconnects.io` forever.

## Create an API

```bash
cd operator
# namespaced is the default; the flag is shown for clarity
kubebuilder create api --group platform  --version v1alpha1 --kind ModuleInstance --namespaced=true
# cluster-scoped: THIS is the flag that sets CRD scope (not the one on `init`)
kubebuilder create api --group platform  --version v1alpha1 --kind Module --namespaced=false
kubebuilder create api --group licensing --version v1alpha1 --kind License
```

## Rules

- `api/` imports nothing from `internal/`. It is a leaf package — modules and customer tooling
  import it.
- Run `make manifests generate` after editing, then **read the YAML diff**. A marker typo can be
  silently ignored.
- **Status is written only by the controller that owns it.** The License Service is the only writer
  of `License.status`, enforced by RBAC on the status subresource.
- Prefer `+kubebuilder:validation:` markers and CEL over webhook logic: they run inside the API
  server and cannot be down.

## Example

```go
type ModuleInstanceSpec struct {
	// Module is the module id, matching ModuleMetadata.module.id — e.g. "crm".
	// +kubebuilder:validation:Pattern=`^[a-z][a-z0-9-]{1,30}$`
	Module string `json:"module"`

	// Version must satisfy a range granted by a valid License. The operator refuses to install
	// a version the licence does not cover.
	Version string `json:"version"`

	// Config is the customer's own values, collected by the UI form generated from the module's
	// values.schema.json. RawExtension because its shape is defined by the MODULE, not by us —
	// validated by an admission webhook against that schema, so the error arrives at submit time
	// rather than three minutes into a failed rollout.
	// +kubebuilder:pruning:PreserveUnknownFields
	// +optional
	Config *apiextv1.JSON `json:"config,omitempty"`
}

type ModuleInstanceStatus struct {
	// Phase is a coarse summary for the UI: Pending, Installing, Ready, Degraded, Failed.
	// +optional
	Phase string `json:"phase,omitempty"`

	// LicenseState is separate from Phase because a module can be perfectly healthy AND out of
	// licence. The UI must show both, not collapse them into one word.
	// +optional
	LicenseState string `json:"licenseState,omitempty"`

	// MetadataRevision of the __metadata__ document the operator fetched and validated —
	// the cache key the Shell and CLI key their caches on.
	// +optional
	MetadataRevision string `json:"metadataRevision,omitempty"`

	// +listType=map
	// +listMapKey=type
	// +optional
	Conditions []metav1.Condition `json:"conditions,omitempty"`
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
// +kubebuilder:printcolumn:name="Module",type=string,JSONPath=`.spec.module`
// +kubebuilder:printcolumn:name="Version",type=string,JSONPath=`.spec.version`
// +kubebuilder:printcolumn:name="Phase",type=string,JSONPath=`.status.phase`
// +kubebuilder:printcolumn:name="Licence",type=string,JSONPath=`.status.licenseState`
type ModuleInstance struct { /* ... */ }
```
