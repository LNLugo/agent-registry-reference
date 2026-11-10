# agent-registry-reference

A reference implementation of an enterprise AI agent registry. It answers the four questions a governance team gets asked about every agent:

1. **Does it exist?** One record per agent, whatever platform it runs on.
2. **Who owns it?** A business owner, a technical owner and an accountable executive, kept current when people leave.
3. **How is it performing?** Telemetry joined to the registry ID: errors, latency, guardrail blocks, tokens and cost.
4. **Is it compliant?** Evaluations, reviews and exceptions checked against tier based limits, enforced at the gateway, and reported monthly.

All data in this repo is synthetic. The AgentCore, Microsoft and vendor inventories are simplified extracts, not the exact API shapes of those products.

## The design in one picture

```
 intake (ServiceNow or similar)
        |
        v
 +------------------+     export-opa      +-------------------+
 |  Registry        | ------------------> |  Gateway policy   |  no registry ID, no route
 |  registry/agents |                     |  policy/*.rego    |  (Kong, AgentCore Gateway, any OPA aware proxy)
 +------------------+                     +-------------------+
        ^    ^                                     |
        |    |  reconcile                          | decision log
        |    +------------------------------+      v
        |  AgentCore auto detection         |  gateway_decisions.jsonl
        |  Microsoft agent inventory        |
        |  vendor contractual inventory     |  otel_spans.jsonl (gen_ai.agent.id)
        |  cloud cost by tag                |  cloud_cost_by_tag.csv (Application tag)
        |                                   |
        +------ lifecycle (HR leavers, eval age, review dates, exception expiry)
                         |
                         v
            reports/governance-report-<date>.md
```

## What it checks

| Rule | What it catches | Why it matters |
|---|---|---|
| `UNREGISTERED_AGENT` | An agent found on AgentCore, in the Microsoft inventory or in a vendor's inventory with no registry record | Registration that depends on people volunteering is incomplete by design. Discovery is reconciled, not trusted |
| `UNREGISTERED_CALLER` | A gateway call with no or an unknown `x-agent-id` | Shows who is trying to bypass registration |
| `ENFORCEMENT_GAP` | A suspended or retired agent that the gateway still allowed | A control that is not enforced everywhere is not a control |
| `UNATTRIBUTED_SPEND` | Cloud spend whose `Application` tag maps to no agent | Cost tags find workloads that registration missed |
| `ORPHANED` / `ORPHANED_OVERDUE` | An owner on the HR leaver feed, inside or past the reassignment window for the tier (high 1 day, medium 5, low 10) | Every production agent needs an active owner for its whole life |
| `PERSONAL_CREDENTIALS` | A production agent running on a person's connection | It breaks, or keeps that person's access, when they leave |
| `EVAL_STALE` / `EVAL_FAILING` | Evaluation older than the tier limit (high 30 days, medium 90, low 180) or failing | Approval is not permanent |
| `REVIEW_OVERDUE` | Re-attestation date passed | Ownership is a standing responsibility, not a one time sign off |
| `EXCEPTION_EXPIRED` | A time bound exception past its expiry | Exceptions carry a rationale, a remediation and an end date |
| `DORMANT` | An approved agent with no traffic for 60 days | Unused agents are attack surface; retire them |
| `SINGLE_OWNER`, `SCHEMA_INVALID` | Record quality | One departure should never orphan an agent |

The gateway policy denies a call when the agent is unknown, not approved, in the wrong environment, on an unlisted route, failing evaluation, or (high tier only) past its evaluation age limit.

## Tags versus registry fields

Cloud tags (`Application`, `ApplicationOwner`, `Environment`, `CostCenter`, `Model`, `Project`, `ClientEngagement`) are good for ownership and cost attribution and are kept in each record as `cost_tags`. They are not enough for governance: risk tier, autonomy level, data classification, evaluation status and review dates live in the registry, where changes go through approval. See [ADR 0004](docs/adr/0004-tags-versus-registry-fields.md).

## Run it

Windows PowerShell:

```powershell
./scripts/run.ps1                 # venv, install, tests, policy tests, report
./scripts/run.ps1 -AsOf 2026-11-10
```

Any shell:

```bash
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
agent-registry export-opa
opa test policy/                                   # needs the opa binary
agent-registry reconcile --as-of 2026-11-10
agent-registry lifecycle --as-of 2026-11-10
agent-registry report    --as-of 2026-11-10        # writes reports/governance-report-2026-11-10.md
```

Commands exit with code 1 when a critical finding exists, so they can gate a pipeline.

The committed sample report is [reports/governance-report-2026-11-10.md](reports/governance-report-2026-11-10.md).

## Repository layout

```
schema/agent-record.schema.json   the registry record contract
registry/agents/*.json            one file per agent (7 synthetic agents across 5 platforms)
data/                             synthetic discovery, gateway, telemetry, cost and HR extracts
policy/gateway.rego               gateway admission policy, with tests in gateway_test.rego
src/agent_registry/               validate, reconcile, lifecycle, KPIs, report, OPA export
tests/                            pytest suite
docs/adr/                         design decisions
docs/control-mapping.md           how the checks map to SR 11-7, NIST AI RMF and ISO/IEC 42001
scripts/                          sample data generator and PowerShell runner
```

## Known limits

* Auto detection exists only where the platform offers it (AgentCore in this sample). Vendor and SaaS agents are covered by contractual inventories and gateway and cost signals, which is weaker.
* OpenTelemetry GenAI agent attributes such as `gen_ai.agent.id` are still at Development stability and may be renamed. `guardrail.action` is a custom attribute.
* The registry here is a folder of JSON files to keep the reference readable. In production it would be a managed registry (AWS Agent Registry, Microsoft Agent 365, ModelOp, OneTrust or a database) with the same contract.
* Thresholds and windows are illustrative defaults, set per organization by the governance forum.

## License

MIT
