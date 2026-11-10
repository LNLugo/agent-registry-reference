"""Command line entry point.

    agent-registry validate          schema and ownership checks on registry/agents/*.json
    agent-registry reconcile         discovered agents, gateway traffic and spend vs the registry
    agent-registry lifecycle         owners who left, stale evals, overdue reviews, expired exceptions
    agent-registry export-opa        write policy/data.json for the gateway policy
    agent-registry report            all checks plus KPIs, written to reports/governance-report-<date>.md

Use --as-of YYYY-MM-DD to make runs reproducible. Exit code is 1 when any
critical finding exists, so the command can gate a pipeline.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from .core import ROOT, lifecycle, load_registry, load_schema, reconcile, sort_findings, validate_records
from .report import agent_kpis, opa_data, render_report


def _print(findings) -> None:
    if not findings:
        print("No findings.")
    for f in findings:
        print(f"[{f.severity.upper():8}] {f.rule:22} {f.subject}\n           {f.detail}\n           -> {f.action}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="agent-registry")
    ap.add_argument("command", choices=["validate", "reconcile", "lifecycle", "export-opa", "report"])
    ap.add_argument("--as-of", default=date.today().isoformat())
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--json", action="store_true", help="print findings as JSON")
    args = ap.parse_args(argv)

    root = Path(args.root)
    as_of = date.fromisoformat(args.as_of)
    data = root / "data"
    records = load_registry(root)

    if args.command == "export-opa":
        out = root / "policy" / "data.json"
        out.write_text(json.dumps(opa_data(records), indent=2) + "\n")
        print(f"wrote {out.relative_to(root)}")
        return 0

    findings = []
    if args.command in ("validate", "report"):
        findings += validate_records(records, load_schema(root))
    if args.command in ("reconcile", "report"):
        findings += reconcile(records, data, as_of)
    if args.command in ("lifecycle", "report"):
        findings += lifecycle(records, data, as_of)
    findings = sort_findings(findings)

    if args.command == "report":
        kpis = agent_kpis(data / "otel_spans.jsonl", data / "cloud_cost_by_tag.csv", records)
        out = root / "reports" / f"governance-report-{as_of.isoformat()}.md"
        out.parent.mkdir(exist_ok=True)
        out.write_text(render_report(records, findings, kpis, as_of))
        print(f"wrote {out.relative_to(root)} with {len(findings)} findings")
    elif args.json:
        print(json.dumps([f.to_dict() for f in findings], indent=2))
    else:
        _print(findings)

    return 1 if any(f.severity == "critical" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
