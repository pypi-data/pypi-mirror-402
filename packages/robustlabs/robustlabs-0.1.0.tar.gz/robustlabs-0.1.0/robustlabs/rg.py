from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from .domain import (
    RunSpec,
    Artifact,
    ArtifactType,
    AssumptionMap,
    Report,
)


def _get_metric(artifacts: list[Artifact], name: str) -> float | None:
    for a in artifacts:
        if a.type == ArtifactType.METRIC and a.name == name:
            value = a.payload.get("value")
            if isinstance(value, (int, float)):
                return float(value)
    return None


def generate_report_markdown(
    *,
    run_id: str,
    run: RunSpec,
    artifacts: list[Artifact],
    assumption_map: AssumptionMap,
) -> str:
    def fmt_metric(metric_name: str) -> str:
        val = _get_metric(artifacts, metric_name)
        return "N/A" if val is None else f"{val:.4g}"

    lines: list[str] = []
    lines.append(f"# Decision Robustness Report — {run.strategy.name}")
    lines.append("")
    lines.append(f"- **Run ID:** `{run_id}`")
    lines.append(f"- **As of:** {run.as_of.isoformat()}")
    lines.append(f"- **Data window:** {run.data_window}")
    if run.notes:
        lines.append(f"- **Notes:** {run.notes}")
    lines.append("")
    lines.append("## Key metrics")
    lines.append("")
    lines.append(f"- CAGR: **{fmt_metric('cagr')}**")
    lines.append(f"- Max drawdown: **{fmt_metric('max_drawdown')}**")
    lines.append(f"- Tail amplification: **{fmt_metric('tail_amplification')}**")
    lines.append(f"- Timing sensitivity: **{fmt_metric('timing_sensitivity')}**")
    lines.append("")
    
    # Check for tables
    for a in artifacts:
        if a.type == ArtifactType.TABLE:
            lines.append(f"### {a.name.replace('_', ' ').title()}")
            # Simple table render
            rows = a.payload.get("rows", [])
            if rows:
                headers = list(rows[0].keys())
                lines.append("| " + " | ".join(headers) + " |")
                lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
                for r in rows:
                    lines.append("| " + " | ".join(str(r.get(h, "")) for h in headers) + " |")
            lines.append("")

    lines.append("## Assumption map")
    lines.append("")
    for a in assumption_map.assumptions:
        lines.append(f"### {a.assumption_id}: {a.title}")
        lines.append(f"- Severity: **{a.severity.value.upper()}**")
        lines.append(f"- Confidence: **{a.confidence:.2f}**")
        lines.append(f"- Description: {a.description}")
        if a.evidence:
            ev = [e for e in a.evidence if e]
            if ev:
                lines.append(f"- Evidence artifacts: {', '.join(f'`{x}`' for x in ev)}")
        if a.gaps:
            lines.append("- Gaps / unknowns:")
            for g in a.gaps:
                lines.append(f"  - {g}")
        if a.recommended_tests:
            lines.append("- Recommended tests:")
            for t in a.recommended_tests:
                lines.append(f"  - {t}")
        lines.append("")

    lines.append("## Review triggers")
    lines.append("")
    if not assumption_map.triggers:
        lines.append("- None triggered in this run.")
    else:
        for t in assumption_map.triggers:
            lines.append(f"- **{t.severity.value.upper()}** — {t.title}: `{t.condition}`")
            lines.append(f"  - Rationale: {t.rationale}")

    lines.append("")
    lines.append("## Disclaimer")
    lines.append(
        "This report is **forecast-agnostic**: it evaluates robustness under provided data/scenarios "
        "and does not claim predictive accuracy."
    )
    lines.append("")
    return "\n".join(lines)


def generate_report(
    *,
    run_id: str,
    run: RunSpec,
    artifacts: list[Artifact],
    assumption_map: AssumptionMap,
) -> Report:
    md = generate_report_markdown(
        run_id=run_id, run=run, artifacts=artifacts, assumption_map=assumption_map
    )
    data = {
        "run_id": run_id,
        "strategy": run.strategy.model_dump(),
        "as_of": run.as_of.isoformat(),
        "data_window": run.data_window,
        "artifacts": [a.model_dump() for a in artifacts],
        "assumption_map": assumption_map.model_dump(),
    }
    return Report(
        report_id=str(uuid4()),
        run_id=run_id,
        created_at=datetime.now(timezone.utc),
        markdown=md,
        data=data,
    )
