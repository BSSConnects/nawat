# `test/`

| Directory | Scope | Runs |
|---|---|---|
| [`conformance/`](conformance/) | does a module satisfy the contract? | every PR, against `hello-module`; shipped to module teams |
| [`e2e/`](e2e/) | does the whole platform work? | every PR on kind; nightly on a full cluster |

Unit tests live beside the code they test, not here.

## Why conformance is a separate, shippable suite

"Integrates with the ecosystem" has to mean something checkable. A module team must be able to
run one command and find out, rather than discovering at integration time that their pagination
is subtly different.

This is also the answer to the obvious objection to the whole design — *what stops module teams
from quietly diverging from the contract?* Two things: `bssconnectsctl module validate` in their
CI, and this suite.
