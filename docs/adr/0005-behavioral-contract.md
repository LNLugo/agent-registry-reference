# ADR 0005: Record a behavioral contract and compute the risk tier

Status: accepted

## Context
Through v0.1.0 the registry answers who owns an agent, whether it is evaluated and reviewed, and whether the gateway enforces its status. All of that is access control: it decides who may act. It does not decide whether a specific action is in scope. An agent with every permission it needs can still take an action nobody asked for, after an indirect prompt injection or because a tool does more than its name suggests.

Uber's published agent security design (Securing AI Agents, Uber Engineering, Nov 6, 2026) makes the same point. Its AI Registry records each agent's identity, owner, persona, permitted intents, constraints, dependencies and risk tier as a behavioral contract, acts as the policy administration point, and feeds a decision service and enforcement hooks. Uber reports that restricting agents to explicit intents and constraints was its most effective mitigation.

Separately, `risk_tier` was set by hand. Every limit in the registry (evaluation age, owner reassignment window, forum review) keys off it, so an understated tier weakens every control at once.

## Decision
1. Add an optional `behavioral_contract` block: persona, permitted intents, constraints, delegated agents, latest contract scan (`match`, `drift`, `not_run`), runtime guardrail mode (`none`, `shadow`, `enforcing`), tool vetting status and last red team date.
2. Add `risk_factors` (`action_scope`, `customer_impact`), required for approved agents. With `autonomy_level` and `data_classification` they give a score of 4 to 15; 11 or more is high, 7 or more medium. Any agent that takes financial or binding actions, or decides about a customer, is high whatever it scores.
3. Keep `risk_tier` as the governed value and flag `TIER_UNDERSTATED` when the computed tier is higher. A stored tier above the computed one is allowed: stricter is a valid choice.
4. Add contract checks (`NO_BEHAVIORAL_CONTRACT`, `CONTRACT_DRIFT`, `CONTRACT_NOT_VERIFIED`, `GUARDRAIL_NOT_ENFORCING`, `TOOLS_NOT_VETTED`, `UNKNOWN_DEPENDENCY`) and publish the guardrail mode to the gateway, which denies high tier agents whose guardrail is not enforcing.

## Why
* The contract makes "appropriate" checkable. Without declared intents, a guardrail has nothing to compare an action against.
* Recording scan results and guardrail mode in the registry, rather than running them here, keeps one system of record (ADR 0001) while the scanner and guardrail stay separate systems.
* Two triggers stop a well controlled but consequential agent from scoring its way into a lighter tier.

## Consequences
* Approved agents without `risk_factors` fail schema validation.
* `CONTRACT_DRIFT` on a high tier agent that acts without approval is critical and gates the pipeline.
* New guardrails start in shadow mode and are reported until they enforce; shadow is for calibration, not production.
* The Agent Catalog (`docs/catalog/`) reads the same export, so what people browse is what governance reports.
