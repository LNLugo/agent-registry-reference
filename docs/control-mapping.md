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

For insurers, state insurance guidance on AI use (for example NYDFS Insurance Circular Letter No. 7 of 2024) expects a governance and risk management framework and oversight of third party AI systems; the inventory, ownership, vendor and reporting checks above are the operational evidence for that framework.
