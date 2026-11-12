# Control mapping

How the registry checks support common model risk and AI management frameworks. This is a working map for discussion with risk and compliance partners, not a compliance attestation.

| Registry capability | Checks in this repo | SR 11-7 (model risk management) | NIST AI RMF 1.0 | ISO/IEC 42001 |
|---|---|---|---|---|
| Complete inventory across platforms | `UNREGISTERED_AGENT`, `UNREGISTERED_CALLER`, `UNATTRIBUTED_SPEND` | Firm wide model inventory | GOVERN 1.6 (inventory of AI systems) | AI system inventory within the AI management system |
| Named accountability for each agent | `ORPHANED`, `ORPHANED_OVERDUE`, `SINGLE_OWNER` | Roles and responsibilities, model owners | GOVERN 2 (accountability structures) | Roles, responsibilities and authorities |
| Risk tiering drives control intensity | tier based eval age, reassignment windows, forum review for high tier | Rigor proportional to model risk | MAP 1 to 5 (context and impact) | AI risk assessment and treatment |
| Pre deployment and ongoing validation | `EVAL_STALE`, `EVAL_FAILING`, gateway eval check | Validation and ongoing monitoring | MEASURE 2 (evaluation), MANAGE 4 (post deployment monitoring) | Performance evaluation and monitoring |
| Runtime monitoring of behavior and cost | per agent KPIs joined on `gen_ai.agent.id` | Ongoing monitoring and outcomes analysis | MEASURE 3, MANAGE 4 | Monitoring, measurement, analysis |
| Enforcement, not only policy | gateway policy, `ENFORCEMENT_GAP` | Effective challenge and controls | MANAGE 1 and 2 | Operational planning and control |
| Time bound exceptions | `EXCEPTION_EXPIRED` | Documented exceptions and limitations | GOVERN 1 (policies and processes) | Nonconformity and corrective action |
| Identity hygiene | `PERSONAL_CREDENTIALS` | Controls over model use | MANAGE 2 | Information security controls |
| Retirement | `DORMANT`, `retired` status | Model decommissioning in inventory | MANAGE 4 | AI system life cycle |
| Third party agents | vendor inventory reconciliation | Vendor and third party models are in scope | GOVERN 6 (third party risk) | Supplier relationships |
| Risk tier derived from documented factors | `TIER_UNDERSTATED` | Risk rating based on use and impact | MAP 1.1, MAP 5.1 (context, likelihood and impact) | AI risk assessment (6.1.2), impact assessment (A.5) |
| Intended use declared and checked | `NO_BEHAVIORAL_CONTRACT`, `CONTRACT_DRIFT`, `CONTRACT_NOT_VERIFIED` | Model use within documented purpose and limitations | MAP 1.1 (intended purpose), MEASURE 2.7 (security and resilience) | Intended use (A.9.4), verification and validation (A.6.2.4) |
| Runtime behavioral enforcement | `GUARDRAIL_NOT_ENFORCING`, gateway guardrail rule | Controls over model use and ongoing monitoring | MANAGE 2.2, MANAGE 2.4 (disengage or deactivate) | Operation and monitoring (A.6.2.6) |
| Tool and MCP supply chain | `TOOLS_NOT_VETTED`, `UNKNOWN_DEPENDENCY` | Vendor and third party components in scope | GOVERN 6.1, MAP 4.1 (third party components) | Suppliers (A.10.3), resource documentation (A.4.2) |

For insurers, state insurance guidance on AI use (for example NYDFS Insurance Circular Letter No. 7 of 2024) expects a governance and risk management framework and oversight of third party AI systems; the inventory, ownership, vendor and reporting checks above are the operational evidence for that framework.
