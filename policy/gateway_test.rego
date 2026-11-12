package gateway_test

import rego.v1

import data.gateway

agents := {
	"agt-ok": {
		"status": "approved", "risk_tier": "high", "environment": "production",
		"eval_result": "pass", "eval_last_run": "2026-11-01", "eval_max_age_days": 30,
		"data_classification": "confidential", "runtime_guardrail": "enforcing",
		"allowed_routes": ["llm-default"],
	},
	"agt-shadow-guardrail": {
		"status": "approved", "risk_tier": "high", "environment": "production",
		"eval_result": "pass", "eval_last_run": "2026-11-01", "eval_max_age_days": 30,
		"data_classification": "restricted", "runtime_guardrail": "shadow",
		"allowed_routes": ["llm-default"],
	},
	"agt-medium-no-guardrail": {
		"status": "approved", "risk_tier": "medium", "environment": "production",
		"eval_result": "pass", "eval_last_run": "2026-11-01", "eval_max_age_days": 90,
		"data_classification": "confidential", "runtime_guardrail": "none",
		"allowed_routes": ["llm-default"],
	},
	"agt-stale": {
		"status": "approved", "risk_tier": "high", "environment": "production",
		"eval_result": "pass", "eval_last_run": "2026-08-30", "eval_max_age_days": 30,
		"data_classification": "restricted", "runtime_guardrail": "enforcing",
		"allowed_routes": ["llm-default"],
	},
	"agt-low-old-eval": {
		"status": "approved", "risk_tier": "low", "environment": "production",
		"eval_result": "pass", "eval_last_run": "2026-08-30", "eval_max_age_days": 180,
		"data_classification": "internal", "allowed_routes": ["llm-default"],
	},
	"agt-suspended": {
		"status": "suspended", "risk_tier": "medium", "environment": "production",
		"eval_result": "fail", "eval_last_run": "2026-09-01", "eval_max_age_days": 90,
		"data_classification": "confidential", "allowed_routes": ["llm-default"],
	},
}

req(id, route) := {"request": {
	"headers": {"x-agent-id": id},
	"route": route,
	"environment": "production",
	"date": "2026-11-10",
}}

test_approved_agent_allowed if {
	gateway.allow with input as req("agt-ok", "llm-default") with data.agents as agents
}

test_missing_header_denied if {
	not gateway.allow with input as {"request": {"headers": {}, "route": "llm-default", "environment": "production", "date": "2026-11-10"}}
		with data.agents as agents
	"missing x-agent-id header" in gateway.reasons with input as {"request": {"headers": {}, "route": "llm-default", "environment": "production", "date": "2026-11-10"}}
		with data.agents as agents
}

test_unknown_agent_denied if {
	not gateway.allow with input as req("agt-nobody", "llm-default") with data.agents as agents
}

test_suspended_agent_denied if {
	not gateway.allow with input as req("agt-suspended", "llm-default") with data.agents as agents
}

test_unlisted_route_denied if {
	not gateway.allow with input as req("agt-ok", "llm-legacy") with data.agents as agents
}

test_high_tier_stale_eval_denied if {
	not gateway.allow with input as req("agt-stale", "llm-default") with data.agents as agents
}

test_low_tier_old_eval_still_allowed if {
	gateway.allow with input as req("agt-low-old-eval", "llm-default") with data.agents as agents
}

test_wrong_environment_denied if {
	not gateway.allow with input as {"request": {"headers": {"x-agent-id": "agt-ok"}, "route": "llm-default", "environment": "development", "date": "2026-11-10"}}
		with data.agents as agents
}

test_high_tier_needs_enforcing_guardrail if {
	not gateway.allow with input as req("agt-shadow-guardrail", "llm-default") with data.agents as agents
	r := gateway.reasons with input as req("agt-shadow-guardrail", "llm-default") with data.agents as agents
	r == {"high tier agent needs an enforcing runtime guardrail, registry says shadow"}
}

test_guardrail_rule_is_high_tier_only if {
	gateway.allow with input as req("agt-medium-no-guardrail", "llm-default") with data.agents as agents
}

test_missing_guardrail_field_fails_closed_for_high_tier if {
	legacy := object.remove(agents["agt-ok"], ["runtime_guardrail"])
	not gateway.allow with input as req("agt-legacy", "llm-default") with data.agents as {"agt-legacy": legacy}
}
