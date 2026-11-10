# ADR 0003: Reconcile what runs against what is registered

Status: accepted

## Context
Self registration catches the agents whose owners follow the process. The agents that matter most to find are the ones that did not.

## Decision
Reconcile the registry against independent signals on a schedule:
* platform auto detection (AgentCore runtime and gateway in this sample),
* platform inventories (Microsoft agent inventory),
* vendor inventories supplied under contract,
* gateway decision logs (calls with missing or unknown agent IDs, allowed calls by suspended agents),
* cloud cost lines whose `Application` tag maps to no agent.

Anything found that is not registered becomes a finding with an owner and a deadline.

## Consequences
* Coverage is only as good as the signals. Auto detection is strongest on platforms that offer it; vendor and SaaS agents rely on weaker signals, which the report states.
* Cost tags double as a discovery signal, which makes tag hygiene a governance control, not only a finance one.
