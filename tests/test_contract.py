"""Computed risk tier and behavioral contract checks (v0.2.0)."""
import copy
from datetime import date

import pytest

from agent_registry.cli import main
from agent_registry.core import (
    ROOT, computed_tier, contract_checks, lifecycle, load_registry, load_schema, reconcile, risk_score,
    sort_findings, validate_records,
)
from agent_registry.report import catalog_data, opa_data

AS_OF = date(2026, 11, 10)


@pytest.fixture(scope="module")
def records():
    return load_registry()


def by_id(records, aid):
    return copy.deepcopy(next(r for r in records if r["agent_id"] == aid))


def rules(findings, subject=None):
    return {f.rule for f in findings if subject is None or f.subject == subject}


# ---------- computed tier ----------

def test_score_is_sum_of_four_factors(records):
    r = by_id(records, "agt-wholesaler-recap")  # assist 1, write_internal 2, confidential 3, internal_only 1
    assert risk_score(r) == 7
    assert computed_tier(r) == "medium"


def test_financial_binding_is_high_whatever_the_score(records):
    r = by_id(records, "agt-hr-policy-qa")
    r["risk_factors"]["action_scope"] = "financial_binding"
    assert risk_score(r) < 11
    assert computed_tier(r) == "high"


def test_decides_on_customers_is_high(records):
    r = by_id(records, "agt-hr-policy-qa")
    r["risk_factors"]["customer_impact"] = "decides_on_customers"
    assert computed_tier(r) == "high"


def test_understated_tier_is_flagged_overstated_is_not(records):
    r = by_id(records, "agt-hr-policy-qa")
    r["risk_factors"]["customer_impact"] = "decides_on_customers"
    assert "TIER_UNDERSTATED" in rules(contract_checks([r], AS_OF))
    # advisor-assist computes medium but is stored high: stricter than needed is allowed
    assert computed_tier(by_id(records, "agt-advisor-assist")) == "medium"
    assert "TIER_UNDERSTATED" not in rules(contract_checks(records, AS_OF), "agt-advisor-assist")


def test_schema_requires_risk_factors_for_approved_agents(records):
    r = by_id(records, "agt-advisor-assist")
    del r["risk_factors"]
    assert "SCHEMA_INVALID" in rules(validate_records([r], load_schema()))


def test_schema_rejects_unknown_guardrail_mode(records):
    r = by_id(records, "agt-advisor-assist")
    r["behavioral_contract"]["runtime_guardrail"] = "sometimes"
    assert "SCHEMA_INVALID" in rules(validate_records([r], load_schema()))


# ---------- behavioral contract ----------

def test_authorized_agent_can_still_drift(records):
    """Policy servicing passes every v0.1 check and still does more than it declares."""
    v1 = validate_records(records, load_schema()) + reconcile(records, ROOT / "data", AS_OF) + lifecycle(records, ROOT / "data", AS_OF)
    assert rules(v1, "agt-policy-servicing") == set()
    f = [x for x in contract_checks(records, AS_OF) if x.subject == "agt-policy-servicing"]
    assert [(x.rule, x.severity) for x in f] == [("CONTRACT_DRIFT", "critical")]
    assert "surrender" in f[0].detail


def test_drift_is_high_not_critical_without_autonomy(records):
    r = by_id(records, "agt-policy-servicing")
    r["autonomy_level"] = "act_with_approval"
    assert [(x.rule, x.severity) for x in contract_checks([r], AS_OF)] == [("CONTRACT_DRIFT", "high")]


def test_shadow_guardrail_on_high_tier(records):
    assert "GUARDRAIL_NOT_ENFORCING" in rules(contract_checks(records, AS_OF), "agt-claims-intake")


def test_scan_age_follows_tier(records):
    f = contract_checks(records, AS_OF)
    assert "CONTRACT_NOT_VERIFIED" in rules(f, "agt-claims-intake")   # 56 days, high limit 30
    assert "CONTRACT_NOT_VERIFIED" not in rules(f, "agt-hr-policy-qa")  # low tier is exempt


def test_unvetted_tools_with_write_access_are_high(records):
    f = [x for x in contract_checks(records, AS_OF) if x.rule == "TOOLS_NOT_VETTED"]
    assert [(x.subject, x.severity) for x in f] == [("agt-wholesaler-recap", "high")]


def test_missing_contract_and_unknown_dependency(records):
    f = contract_checks(records, AS_OF)
    assert "NO_BEHAVIORAL_CONTRACT" in rules(f, "agt-legacy-faq")
    r = by_id(records, "agt-advisor-assist")
    r["behavioral_contract"]["calls_agents"] = ["agt-not-registered"]
    assert "UNKNOWN_DEPENDENCY" in rules(contract_checks([r], AS_OF))


def test_suspended_and_clean_agents(records):
    f = contract_checks(records, AS_OF)
    assert rules(f, "agt-sourcing-analyst") == set()  # suspended: not checked
    assert rules(f, "agt-advisor-assist") == set()


# ---------- exports ----------

def test_opa_export_carries_guardrail(records):
    d = opa_data(records)["agents"]
    assert d["agt-claims-intake"]["runtime_guardrail"] == "shadow"
    assert d["agt-legacy-faq"]["runtime_guardrail"] == "none"


def test_catalog_export(records):
    findings = sort_findings(reconcile(records, ROOT / "data", AS_OF) + contract_checks(records, AS_OF))
    c = catalog_data(records, findings, AS_OF)
    ps = next(a for a in c["agents"] if a["agent_id"] == "agt-policy-servicing")
    assert ps["computed_tier"] == "high" and ps["build_path"] == "Vendor embedded"
    assert {f["rule"] for f in ps["findings"]} == {"CONTRACT_DRIFT"}
    assert len(c["discovered"]) == 2  # AgentCore runtime and Copilot Studio agent with no record


def test_contract_command_gates_on_critical():
    assert main(["contract", "--as-of", AS_OF.isoformat()]) == 1
