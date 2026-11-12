# Gateway admission policy: no registry ID, no route.
#
# The AI gateway (Kong AI Gateway, AgentCore Gateway or any proxy that can call
# OPA) sends each model or tool request as input. The registry publishes
# data.agents via `agent-registry export-opa`. The gateway allows the call only
# when `allow` is true and logs `reasons` when it is not.
#
# Input shape:
#   {"request": {"headers": {"x-agent-id": "agt-..."}, "route": "llm-default",
#                "environment": "production", "date": "2026-11-10"}}

package gateway

import rego.v1

default allow := false

agent_id := input.request.headers["x-agent-id"]

agent := data.agents[agent_id]

allow if count(reasons) == 0

reasons contains "missing x-agent-id header" if not agent_id

reasons contains sprintf("agent %s is not in the registry", [agent_id]) if {
	agent_id
	not data.agents[agent_id]
}

reasons contains sprintf("agent status is %s, only approved agents may call", [agent.status]) if {
	agent.status != "approved"
}

reasons contains sprintf("agent is registered for %s, request is from %s", [agent.environment, input.request.environment]) if {
	agent.environment != input.request.environment
}

reasons contains sprintf("route %s is not allowed for this agent", [input.request.route]) if {
	agent
	not input.request.route in agent.allowed_routes
}

reasons contains "latest evaluation did not pass" if {
	agent.eval_result != "pass"
}

reasons contains sprintf("evaluation is %d days old, limit for %s tier is %d", [age, agent.risk_tier, agent.eval_max_age_days]) if {
	agent.eval_result == "pass"
	agent.risk_tier == "high"
	age := eval_age_days
	age > agent.eval_max_age_days
}

reasons contains sprintf("high tier agent needs an enforcing runtime guardrail, registry says %s", [guardrail]) if {
	agent.risk_tier == "high"
	guardrail != "enforcing"
}

# A record without the field fails closed for high tier agents.
guardrail := object.get(agent, "runtime_guardrail", "none")

eval_age_days := floor((day_ns(input.request.date) - day_ns(agent.eval_last_run)) / (((24 * 60) * 60) * 1000000000))

day_ns(d) := time.parse_rfc3339_ns(concat("", [d, "T00:00:00Z"]))
