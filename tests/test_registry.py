import copy
from datetime import date
from pathlib import Path

import pytest

from agent_registry.core import ROOT, lifecycle, load_registry, load_schema, reconcile, validate_records
from agent_registry.report import agent_kpis, opa_data, render_report
from agent_registry.cli import main

AS_OF = date(2026, 11, 10)
DATA = ROOT / "data"


@pytest.fixture(scope="module")
def records():
    return load_registry()


def rules(findings, subject=None):
    return {f.rule for f in findings if subject is None or f.subject == subject}


def test_sample_registry_is_schema_valid(records):
    assert [f for f in validate_records(records, load_schema()) if f.rule == "SCHEMA_INVALID"] == []


def test_schema_rejects_missing_owner(records):
    bad = copy.deepcopy(records[0])
    del bad["technical_owner"]
    assert "SCHEMA_INVALID" in rules(validate_records([bad], load_schema()))


def test_schema_requires_vendor_for_vendor_agents(records):
    bad = copy.deepcopy(next(r for r in records if r["platform"] == "agentforce"))
    del bad["vendor"]
    assert "SCHEMA_INVALID" in rules(validate_records([bad], load_schema()))


def test_schema_requires_forum_for_high_tier(records):
    bad = copy.deepcopy(next(r for r in records if r["risk_tier"] == "high"))
    del bad["review"]["governance_forum"]
    assert "SCHEMA_INVALID" in rules(validate_records([bad], load_schema()))


def test_single_owner_flagged(records):
    r = copy.deepcopy(records[0])
    r["technical_owner"] = dict(r["business_owner"])
    assert "SINGLE_OWNER" in rules(validate_records([r], load_schema()))


def test_reconcile_finds_unregistered_agents_on_every_platform(records):
    f = reconcile(records, DATA, AS_OF)
    subjects = " ".join(x.subject for x in f if x.rule == "UNREGISTERED_AGENT")
    assert "underwriting-notes-summarizer" in subjects  # AgentCore auto detection
    assert "Team Expense Helper" in subjects  # Microsoft agent inventory


def test_reconcile_catches_enforcement_gap(records):
    f = reconcile(records, DATA, AS_OF)
    assert "ENFORCEMENT_GAP" in rules(f, "agt-sourcing-analyst")


def test_reconcile_flags_dormant_and_unattributed_spend(records):
    f = reconcile(records, DATA, AS_OF)
    assert "DORMANT" in rules(f, "agt-legacy-faq")
    assert any(x.rule == "UNATTRIBUTED_SPEND" and "marketing-genai" in x.subject for x in f)


def test_lifecycle_orphan_overdue_for_high_tier(records):
    f = lifecycle(records, DATA, AS_OF)
    hit = [x for x in f if x.subject == "agt-claims-intake" and x.rule == "ORPHANED_OVERDUE"]
    assert hit and hit[0].severity == "critical"


def test_orphan_within_window_is_not_overdue(records):
    f = lifecycle(records, DATA, date(2026, 11, 4))
    assert "ORPHANED" in rules(f, "agt-claims-intake")
    assert "ORPHANED_OVERDUE" not in rules(f, "agt-claims-intake")


def test_lifecycle_eval_review_exception_and_identity(records):
    f = lifecycle(records, DATA, AS_OF)
    assert "EVAL_STALE" in rules(f, "agt-claims-intake")
    assert "REVIEW_OVERDUE" in rules(f, "agt-wholesaler-recap")
    assert {"EXCEPTION_EXPIRED", "PERSONAL_CREDENTIALS"} <= rules(f, "agt-hr-policy-qa")


def test_clean_agents_stay_clean(records):
    f = validate_records(records, load_schema()) + reconcile(records, DATA, AS_OF) + lifecycle(records, DATA, AS_OF)
    assert rules(f, "agt-advisor-assist") == set()
    assert rules(f, "agt-policy-servicing") == set()


def test_kpis_join_on_agent_id_and_cost_tag(records):
    k = agent_kpis(DATA / "otel_spans.jsonl", DATA / "cloud_cost_by_tag.csv", records)
    assert k["agt-advisor-assist"]["invocations"] == 1800
    assert k["agt-advisor-assist"]["cost_usd"] == pytest.approx(18420.55)
    assert k["agt-policy-servicing"]["cost_usd"] is None  # vendor billed, no cloud tag


def test_opa_export_shape(records):
    d = opa_data(records)
    assert d["agents"]["agt-claims-intake"]["eval_max_age_days"] == 30


def test_report_renders_and_cli_gates_on_critical(tmp_path, records):
    text = render_report(records, [], {}, AS_OF)
    assert "# AI Agent Governance Report" in text
    assert main(["lifecycle", "--as-of", AS_OF.isoformat()]) == 1  # critical orphan present
    assert main(["validate", "--as-of", AS_OF.isoformat()]) == 0
