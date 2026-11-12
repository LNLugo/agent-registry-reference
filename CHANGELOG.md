# Changelog

## v0.2.0 (2026-11-12)

Behavioral contract, computed risk tier and the Agent Catalog. See [ADR 0005](docs/adr/0005-behavioral-contract.md).

### Added
- `behavioral_contract` record block: persona, permitted intents, constraints, delegated agents, contract scan result, runtime guardrail mode, tool vetting and last red team
- `risk_factors` record block (`action_scope`, `customer_impact`), required for approved agents
- Computed risk tier: four factors, score 4 to 15, two high tier triggers
- Contract checks: `TIER_UNDERSTATED`, `NO_BEHAVIORAL_CONTRACT`, `CONTRACT_DRIFT`, `CONTRACT_NOT_VERIFIED`, `GUARDRAIL_NOT_ENFORCING`, `TOOLS_NOT_VETTED`, `UNKNOWN_DEPENDENCY`
- `agent-registry contract` and `agent-registry export-catalog` commands
- Gateway policy denies high tier agents without an enforcing runtime guardrail; a record without the field fails closed
- Report: behavioral contract section, contract coverage and hairball quotient in the headline
- Agent Catalog page (`docs/catalog/`): find, use or copy an agent, with open findings on every card
- Design guide (`docs/design-guide.md`) and ADR 0005
- Control mapping rows for the new checks
- `tests/test_contract.py` (16 tests) and three policy tests

### Changed
- Sample registry records carry risk factors and, except `agt-legacy-faq`, a behavioral contract
- `agt-policy-servicing` is no longer clean: its contract scan shows undeclared capabilities
- CI checks that the catalog export is reproducible

## v0.1.0

- Registry schema, gateway policy, reconciliation, lifecycle checks and governance report
