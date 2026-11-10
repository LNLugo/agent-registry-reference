# ADR 0004: Cloud tags carry ownership and cost; the registry carries risk

Status: accepted

## Context
A mandatory tag taxonomy (`Application`, `ApplicationOwner`, `ClientEngagement`, `Environment`, `CostCenter`, `Model`, `Project`) already makes every workload attributable to an owner and a cost center and supports cost analysis by model. It is tempting to extend tags to hold governance data.

## Decision
Keep tags for attribution and keep governance fields in the registry. Each record stores its tag mapping in `cost_tags` so spend joins to the agent, but risk tier, autonomy level, data classification, evaluation status, review dates and exceptions are registry fields only.

## Why
* Anyone with resource permissions can change a tag, and nothing validates it. A registry change goes through approval and is versioned.
* Tags exist per cloud resource; one agent can span several resources and several clouds.
* Vendor and SaaS agents have no cloud tags at all.

## Consequences
Tag drift (spend under an `Application` tag no agent claims) is reported as `UNATTRIBUTED_SPEND`.
