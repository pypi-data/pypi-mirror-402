from __future__ import annotations
from typing import Protocol, runtime_checkable
import random
from uuid import uuid4

from .domain import RunSpec, Artifact, ArtifactType, mk_metric


@runtime_checkable
class EvidencePlugin(Protocol):
    @property
    def name(self) -> str:
        ...

    def run(self, run_spec: RunSpec) -> list[Artifact]:
        ...


class RegimeSlicingPlugin:
    """
    Simulates performance across key market regimes (Bull, Bear, Crisis).
    Generates 'tail_amplification' metric and 'regime_table' artifact.
    """
    @property
    def name(self) -> str:
        return "regime_slicing"

    def run(self, run_spec: RunSpec) -> list[Artifact]:
        # Simulation: In a real system, this would query a backtest engine.
        # Here we simulate valid returns.
        
        # Calculate a synthetic 'tail_amplification'
        # Randomly choose if this is a risky strategy or not for demo purposes
        # (seeded by strategy name to be consistent-ish)
        seed = sum(ord(c) for c in run_spec.strategy.name)
        rng = random.Random(seed)
        
        tail_amp = 1.5 + rng.random() * 2.0  # Range 1.5 to 3.5
        
        regime_data = [
            {"regime": "Bull Market", "cagr": 0.15, "sharpe": 1.2},
            {"regime": "Bear Market", "cagr": -0.05, "sharpe": -0.3},
            {"regime": "Crisis (VIX>30)", "cagr": -0.25, "sharpe": -1.5},
        ]
        
        artifacts = [
            mk_metric("tail_amplification", tail_amp),
            Artifact(
                artifact_id=str(uuid4()),
                type=ArtifactType.TABLE,
                name="regime_performance",
                payload={"rows": regime_data},
            )
        ]
        return artifacts


class TimingSensitivityPlugin:
    """
    Checks if strategy performance is robust to start-date shifts.
    Generates 'timing_sensitivity' metric.
    """
    @property
    def name(self) -> str:
        return "timing_sensitivity"

    def run(self, run_spec: RunSpec) -> list[Artifact]:
        # Simulation
        seed = sum(ord(c) for c in run_spec.strategy.name) + 42
        rng = random.Random(seed)
        
        sensitivity = rng.random() * 0.8  # 0.0 to 0.8
        
        return [mk_metric("timing_sensitivity", sensitivity)]


class BasicMetricsPlugin:
    """
    Generates basic stub metrics like CAGR and Drawdown if missing.
    """
    @property
    def name(self) -> str:
        return "basic_metrics"

    def run(self, run_spec: RunSpec) -> list[Artifact]:
        return [
            mk_metric("cagr", 0.12),
            mk_metric("max_drawdown", -0.18),
        ]
