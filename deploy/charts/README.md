# `deploy/charts/`

Only `platform-core` lives here. Module charts belong with their modules.

```
platform-core/
  Chart.yaml          subchart dependencies, pinned by exact version
  values.yaml         documented defaults
  values.schema.json  validates the customer's values at install time
  crds/               GENERATED from api/ — never hand-edited
  templates/
    operator/
    platform-api/
    authz-service/
    license-service/
    shell-service/
    gateway/          Gateway, RequestAuthentication, AuthorizationPolicy
    rbac/
```

## The security template worth reviewing carefully

```yaml
# templates/gateway/request-authentication.yaml
#
# RequestAuthentication validates a token IF ONE IS PRESENT. It does NOT require one.
# Shipping only this object produces an endpoint that correctly rejects a FORGED token but
# happily accepts a request with NO token at all. This is a common and serious mistake, so
# the two objects are generated together here and must never be separated.
apiVersion: security.istio.io/v1
kind: RequestAuthentication
metadata:
  name: platform-jwt
  namespace: {{ .Release.Namespace }}
spec:
  selector:
    matchLabels: { app: istio-ingressgateway }
  jwtRules:
    - issuer: {{ printf "https://%s/realms/platform" .Values.global.domain | quote }}
      jwksUri: {{ printf "http://keycloak.%s.svc:8080/realms/platform/protocol/openid-connect/certs" .Release.Namespace | quote }}
      forwardOriginalToken: true   # modules re-validate; zero trust means no implicit trust
---
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: platform-require-jwt
  namespace: {{ .Release.Namespace }}
spec:
  selector:
    matchLabels: { app: istio-ingressgateway }
  action: ALLOW
  rules:
    - from:
        - source:
            requestPrincipals: ["*"]   # THIS is what actually requires a token
      to:
        - operation:
            notPaths: ["/healthz", "/readyz", "/realms/*"]  # login must be reachable
```
