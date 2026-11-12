# Design guide: AI agent inventory and registry

Operating model, anchored to NIST AI RMF 1.0 and ISO/IEC 42001:2023. Companion to the [record schema](../schema/agent-record.schema.json), the [gateway policy](../policy/gateway.rego) and the [Agent Catalog](catalog/). Field names below are the ones in the schema. All agents named in the examples are fictional.

# 1. Why an agent inventory comes first

Agents are being built faster than they are being governed. Gartner projects the average Fortune 500 company will run more than 150,000 agents by 2028, up from fewer than 15 in 2025, while only 13% of surveyed organizations believe their governance is adequate. An organization cannot assess, monitor, cost or switch off an agent it does not know exists.

NIST AI RMF makes this explicit in GOVERN 1.6: mechanisms are in place to inventory AI systems, resourced according to risk priorities. ISO/IEC 42001 assumes the same thing: every control in Annex A, from impact assessment to event logs, needs a list of systems to apply to. The inventory is that list, and the registry is the system of record behind it.

# 2. What Uber and Grab show

John Sviokla's Forbes piece (Nov 11, 2026) describes how two companies are untangling what he calls the agentic hairball: fast, employee built agents colliding with the slower work of scaling them safely.

## Uber: one registry as the behavioral contract

Uber's own engineering posts (May 21 and November 6, 2026) give far more detail than the Forbes summary. The design, which Uber calls Uber Secure AI, runs in three layers: provisioning time validation, runtime enforcement and continuous assurance.

- **Two on-ramps, one platform.** On the Michelangelo AI platform engineers write agents with an internal Python SDK and others use a no code option; either way the agent deploys as a Kubernetes workload.

- **The AI Registry is the contract.** It is the authoritative record of each agent's identity, ownership, persona, permitted intents, constraints, dependencies and risk tier, and it acts as the policy administration point (PAP).

- **AI Guard decides; hooks enforce.** AI Guard is the policy decision point, using small specialized models hosted locally and run in parallel. Agent Guard hooks, LangFx and the AI Guard SDK are the enforcement points that apply its verdict before an action proceeds.

- **Argus checks the contract against the code.** It scans source, prompts, configuration, dependencies, endpoints and tool invocation paths, derives intents from the implementation, and flags unregistered agents and unauthorized MCP endpoints in the monorepo.

- **Tools are vetted before connection.** Third party MCP servers go through static and dynamic analysis, composition analysis and semantic inspection of tool descriptions for poisoning and indirect prompt injection.

- **Identity per hop.** A Security Token Service is the only component allowed to mint agent tokens. It verifies the agent against the registry and issues short lived JWTs for each hop that carry the full actor chain.

- **Trace, replay, red team.** One trace links agent actions, tool calls and guardrail decisions, with sensitive content redacted. Recorded traffic is replayed against candidate guardrails, which run in shadow mode before they enforce.

**Uber's lessons.** Restricting agents to explicit intents and constraints was the most effective mitigation, at some cost in flexibility. Guardrails handled known attack patterns well but were less predictable against new injection techniques. Uniform thresholds gave way to per agent calibration by risk.

## Grab: builder platforms with a review gate

- **Two paths again.** SpellVault for non coders; LLM-Kit, a shared framework running 500+ internal agent services, cut day one setup for secrets, tracing and evaluation from two weeks or more to about an hour.

- **Light gate.** Each use case files a short proposal and checklist for platform review, with a task force for deeper cases.

- **Gateway as the control and cost plane.** Authentication, rate limits, logging of every call, cost reporting and budget alerts.

- **Funnel.** 3,000+ employees requested experimentation keys and 300+ use cases reached production.

## What the article leaves open

Uber publishes its registry fields but not its tier definitions, thresholds or detection rates. Grab publishes neither. Sviokla names an "agentic hairball quotient" without defining it. This guide fills those gaps with a schema, a tiering model, a lifecycle and a proposed quotient definition.

# 3. Design principles

1.  **Register at build, not by search.** The SDK and the no code builder both write the registry entry before an agent can get credentials. Discovery sweeps catch the rest, but they are the safety net, not the process.

2.  **One agent, one owner, one entry.** Sviokla's 30 day action, and the right one: a named person, not a team. No owner means no production credentials.

3.  **Same controls through every door.** Build path is recorded, but tier, not build path, decides controls. A no code agent that emails customers is governed like an SDK agent that emails customers.

4.  **Identity that survives the chain.** Every hop carries the requesting person. Shared service accounts and personal keys are findings, not configurations.

5.  **The shadow belongs on the list.** Unapproved agents are registered as Discovered first and assessed second. Leaving them off makes the inventory look clean and the risk invisible.

6.  **Access is not the same as appropriate.** An agent can hold every permission it needs and still take an action the user never asked for. The registry records what the agent is for (intents) and what it must never do (constraints), and runtime checks hold it to that.

# 4. Registry record

[`schema/agent-record.schema.json`](../schema/agent-record.schema.json) is the contract for one record. The groups and the questions they answer:

| Group | Fields | Question it answers |
|---|---|---|
| Identity and ownership | `agent_id`, `name`, `purpose`, `business_owner`, `technical_owner`, `accountable_executive` | Can we list every running agent with named, current owners? |
| Platform and status | `platform`, `platform_ref`, `vendor`, `environment`, `status`, `registered_on` | Where does it run, how do we reconcile it, and is it approved? |
| Risk | `risk_tier`, `autonomy_level`, `data_classification`, `risk_factors` | How much harm can it do, and what controls does that require? |
| Runtime | `models`, `prompt_version`, `tools`, `identity` | What can it call, as whom? |
| Assurance | `evaluation`, `review`, `exceptions` | Is it tested, re-attested on time, and are exceptions bounded? |
| Attribution | `cost_tags` | Which spend is this agent's? |
| Behavioral contract | `behavioral_contract`: persona, permitted intents, constraints, delegated agents, contract scan, runtime guardrail, tool vetting, last red team | Is it doing only what it was registered to do, and would we catch it if not? |

# 5. Risk tiering

Four factors sum to a risk score of 4 to 15. Two triggers override the score: any agent that takes `financial_binding` actions or `decides_on_customers` is high tier regardless. This stops a well controlled but consequential agent, such as one that proposes trades a manager approves, from scoring its way into a lighter tier.

| Factor | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| `autonomy_level` | `assist` | `act_with_approval` | `act` | |
| `risk_factors.action_scope` | `read_only` | `write_internal` | `write_external` | `financial_binding` |
| `data_classification` | `public` | `internal` | `confidential` | `restricted` |
| `risk_factors.customer_impact` | `internal_only` | `customer_facing` | | `decides_on_customers` |

| Tier | Score or trigger | Limits in this repo | Minimum controls before approval |
|---|---|---|---|
| high | 11 to 15, or `financial_binding`, or `decides_on_customers` | eval age 30 days, owner reassignment 1 day, contract scan 30 days, governance forum review | named business and technical owners; evaluation and red team; human approval for binding actions; per hop delegated identity; gateway on every call; runtime guardrail enforcing (gateway denies otherwise) |
| medium | 7 to 10 | eval age 90 days, reassignment 5 days, contract scan 90 days | named owners; evaluation; gateway on every call; runtime guardrail enforcing; incident runbook |
| low | 4 to 6 | eval age 180 days, reassignment 10 days | named owners; registry entry; gateway or approved vendor controls; periodic re-attestation |

`risk_tier` stays the governed value. When the factors compute a higher tier, `TIER_UNDERSTATED` is raised; a stored tier above the computed one is allowed. Autonomy is recorded at the highest level the agent can reach with its granted permissions, not its usual behavior, and action scope is checked against the tool grants, not the builder's description.

# 6. Lifecycle and gates

| `status` | Entry gate | Who approves |
|---|---|---|
| `draft` | Record created through intake with owners, purpose and risk factors | Business owner |
| `pending_approval` | Tier confirmed, behavioral contract declared, evaluation plan, identity per hop in place | Platform team, plus risk for high tier |
| `approved` | Tier minimum controls met; evaluation passed; contract scan matches; guardrail enforcing for medium and high | Business owner, plus the governance forum for high tier |
| `suspended` | Gateway denies all calls; incident, failed review, overdue orphan or critical drift | Technical owner, risk, or automatic on policy breach |
| `retired` | Credentials revoked, data retained per schedule, record kept for audit | Business owner |

# 7. From registry to runtime

Uber's design makes the registry the source of policy, not just a list. The same separation works on any stack:

| **Role**                    | **Uber**                                                   | **Generic equivalent**                                             |
|-----------------------------|------------------------------------------------------------|--------------------------------------------------------------------|
| Policy administration (PAP) | AI Registry: persona, intents, constraints, risk tier      | `registry/agents/*.json` with `behavioral_contract`  |
| Policy decision (PDP)       | AI Guard, small local models in parallel                   | Guardrail service calibrated by tier; the gateway policy reads its mode from the registry              |
| Policy enforcement (PEP)    | Agent Guard hooks, LangFx, AI Guard SDK                    | Gateway (`policy/gateway.rego`) and SDK hooks before every tool call              |
| Identity                    | Security Token Service, per hop JWT with actor chain       | Token exchange with audience scoping; no shared service accounts   |
| Verification                | Argus static analysis of code, prompts, config, tool paths | Scheduled scan; result recorded in `behavioral_contract.contract_scan` |

New guardrails start in Shadow mode, logging verdicts without blocking, and move to Enforcing once replayed traffic shows an acceptable false block rate for that agent. Model based checks add cost and latency, so binding actions keep deterministic limits and human approval as the backstop.

# 8. Finding the shadow agents

Sviokla's first step is a central inventory that includes unapproved agents. These sources find them, in rough order of yield:

- **AI gateway and egress logs:** calls to model APIs that did not come through the gateway, or came through with an unregistered client ID.

- **Identity provider:** service principals, OAuth app consents and API keys with model provider scopes.

- **SaaS admin consoles:** Copilot Studio, Agentforce, Now Assist and similar builders each keep their own agent lists.

- **CASB and browser telemetry:** uploads to consumer AI services and custom chatbots on personal accounts.

- **Code and pipelines:** repositories importing agent SDKs or model clients; container images with model endpoints in config. Uber's Argus does this across its monorepo and also flags unauthorized MCP endpoints.

- **Cloud billing and expenses:** model spend without a registry tag; AI subscriptions on expense reports.

Each find becomes a Discovered (unapproved) entry the same day. The owner is then given a short window to claim, assess and register it, or it is suspended at the gateway.

# 9. Scorecard

The monthly report (`agent-registry report`) turns Sviokla's three questions into measures, plus registration and the behavioral contract:

| Question | Measured as |
|---|---|
| Every running agent has a named owner | Approved agents with an active business and technical owner (no `ORPHANED*` finding) |
| Every action traces back to the requesting human | Calls carry `x-agent-id` and spans carry `gen_ai.agent.id`; gaps show as `UNREGISTERED_CALLER` |
| Both on-ramps get the same controls | One record contract and one gateway policy for AgentCore, Copilot Studio, Agentforce, vendor and in-house agents |
| Agents are registered, not found later | `UNREGISTERED_AGENT` from AgentCore, Microsoft and vendor inventories, `UNATTRIBUTED_SPEND` from cost tags |
| Agents do only what they declare | Share with a declared contract, share whose contract matches the latest scan, guardrail and tool vetting status per agent |

**Hairball quotient (proposed):** the share of agents, registered or discovered, with at least one open finding from reconciliation, ownership or the contract checks. John Sviokla names the metric without defining it; this is a proposed definition, and the trend matters more than the starting point.

In the sample, `agt-policy-servicing` passes every v0.1 check and still fails one here: its scan shows the update tool accepts coverage changes and surrenders it never declared. That is the gap access control alone cannot see.

# 10. Framework mapping

| **Inventory element**                  | **NIST AI RMF 1.0**                   | **ISO/IEC 42001:2023**                         |
|----------------------------------------|---------------------------------------|------------------------------------------------|
| The registry itself                    | GOVERN 1.6 inventory                  | A.6 AI system life cycle                       |
| Named owners                           | GOVERN 2.1 roles and responsibilities | A.3.2 AI roles and responsibilities            |
| Risk factors and tier                  | MAP 1.1, MAP 5.1                      | 6.1.2 risk assessment; A.5.2 impact assessment |
| Third party and vendor agents          | GOVERN 6.1                            | A.10.3 suppliers                               |
| Evaluation status                      | MEASURE 2.1, 2.3                      | A.6.2.4 verification and validation            |
| Human trace and identity               | MEASURE 2.8                           | A.6.2.8 event logs                             |
| Periodic review                        | GOVERN 1.5                            | 9.1 monitoring and evaluation                  |
| Kill switch                            | MANAGE 2.4 disengage or deactivate    | A.6.2.6 operation and monitoring               |
| Incidents                              | MANAGE 4.3                            | A.8.4 communication of incidents               |
| Retirement                             | GOVERN 1.7 decommissioning            | A.6 AI system life cycle                       |
| Intents and constraints                | MAP 1.1, MAP 3.5                      | A.9.4 intended use; A.9.2 responsible use      |
| Contract scans, tool vetting, red team | MEASURE 2.7 security and resilience   | A.6.2.4; A.10.3 suppliers                      |

*This is a practitioner mapping for discussion. Check control wording against the licensed ISO/IEC 42001 text and the NIST AI RMF playbook before formal use.*

# 11. First 90 days

| **Window**    | **Outcome**                                                                                                                                                                                                                                                                                                                                                 |
|---------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Days 1 to 30  | Stand up the registry with this schema. Load every known agent from builder platforms and the gateway. Run the first discovery sweep and log every find as Discovered. Enforce one named owner per agent. Publish the baseline scorecard and hairball quotient.                                                                                             |
| Days 31 to 60 | Tier every agent. Close high tier gaps first: owner, per-hop identity, gateway mediation, kill switch test. Wire registration into the SDK and no code builder so new agents cannot get credentials without an entry. Capture intents and constraints for every high tier agent and put runtime guardrails in shadow mode. Agree review cadence with second line. |
| Days 61 to 90 | Automate discovery on a weekly schedule. Run the first contract scan comparing declared intents to code and tool paths. Move high tier guardrails to enforcing after replay. Feed gateway cost and incident data into the registry. Run the first quarterly high tier review. Report the quotient trend and overdue reviews to the AI risk committee.             |

# Sources

- John Sviokla, "Do You Suffer From AI AgentBabble? Learn From Uber And More," Forbes, Nov 11, 2026

- Sean Tout, Max Zhurovich, Adi Raghavendra, "Securing AI Agents: Lessons From Real-World Deployment," Uber Engineering, Nov 6, 2026 (uber.com/blog/securing-ai-agents)

- Matt Mathew, Prasad Borole, Meng Huang, "Solving the Identity Crisis for AI Agents," Uber Engineering, May 21, 2026 (uber.com/blog/solving-the-agent-identity-crisis)

- Learnetto, "Uber production agent security" (secondary summary)
