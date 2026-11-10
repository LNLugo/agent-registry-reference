# ADR 0001: The registry is the system of record for agents

Status: accepted

## Context
Agents run on several platforms: AgentCore, Copilot Studio, Agentforce, vendor SaaS and in-house frameworks. Each platform has its own inventory, and none of them sees the others. Governance questions (who owns it, what tier is it, when was it last evaluated) have no home in any single platform.

## Decision
One registry record per agent, with a stable `agent_id`, is the source of truth for identity, ownership, risk tier, autonomy level, data classification, evaluation status, review dates and exceptions. Platform inventories are inputs to reconciliation, not sources of truth. The `agent_id` is propagated as the `x-agent-id` header at the gateway and as `gen_ai.agent.id` on spans, so every control and every metric joins on the same key.

## Consequences
* Every platform needs a mapping from its own identifier (`platform_ref`) to `agent_id`.
* Records change through intake and approval, not by editing a platform setting.
* Where a managed registry exists (AWS Agent Registry, Microsoft Agent 365) it can hold the platform side of the record; the enterprise record keeps the governance fields that span platforms.
