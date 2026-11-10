# ADR 0002: Enforce registration at the gateway: no registry ID, no route

Status: accepted

## Context
A registry that teams can ignore decays within a quarter. Review meetings do not stop an unregistered agent from calling a model.

## Decision
Every model and tool call passes through an AI gateway that evaluates `policy/gateway.rego` against registry data published by `agent-registry export-opa`. Calls are denied when the agent ID is missing or unknown, the agent is not approved, the environment or route does not match the record, the latest evaluation failed, or a high tier agent's evaluation is past its age limit.

## Alternatives rejected
* **Periodic attestation only.** Finds problems weeks late and depends on owners volunteering.
* **Enforcement inside each agent framework.** Every team would implement it differently, and vendor agents cannot be changed.

## Consequences
* Routes that bypass the gateway are an enforcement gap and are reported as `ENFORCEMENT_GAP`.
* Vendor agents that call their own models do not pass through the gateway; they are covered by contractual inventories, vendor telemetry and third party risk review instead.
* The policy is tested with `opa test` in CI like any other code.
