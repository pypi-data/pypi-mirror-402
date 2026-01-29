from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


# ----------------------------
# Domain models
# ----------------------------


class ArtifactType(str, Enum):
    METRIC = "metric"
    TABLE = "table"
    TEXT = "text"
    TRIGGER = "trigger"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StrategySpec(BaseModel):
    strategy_id: str = Field(..., description="Stable identifier (e.g., slug or UUID).")
    name: str
    description: str | None = None
    asset_class: Literal["equities", "futures", "fx", "rates", "credit", "multi_asset"]
    horizon: Literal["intraday", "daily", "weekly", "monthly"]
    universe: str = Field(..., description="Human-readable universe definition.")
    constraints: list[str] = Field(default_factory=list)


class RunSpec(BaseModel):
    strategy: StrategySpec
    as_of: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data_window: str = Field(..., description="e.g., '2010-01-01..2025-12-31'")
    notes: str | None = None


class Artifact(BaseModel):
    artifact_id: str
    type: ArtifactType
    name: str
    payload: dict[str, Any]


class Assumption(BaseModel):
    assumption_id: str
    title: str
    description: str
    severity: Severity
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: list[str] = Field(
        default_factory=list, description="Artifact IDs supporting this assessment."
    )
    gaps: list[str] = Field(
        default_factory=list, description="Explicit unknowns / missing validations."
    )
    recommended_tests: list[str] = Field(default_factory=list)
    owner: Literal["research", "risk", "trading", "ops", "compliance"] = "risk"


class ReviewTrigger(BaseModel):
    trigger_id: str
    title: str
    severity: Severity
    condition: str = Field(..., description="Human-readable condition.")
    rationale: str


class AssumptionMap(BaseModel):
    map_id: str
    strategy_id: str
    created_at: datetime
    assumptions: list[Assumption]
    triggers: list[ReviewTrigger] = Field(default_factory=list)


class Report(BaseModel):
    report_id: str
    run_id: str
    created_at: datetime
    markdown: str
    data: dict[str, Any]


class EvalInput(BaseModel):
    run: RunSpec
    artifacts: list[Artifact] = Field(default_factory=list)


class EvalOutput(BaseModel):
    run_id: str
    artifacts: list[Artifact]


def mk_metric(name: str, value: float) -> Artifact:
    """Helper to create a metric artifact."""
    return Artifact(
        artifact_id=str(uuid4()),
        type=ArtifactType.METRIC,
        name=name,
        payload={"value": value},
    )
