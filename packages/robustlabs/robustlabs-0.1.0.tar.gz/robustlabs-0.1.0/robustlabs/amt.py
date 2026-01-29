from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from .domain import (
    StrategySpec,
    Artifact,
    ArtifactType,
    Assumption,
    Severity,
    ReviewTrigger,
    AssumptionMap,
)


@dataclass(frozen=True)
class Thresholds:
    tail_amplification_high: float = 2.5
    timing_sensitivity_high: float = 0.5
    max_drawdown_high: float = -0.25


def _get_metric(artifacts: list[Artifact], name: str) -> float | None:
    for a in artifacts:
        if a.type == ArtifactType.METRIC and a.name == name:
            value = a.payload.get("value")
            if isinstance(value, (int, float)):
                return float(value)
    return None


def map_assumptions(
    *,
    strategy: StrategySpec,
    artifacts: list[Artifact],
    thresholds: Thresholds = Thresholds(),
) -> AssumptionMap:
    """
    Produces a machine-readable assumption map with explicit evidence + gaps.
    """
    tail_amp = _get_metric(artifacts, "tail_amplification")
    timing = _get_metric(artifacts, "timing_sensitivity")
    mdd = _get_metric(artifacts, "max_drawdown")

    evidence_ids = {a.name: a.artifact_id for a in artifacts}

    assumptions: list[Assumption] = []

    # A1: Tail behavior is manageable
    if tail_amp is None:
        assumptions.append(
            Assumption(
                assumption_id="A1",
                title="Tail losses are controllable (no nonlinear blow-ups).",
                description=(
                    "Strategy loss profile under stress does not exhibit severe tail "
                    "amplification beyond expected risk budget."
                ),
                severity=Severity.HIGH,
                confidence=0.2,
                gaps=["No tail amplification metric provided."],
                recommended_tests=[
                    "Run tail stress scenarios (vol up, corr up, gap risk).",
                    "Compute tail amplification factor across regimes.",
                ],
                owner="risk",
            )
        )
    else:
        sev = Severity.MEDIUM
        conf = 0.7
        gaps: list[str] = []
        rec: list[str] = []
        if tail_amp >= thresholds.tail_amplification_high:
            sev = Severity.CRITICAL
            conf = 0.8
            gaps.append("Tail amplification is high; confirm with multiple stress models.")
            rec.extend(
                [
                    "Add stop/hedge policy and re-evaluate tail profile.",
                    "Test crisis regimes and correlation spikes.",
                ]
            )
        assumptions.append(
            Assumption(
                assumption_id="A1",
                title="Tail losses are controllable (no nonlinear blow-ups).",
                description=(
                    "Tail amplification summarizes whether losses accelerate in the "
                    "worst outcomes relative to baseline risk."
                ),
                severity=sev,
                confidence=conf,
                evidence=[evidence_ids.get("tail_amplification", "")],
                gaps=[g for g in gaps if g],
                recommended_tests=rec or ["Validate tail amplification using real historical crisis windows."],
                owner="risk",
            )
        )

    # A2: Timing luck is not the primary driver
    if timing is None:
        assumptions.append(
            Assumption(
                assumption_id="A2",
                title="Returns are not dominated by timing luck.",
                description=(
                    "Small shifts in entry/rebalance timing should not flip the "
                    "strategy from profitable to unprofitable."
                ),
                severity=Severity.MEDIUM,
                confidence=0.2,
                gaps=["No timing sensitivity metric provided."],
                recommended_tests=[
                    "Shift entries by +/- N days (or minutes) and re-evaluate.",
                    "Test rebalance offsets and execution delays.",
                ],
                owner="research",
            )
        )
    else:
        sev = Severity.LOW if timing < thresholds.timing_sensitivity_high else Severity.HIGH
        conf = 0.75
        rec = (
            ["Add timing-robust execution rules; widen signal confirmation windows."]
            if sev in {Severity.HIGH, Severity.CRITICAL}
            else ["Continue monitoring timing sensitivity as market microstructure changes."]
        )
        assumptions.append(
            Assumption(
                assumption_id="A2",
                title="Returns are not dominated by timing luck.",
                description="Timing sensitivity indicates fragility to small schedule perturbations.",
                severity=sev,
                confidence=conf,
                evidence=[evidence_ids.get("timing_sensitivity", "")],
                gaps=[],
                recommended_tests=rec,
                owner="research",
            )
        )

    # A3: Drawdowns remain within governance tolerance
    if mdd is None:
        assumptions.append(
            Assumption(
                assumption_id="A3",
                title="Drawdowns are within governance tolerance.",
                description="Maximum drawdown should remain compatible with allocation mandates.",
                severity=Severity.MEDIUM,
                confidence=0.2,
                gaps=["No max drawdown metric provided."],
                recommended_tests=["Compute max drawdown across regimes and rolling windows."],
                owner="risk",
            )
        )
    else:
        sev = Severity.MEDIUM if mdd > thresholds.max_drawdown_high else Severity.HIGH
        conf = 0.7
        assumptions.append(
            Assumption(
                assumption_id="A3",
                title="Drawdowns are within governance tolerance.",
                description="Maximum drawdown indicates peak-to-trough loss; compare to risk budget.",
                severity=sev,
                confidence=conf,
                evidence=[evidence_ids.get("max_drawdown", "")],
                gaps=[],
                recommended_tests=["Evaluate drawdowns by macro regime (inflation, rates, vol)."],
                owner="risk",
            )
        )

    # Triggers (MVP)
    triggers: list[ReviewTrigger] = []
    if tail_amp is not None and tail_amp >= thresholds.tail_amplification_high:
        triggers.append(
            ReviewTrigger(
                trigger_id="T1",
                title="Tail amplification breach",
                severity=Severity.CRITICAL,
                condition=f"tail_amplification >= {thresholds.tail_amplification_high}",
                rationale="Tail losses appear nonlinear; allocation should require committee review.",
            )
        )
    if timing is not None and timing >= thresholds.timing_sensitivity_high:
        triggers.append(
            ReviewTrigger(
                trigger_id="T2",
                title="Timing fragility breach",
                severity=Severity.HIGH,
                condition=f"timing_sensitivity >= {thresholds.timing_sensitivity_high}",
                rationale="Results may be driven by timing luck; require robustness improvements.",
            )
        )

    return AssumptionMap(
        map_id=str(uuid4()),
        strategy_id=strategy.strategy_id,
        created_at=datetime.now(timezone.utc),
        assumptions=assumptions,
        triggers=triggers,
    )
