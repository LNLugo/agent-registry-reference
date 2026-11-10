"""Generate the synthetic sample registry and source data.

Every name, email, ARN and figure here is invented. The data is shaped so the
pipeline produces at least one finding of each type, which makes the sample
report useful for walking through the controls.

Run from the repo root:  python scripts/make_sample_data.py
"""
import csv
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "registry" / "agents"
DATA = ROOT / "data"
AGENTS.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)


def person(name, email):
    return {"name": name, "email": email}


def record(**kw):
    base = {
        "environment": "production",
        "status": "approved",
        "accountable_executive": person("Dana Whitfield", "dana.whitfield@example.com"),
        "prompt_version": "v1",
        "exceptions": [],
        "registered_on": "2026-06-01",
    }
    base.update(kw)
    return base


records = [
    record(
        agent_id="agt-advisor-assist",
        name="Advisor Assist",
        purpose="Answers financial advisor questions on products, quotes and forms with citations to approved content.",
        platform="aws-agentcore",
        platform_ref="arn:aws:bedrock-agentcore:us-east-1:111122223333:runtime/advisor-assist",
        business_owner=person("Maria Chen", "maria.chen@example.com"),
        technical_owner=person("Raj Patel", "raj.patel@example.com"),
        risk_tier="high",
        autonomy_level="act_with_approval",
        data_classification="confidential",
        models=[{"provider": "anthropic", "model": "claude-sonnet", "version": "2026-05"}],
        prompt_version="v14",
        tools=[
            {"name": "quote_lookup", "access": "read", "mcp_server": "mcp-quotes"},
            {"name": "create_illustration_request", "access": "write", "mcp_server": "mcp-illustrations"},
        ],
        identity={"type": "service_identity", "principal": "agentcore-identity/advisor-assist"},
        evaluation={"last_run": "2026-10-28", "result": "pass", "suite": "advisor-golden-set-v6"},
        review={"last_review": "2026-09-15", "next_review": "2026-12-15", "governance_forum": "AI Governance Committee"},
        cost_tags={"Application": "advisor-assist", "ApplicationOwner": "Advisor-Platforms", "Environment": "production", "CostCenter": "CC-210", "Model": "Claude-Sonnet", "Project": "Advisor-Intelligence"},
    ),
    record(
        agent_id="agt-claims-intake",
        name="Claims Intake Triage",
        purpose="Classifies incoming claim documents, extracts key fields and routes the claim to the right queue.",
        platform="aws-agentcore",
        platform_ref="arn:aws:bedrock-agentcore:us-east-1:111122223333:runtime/claims-intake",
        business_owner=person("Tom Alvarez", "tom.alvarez@example.com"),
        technical_owner=person("Raj Patel", "raj.patel@example.com"),
        risk_tier="high",
        autonomy_level="act",
        data_classification="restricted",
        models=[{"provider": "anthropic", "model": "claude-haiku", "version": "2026-03"}],
        prompt_version="v7",
        tools=[{"name": "route_claim", "access": "write", "mcp_server": "mcp-claims"}],
        identity={"type": "service_identity", "principal": "agentcore-identity/claims-intake"},
        evaluation={"last_run": "2026-08-30", "result": "pass", "suite": "claims-routing-v3"},
        review={"last_review": "2026-08-01", "next_review": "2026-11-30", "governance_forum": "AI Governance Committee"},
        cost_tags={"Application": "claims-intake", "ApplicationOwner": "Claims-Ops", "Environment": "production", "CostCenter": "CC-330", "Model": "Claude-Haiku", "Project": "Claims-Automation"},
    ),
    record(
        agent_id="agt-hr-policy-qa",
        name="HR Policy Q&A",
        purpose="Answers employee questions about HR policies from the published policy library.",
        platform="copilot-studio",
        platform_ref="copilot-bot-7f3a2c",
        business_owner=person("Lena Brooks", "lena.brooks@example.com"),
        technical_owner=person("Sam Okafor", "sam.okafor@example.com"),
        risk_tier="low",
        autonomy_level="assist",
        data_classification="internal",
        models=[{"provider": "azure-openai", "model": "gpt-4.1", "version": "2025-04"}],
        tools=[{"name": "sharepoint_policy_search", "access": "read"}],
        identity={"type": "maker_connection", "principal": "sam.okafor@example.com"},
        evaluation={"last_run": "2026-07-20", "result": "pass", "suite": "hr-faq-v2"},
        review={"last_review": "2026-05-01", "next_review": "2026-11-30"},
        exceptions=[{"id": "EXC-014", "reason": "Runs on maker connection until service account is provisioned", "remediation": "Move SharePoint connector to a service principal", "expires": "2026-10-31", "approved_by": "Architecture Review Board"}],
        cost_tags={"Application": "hr-policy-qa", "ApplicationOwner": "HR-Technology", "Environment": "production", "CostCenter": "CC-120"},
    ),
    record(
        agent_id="agt-wholesaler-recap",
        name="Wholesaler Meeting Recap",
        purpose="Drafts meeting recaps and follow up tasks for retirement wholesalers in the CRM.",
        platform="agentforce",
        vendor="Salesforce",
        platform_ref="Wholesaler_Recap_Agent",
        business_owner=person("Priya Nair", "priya.nair@example.com"),
        technical_owner=person("Chris Dunn", "chris.dunn@example.com"),
        risk_tier="medium",
        autonomy_level="assist",
        data_classification="confidential",
        models=[{"provider": "salesforce", "model": "vendor-managed", "version": "vendor-managed"}],
        tools=[{"name": "crm_activity_write", "access": "write"}],
        identity={"type": "service_identity", "principal": "sf-integration-user/recap"},
        evaluation={"last_run": "2026-09-10", "result": "pass", "suite": "recap-accuracy-v1"},
        review={"last_review": "2026-04-15", "next_review": "2026-10-15"},
        cost_tags={"Application": "wholesaler-recap", "ApplicationOwner": "Retirement-Sales", "Environment": "production", "CostCenter": "CC-410"},
    ),
    record(
        agent_id="agt-policy-servicing",
        name="Policy Servicing Agent",
        purpose="Processes routine policy service requests such as address and beneficiary changes, with QA sampling.",
        platform="vendor-saas",
        vendor="Example Automation Vendor",
        platform_ref="vendor-agent-ps-01",
        business_owner=person("Grace Kim", "grace.kim@example.com"),
        technical_owner=person("Chris Dunn", "chris.dunn@example.com"),
        risk_tier="high",
        autonomy_level="act",
        data_classification="restricted",
        models=[{"provider": "vendor", "model": "vendor-managed", "version": "vendor-managed"}],
        tools=[{"name": "policy_admin_update", "access": "write"}],
        identity={"type": "service_identity", "principal": "vendor-svc-ps01"},
        evaluation={"last_run": "2026-10-20", "result": "pass", "suite": "vendor-qa-sample-oct"},
        review={"last_review": "2026-10-01", "next_review": "2027-01-01", "governance_forum": "AI Governance Committee"},
        cost_tags={"Application": "policy-servicing", "ApplicationOwner": "Individual-Life-Ops", "Environment": "production", "CostCenter": "CC-350"},
    ),
    record(
        agent_id="agt-sourcing-analyst",
        name="Sourcing Analyst",
        purpose="Prepares sourcing strategies by combining spend data, contracts and meeting notes.",
        platform="in-house",
        platform_ref="langgraph-sourcing-analyst",
        status="suspended",
        business_owner=person("Omar Haddad", "omar.haddad@example.com"),
        technical_owner=person("Raj Patel", "raj.patel@example.com"),
        risk_tier="medium",
        autonomy_level="assist",
        data_classification="confidential",
        models=[{"provider": "openai", "model": "gpt-4.1", "version": "2025-04"}],
        tools=[{"name": "spend_cube_query", "access": "read"}],
        identity={"type": "service_identity", "principal": "svc-sourcing-analyst"},
        evaluation={"last_run": "2026-09-01", "result": "fail", "suite": "sourcing-v2"},
        review={"last_review": "2026-09-05", "next_review": "2026-12-05"},
        cost_tags={"Application": "sourcing-analyst", "ApplicationOwner": "Procurement-Tech", "Environment": "production", "CostCenter": "CC-520"},
    ),
    record(
        agent_id="agt-legacy-faq",
        name="Legacy Benefits FAQ",
        purpose="Answers benefits questions for a closed block of group policies.",
        platform="in-house",
        platform_ref="legacy-faq-bot",
        business_owner=person("Lena Brooks", "lena.brooks@example.com"),
        technical_owner=person("Sam Okafor", "sam.okafor@example.com"),
        risk_tier="low",
        autonomy_level="assist",
        data_classification="internal",
        models=[{"provider": "openai", "model": "gpt-4o-mini", "version": "2024-07"}],
        tools=[],
        identity={"type": "service_identity", "principal": "svc-legacy-faq"},
        evaluation={"last_run": "2026-06-01", "result": "pass", "suite": "faq-v1"},
        review={"last_review": "2026-06-01", "next_review": "2026-12-01"},
        cost_tags={"Application": "legacy-faq", "ApplicationOwner": "Group-Benefits", "Environment": "production", "CostCenter": "CC-150"},
    ),
]

for r in records:
    (AGENTS / f"{r['agent_id']}.json").write_text(json.dumps(r, indent=2) + "\n")

# Agents auto detected on AgentCore runtime (simplified export, not the exact API shape)
agentcore = [
    {"name": "advisor-assist", "runtime_arn": records[0]["platform_ref"], "account": "111122223333", "first_seen": "2026-06-02"},
    {"name": "claims-intake", "runtime_arn": records[1]["platform_ref"], "account": "111122223333", "first_seen": "2026-06-10"},
    {"name": "underwriting-notes-summarizer", "runtime_arn": "arn:aws:bedrock-agentcore:us-east-1:444455556666:runtime/uw-notes", "account": "444455556666", "first_seen": "2026-10-22"},
]
(DATA / "agentcore_detected.json").write_text(json.dumps(agentcore, indent=2) + "\n")

# Microsoft agent inventory export (simplified)
with open(DATA / "m365_agent_inventory.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["bot_id", "display_name", "owner_upn", "environment", "created"])
    w.writerow(["copilot-bot-7f3a2c", "HR Policy Q&A", "sam.okafor@example.com", "Production", "2026-03-11"])
    w.writerow(["copilot-bot-91be04", "Team Expense Helper", "jordan.lee@example.com", "Production", "2026-10-05"])

# Vendor agent inventory supplied by vendors under contract
with open(DATA / "vendor_agent_inventory.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["vendor", "agent_ref", "display_name", "business_unit"])
    w.writerow(["Salesforce", "Wholesaler_Recap_Agent", "Wholesaler Meeting Recap", "Retirement"])
    w.writerow(["Example Automation Vendor", "vendor-agent-ps-01", "Policy Servicing Agent", "Individual Life"])

# HR leaver feed
with open(DATA / "hr_leavers.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["email", "leave_date"])
    w.writerow(["tom.alvarez@example.com", "2026-11-03"])

# Cloud cost lines by tag (one month)
with open(DATA / "cloud_cost_by_tag.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["month", "Application", "ApplicationOwner", "CostCenter", "Model", "cost_usd"])
    w.writerow(["2026-10", "advisor-assist", "Advisor-Platforms", "CC-210", "Claude-Sonnet", "18420.55"])
    w.writerow(["2026-10", "claims-intake", "Claims-Ops", "CC-330", "Claude-Haiku", "6210.10"])
    w.writerow(["2026-10", "marketing-genai", "", "", "Claude-Sonnet", "3975.00"])
    w.writerow(["2026-10", "uw-notes", "Underwriting", "CC-360", "Claude-Haiku", "1120.40"])

# Gateway decision log (simplified, Kong style fields)
rng = random.Random(7)
start = datetime(2026, 10, 12, tzinfo=timezone.utc)
gw = []
active = ["agt-advisor-assist", "agt-claims-intake", "agt-hr-policy-qa", "agt-wholesaler-recap", "agt-policy-servicing"]
for i in range(400):
    a = rng.choice(active)
    gw.append({"ts": (start + timedelta(minutes=97 * i)).isoformat(), "route": "llm-default", "x_agent_id": a, "consumer": a.replace("agt-", "svc-"), "decision": "allow"})
gw.append({"ts": "2026-11-02T14:05:00+00:00", "route": "llm-default", "x_agent_id": None, "consumer": "svc-marketing-gen", "decision": "deny", "reason": "missing x-agent-id"})
gw.append({"ts": "2026-11-04T09:30:00+00:00", "route": "llm-legacy", "x_agent_id": "agt-sourcing-analyst", "consumer": "svc-sourcing-analyst", "decision": "allow"})
with open(DATA / "gateway_decisions.jsonl", "w") as f:
    for row in gw:
        f.write(json.dumps(row) + "\n")

# OpenTelemetry style spans (flattened). gen_ai.* names follow the GenAI semantic conventions;
# guardrail.action is a custom attribute.
profiles = {
    "agt-advisor-assist": (1800, 0.012, 2400, 0.004),
    "agt-claims-intake": (900, 0.041, 3100, 0.010),
    "agt-hr-policy-qa": (300, 0.006, 1500, 0.002),
    "agt-wholesaler-recap": (500, 0.015, 2800, 0.001),
    "agt-policy-servicing": (700, 0.022, 4200, 0.006),
}
with open(DATA / "otel_spans.jsonl", "w") as f:
    for agent, (n, err, p50, guard) in profiles.items():
        for _ in range(n):
            lat = max(200, int(rng.lognormvariate(0, 0.45) * p50))
            span = {
                "name": f"invoke_agent {agent}",
                "gen_ai.operation.name": "invoke_agent",
                "gen_ai.agent.id": agent,
                "duration_ms": lat,
                "status": "ERROR" if rng.random() < err else "OK",
                "gen_ai.usage.input_tokens": rng.randint(800, 4000),
                "gen_ai.usage.output_tokens": rng.randint(100, 900),
                "guardrail.action": "blocked" if rng.random() < guard else "none",
            }
            f.write(json.dumps(span) + "\n")

print(f"wrote {len(records)} registry records and sample source data")
