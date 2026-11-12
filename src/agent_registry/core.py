"""Registry loading, schema validation, reconciliation and lifecycle checks.

Each check returns Finding objects. A finding names the agent (or the
discovered thing that should have been an agent), the rule it broke, a
severity, and the action the owner or governance team should take.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, asdict
from datetime import date, datetime
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]

# Policy settings. Tighter for higher tiers.
OWNER_REASSIGN_DAYS = {"high": 1, "medium": 5, "low": 10}
EVAL_MAX_AGE_DAYS = {"high": 30, "medium": 90, "low": 180}
DORMANT_DAYS = 60
ACTIVE_STATUSES = {"approved"}

# Computed risk tier. Four factors; two triggers make an agent high tier
# whatever it scores. See docs/adr/0005-behavioral-contract.md.
RISK_POINTS = {
    "autonomy_level": {"assist": 1, "act_with_approval": 2, "act": 3},
    "action_scope": {"read_only": 1, "write_internal": 2, "write_external": 3, "financial_binding": 4},
    "data_classification": {"public": 1, "internal": 2, "confidential": 3, "restricted": 4},
    "customer_impact": {"internal_only": 1, "customer_facing": 2, "decides_on_customers": 4},
}
TIER_THRESHOLDS = (("high", 11), ("medium", 7), ("low", 0))
TIER_RANK = {"low": 0, "medium": 1, "high": 2}
CONTRACT_SCAN_MAX_AGE_DAYS = {"high": 30, "medium": 90, "low": 180}


@dataclass
class Finding:
    rule: str
    severity: str  # critical, high, medium, low
    subject: str  # agent_id, or a description of an unregistered resource
    detail: str
    action: str

    def to_dict(self) -> dict:
        return asdict(self)


def _d(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


# ---------- loading ----------

def load_schema(root: Path = ROOT) -> dict:
    return json.loads((root / "schema" / "agent-record.schema.json").read_text())


def load_registry(root: Path = ROOT) -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted((root / "registry" / "agents").glob("*.json"))]


def load_csv(path: Path) -> list[dict]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def load_jsonl(path: Path) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


# ---------- validation ----------

def validate_records(records: list[dict], schema: dict) -> list[Finding]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    findings: list[Finding] = []
    seen: set[str] = set()
    for r in records:
        aid = r.get("agent_id", "<missing agent_id>")
        for err in sorted(validator.iter_errors(r), key=lambda e: list(e.path)):
            where = "/".join(str(p) for p in err.path) or "(record)"
            findings.append(Finding("SCHEMA_INVALID", "high", aid, f"{where}: {err.message}", "Fix the record before it can be approved"))
        if aid in seen:
            findings.append(Finding("DUPLICATE_ID", "high", aid, "agent_id appears more than once", "Assign a unique agent_id"))
        seen.add(aid)
        if r.get("business_owner", {}).get("email") == r.get("technical_owner", {}).get("email"):
            findings.append(Finding("SINGLE_OWNER", "medium", aid, "Business and technical owner are the same person", "Name a separate technical owner so one departure cannot orphan the agent"))
    return findings


# ---------- reconciliation: what runs vs what is registered ----------

def reconcile(records: list[dict], data_dir: Path, as_of: date) -> list[Finding]:
    findings: list[Finding] = []
    by_ref = {r["platform_ref"]: r for r in records}
    by_id = {r["agent_id"]: r for r in records}
    by_app = {r["cost_tags"]["Application"]: r for r in records}

    for d in json.loads((data_dir / "agentcore_detected.json").read_text()):
        if d["runtime_arn"] not in by_ref:
            findings.append(Finding("UNREGISTERED_AGENT", "high", f"AgentCore runtime {d['name']} (account {d['account']})",
                                    f"Auto detected on AgentCore since {d['first_seen']}, no registry record",
                                    "Register through intake or shut down; block at the gateway until registered"))

    for row in load_csv(data_dir / "m365_agent_inventory.csv"):
        if row["bot_id"] not in by_ref:
            findings.append(Finding("UNREGISTERED_AGENT", "high", f"Copilot Studio agent '{row['display_name']}' ({row['bot_id']})",
                                    f"In the Microsoft agent inventory ({row['environment']}), owner {row['owner_upn']}, no registry record",
                                    "Owner registers it through the approval gate within 10 business days or it is disabled"))

    for row in load_csv(data_dir / "vendor_agent_inventory.csv"):
        if row["agent_ref"] not in by_ref:
            findings.append(Finding("UNREGISTERED_AGENT", "high", f"{row['vendor']} agent '{row['display_name']}'",
                                    "Listed in the vendor's contractual inventory, no registry record",
                                    "Register and route through third party risk review"))

    gateway = load_jsonl(data_dir / "gateway_decisions.jsonl")
    last_seen: dict[str, date] = {}
    for g in gateway:
        aid = g.get("x_agent_id")
        ts = datetime.fromisoformat(g["ts"]).date()
        if aid:
            last_seen[aid] = max(last_seen.get(aid, ts), ts)
        if not aid:
            findings.append(Finding("UNREGISTERED_CALLER", "medium", f"Gateway consumer {g['consumer']}",
                                    f"Called route {g['route']} with no x-agent-id on {ts} (decision: {g['decision']})",
                                    "Identify the owner and register, or revoke the consumer credential"))
            continue
        rec = by_id.get(aid)
        if rec is None:
            findings.append(Finding("UNREGISTERED_CALLER", "high", aid, f"Unknown agent ID used at the gateway on {ts}", "Revoke the credential"))
        elif rec["status"] not in ACTIVE_STATUSES and g["decision"] == "allow":
            findings.append(Finding("ENFORCEMENT_GAP", "critical", aid,
                                    f"Status is {rec['status']} but the gateway allowed a call on route {g['route']} on {ts}",
                                    "Put the route behind the registry policy; investigate why the route bypassed it"))

    for r in records:
        if r["status"] in ACTIVE_STATUSES and r["platform"] in ("aws-agentcore", "in-house"):
            seen = last_seen.get(r["agent_id"])
            if seen is None or (as_of - seen).days > DORMANT_DAYS:
                findings.append(Finding("DORMANT", "low", r["agent_id"],
                                        f"No gateway traffic in the last {DORMANT_DAYS} days",
                                        "Confirm with the owner and retire if no longer needed"))

    for row in load_csv(data_dir / "cloud_cost_by_tag.csv"):
        app = row["Application"]
        if app not in by_app:
            missing = [k for k in ("ApplicationOwner", "CostCenter") if not row[k]]
            note = f"; missing tags: {', '.join(missing)}" if missing else ""
            findings.append(Finding("UNATTRIBUTED_SPEND", "medium", f"Application tag '{app}'",
                                    f"${float(row['cost_usd']):,.2f} in {row['month']} not linked to a registered agent{note}",
                                    "Map the spend to a registry record or stop the workload"))
    return findings


# ---------- lifecycle: ownership, reviews, evaluations, exceptions ----------

def lifecycle(records: list[dict], data_dir: Path, as_of: date) -> list[Finding]:
    findings: list[Finding] = []
    leavers = {row["email"].lower(): _d(row["leave_date"]) for row in load_csv(data_dir / "hr_leavers.csv")}

    for r in records:
        if r["status"] == "retired":
            continue
        aid, tier = r["agent_id"], r["risk_tier"]

        for role in ("business_owner", "technical_owner"):
            left = leavers.get(r[role]["email"].lower())
            if left:
                days = (as_of - left).days
                window = OWNER_REASSIGN_DAYS[tier]
                if days > window:
                    findings.append(Finding("ORPHANED_OVERDUE", "critical" if tier == "high" else "high", aid,
                                            f"{role.replace('_', ' ')} {r[role]['name']} left on {left}; {days} days without a replacement (window {window} for {tier} tier)",
                                            "Suspend now (high tier: restrict to read only) until the business sponsor names a replacement who re-attests"))
                else:
                    findings.append(Finding("ORPHANED", "high", aid,
                                            f"{role.replace('_', ' ')} {r[role]['name']} left on {left}",
                                            f"Business sponsor names a replacement within {window} days; new owner re-attests purpose, data scope and connectors"))

        if r["status"] in ACTIVE_STATUSES:
            ev = r["evaluation"]
            last = _d(ev["last_run"])
            max_age = EVAL_MAX_AGE_DAYS[tier]
            if ev["result"] != "pass":
                findings.append(Finding("EVAL_FAILING", "high", aid, f"Last evaluation result: {ev['result']}", "Fix or roll back to the last passing version"))
            elif last is None or (as_of - last).days > max_age:
                age = "never run" if last is None else f"{(as_of - last).days} days old"
                findings.append(Finding("EVAL_STALE", "high" if tier == "high" else "medium", aid,
                                        f"Evaluation {age}; limit for {tier} tier is {max_age} days",
                                        "Re-run the evaluation suite before the next release"))

            nxt = _d(r["review"]["next_review"])
            if nxt and nxt < as_of:
                findings.append(Finding("REVIEW_OVERDUE", "medium" if tier != "high" else "high", aid,
                                        f"Review was due {nxt}", "Owner re-attests; governance team records the review"))

            if r["identity"]["type"] == "maker_connection" and r["environment"] == "production":
                findings.append(Finding("PERSONAL_CREDENTIALS", "high", aid,
                                        f"Runs in production on a person's connection ({r['identity']['principal']})",
                                        "Move to a service identity; the agent breaks or keeps the person's access when they leave"))

            if tier == "high" and r["autonomy_level"] == "act" and r["data_classification"] == "restricted" \
                    and "governance_forum" not in r["review"]:
                findings.append(Finding("MISSING_FORUM_REVIEW", "high", aid, "High tier autonomous agent on restricted data without a governance forum review", "Schedule committee review"))

        for ex in r.get("exceptions", []):
            exp = _d(ex["expires"])
            if exp < as_of:
                findings.append(Finding("EXCEPTION_EXPIRED", "high", aid,
                                        f"Exception {ex['id']} expired {exp}: {ex['reason']}",
                                        f"Close it ({ex['remediation']}) or renew it with {ex['approved_by']}"))
    return findings


# ---------- risk tier: computed from factors, compared with the stored tier ----------

def risk_score(record: dict) -> int | None:
    """Sum of the four factor points (4 to 15), or None when risk_factors is missing."""
    factors = record.get("risk_factors")
    if not factors:
        return None
    values = {
        "autonomy_level": record["autonomy_level"],
        "data_classification": record["data_classification"],
        **factors,
    }
    return sum(RISK_POINTS[k][v] for k, v in values.items())


def computed_tier(record: dict) -> str | None:
    score = risk_score(record)
    if score is None:
        return None
    f = record["risk_factors"]
    if f["action_scope"] == "financial_binding" or f["customer_impact"] == "decides_on_customers":
        return "high"
    return next(tier for tier, floor in TIER_THRESHOLDS if score >= floor)


# ---------- behavioral contract: is the agent doing only what it was registered to do ----------

def contract_checks(records: list[dict], as_of: date) -> list[Finding]:
    """Access control says who may act. These checks ask whether the action is in scope."""
    findings: list[Finding] = []
    for r in records:
        if r["status"] not in ACTIVE_STATUSES:
            continue
        aid, tier = r["agent_id"], r["risk_tier"]

        computed = computed_tier(r)
        if computed and TIER_RANK[computed] > TIER_RANK[tier]:
            findings.append(Finding("TIER_UNDERSTATED", "high", aid,
                                    f"Stored tier is {tier}; risk factors compute {computed} (score {risk_score(r)})",
                                    f"Raise the tier to {computed} and apply its controls, or record the rationale as a time bound exception"))

        c = r.get("behavioral_contract")
        if not c or not c.get("permitted_intents"):
            findings.append(Finding("NO_BEHAVIORAL_CONTRACT", "high" if tier == "high" else "medium", aid,
                                    "No declared intents or constraints, so runtime checks have nothing to hold the agent to",
                                    "Owner declares permitted intents and constraints; platform team reviews them"))
            continue

        scan = c["contract_scan"]
        last = _d(scan["last_run"])
        if scan["result"] == "drift":
            undeclared = "; ".join(scan.get("undeclared_capabilities", [])) or "capabilities not listed"
            severe = tier == "high" and r["autonomy_level"] == "act"
            findings.append(Finding("CONTRACT_DRIFT", "critical" if severe else "high", aid,
                                    f"Scan on {last} found capabilities the agent does not declare: {undeclared}",
                                    "Remove the capability or declare it and re-review the tier; until then block the tool at the gateway"))
        elif tier != "low":
            max_age = CONTRACT_SCAN_MAX_AGE_DAYS[tier]
            if scan["result"] == "not_run" or last is None or (as_of - last).days > max_age:
                age = "never run" if last is None or scan["result"] == "not_run" else f"{(as_of - last).days} days old"
                findings.append(Finding("CONTRACT_NOT_VERIFIED", "medium", aid,
                                        f"Contract scan {age}; limit for {tier} tier is {max_age} days",
                                        "Scan code, prompts, configuration and tool paths against the declared intents"))

        if tier != "low" and c["runtime_guardrail"] != "enforcing":
            findings.append(Finding("GUARDRAIL_NOT_ENFORCING", "high" if tier == "high" else "medium", aid,
                                    f"Runtime guardrail is {c['runtime_guardrail']} on a {tier} tier agent",
                                    "Replay recorded traffic against the guardrail, then move it from shadow to enforcing"))

        if c["tool_vetting"] != "vetted":
            writes = any(t["access"] == "write" for t in r["tools"])
            findings.append(Finding("TOOLS_NOT_VETTED", "high" if writes else "medium", aid,
                                    f"Tool vetting is {c['tool_vetting'].replace('_', ' ')}" + ("; the agent has write tools" if writes else ""),
                                    "Inspect tool and MCP server descriptions for poisoning and injection, and close open findings"))

        for callee in c.get("calls_agents", []):
            if callee not in {x["agent_id"] for x in records}:
                findings.append(Finding("UNKNOWN_DEPENDENCY", "high", aid, f"Delegates to {callee}, which is not in the registry",
                                        "Register the called agent or remove the delegation"))
    return findings


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def sort_findings(findings: list[Finding]) -> list[Finding]:
    return sorted(findings, key=lambda f: (SEVERITY_ORDER[f.severity], f.rule, f.subject))
