# `examples/`

Reference implementations. These are **tested in CI** — an example that does not build is worse
than no example, because people copy it anyway.

| Example | Purpose |
|---|---|
| [`hello-module/`](hello-module/) | the reference module, the conformance target, and the phase-1 demo subject |

## Why `hello-module` exists

1. **It is the phase-1 demo.** The walking skeleton installs *this*, not CRM — so the platform
   can be proven end to end before any real product is touched.
2. **It is the conformance target.** `test/conformance` runs against it on every PR, so a change
   that breaks the contract fails CI immediately.
3. **It is the template.** A new module starts as a copy of this directory.

Keep it trivial — one resource, roughly six fields, one action. The temptation is to grow it into
a realistic application; resist that. Its job is to exercise the contract, and complexity makes
contract failures harder to spot, not easier.
